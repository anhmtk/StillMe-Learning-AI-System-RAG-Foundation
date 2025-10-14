"""
🛡️ SECURITY MIDDLEWARE

Middleware để implement security best practices và protect against common attacks.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import hashlib
import json
import logging
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

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
    details: dict[str, Any]
    action_taken: str


class SecurityMiddleware:
    """
    Security middleware for StillMe framework
    """

    def __init__(self, config_path: str = "config/security_config.json"):
        self.config = self._load_config(config_path)
        self.security_events: list[SecurityEvent] = []
        self.rate_limit_tracker: dict[str, list[datetime]] = {}
        self.blocked_ips: set[str] = set()
        self.csrf_tokens: dict[str, str] = {}

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load security configuration"""
        default_config = {
            "security": {
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                },
                "headers": {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                    "Content-Security-Policy": "default-src 'self'",
                },
                "input_validation": {
                    "enabled": True,
                    "max_length": 10000,
                    "blocked_patterns": [
                        r"<script.*?>.*?</script>",
                        r"javascript:",
                        r"on\w+\s*=",
                        r"eval\s*\(",
                        r"expression\s*\(",
                    ],
                },
                "logging": {
                    "enabled": True,
                    "log_file": "logs/security.log",
                    "max_events": 10000,
                },
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            logger.warning(f"Could not load security config: {e}")

        return default_config

    def check_rate_limit(self, client_ip: str, endpoint: str = "default") -> bool:
        """Check if client is within rate limit"""
        if not self.config["security"]["rate_limiting"]["enabled"]:
            return True

        now = datetime.now()
        key = f"{client_ip}:{endpoint}"

        if key not in self.rate_limit_tracker:
            self.rate_limit_tracker[key] = []

        # Clean old requests
        cutoff_time = now - timedelta(minutes=1)
        self.rate_limit_tracker[key] = [
            req_time
            for req_time in self.rate_limit_tracker[key]
            if req_time > cutoff_time
        ]

        # Check rate limit
        max_requests = self.config["security"]["rate_limiting"]["requests_per_minute"]
        if len(self.rate_limit_tracker[key]) >= max_requests:
            self._log_security_event(
                "rate_limit_exceeded",
                "medium",
                client_ip,
                "unknown",
                {"endpoint": endpoint, "requests": len(self.rate_limit_tracker[key])},
                "blocked",
            )
            return False

        # Add current request
        self.rate_limit_tracker[key].append(now)
        return True

    def validate_input(self, data: str) -> dict[str, Any]:
        """Validate and sanitize input data"""
        result = {"is_valid": True, "sanitized_data": data, "threats_detected": []}

        if not self.config["security"]["input_validation"]["enabled"]:
            return result

        # Check length
        max_length = self.config["security"]["input_validation"]["max_length"]
        if len(data) > max_length:
            result["is_valid"] = False
            result["threats_detected"].append("input_too_long")
            return result

        # Check for blocked patterns
        blocked_patterns = self.config["security"]["input_validation"][
            "blocked_patterns"
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                result["is_valid"] = False
                result["threats_detected"].append(f"blocked_pattern: {pattern}")
                break

        # Sanitize if valid
        if result["is_valid"]:
            result["sanitized_data"] = self._sanitize_input(data)

        return result

    def _sanitize_input(self, data: str) -> str:
        """Basic input sanitization"""
        # Remove null bytes
        data = data.replace("\x00", "")

        # Remove control characters except newlines and tabs
        data = "".join(char for char in data if ord(char) >= 32 or char in "\n\t")

        # Escape HTML entities
        data = data.replace("&", "&amp;")
        data = data.replace("<", "&lt;")
        data = data.replace(">", "&gt;")
        data = data.replace('"', "&quot;")
        data = data.replace("'", "&#x27;")

        return data

    def add_security_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Add security headers"""
        security_headers = self.config["security"]["headers"]
        headers.update(security_headers)
        return headers

    def _log_security_event(
        self,
        event_type: str,
        severity: str,
        source_ip: str,
        user_agent: str,
        details: dict[str, Any],
        action_taken: str,
    ):
        """Log security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details,
            action_taken=action_taken,
        )

        self.security_events.append(event)

        # Keep only recent events
        max_events = self.config["security"]["logging"]["max_events"]
        if len(self.security_events) > max_events:
            self.security_events = self.security_events[-max_events:]

        # Write to log file if enabled
        if self.config["security"]["logging"]["enabled"]:
            self._write_security_log(event)

        # Send alert for critical events
        if severity in ["high", "critical"]:
            self._send_security_alert(event)

    def _write_security_log(self, event: SecurityEvent):
        """Write security event to log file"""
        try:
            log_file = self.config["security"]["logging"]["log_file"]
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"{event.timestamp.isoformat()} | {event.event_type} | {event.severity} | {event.source_ip} | {event.action_taken}\n"
                )
        except Exception as e:
            logger.error(f"Error writing security log: {e}")

    def _send_security_alert(self, event: SecurityEvent):
        """Send security alert for critical events"""
        logger.warning(
            f"SECURITY ALERT: {event.event_type} from {event.source_ip} - {event.details}"
        )
        # In production, this would send alerts via email, Slack, etc.

    def check_ip_reputation(self, client_ip: str) -> bool:
        """Check if IP is in blocked list or has bad reputation"""
        return client_ip not in self.blocked_ips

    def block_ip(self, client_ip: str, reason: str = "security_violation"):
        """Block IP address"""
        self.blocked_ips.add(client_ip)
        self._log_security_event(
            "ip_blocked", "high", client_ip, "unknown", {"reason": reason}, "blocked"
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
            "sha256", password.encode(), salt.encode(), 100000
        )
        return f"{salt}:{password_hash.hex()}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = password_hash.split(":")
            password_hash_bytes = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt.encode(), 100000
            )
            return password_hash_bytes.hex() == hash_hex
        except Exception:
            return False

    def get_security_report(self) -> dict[str, Any]:
        """Get security report"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)

        recent_events = [e for e in self.security_events if e.timestamp > last_24h]

        return {
            "total_events": len(self.security_events),
            "recent_events_24h": len(recent_events),
            "blocked_ips": len(self.blocked_ips),
            "security_score": self._calculate_security_score(),
            "last_updated": now.isoformat(),
        }

    def _calculate_security_score(self) -> float:
        """Calculate security score based on recent events"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)

        recent_events = [e for e in self.security_events if e.timestamp > last_24h]

        if not recent_events:
            return 100.0

        # Calculate score based on severity
        score = 100.0
        for event in recent_events:
            if event.severity == "low":
                score -= 1
            elif event.severity == "medium":
                score -= 5
            elif event.severity == "high":
                score -= 15
            elif event.severity == "critical":
                score -= 30

        return max(0.0, score)


def main():
    """Test the security middleware"""
    middleware = SecurityMiddleware()

    # Test rate limiting
    print("Testing rate limiting...")
    for i in range(65):
        result = middleware.check_rate_limit("192.168.1.1")
        print(f"Request {i+1}: {'Allowed' if result else 'Blocked'}")

    # Test input validation
    print("\nTesting input validation...")
    test_inputs = [
        "Hello world",
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "A" * 10001,
    ]

    for test_input in test_inputs:
        result = middleware.validate_input(test_input)
        print(f"Input: {test_input[:50]}... -> Valid: {result['is_valid']}")

    # Test security report
    print("\nSecurity Report:")
    report = middleware.get_security_report()
    for key, value in report.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()