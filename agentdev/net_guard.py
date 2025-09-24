#!/usr/bin/env python3
"""
AgentDev Network Guard - SEAL-grade Egress Control
Implements egress allowlist, rate limiting, and content filtering for network requests.
"""

import asyncio
import aiohttp
import time
import logging
import yaml
import re
import ipaddress
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, deque

@dataclass
class NetworkRequest:
    """Network request structure"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    data: Optional[bytes] = None
    timeout: float = 30.0
    user_id: str = "unknown"
    job_id: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class NetworkResponse:
    """Network response structure"""
    success: bool
    status_code: Optional[int] = None
    content: Optional[bytes] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    blocked_reason: Optional[str] = None
    size_bytes: int = 0
    duration_ms: float = 0

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.requests_log = deque()  # For detailed tracking
    
    def is_allowed(self, user_id: str = "global") -> bool:
        """Check if request is allowed under rate limit"""
        current_time = time.time()
        
        # Refill tokens
        time_passed = current_time - self.last_update
        tokens_to_add = time_passed * self.requests_per_second
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = current_time
        
        # Clean old requests (keep last hour)
        hour_ago = current_time - 3600
        while self.requests_log and self.requests_log[0][0] < hour_ago:
            self.requests_log.popleft()
        
        # Check if we have tokens
        if self.tokens >= 1:
            self.tokens -= 1
            self.requests_log.append((current_time, user_id))
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        current_time = time.time()
        
        # Count requests in last minute/hour
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        last_minute = sum(1 for t, _ in self.requests_log if t > minute_ago)
        last_hour = len(self.requests_log)
        
        return {
            "tokens_available": int(self.tokens),
            "max_tokens": self.burst_size,
            "requests_per_second": self.requests_per_second,
            "requests_last_minute": last_minute,
            "requests_last_hour": last_hour
        }

class NetworkGuard:
    """SEAL-grade network egress control"""
    
    def __init__(self, policy_path: str = None):
        self.policy_path = policy_path or Path(__file__).parent / "policy" / "network_allowlist.yaml"
        self.policy = self._load_policy()
        self.rate_limiter = RateLimiter(
            requests_per_second=self.policy.get("rate_limit", {}).get("requests_per_second", 10.0),
            burst_size=self.policy.get("rate_limit", {}).get("burst_size", 20)
        )
        self.blocked_domains: Set[str] = set()
        self.blocked_ips: Set[str] = set() 
        self.request_log: List[Dict[str, Any]] = []
        
        # Initialize blocked lists
        self._load_blocked_lists()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load network policy"""
        try:
            with open(self.policy_path, 'r', encoding='utf-8') as f:
                policy = yaml.safe_load(f)
            self.logger.info(f"✅ Network policy loaded: {self.policy_path}")
            return policy
        except FileNotFoundError:
            self.logger.error(f"❌ Network policy file not found: {self.policy_path}")
            return self._default_policy()
        except yaml.YAMLError as e:
            self.logger.error(f"❌ Network policy invalid YAML: {e}")
            return self._default_policy()
    
    def _default_policy(self) -> Dict[str, Any]:
        """Default restrictive policy"""
        return {
            "allowed_domains": [],
            "allowed_schemes": ["https"],
            "blocked_domains": ["*"],  # Block all by default
            "content_limits": {
                "max_size_mb": 10,
                "max_redirects": 3
            },
            "rate_limit": {
                "requests_per_second": 5.0,
                "burst_size": 10
            }
        }
    
    def _load_blocked_lists(self):
        """Load additional blocked domains/IPs"""
        # Add policy-defined blocked domains
        for domain in self.policy.get("blocked_domains", []):
            self.blocked_domains.add(domain.lower())
        
        # Add policy-defined blocked IPs
        for ip in self.policy.get("blocked_ips", []):
            self.blocked_ips.add(ip)
    
    async def make_request(self, request: NetworkRequest) -> NetworkResponse:
        """Make a controlled network request"""
        start_time = time.time()
        
        try:
            # Validate request
            validation_result = self._validate_request(request)
            if not validation_result[0]:
                return NetworkResponse(
                    success=False,
                    blocked_reason=validation_result[1]
                )
            
            # Check rate limit
            if not self.rate_limiter.is_allowed(request.user_id):
                return NetworkResponse(
                    success=False,
                    blocked_reason="Rate limit exceeded"
                )
            
            # Make the actual request
            response = await self._execute_request(request)
            
            # Log request
            self._log_request(request, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Network request failed: {e}")
            return NetworkResponse(
                success=False,
                error=str(e)
            )
    
    def _validate_request(self, request: NetworkRequest) -> Tuple[bool, Optional[str]]:
        """Validate network request against policy"""
        try:
            parsed = urlparse(request.url)
            
            # Check scheme
            allowed_schemes = self.policy.get("allowed_schemes", ["https"])
            if parsed.scheme not in allowed_schemes:
                return False, f"Scheme '{parsed.scheme}' not allowed"
            
            # Check domain allowlist
            domain = parsed.hostname.lower() if parsed.hostname else ""
            allowed_domains = self.policy.get("allowed_domains", [])
            
            if allowed_domains:  # If allowlist exists, domain must be in it
                domain_allowed = False
                for allowed_domain in allowed_domains:
                    if allowed_domain == "*":  # Wildcard allows all
                        domain_allowed = True
                        break
                    elif allowed_domain.startswith("*."):  # Subdomain wildcard
                        parent_domain = allowed_domain[2:]
                        if domain == parent_domain or domain.endswith("." + parent_domain):
                            domain_allowed = True
                            break
                    elif domain == allowed_domain:
                        domain_allowed = True
                        break
                
                if not domain_allowed:
                    return False, f"Domain '{domain}' not in allowlist"
            
            # Check domain blocklist
            if domain in self.blocked_domains or "*" in self.blocked_domains:
                return False, f"Domain '{domain}' is blocked"
            
            # Check for malicious patterns
            malicious_patterns = [
                r"localhost",
                r"127\.0\.0\.1",
                r"192\.168\.",
                r"10\.",
                r"172\.(1[6-9]|2[0-9]|3[01])\.",  # Private network ranges
                r"169\.254\.",  # Link-local
                r"::1",  # IPv6 localhost
                r"metadata\.google\.internal",  # Cloud metadata
                r"169\.254\.169\.254"  # AWS metadata
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, request.url, re.IGNORECASE):
                    return False, f"URL matches blocked pattern: {pattern}"
            
            # Check for IP addresses (should use domains)
            try:
                ipaddress.ip_address(domain)
                return False, "Direct IP access not allowed, use domain names"
            except ValueError:
                pass  # Not an IP, good
            
            # Check URL length
            max_url_length = self.policy.get("content_limits", {}).get("max_url_length", 2000)
            if len(request.url) > max_url_length:
                return False, f"URL too long (max {max_url_length})"
            
            return True, None
            
        except Exception as e:
            return False, f"URL validation error: {e}"
    
    async def _execute_request(self, request: NetworkRequest) -> NetworkResponse:
        """Execute the actual network request"""
        max_size = self.policy.get("content_limits", {}).get("max_size_mb", 10) * 1024 * 1024
        max_redirects = self.policy.get("content_limits", {}).get("max_redirects", 3)
        
        connector = aiohttp.TCPConnector(
            limit=10,  # Connection pool size
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=request.timeout)
        
        try:
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "AgentDev-NetworkGuard/1.0"}
            ) as session:
                
                async with session.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    data=request.data,
                    max_redirects=max_redirects,
                    allow_redirects=True
                ) as response:
                    
                    # Check content size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size:
                        return NetworkResponse(
                            success=False,
                            blocked_reason=f"Content too large: {content_length} bytes (max {max_size})"
                        )
                    
                    # Read content with size limit
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        content.extend(chunk)
                        if len(content) > max_size:
                            return NetworkResponse(
                                success=False,
                                blocked_reason=f"Content exceeded size limit during streaming"
                            )
                    
                    return NetworkResponse(
                        success=True,
                        status_code=response.status,
                        content=bytes(content),
                        headers=dict(response.headers),
                        size_bytes=len(content)
                    )
                    
        except asyncio.TimeoutError:
            return NetworkResponse(
                success=False,
                error="Request timeout"
            )
        except aiohttp.ClientError as e:
            return NetworkResponse(
                success=False,
                error=f"Client error: {e}"
            )
    
    def _log_request(self, request: NetworkRequest, response: NetworkResponse, duration: float):
        """Log network request for audit"""
        log_entry = {
            "timestamp": request.timestamp,
            "url": request.url,
            "method": request.method,
            "user_id": request.user_id,
            "job_id": request.job_id,
            "success": response.success,
            "status_code": response.status_code,
            "size_bytes": response.size_bytes,
            "duration_ms": duration * 1000,
            "blocked_reason": response.blocked_reason,
            "error": response.error
        }
        
        self.request_log.append(log_entry)
        
        # Keep only last 1000 requests
        if len(self.request_log) > 1000:
            self.request_log = self.request_log[-1000:]
        
        # Log to file
        if response.success:
            self.logger.info(f"🌐 Network request: {request.method} {request.url} -> {response.status_code} ({response.size_bytes} bytes)")
        else:
            self.logger.warning(f"🚫 Network request blocked: {request.url} -> {response.blocked_reason or response.error}")
    
    def add_allowed_domain(self, domain: str) -> bool:
        """Dynamically add domain to allowlist"""
        try:
            # Validate domain format
            if not domain or "." not in domain:
                return False
            
            allowed_domains = self.policy.setdefault("allowed_domains", [])
            if domain not in allowed_domains:
                allowed_domains.append(domain.lower())
                self.logger.info(f"✅ Added domain to allowlist: {domain}")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to add domain: {e}")
            return False
    
    def remove_allowed_domain(self, domain: str) -> bool:
        """Remove domain from allowlist"""
        try:
            allowed_domains = self.policy.get("allowed_domains", [])
            if domain.lower() in allowed_domains:
                allowed_domains.remove(domain.lower())
                self.logger.info(f"🗑️ Removed domain from allowlist: {domain}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to remove domain: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network guard statistics"""
        total_requests = len(self.request_log)
        if total_requests == 0:
            return {"total_requests": 0}
        
        successful = sum(1 for r in self.request_log if r["success"])
        blocked = sum(1 for r in self.request_log if r["blocked_reason"])
        errors = sum(1 for r in self.request_log if r["error"])
        
        total_bytes = sum(r["size_bytes"] for r in self.request_log if r["success"])
        avg_duration = sum(r["duration_ms"] for r in self.request_log if r["success"]) / max(successful, 1)
        
        # Rate limiter stats
        rate_stats = self.rate_limiter.get_stats()
        
        return {
            "total_requests": total_requests,
            "successful": successful,
            "blocked": blocked,
            "errors": errors,
            "success_rate": successful / total_requests * 100,
            "total_bytes_transferred": total_bytes,
            "average_duration_ms": avg_duration,
            "rate_limiter": rate_stats,
            "allowed_domains": len(self.policy.get("allowed_domains", [])),
            "blocked_domains": len(self.blocked_domains)
        }
    
    def get_recent_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent network requests for monitoring"""
        return self.request_log[-limit:]

# Example usage and testing
if __name__ == "__main__":
    async def test_network_guard():
        # Create network guard
        guard = NetworkGuard()
        
        # Add some allowed domains for testing
        guard.add_allowed_domain("httpbin.org")
        guard.add_allowed_domain("jsonplaceholder.typicode.com")
        
        # Test cases
        test_requests = [
            # Allowed domain
            NetworkRequest(
                url="https://httpbin.org/get",
                user_id="test_user"
            ),
            
            # Blocked scheme
            NetworkRequest(
                url="http://httpbin.org/get",
                user_id="test_user"
            ),
            
            # Blocked domain
            NetworkRequest(
                url="https://malicious-site.com/data",
                user_id="test_user"
            ),
            
            # Private IP attempt
            NetworkRequest(
                url="https://192.168.1.1/admin",
                user_id="test_user"
            ),
            
            # Localhost attempt
            NetworkRequest(
                url="https://localhost:8080/api",
                user_id="test_user"
            )
        ]
        
        print("🔒 Network Guard Testing")
        print("=" * 50)
        
        for i, request in enumerate(test_requests, 1):
            print(f"\nTest {i}: {request.url}")
            response = await guard.make_request(request)
            print(f"Success: {response.success}")
            if not response.success:
                print(f"Blocked: {response.blocked_reason or response.error}")
            else:
                print(f"Status: {response.status_code}, Size: {response.size_bytes} bytes")
        
        print(f"\n📊 Statistics:")
        stats = guard.get_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
    
    # Run the test
    asyncio.run(test_network_guard())
