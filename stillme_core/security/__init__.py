"""Security module for StillMe Framework"""

from .security_manager import SecurityManager

# Stubs to avoid circular import
class SecurityAuditLogger:
    """Security audit logging system - stub implementation"""
    def __init__(self):
        pass

    def log_security_event(self, event_type, details):
        """Log security event"""
        pass

class SecurityEvent:
    """Security event - stub implementation"""
    def __init__(self, event_type, details):
        self.event_type = event_type
        self.details = details

class SecurityLevel:
    """Security level - stub implementation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityMonitor:
    """Security monitor - stub implementation"""
    def __init__(self):
        pass

    def start_monitoring(self):
        """Start security monitoring"""
        pass

class RateLimiter:
    """Rate limiter - stub implementation"""
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window

    def is_allowed(self, key):
        """Check if request is allowed"""
        return True

    def record_request(self, key):
        """Record a request"""
        pass

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

__all__ = [
    'SecurityManager',
    'SecurityAuditLogger',
    'SecurityEvent',
    'SecurityLevel',
    'SecurityMonitor',
    'RateLimiter',
    'SecurityHeaders'
]