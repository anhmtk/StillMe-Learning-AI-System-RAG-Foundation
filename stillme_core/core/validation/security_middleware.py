"""
🛡️ SECURITY MIDDLEWARE

Security middleware for StillMe validation framework.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityThreat:
    """Represents a security threat"""

    threat_type: str
    severity: str
    description: str
    pattern: str
    confidence: float


class SecurityMiddleware:
    """
    Security middleware for input validation and threat detection
    """

    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.blocked_patterns = self._load_blocked_patterns()
        self.rate_limits = {}
        self.security_events = []

    def _load_threat_patterns(self) -> dict[str, list[str]]:
        """Load threat detection patterns"""
        return {
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
            ],
            "sql_injection": [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(--|\#|\/\*|\*\/)",
                r"(\b(WAITFOR|DELAY)\b)",
            ],
            "path_traversal": [
                r"\.\.\/",
                r"\.\.\\",
                r"\/etc\/passwd",
                r"\/windows\/system32",
                r"\/proc\/version",
            ],
            "command_injection": [
                r"[;&|`$]",
                r"\b(cat|ls|dir|type|more|less|head|tail|grep|find|awk|sed)\b",
                r"\b(ping|nslookup|tracert|traceroute)\b",
                r"\b(wget|curl|nc|netcat)\b",
            ],
        }

    def _load_blocked_patterns(self) -> list[str]:
        """Load blocked patterns"""
        return [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"\.\.\/",
            r"\.\.\\",
            r"[;&|`$]",
            r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b",
        ]

    def validate_input(self, input_data: str) -> dict[str, Any]:
        """Validate input for security threats"""
        if not isinstance(input_data, str):
            return {
                "is_valid": False,
                "threats_detected": ["Invalid input type"],
                "sanitized_input": "",
                "validation_timestamp": datetime.now().isoformat(),
            }

        threats_detected = []
        sanitized_input = input_data

        # Check for threats
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    threats_detected.append(f"{threat_type}: {pattern}")

        # Sanitize input
        for pattern in self.blocked_patterns:
            sanitized_input = re.sub(pattern, "", sanitized_input, flags=re.IGNORECASE)

        # Log security event
        if threats_detected:
            self._log_security_event(
                "input_validation",
                "HIGH",
                {
                    "threats_detected": threats_detected,
                    "original_input": input_data,
                    "sanitized_input": sanitized_input,
                },
            )

        return {
            "is_valid": len(threats_detected) == 0,
            "threats_detected": threats_detected,
            "sanitized_input": sanitized_input,
            "validation_timestamp": datetime.now().isoformat(),
        }

    def check_rate_limit(
        self, identifier: str, limit: int = 100, window: int = 3600
    ) -> bool:
        """Check if rate limit is exceeded"""
        current_time = datetime.now()

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Clean old entries
        self.rate_limits[identifier] = [
            timestamp
            for timestamp in self.rate_limits[identifier]
            if (current_time - timestamp).total_seconds() < window
        ]

        # Check limit
        if len(self.rate_limits[identifier]) >= limit:
            self._log_security_event(
                "rate_limit_exceeded",
                "MEDIUM",
                {
                    "identifier": identifier,
                    "limit": limit,
                    "window": window,
                    "current_count": len(self.rate_limits[identifier]),
                },
            )
            return False

        # Add current request
        self.rate_limits[identifier].append(current_time)
        return True

    def _log_security_event(
        self, event_type: str, severity: str, details: dict[str, Any]
    ):
        """Log security event"""
        event = {
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.security_events.append(event)
        logger.warning(f"Security event: {event_type} - {severity} - {details}")

    def get_security_summary(self) -> dict[str, Any]:
        """Get security summary"""
        total_events = len(self.security_events)
        high_severity_events = sum(
            1 for e in self.security_events if e["severity"] == "HIGH"
        )
        medium_severity_events = sum(
            1 for e in self.security_events if e["severity"] == "MEDIUM"
        )
        low_severity_events = sum(
            1 for e in self.security_events if e["severity"] == "LOW"
        )

        return {
            "total_events": total_events,
            "high_severity_events": high_severity_events,
            "medium_severity_events": medium_severity_events,
            "low_severity_events": low_severity_events,
            "rate_limits_active": len(self.rate_limits),
            "last_event": self.security_events[-1]["timestamp"]
            if self.security_events
            else None,
            "recent_events": self.security_events[-10:] if self.security_events else [],
        }


def main():
    """Test the security middleware"""
    middleware = SecurityMiddleware()

    # Test input validation
    test_inputs = [
        "Hello world",
        "<script>alert('xss')</script>",
        "SELECT * FROM users",
        "../../etc/passwd",
        "cat /etc/passwd",
    ]

    print("🛡️ Security Middleware Test:")
    for test_input in test_inputs:
        result = middleware.validate_input(test_input)
        status = "✅" if result["is_valid"] else "❌"
        print(f"{status} Input: {test_input[:50]}...")
        if result["threats_detected"]:
            print(f"   Threats: {result['threats_detected']}")
        print(f"   Sanitized: {result['sanitized_input'][:50]}...")
        print()

    # Test rate limiting
    print("🚦 Rate Limiting Test:")
    for i in range(5):
        allowed = middleware.check_rate_limit("test_user", limit=3, window=60)
        print(f"Request {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")

    # Get security summary
    summary = middleware.get_security_summary()
    print("\n📊 Security Summary:")
    print(f"Total events: {summary['total_events']}")
    print(f"High severity: {summary['high_severity_events']}")
    print(f"Medium severity: {summary['medium_severity_events']}")
    print(f"Low severity: {summary['low_severity_events']}")


if __name__ == "__main__":
    main()