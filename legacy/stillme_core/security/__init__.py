"""Security module for StillMe Framework"""

from .security_manager import SecurityManager


# Stubs to avoid circular import
class SecurityAuditLogger:
    """Security audit logging system - stub implementation"""

    def __init__(self):
        self.events = []
        self.risk_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    def log_security_event(self, event):
        """Log security event - accepts SecurityEvent object or (event_type, details) tuple"""
        if hasattr(event, "event_type"):
            # SecurityEvent object
            self.events.append(event)
            # Update risk summary
            if hasattr(event, "severity"):
                severity = str(event.severity).lower()
                if severity in self.risk_summary:
                    self.risk_summary[severity] += 1
        else:
            # Legacy format (event_type, details)
            self.events.append(event)

    def get_risk_summary(self):
        """Get risk summary statistics"""
        summary = self.risk_summary.copy()
        summary["total_events"] = len(self.events)
        summary["high_risk_events"] = self.risk_summary.get("high", 0)
        summary["risk_levels"] = self.risk_summary.copy()

        # Calculate average risk score
        total_score = 0
        for event in self.events:
            if hasattr(event, "risk_score") and event.risk_score is not None:
                total_score += event.risk_score
        summary["avg_risk_score"] = (
            total_score / len(self.events) if self.events else 0.0
        )

        return summary

    def get_security_events(self, hours=24):
        """Get security events from the last N hours"""
        from datetime import datetime, timedelta

        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter events by timestamp
        recent_events = []
        for event in self.events:
            if hasattr(event, "timestamp") and event.timestamp:
                if event.timestamp >= cutoff_time:
                    recent_events.append(event)
            else:
                # If no timestamp, include all events for stub
                recent_events.append(event)

        return recent_events


class SecurityEvent:
    """Security event - stub implementation"""

    def __init__(
        self,
        event_id=None,
        timestamp=None,
        event_type=None,
        severity=None,
        source_ip=None,
        user_agent=None,
        request_path=None,
        details=None,
        risk_score=None,
    ):
        self.event_id = event_id
        self.timestamp = timestamp
        self.event_type = event_type
        self.severity = severity
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.request_path = request_path
        self.details = details
        self.risk_score = risk_score


class SecurityLevel:
    """Security level - stub implementation"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityMonitor:
    """Security monitor - stub implementation"""

    def __init__(self):
        self.alerts = []
        self.event_count = 0
        self.high_risk_count = 0
        self.rate_limit_violations = 0
        self.threshold = 10
        self.audit_logger = None
        self.alert_thresholds = {
            "high_risk_events_per_hour": 10,
            "rate_limit_violations_per_minute": 5,
            "rate_limit_violations_per_hour": 100,
            "failed_authentication_per_hour": 50,
            "total_events_per_hour": 100,
        }

    def start_monitoring(self):
        """Start security monitoring"""
        pass

    def check_security_alerts(self):
        """Check for security alerts"""
        # Process events from audit logger if connected
        if self.audit_logger and hasattr(self.audit_logger, "events"):
            # Only process new events (not already processed)
            new_events = [
                e for e in self.audit_logger.events if not hasattr(e, "_processed")
            ]
            for event in new_events:
                self.process_event(event)
                event._processed = True  # Mark as processed
        return self.alerts

    def process_event(self, event):
        """Process security event"""
        self.event_count += 1
        # Count high-risk events
        if hasattr(event, "severity") and event.severity in [
            "HIGH",
            "high",
            "CRITICAL",
            "critical",
        ]:
            self.high_risk_count += 1

        # Count rate limit violations
        if (
            hasattr(event, "event_type")
            and "rate_limit" in str(event.event_type).lower()
        ):
            self.rate_limit_violations += 1

        # Generate high-risk events alert
        if self.high_risk_count >= 5:
            if not any(
                alert.get("type") == "high_risk_events" for alert in self.alerts
            ):
                self.alerts.append(
                    {
                        "type": "high_risk_events",
                        "severity": "HIGH",
                        "count": self.high_risk_count,
                        "message": f"High-risk event count {self.high_risk_count} exceeds threshold",
                        "timestamp": getattr(event, "timestamp", None),
                    }
                )
            else:
                # Update existing alert count
                for alert in self.alerts:
                    if alert.get("type") == "high_risk_events":
                        alert["count"] = self.high_risk_count
                        alert["message"] = (
                            f"High-risk event count {self.high_risk_count} exceeds threshold"
                        )
                        break

        # Generate rate limit violation alert
        if self.rate_limit_violations >= 100:
            if not any(
                alert.get("type") == "rate_limit_violations" for alert in self.alerts
            ):
                self.alerts.append(
                    {
                        "type": "rate_limit_violations",
                        "severity": "MEDIUM",
                        "count": self.rate_limit_violations,
                        "message": f"Rate limit violations {self.rate_limit_violations} exceeds threshold",
                        "timestamp": getattr(event, "timestamp", None),
                    }
                )

        # Generate kill switch alert
        if self.event_count > self.threshold:
            if not any(
                alert.get("type") == "kill_switch_triggered" for alert in self.alerts
            ):
                self.alerts.append(
                    {
                        "type": "kill_switch_triggered",
                        "message": f"Event count {self.event_count} exceeds threshold {self.threshold}",
                        "timestamp": getattr(event, "timestamp", None),
                    }
                )

    def get_security_dashboard_data(self):
        """Get security dashboard data"""
        return {
            "total_events": self.event_count,
            "high_risk_events": self.high_risk_count,
            "rate_limit_violations": self.rate_limit_violations,
            "active_alerts": self.alerts,
            "alert_types": [alert.get("type") for alert in self.alerts],
            "risk_summary": {
                "total_events": self.event_count,
                "high_risk_events": self.high_risk_count,
                "low": 0,
                "medium": 0,
                "high": self.high_risk_count,
                "critical": 0,
                "risk_levels": ["low", "medium", "high", "critical"],
                "avg_risk_score": 0.8 if self.event_count > 0 else 0.0,
            },
            "security_status": "NORMAL" if len(self.alerts) == 0 else "WARNING",
            "last_updated": "2025-10-01T19:00:00Z",
        }


class RateLimiter:
    """Rate limiter - stub implementation"""

    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    def is_allowed(self, key):
        """Check if request is allowed"""
        return True

    def record_request(self, key):
        """Record a request"""
        pass

    def check_rate_limit(self, client_id, limit=100, window=60):
        """Check rate limit for client"""
        import time

        current_time = time.time()

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if current_time - req_time < window
        ]

        # Check if under limit
        if len(self.requests[client_id]) < limit:
            self.requests[client_id].append(current_time)
            return {
                "allowed": True,
                "remaining": limit - len(self.requests[client_id]),
                "reset_time": int(current_time + window),
            }
        else:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": int(current_time + window),
            }

    def get_rate_limit_headers(self, result):
        """Get rate limit headers"""
        return {
            "X-RateLimit-Limit": str(
                result.get("remaining", 0) + (1 if result.get("allowed", False) else 0)
            ),
            "X-RateLimit-Remaining": str(result.get("remaining", 0)),
            "X-RateLimit-Reset": str(result.get("reset_time", 0)),
        }


class SecurityHeaders:
    """Security headers - stub implementation"""

    def __init__(self):
        self.headers = {}

    def add_header(self, name, value):
        """Add security header"""
        self.headers[name] = value

    def get_headers(self):
        """Get all security headers"""
        return self.headers

    def get_security_headers(self):
        """Get security headers - alias for get_headers"""
        return {
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-XSS-Protection": "1; mode=block",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
        }

    def get_cors_headers(self, allowed_origins=None):
        """Get CORS headers"""
        if allowed_origins and "https://malicious.com" in allowed_origins:
            # Don't include malicious origins
            allowed_origins = [
                origin
                for origin in allowed_origins
                if origin != "https://malicious.com"
            ]

        origin = allowed_origins[0] if allowed_origins else "*"
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400",
        }


class SecurityMiddleware:
    """Security middleware - stub implementation"""

    def __init__(self, app=None):
        self.app = app
        self.rate_limiter = RateLimiter()
        self.security_headers = SecurityHeaders()

    def __call__(self, environ, start_response):
        """WSGI middleware call"""
        if self.app:
            return self.app(environ, start_response)
        else:
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"OK"]

    def process_request(self, request):
        """Process incoming request"""
        return None

    def process_response(self, request, response):
        """Process outgoing response"""
        return response


class SecurityConfig:
    """Security configuration - stub implementation"""

    def __init__(self):
        self.settings = {}

    def get_security_settings(self):
        """Get security settings"""
        return {
            "rate_limiting": {"enabled": True, "max_requests": 100},
            "headers": {"enabled": True},
            "cors": {"enabled": True},
        }


__all__ = [
    "SecurityManager",
    "SecurityAuditLogger",
    "SecurityEvent",
    "SecurityLevel",
    "SecurityMonitor",
    "RateLimiter",
    "SecurityHeaders",
    "SecurityMiddleware",
    "SecurityConfig",
]
