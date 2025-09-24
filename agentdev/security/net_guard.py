#!/usr/bin/env python3
"""
AgentDev Network Guard - SEAL-GRADE
Enterprise-grade network security and egress control
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
import yaml
import re
import ipaddress
import urllib.parse
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkAction(Enum):
    """Network actions"""
    ALLOW = "allow"
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    REDIRECT = "redirect"

class Protocol(Enum):
    """Network protocols"""
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SSH = "ssh"
    TCP = "tcp"
    UDP = "udp"

@dataclass
class NetworkRule:
    """Network access rule"""
    rule_id: str
    domain: str
    protocol: Protocol
    action: NetworkAction
    rate_limit: Optional[int] = None  # requests per minute
    max_size: Optional[int] = None    # max response size in bytes
    allowed_ports: List[int] = None
    redirect_url: Optional[str] = None
    description: str = ""
    enabled: bool = True

@dataclass
class NetworkRequest:
    """Network request being monitored"""
    request_id: str
    url: str
    method: str
    headers: Dict[str, str]
    user_id: str
    session_id: str
    timestamp: float
    size_bytes: int = 0
    response_code: Optional[int] = None
    response_size: Optional[int] = None

@dataclass
class NetworkDecision:
    """Decision made by network guard"""
    request_id: str
    allowed: bool
    action: NetworkAction
    reason: str
    timestamp: float
    rate_limited: bool = False
    redirect_url: Optional[str] = None
    max_size: Optional[int] = None

class NetworkGuard:
    """
    SEAL-GRADE Network Guard
    
    Enforces strict network security policies:
    - Domain allowlist/blocklist
    - Protocol restrictions
    - Rate limiting
    - Size limits
    - Redirect rules
    - Homoglyph/IDN protection
    - Audit logging
    """
    
    def __init__(self, policy_file: str = "agentdev/policy/network_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.rules: Dict[str, NetworkRule] = {}
        self.request_history: List[NetworkRequest] = []
        self.rate_limits: Dict[str, List[float]] = {}  # domain -> timestamps
        self.blocked_requests: Set[str] = set()
        
        # Load network policies
        self._load_policies()
        
        # Security patterns
        self.suspicious_patterns = [
            r"\.onion$",           # Tor domains
            r"\.bit$",             # Namecoin domains
            r"\.i2p$",             # I2P domains
            r"localhost",          # Local access
            r"127\.0\.0\.1",       # Localhost IP
            r"192\.168\.",         # Private network
            r"10\.",               # Private network
            r"172\.(1[6-9]|2[0-9]|3[0-1])\.",  # Private network
        ]
        
        # Homoglyph protection
        self.homoglyph_map = {
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x',
            'у': 'y', 'і': 'i', 'ј': 'j', 'ѕ': 's', 'ѡ': 'w', 'ѵ': 'v',
            'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z',
            'η': 'n', 'θ': 'o', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm',
            'ν': 'v', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's',
            'τ': 't', 'υ': 'u', 'φ': 'f', 'χ': 'x', 'ψ': 'p', 'ω': 'w'
        }
        
        logger.info("🛡️ Network Guard initialized with SEAL-GRADE security")
    
    def _load_policies(self):
        """Load network policies from YAML file"""
        if not self.policy_file.exists():
            self._create_default_policies()
            return
        
        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                policy_data = yaml.safe_load(f)
            
            for rule_id, rule_config in policy_data.get('rules', {}).items():
                self.rules[rule_id] = NetworkRule(
                    rule_id=rule_id,
                    domain=rule_config['domain'],
                    protocol=Protocol(rule_config['protocol']),
                    action=NetworkAction(rule_config['action']),
                    rate_limit=rule_config.get('rate_limit'),
                    max_size=rule_config.get('max_size'),
                    allowed_ports=rule_config.get('allowed_ports', []),
                    redirect_url=rule_config.get('redirect_url'),
                    description=rule_config.get('description', ''),
                    enabled=rule_config.get('enabled', True)
                )
            
            logger.info(f"✅ Loaded {len(self.rules)} network rules")
            
        except Exception as e:
            logger.error(f"❌ Failed to load network policies: {e}")
            self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default network policies"""
        default_rules = {
            "allow_https_common": NetworkRule(
                rule_id="allow_https_common",
                domain="*.google.com",
                protocol=Protocol.HTTPS,
                action=NetworkAction.ALLOW,
                rate_limit=60,
                max_size=10*1024*1024,  # 10MB
                allowed_ports=[443],
                description="Allow HTTPS to Google services"
            ),
            "allow_https_github": NetworkRule(
                rule_id="allow_https_github",
                domain="*.github.com",
                protocol=Protocol.HTTPS,
                action=NetworkAction.ALLOW,
                rate_limit=30,
                max_size=50*1024*1024,  # 50MB
                allowed_ports=[443],
                description="Allow HTTPS to GitHub"
            ),
            "allow_https_stackoverflow": NetworkRule(
                rule_id="allow_https_stackoverflow",
                domain="*.stackoverflow.com",
                protocol=Protocol.HTTPS,
                action=NetworkAction.ALLOW,
                rate_limit=20,
                max_size=5*1024*1024,   # 5MB
                allowed_ports=[443],
                description="Allow HTTPS to Stack Overflow"
            ),
            "block_http": NetworkRule(
                rule_id="block_http",
                domain="*",
                protocol=Protocol.HTTP,
                action=NetworkAction.BLOCK,
                description="Block all HTTP traffic"
            ),
            "block_private_networks": NetworkRule(
                rule_id="block_private_networks",
                domain="192.168.*",
                protocol=Protocol.HTTPS,
                action=NetworkAction.BLOCK,
                description="Block private network access"
            ),
            "block_localhost": NetworkRule(
                rule_id="block_localhost",
                domain="localhost",
                protocol=Protocol.HTTPS,
                action=NetworkAction.BLOCK,
                description="Block localhost access"
            )
        }
        
        self.rules = default_rules
        self._save_policies()
        logger.info("✅ Created default network policies")
    
    def _save_policies(self):
        """Save network policies to YAML file"""
        try:
            policy_data = {
                'rules': {
                    rule_id: {
                        'domain': rule.domain,
                        'protocol': rule.protocol.value,
                        'action': rule.action.value,
                        'rate_limit': rule.rate_limit,
                        'max_size': rule.max_size,
                        'allowed_ports': rule.allowed_ports,
                        'redirect_url': rule.redirect_url,
                        'description': rule.description,
                        'enabled': rule.enabled
                    }
                    for rule_id, rule in self.rules.items()
                }
            }
            
            with open(self.policy_file, 'w', encoding='utf-8') as f:
                yaml.dump(policy_data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save network policies: {e}")
    
    async def validate_request(self, url: str, method: str, headers: Dict[str, str],
                             user_id: str, session_id: str) -> NetworkDecision:
        """
        Validate network request against security policies
        
        SEAL-GRADE validation includes:
        - URL parsing and validation
        - Homoglyph detection
        - Domain allowlist/blocklist
        - Protocol restrictions
        - Rate limiting
        - Size limits
        - Redirect rules
        """
        request_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Create network request
        request = NetworkRequest(
            request_id=request_id,
            url=url,
            method=method,
            headers=headers,
            user_id=user_id,
            session_id=session_id,
            timestamp=timestamp
        )
        
        # 1. URL validation
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.hostname
            protocol = parsed_url.scheme.lower()
            port = parsed_url.port
        except Exception as e:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Invalid URL: {e}",
                timestamp=timestamp
            )
        
        if not domain:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason="No domain in URL",
                timestamp=timestamp
            )
        
        # 2. Homoglyph detection
        homoglyph_check = self._check_homoglyphs(domain)
        if not homoglyph_check["safe"]:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Homoglyph detected: {homoglyph_check['reason']}",
                timestamp=timestamp
            )
        
        # 3. Suspicious pattern detection
        suspicious_check = self._check_suspicious_patterns(domain)
        if suspicious_check["suspicious"]:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Suspicious pattern: {suspicious_check['reason']}",
                timestamp=timestamp
            )
        
        # 4. Find matching rule
        matching_rule = self._find_matching_rule(domain, protocol, port)
        if not matching_rule:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"No policy found for {protocol}://{domain}",
                timestamp=timestamp
            )
        
        # 5. Check if rule is enabled
        if not matching_rule.enabled:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Rule '{matching_rule.rule_id}' is disabled",
                timestamp=timestamp
            )
        
        # 6. Apply rule action
        if matching_rule.action == NetworkAction.BLOCK:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Blocked by rule '{matching_rule.rule_id}': {matching_rule.description}",
                timestamp=timestamp
            )
        
        # 7. Rate limiting check
        if matching_rule.rate_limit:
            rate_limited = not await self._check_rate_limit(domain, matching_rule.rate_limit)
            if rate_limited:
                return NetworkDecision(
                    request_id=request_id,
                    allowed=False,
                    action=NetworkAction.RATE_LIMIT,
                    reason=f"Rate limit exceeded for {domain}",
                    rate_limited=True,
                    timestamp=timestamp
                )
        
        # 8. Port validation
        if matching_rule.allowed_ports and port is not None and port not in matching_rule.allowed_ports:
            return NetworkDecision(
                request_id=request_id,
                allowed=False,
                action=NetworkAction.BLOCK,
                reason=f"Port {port} not allowed for {domain}",
                timestamp=timestamp
            )
        
        # 9. Redirect check
        if matching_rule.action == NetworkAction.REDIRECT and matching_rule.redirect_url:
            return NetworkDecision(
                request_id=request_id,
                allowed=True,
                action=NetworkAction.REDIRECT,
                reason=f"Redirected by rule '{matching_rule.rule_id}'",
                redirect_url=matching_rule.redirect_url,
                timestamp=timestamp
            )
        
        # 10. Allow request
        self._record_request(request)
        return NetworkDecision(
            request_id=request_id,
            allowed=True,
            action=NetworkAction.ALLOW,
            reason=f"Allowed by rule '{matching_rule.rule_id}'",
            max_size=matching_rule.max_size,
            timestamp=timestamp
        )
    
    def _check_homoglyphs(self, domain: str) -> Dict[str, Any]:
        """Check for homoglyph attacks"""
        # Convert to lowercase for comparison
        domain_lower = domain.lower()
        
        # Check for homoglyphs
        for homoglyph, normal in self.homoglyph_map.items():
            if homoglyph in domain_lower:
                return {
                    "safe": False,
                    "reason": f"Homoglyph '{homoglyph}' detected (should be '{normal}')"
                }
        
        return {"safe": True}
    
    def _check_suspicious_patterns(self, domain: str) -> Dict[str, Any]:
        """Check for suspicious domain patterns"""
        domain_lower = domain.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, domain_lower):
                return {
                    "suspicious": True,
                    "reason": f"Suspicious pattern: {pattern}"
                }
        
        return {"suspicious": False}
    
    def _find_matching_rule(self, domain: str, protocol: str, port: Optional[int]) -> Optional[NetworkRule]:
        """Find matching network rule"""
        protocol_enum = None
        try:
            protocol_enum = Protocol(protocol)
        except ValueError:
            return None
        
        # Check exact domain matches first
        for rule in self.rules.values():
            if rule.protocol == protocol_enum and rule.domain == domain:
                return rule
        
        # Check wildcard matches
        for rule in self.rules.values():
            if rule.protocol == protocol_enum:
                if rule.domain.startswith("*."):
                    # Wildcard subdomain
                    base_domain = rule.domain[2:]  # Remove "*."
                    if domain.endswith("." + base_domain) or domain == base_domain:
                        return rule
                elif rule.domain.endswith(".*"):
                    # Wildcard TLD
                    base_domain = rule.domain[:-2]  # Remove ".*"
                    if domain.startswith(base_domain + "."):
                        return rule
        
        # Check IP address matches
        try:
            ip = ipaddress.ip_address(domain)
            for rule in self.rules.values():
                if rule.protocol == protocol_enum and rule.domain == "*":
                    return rule
        except ValueError:
            pass
        
        # Check for default rule
        for rule in self.rules.values():
            if rule.protocol == protocol_enum and rule.domain == "*":
                return rule
        
        return None
    
    async def _check_rate_limit(self, domain: str, max_per_minute: int) -> bool:
        """Check if domain is within rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old timestamps
        if domain in self.rate_limits:
            self.rate_limits[domain] = [
                ts for ts in self.rate_limits[domain] if ts > minute_ago
            ]
        else:
            self.rate_limits[domain] = []
        
        # Check limit
        if len(self.rate_limits[domain]) >= max_per_minute:
            return False
        
        # Add current request
        self.rate_limits[domain].append(now)
        return True
    
    def _record_request(self, request: NetworkRequest):
        """Record network request in history"""
        self.request_history.append(request)
        
        # Keep only last 1000 requests
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
    
    async def update_request_response(self, request_id: str, response_code: int, 
                                    response_size: int):
        """Update request with response information"""
        for request in self.request_history:
            if request.request_id == request_id:
                request.response_code = response_code
                request.response_size = response_size
                break
    
    def get_request_history(self, limit: int = 100) -> List[NetworkRequest]:
        """Get recent network request history"""
        return self.request_history[-limit:]
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network security statistics"""
        total_requests = len(self.request_history)
        blocked_requests = len(self.blocked_requests)
        
        # Count by action
        action_counts = {}
        for request in self.request_history:
            # This would need to be tracked separately in a real implementation
            pass
        
        # Count by domain
        domain_counts = {}
        for request in self.request_history:
            try:
                domain = urlparse(request.url).hostname
                if domain:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            except:
                pass
        
        return {
            "total_requests": total_requests,
            "blocked_requests": blocked_requests,
            "requests_by_domain": dict(sorted(domain_counts.items(), 
                                            key=lambda x: x[1], reverse=True)[:10]),
            "rate_limits": {
                domain: len(timestamps) 
                for domain, timestamps in self.rate_limits.items()
            },
            "active_rules": len([r for r in self.rules.values() if r.enabled])
        }
    
    def add_rule(self, rule: NetworkRule):
        """Add new network rule"""
        self.rules[rule.rule_id] = rule
        self._save_policies()
        logger.info(f"✅ Added network rule: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str):
        """Remove network rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_policies()
            logger.info(f"✅ Removed network rule: {rule_id}")
    
    def enable_rule(self, rule_id: str):
        """Enable network rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            self._save_policies()
            logger.info(f"✅ Enabled network rule: {rule_id}")
    
    def disable_rule(self, rule_id: str):
        """Disable network rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self._save_policies()
            logger.info(f"✅ Disabled network rule: {rule_id}")

# Global network guard instance
network_guard = NetworkGuard()

# Convenience functions
async def validate_network_request(url: str, method: str, headers: Dict[str, str],
                                 user_id: str, session_id: str) -> NetworkDecision:
    """Validate network request"""
    return await network_guard.validate_request(url, method, headers, user_id, session_id)

def get_network_stats() -> Dict[str, Any]:
    """Get network security statistics"""
    return network_guard.get_network_stats()
