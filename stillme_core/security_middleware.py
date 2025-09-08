"""
🛡️ SECURITY MIDDLEWARE

Middleware để implement security best practices và protect against common attacks.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import os
import json
import time
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event log entry"""
    timestamp: datetime
    event_type: str
    severity: str
    source_ip: str
    user_agent: str
    details: Dict[str, Any]
    action_taken: str

class SecurityMiddleware:
    """
    Security middleware for StillMe framework
    """
    
    def __init__(self, config_path: str = "config/security_config.json"):
        self.config = self._load_config(config_path)
        self.security_events: List[SecurityEvent] = []
        self.rate_limit_tracker: Dict[str, List[datetime]] = {}
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union\s+select',  # SQL injection
            r'drop\s+table',  # SQL injection
            r'exec\s*\(',  # Command injection
            r'eval\s*\(',  # Code injection
            r'javascript:',  # XSS
            r'on\w+\s*=',  # XSS event handlers
        ]
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load security configuration"""
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading security config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default security configuration"""
        return {
            "security": {
                "rate_limiting": {
                    "enabled": True,
                    "default_limit": 100,
                    "window_size": 60
                },
                "headers": {
                    "x_frame_options": "DENY",
                    "x_content_type_options": "nosniff",
                    "x_xss_protection": "1; mode=block"
                },
                "input_validation": {
                    "enabled": True,
                    "max_string_length": 10000
                }
            }
        }
    
    def check_rate_limit(self, client_ip: str, endpoint: str = "default") -> bool:
        """Check if client is within rate limit"""
        if not self.config["security"]["rate_limiting"]["enabled"]:
            return True
        
        key = f"{client_ip}:{endpoint}"
        now = datetime.now()
        window_size = self.config["security"]["rate_limiting"]["window_size"]
        limit = self.config["security"]["rate_limiting"]["default_limit"]
        
        # Clean old requests
        if key in self.rate_limit_tracker:
            cutoff = now - timedelta(seconds=window_size)
            self.rate_limit_tracker[key] = [
                req_time for req_time in self.rate_limit_tracker[key] 
                if req_time > cutoff
            ]
        else:
            self.rate_limit_tracker[key] = []
        
        # Check limit
        if len(self.rate_limit_tracker[key]) >= limit:
            self._log_security_event(
                event_type="rate_limit_exceeded",
                severity="medium",
                source_ip=client_ip,
                details={"endpoint": endpoint, "limit": limit}
            )
            return False
        
        # Add current request
        self.rate_limit_tracker[key].append(now)
        return True
    
    def validate_input(self, data: str) -> Dict[str, Any]:
        """Validate and sanitize input data"""
        result = {
            "is_valid": True,
            "sanitized_data": data,
            "threats_detected": []
        }
        
        if not self.config["security"]["input_validation"]["enabled"]:
            return result
        
        # Check length
        max_length = self.config["security"]["input_validation"]["max_string_length"]
        if len(data) > max_length:
            result["is_valid"] = False
            result["threats_detected"].append("input_too_long")
            return result
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                result["threats_detected"].append(f"suspicious_pattern: {pattern}")
                result["is_valid"] = False
        
        # Basic sanitization
        if result["is_valid"]:
            result["sanitized_data"] = self._sanitize_input(data)
        
        return result
    
    def _sanitize_input(self, data: str) -> str:
        """Basic input sanitization"""
        # Remove null bytes
        data = data.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
        
        # HTML encode dangerous characters
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }
        
        for char, encoded in dangerous_chars.items():
            data = data.replace(char, encoded)
        
        return data
    
    def add_security_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add security headers"""
        security_headers = self.config["security"]["headers"]
        
        for header, value in security_headers.items():
            # Convert header name to proper format
            header_name = header.replace('_', '-').title()
            headers[header_name] = value
        
        return headers
    
    def _log_security_event(self, event_type: str, severity: str, 
                          source_ip: str, details: Dict[str, Any], 
                          action_taken: str = "logged"):
        """Log security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_agent="",  # Would be passed from request
            details=details,
            action_taken=action_taken
        )
        
        self.security_events.append(event)
        
        # Log to file
        self._write_security_log(event)
        
        # Alert on critical events
        if severity == "critical":
            self._send_security_alert(event)
    
    def _write_security_log(self, event: SecurityEvent):
        """Write security event to log file"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "security.log"
            
            log_entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "severity": event.severity,
                "source_ip": event.source_ip,
                "details": event.details,
                "action_taken": event.action_taken
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error writing security log: {e}")
    
    def _send_security_alert(self, event: SecurityEvent):
        """Send security alert for critical events"""
        logger.warning(f"🚨 CRITICAL SECURITY EVENT: {event.event_type} from {event.source_ip}")
        # In production, this would send alerts via email, Slack, etc.
    
    def check_ip_reputation(self, client_ip: str) -> bool:
        """Check if IP is in blocked list or has bad reputation"""
        return client_ip not in self.blocked_ips
    
    def block_ip(self, client_ip: str, reason: str = "security_violation"):
        """Block IP address"""
        self.blocked_ips.add(client_ip)
        self._log_security_event(
            event_type="ip_blocked",
            severity="high",
            source_ip=client_ip,
            details={"reason": reason},
            action_taken="ip_blocked"
        )
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return token == session_token and len(token) > 0
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return password_hash_check.hex() == hash_hex
        except Exception:
            return False
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security report"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events 
            if event.timestamp > last_24h
        ]
        
        event_counts = {}
        for event in recent_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        return {
            "timestamp": now.isoformat(),
            "total_events_24h": len(recent_events),
            "event_breakdown": event_counts,
            "blocked_ips": len(self.blocked_ips),
            "rate_limit_violations": event_counts.get("rate_limit_exceeded", 0),
            "security_score": self._calculate_security_score()
        }
    
    def _calculate_security_score(self) -> float:
        """Calculate security score based on recent events"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events 
            if event.timestamp > last_24h
        ]
        
        if not recent_events:
            return 100.0
        
        # Penalize based on event severity
        penalty = 0
        for event in recent_events:
            if event.severity == "critical":
                penalty += 10
            elif event.severity == "high":
                penalty += 5
            elif event.severity == "medium":
                penalty += 2
            else:
                penalty += 1
        
        return max(0, 100 - penalty)

# Security decorator for functions
def secure_endpoint(rate_limit: int = 100, require_auth: bool = True):
    """Decorator to secure API endpoints"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # This would be implemented with actual request context
            # For now, just return the function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def main():
    """Test security middleware"""
    middleware = SecurityMiddleware()
    
    # Test rate limiting
    print("Testing rate limiting...")
    for i in range(5):
        allowed = middleware.check_rate_limit("192.168.1.1", "test")
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
    
    # Test input validation
    print("\nTesting input validation...")
    test_inputs = [
        "Hello World",
        "<script>alert('xss')</script>",
        "SELECT * FROM users",
        "A" * 15000  # Too long
    ]
    
    for test_input in test_inputs:
        result = middleware.validate_input(test_input)
        print(f"Input: {test_input[:50]}...")
        print(f"Valid: {result['is_valid']}")
        print(f"Threats: {result['threats_detected']}")
        print()
    
    # Test security report
    print("Security Report:")
    report = middleware.get_security_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
