"""
StillMe Security System
Implements OWASP ASVS compliance, security headers, rate limiting, and audit logging
"""

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    request_path: str
    details: dict[str, Any]
    risk_score: float

@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: int
    limit: int
    window: int

class SecurityHeaders:
    """Security headers implementation for OWASP ASVS compliance"""

    def __init__(self):
        self.headers = {}
        self._initialize_security_headers()

    def _initialize_security_headers(self):
        """Initialize security headers according to OWASP ASVS"""
        self.headers = {
            # Content Security Policy (CSP)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "media-src 'self'; "
                "object-src 'none'; "
                "child-src 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "base-uri 'self'"
            ),

            # HTTP Strict Transport Security (HSTS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

            # Content Type Options
            "X-Content-Type-Options": "nosniff",

            # Frame Options
            "X-Frame-Options": "DENY",

            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # XSS Protection
            "X-XSS-Protection": "1; mode=block",

            # Permissions Policy
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),

            # Additional security headers
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }

    def get_security_headers(self) -> dict[str, str]:
        """Get all security headers"""
        return self.headers.copy()

    def get_cors_headers(self, allowed_origins: Optional[list[str]] = None) -> dict[str, str]:
        """Get CORS headers"""
        if allowed_origins is None:
            allowed_origins = ["https://stillme.ai", "https://staging.stillme.ai"]

        return {
            "Access-Control-Allow-Origin": ", ".join(allowed_origins),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400",
            "Access-Control-Allow-Credentials": "true"
        }

    def get_custom_headers(self, custom_headers: dict[str, str]) -> dict[str, str]:
        """Get custom security headers"""
        return {**self.headers, **custom_headers}

class RateLimiter:
    """Rate limiting implementation"""

    def __init__(self):
        self.requests = {}  # Store request counts per client
        self.windows = {}   # Store window start times per client

    def check_rate_limit(self, client_id: str, limit: int = 100, window: int = 60) -> RateLimitResult:
        """Check if client is within rate limit"""
        current_time = time.time()

        # Initialize client data if not exists
        if client_id not in self.requests:
            self.requests[client_id] = 0
            self.windows[client_id] = current_time

        # Check if window has expired
        if current_time - self.windows[client_id] >= window:
            # Reset window
            self.requests[client_id] = 0
            self.windows[client_id] = current_time

        # Check rate limit
        if self.requests[client_id] >= limit:
            # Rate limit exceeded
            reset_time = int(self.windows[client_id] + window)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                limit=limit,
                window=window
            )

        # Increment request count
        self.requests[client_id] += 1

        # Calculate remaining requests
        remaining = limit - self.requests[client_id]
        reset_time = int(self.windows[client_id] + window)

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=reset_time,
            limit=limit,
            window=window
        )

    def get_rate_limit_headers(self, result: RateLimitResult) -> dict[str, str]:
        """Get rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_time)
        }

    def cleanup_expired_windows(self):
        """Clean up expired rate limit windows"""
        current_time = time.time()
        expired_clients = []

        for client_id, window_start in self.windows.items():
            if current_time - window_start >= 3600:  # 1 hour cleanup
                expired_clients.append(client_id)

        for client_id in expired_clients:
            del self.requests[client_id]
            del self.windows[client_id]

class SecurityAuditLogger:
    """Security audit logging system"""

    def __init__(self):
        self.events = []
        self.risk_thresholds = {
            SecurityLevel.LOW: 0.3,
            SecurityLevel.MEDIUM: 0.5,
            SecurityLevel.HIGH: 0.7,
            SecurityLevel.CRITICAL: 0.9
        }

    def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        self.events.append(event)

        # Log to file
        logger.warning(f"Security Event: {event.event_type} - {event.severity.value} - {event.details}")

        # Check for high-risk events
        if event.risk_score >= self.risk_thresholds[SecurityLevel.HIGH]:
            self._handle_high_risk_event(event)

    def _handle_high_risk_event(self, event: SecurityEvent):
        """Handle high-risk security events"""
        logger.critical(f"HIGH RISK EVENT: {event.event_type} - Risk Score: {event.risk_score}")

        # In a real implementation, this would trigger alerts
        # For now, we'll just log it
        if event.risk_score >= self.risk_thresholds[SecurityLevel.CRITICAL]:
            logger.critical("CRITICAL SECURITY EVENT - IMMEDIATE ATTENTION REQUIRED")

    def get_security_events(self, hours: int = 24) -> list[SecurityEvent]:
        """Get security events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [event for event in self.events if event.timestamp >= cutoff_time]

    def get_risk_summary(self) -> dict[str, Any]:
        """Get risk summary statistics"""
        if not self.events:
            return {"total_events": 0, "risk_levels": {}, "avg_risk_score": 0.0}

        risk_levels = {level.value: 0 for level in SecurityLevel}
        total_risk_score = 0.0

        for event in self.events:
            risk_levels[event.severity.value] += 1
            total_risk_score += event.risk_score

        avg_risk_score = total_risk_score / len(self.events)

        return {
            "total_events": len(self.events),
            "risk_levels": risk_levels,
            "avg_risk_score": avg_risk_score,
            "high_risk_events": len([e for e in self.events if e.risk_score >= 0.7])
        }

class SecurityMiddleware:
    """Security middleware for web framework integration"""

    def __init__(self):
        self.security_headers = SecurityHeaders()
        self.rate_limiter = RateLimiter()
        self.audit_logger = SecurityAuditLogger()

    def process_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Process incoming request for security checks"""
        client_id = self._get_client_id(request_data)

        # Check rate limit
        rate_limit_result = self.rate_limiter.check_rate_limit(client_id)

        if not rate_limit_result.allowed:
            # Log rate limit violation
            event = SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.now(),
                event_type="rate_limit_violation",
                severity=SecurityLevel.MEDIUM,
                source_ip=request_data.get("source_ip", "unknown"),
                user_agent=request_data.get("user_agent", "unknown"),
                request_path=request_data.get("path", "unknown"),
                details={"rate_limit_result": rate_limit_result.__dict__},
                risk_score=0.6
            )
            self.audit_logger.log_security_event(event)

            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "rate_limit_headers": self.rate_limiter.get_rate_limit_headers(rate_limit_result)
            }

        # Additional security checks can be added here
        return {
            "allowed": True,
            "rate_limit_headers": self.rate_limiter.get_rate_limit_headers(rate_limit_result)
        }

    def process_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Process outgoing response for security headers"""
        # Add security headers
        security_headers = self.security_headers.get_security_headers()

        if "headers" not in response_data:
            response_data["headers"] = {}

        response_data["headers"].update(security_headers)

        return response_data

    def _get_client_id(self, request_data: dict[str, Any]) -> str:
        """Get client identifier for rate limiting"""
        # Use IP address as client ID
        source_ip = request_data.get("source_ip", "unknown")
        user_agent = request_data.get("user_agent", "unknown")

        # Create a hash of IP + User Agent for better identification
        client_string = f"{source_ip}:{user_agent}"
        return hashlib.md5(client_string.encode()).hexdigest()

class SecurityConfig:
    """Security configuration management"""

    def __init__(self):
        self.config = {
            "headers": {
                "enabled": True,
                "csp_enabled": True,
                "hsts_enabled": True,
                "cors_enabled": True
            },
            "rate_limiting": {
                "enabled": True,
                "default_limit": 100,
                "default_window": 60,
                "burst_protection": True
            },
            "audit_logging": {
                "enabled": True,
                "log_level": "WARNING",
                "retention_days": 30
            },
            "cors": {
                "allowed_origins": ["https://stillme.ai", "https://staging.stillme.ai"],
                "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allowed_headers": ["Content-Type", "Authorization", "X-Requested-With"]
            }
        }

    def get_security_settings(self) -> dict[str, Any]:
        """Get security configuration settings"""
        return self.config.copy()

    def update_setting(self, section: str, key: str, value: Any):
        """Update a security setting"""
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
        else:
            logger.warning(f"Unknown security setting: {section}.{key}")

    def get_rate_limit_config(self) -> dict[str, Any]:
        """Get rate limiting configuration"""
        return self.config["rate_limiting"].copy()

    def get_cors_config(self) -> dict[str, Any]:
        """Get CORS configuration"""
        return self.config["cors"].copy()

class SecurityMonitor:
    """Security monitoring and alerting system"""

    def __init__(self):
        self.audit_logger = SecurityAuditLogger()
        self.alert_thresholds = {
            "high_risk_events_per_hour": 10,
            "rate_limit_violations_per_hour": 100,
            "failed_authentication_per_hour": 50
        }

    def check_security_alerts(self) -> list[dict[str, Any]]:
        """Check for security alerts based on recent events"""
        alerts = []
        recent_events = self.audit_logger.get_security_events(hours=1)

        # Check for high-risk events
        high_risk_events = [e for e in recent_events if e.risk_score >= 0.7]
        if len(high_risk_events) >= self.alert_thresholds["high_risk_events_per_hour"]:
            alerts.append({
                "type": "high_risk_events",
                "severity": "HIGH",
                "message": f"High risk events detected: {len(high_risk_events)}",
                "count": len(high_risk_events),
                "threshold": self.alert_thresholds["high_risk_events_per_hour"]
            })

        # Check for rate limit violations
        rate_limit_events = [e for e in recent_events if e.event_type == "rate_limit_violation"]
        if len(rate_limit_events) >= self.alert_thresholds["rate_limit_violations_per_hour"]:
            alerts.append({
                "type": "rate_limit_violations",
                "severity": "MEDIUM",
                "message": f"Rate limit violations detected: {len(rate_limit_events)}",
                "count": len(rate_limit_events),
                "threshold": self.alert_thresholds["rate_limit_violations_per_hour"]
            })

        return alerts

    def get_security_dashboard_data(self) -> dict[str, Any]:
        """Get data for security dashboard"""
        risk_summary = self.audit_logger.get_risk_summary()
        alerts = self.check_security_alerts()

        return {
            "risk_summary": risk_summary,
            "active_alerts": alerts,
            "security_status": "HEALTHY" if not alerts else "WARNING",
            "last_updated": datetime.now().isoformat()
        }
