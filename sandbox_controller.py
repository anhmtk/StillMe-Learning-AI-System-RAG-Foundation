#!/usr/bin/env python3
"""
StillMe Sandbox Controller - Enhanced Security
Kiểm soát truy cập internet với egress allowlist mạnh, redirect rules, và homoglyph protection
"""
import logging
import os
import re
import yaml
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple, Optional
from urllib.parse import urlparse, urljoin
from pathlib import Path
import idna  # For IDN/Punycode handling

logger = logging.getLogger(__name__)

class SandboxController:
    """Enhanced controller để kiểm soát sandbox và network access với bảo mật mạnh"""
    
    def __init__(self, config_file: str = "policies/network_allowlist.yaml"):
        # Load allowlist from config file
        self.config_file = Path(config_file)
        self.egress_allowlist = self._load_allowlist()
        
        # Network egress limit (0 = block all, -1 = unlimited)
        self.network_egress_limit = int(os.getenv("NETWORK_EGRESS_LIMIT", "10"))
        
        # Current egress count
        self.egress_count = 0
        
        # Blocked domains log
        self.blocked_domains: Set[str] = set()
        
        # Redirect tracking
        self.redirect_count = 0
        self.max_redirects = 3
        
        # Allowed schemes (only HTTPS)
        self.allowed_schemes = {"https"}
        
        # Homoglyph detection patterns
        self.homoglyph_patterns = [
            r'[а-я]',  # Cyrillic
            r'[α-ω]',  # Greek
            r'[０-９]',  # Full-width digits
            r'[ａ-ｚ]',  # Full-width letters
        ]
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "egress_limit_hit": 0,
            "scheme_blocked": 0,
            "homoglyph_blocked": 0,
            "redirect_blocked": 0,
            "idn_blocked": 0
        }
    
    def _load_allowlist(self) -> Set[str]:
        """Load allowlist from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    allowlist = set(config.get('allowed_domains', []))
                    logger.info(f"✅ Loaded {len(allowlist)} domains from {self.config_file}")
                    return allowlist
            else:
                # Fallback to default allowlist
                default_allowlist = {
                    "api.github.com",
                    "newsapi.org",
                    "gnews.io", 
                    "hn.algolia.com",
                    "trends.google.com",
                    "reddit.com",
                    "api.openrouter.ai",
                    "api.deepseek.com",
                    "api.openai.com",
                    "localhost",
                    "127.0.0.1"
                }
                logger.warning(f"⚠️ Config file {self.config_file} not found, using default allowlist")
                return default_allowlist
        except Exception as e:
            logger.error(f"❌ Failed to load allowlist: {e}")
            return {"localhost", "127.0.0.1"}  # Minimal safe fallback
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain to ASCII punycode"""
        try:
            # Convert IDN to punycode
            normalized = idna.encode(domain).decode('ascii')
            return normalized.lower()
        except Exception as e:
            logger.warning(f"⚠️ Failed to normalize domain {domain}: {e}")
            return domain.lower()
    
    def _detect_homoglyph(self, domain: str) -> bool:
        """Detect homoglyph characters in domain"""
        for pattern in self.homoglyph_patterns:
            if re.search(pattern, domain):
                return True
        return False
    
    def _validate_scheme(self, scheme: str) -> bool:
        """Validate URL scheme"""
        return scheme.lower() in self.allowed_schemes
    
    def is_egress_allowed(self, url: str, redirect_count: int = 0) -> Dict[str, Any]:
        """Enhanced egress permission check with security validations"""
        try:
            self.stats["total_requests"] += 1
            
            # Parse URL
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            domain = parsed.netloc.lower()
            
            # Check scheme (only HTTPS allowed)
            if not self._validate_scheme(scheme):
                self.stats["blocked_requests"] += 1
                self.stats["scheme_blocked"] += 1
                
                logger.warning(f"🚫 Egress blocked: scheme {scheme} not allowed")
                return {
                    "allowed": False,
                    "reason": f"Scheme {scheme} not allowed (only HTTPS)",
                    "domain": domain,
                    "block_type": "scheme"
                }
            
            # Check for homoglyph characters
            if self._detect_homoglyph(domain):
                self.stats["blocked_requests"] += 1
                self.stats["homoglyph_blocked"] += 1
                
                logger.warning(f"🚫 Egress blocked: homoglyph detected in {domain}")
                return {
                    "allowed": False,
                    "reason": f"Homoglyph characters detected in domain {domain}",
                    "domain": domain,
                    "block_type": "homoglyph"
                }
            
            # Normalize domain to ASCII
            normalized_domain = self._normalize_domain(domain)
            
            # Check if normalized domain is in allowlist
            if normalized_domain not in self.egress_allowlist:
                self.stats["blocked_requests"] += 1
                self.blocked_domains.add(domain)
                
                logger.warning(f"🚫 Egress blocked: {normalized_domain} not in allowlist")
                return {
                    "allowed": False,
                    "reason": f"Domain {normalized_domain} not in egress allowlist",
                    "domain": normalized_domain,
                    "block_type": "allowlist"
                }
            
            # Check redirect limit
            if redirect_count > self.max_redirects:
                self.stats["blocked_requests"] += 1
                self.stats["redirect_blocked"] += 1
                
                logger.warning(f"🚫 Egress blocked: too many redirects ({redirect_count})")
                return {
                    "allowed": False,
                    "reason": f"Too many redirects ({redirect_count} > {self.max_redirects})",
                    "domain": normalized_domain,
                    "block_type": "redirect"
                }
            
            # Check egress limit
            if self.network_egress_limit > 0 and self.egress_count >= self.network_egress_limit:
                self.stats["egress_limit_hit"] += 1
                
                logger.warning(f"🚫 Egress blocked: limit reached ({self.egress_count}/{self.network_egress_limit})")
                return {
                    "allowed": False,
                    "reason": f"Egress limit reached ({self.egress_count}/{self.network_egress_limit})",
                    "domain": normalized_domain,
                    "block_type": "limit"
                }
            
            # Allow the request
            self.stats["allowed_requests"] += 1
            self.egress_count += 1
            
            logger.info(f"✅ Egress allowed: {normalized_domain}")
            return {
                "allowed": True,
                "domain": normalized_domain,
                "egress_count": self.egress_count,
                "redirect_count": redirect_count
            }
            
        except Exception as e:
            logger.error(f"❌ Egress check error: {e}")
            return {
                "allowed": False,
                "reason": f"Egress check failed: {str(e)}",
                "domain": "unknown",
                "block_type": "error"
            }
    
    def add_to_allowlist(self, domain: str) -> bool:
        """Thêm domain vào allowlist"""
        try:
            domain = domain.lower().strip()
            if domain:
                self.egress_allowlist.add(domain)
                logger.info(f"✅ Added domain to allowlist: {domain}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to add domain to allowlist: {e}")
            return False
    
    def remove_from_allowlist(self, domain: str) -> bool:
        """Xóa domain khỏi allowlist"""
        try:
            domain = domain.lower().strip()
            if domain in self.egress_allowlist:
                self.egress_allowlist.remove(domain)
                logger.info(f"✅ Removed domain from allowlist: {domain}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to remove domain from allowlist: {e}")
            return False
    
    def get_allowlist(self) -> List[str]:
        """Lấy danh sách allowlist"""
        return sorted(list(self.egress_allowlist))
    
    def get_blocked_domains(self) -> List[str]:
        """Lấy danh sách domains đã bị block"""
        return sorted(list(self.blocked_domains))
    
    def set_egress_limit(self, limit: int):
        """Set egress limit"""
        self.network_egress_limit = limit
        logger.info(f"✅ Egress limit set to: {limit}")
    
    def reset_egress_count(self):
        """Reset egress count"""
        self.egress_count = 0
        logger.info("✅ Egress count reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê sandbox chi tiết"""
        return {
            "total_requests": self.stats["total_requests"],
            "allowed_requests": self.stats["allowed_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "egress_limit_hit": self.stats["egress_limit_hit"],
            "scheme_blocked": self.stats["scheme_blocked"],
            "homoglyph_blocked": self.stats["homoglyph_blocked"],
            "redirect_blocked": self.stats["redirect_blocked"],
            "idn_blocked": self.stats["idn_blocked"],
            "current_egress_count": self.egress_count,
            "egress_limit": self.network_egress_limit,
            "allowlist_size": len(self.egress_allowlist),
            "blocked_domains_count": len(self.blocked_domains),
            "max_redirects": self.max_redirects,
            "allowed_schemes": list(self.allowed_schemes)
        }
    
    def validate_allowlist(self) -> Dict[str, Any]:
        """Validate allowlist configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "domains_checked": len(self.egress_allowlist)
        }
        
        for domain in self.egress_allowlist:
            try:
                # Check if domain is valid
                normalized = self._normalize_domain(domain)
                
                # Check for homoglyphs
                if self._detect_homoglyph(domain):
                    validation_results["warnings"].append(f"Domain {domain} contains homoglyph characters")
                
                # Check for suspicious patterns
                if re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', domain):
                    validation_results["warnings"].append(f"Domain {domain} appears to be an IP address")
                
            except Exception as e:
                validation_results["errors"].append(f"Domain {domain} validation failed: {e}")
                validation_results["valid"] = False
        
        return validation_results
    
    def reload_allowlist(self) -> bool:
        """Reload allowlist from config file"""
        try:
            old_allowlist = self.egress_allowlist.copy()
            self.egress_allowlist = self._load_allowlist()
            
            logger.info(f"✅ Allowlist reloaded: {len(old_allowlist)} -> {len(self.egress_allowlist)} domains")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reload allowlist: {e}")
            return False
    
    def set_max_redirects(self, max_redirects: int) -> None:
        """Set maximum redirect limit"""
        self.max_redirects = max(0, min(max_redirects, 10))  # Limit between 0-10
        logger.info(f"✅ Max redirects set to: {self.max_redirects}")
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report"""
        stats = self.get_stats()
        validation = self.validate_allowlist()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sandbox_status": {
                "enabled": self.is_sandbox_enabled(),
                "egress_limit": self.network_egress_limit,
                "current_count": self.egress_count,
                "max_redirects": self.max_redirects,
                "allowed_schemes": list(self.allowed_schemes)
            },
            "allowlist_status": {
                "size": len(self.egress_allowlist),
                "validation": validation,
                "domains": sorted(list(self.egress_allowlist))
            },
            "security_stats": stats,
            "blocked_domains": sorted(list(self.blocked_domains)),
            "recommendations": self._get_security_recommendations(stats)
        }
    
    def _get_security_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get security recommendations based on stats"""
        recommendations = []
        
        if stats["homoglyph_blocked"] > 0:
            recommendations.append("Consider reviewing homoglyph detection patterns")
        
        if stats["scheme_blocked"] > 0:
            recommendations.append("HTTP requests detected - ensure all traffic uses HTTPS")
        
        if stats["redirect_blocked"] > 0:
            recommendations.append("Redirect chains detected - review redirect policies")
        
        if stats["blocked_requests"] > stats["allowed_requests"] * 0.5:
            recommendations.append("High block rate - review allowlist configuration")
        
        return recommendations
    
    def is_sandbox_enabled(self) -> bool:
        """Kiểm tra xem sandbox có được bật không"""
        return self.network_egress_limit != 0
    
    def enable_sandbox(self):
        """Bật sandbox (block all egress)"""
        self.network_egress_limit = 0
        logger.info("🔒 Sandbox enabled - all egress blocked")
    
    def disable_sandbox(self):
        """Tắt sandbox (allow all egress)"""
        self.network_egress_limit = -1
        logger.info("🔓 Sandbox disabled - all egress allowed")
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái sandbox"""
        return {
            "enabled": self.is_sandbox_enabled(),
            "egress_limit": self.network_egress_limit,
            "current_count": self.egress_count,
            "allowlist": self.get_allowlist(),
            "blocked_domains": self.get_blocked_domains(),
            "stats": self.get_stats()
        }

# Global instance
sandbox_controller = SandboxController()

def check_egress_permission(url: str) -> Dict[str, Any]:
    """Convenience function để check egress permission"""
    return sandbox_controller.is_egress_allowed(url)

def is_sandbox_enabled() -> bool:
    """Convenience function để check sandbox status"""
    return sandbox_controller.is_sandbox_enabled()

if __name__ == "__main__":
    # Test sandbox controller
    print("🧪 Testing Sandbox Controller...")
    
    # Test allowed domains
    allowed_urls = [
        "https://api.github.com/search/repositories",
        "https://newsapi.org/v2/everything",
        "https://gnews.io/api/v4/search"
    ]
    
    print("\n✅ Testing allowed URLs:")
    for url in allowed_urls:
        result = sandbox_controller.is_egress_allowed(url)
        print(f"  {url}: {result['allowed']}")
    
    # Test blocked domains
    blocked_urls = [
        "https://malicious-site.com/evil",
        "https://phishing-site.net/steal",
        "https://unknown-domain.org/data"
    ]
    
    print("\n🚫 Testing blocked URLs:")
    for url in blocked_urls:
        result = sandbox_controller.is_egress_allowed(url)
        print(f"  {url}: {result['allowed']} - {result['reason']}")
    
    # Test egress limit
    print("\n🔢 Testing egress limit:")
    sandbox_controller.set_egress_limit(2)
    for i in range(4):
        result = sandbox_controller.is_egress_allowed("https://api.github.com/test")
        print(f"  Request {i+1}: {result['allowed']} (count: {result.get('egress_count', 'N/A')})")
    
    # Show stats
    stats = sandbox_controller.get_stats()
    print(f"\n📊 Sandbox Stats:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Allowed requests: {stats['allowed_requests']}")
    print(f"  Blocked requests: {stats['blocked_requests']}")
    print(f"  Egress limit hits: {stats['egress_limit_hit']}")
    print(f"  Current count: {stats['current_egress_count']}")
    print(f"  Allowlist size: {stats['allowlist_size']}")
    print(f"  Blocked domains: {stats['blocked_domains_count']}")
    
    # Show status
    status = sandbox_controller.get_status()
    print(f"\n🔍 Sandbox Status:")
    print(f"  Enabled: {status['enabled']}")
    print(f"  Egress limit: {status['egress_limit']}")
    print(f"  Allowlist: {len(status['allowlist'])} domains")
    print(f"  Blocked domains: {len(status['blocked_domains'])} domains")
