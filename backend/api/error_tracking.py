"""
Error Tracking and Monitoring for StillMe API
Optional Sentry integration for production error tracking
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Sentry (optional dependency)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.info("Sentry SDK not available - error tracking will use logging only")


class ErrorTracker:
    """Error tracking and monitoring service"""
    
    def __init__(self):
        self.sentry_enabled = False
        self._init_sentry()
    
    def _init_sentry(self):
        """Initialize Sentry if available and configured"""
        if not SENTRY_AVAILABLE:
            logger.info("Sentry SDK not installed - using logging only")
            return
        
        sentry_dsn = os.getenv("SENTRY_DSN")
        if not sentry_dsn:
            logger.info("SENTRY_DSN not set - error tracking disabled")
            return
        
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FastApiIntegration(),
                    LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
                ],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                environment=os.getenv("ENVIRONMENT", "development"),
                release=os.getenv("APP_VERSION", "unknown"),
                before_send=self._filter_sensitive_data
            )
            self.sentry_enabled = True
            logger.info("✅ Sentry error tracking initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")
    
    def _filter_sensitive_data(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter sensitive data from Sentry events"""
        # Remove sensitive fields
        if "request" in event:
            request = event["request"]
            # Remove headers that might contain sensitive info
            if "headers" in request:
                sensitive_headers = ["authorization", "x-api-key", "cookie"]
                for header in sensitive_headers:
                    request["headers"].pop(header, None)
        
        # Remove user data if present
        if "user" in event:
            # Keep only safe user info
            event["user"] = {"id": event["user"].get("id")}
        
        return event
    
    def capture_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture and track an exception"""
        # Log to standard logging
        logger.error(f"Exception captured: {exc}", exc_info=True, extra=context)
        
        # Send to Sentry if enabled
        if self.sentry_enabled and SENTRY_AVAILABLE:
            try:
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_extra(key, value)
                    sentry_sdk.capture_exception(exc)
            except Exception as e:
                logger.warning(f"Failed to send exception to Sentry: {e}")
    
    def capture_message(self, message: str, level: str = "error", context: Optional[Dict[str, Any]] = None):
        """Capture and track a message"""
        # Log to standard logging
        log_level = getattr(logging, level.upper(), logging.ERROR)
        logger.log(log_level, message, extra=context)
        
        # Send to Sentry if enabled
        if self.sentry_enabled and SENTRY_AVAILABLE:
            try:
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_extra(key, value)
                    sentry_level = getattr(sentry_sdk, level.upper(), sentry_sdk.Severity.ERROR)
                    sentry_sdk.capture_message(message, level=sentry_level)
            except Exception as e:
                logger.warning(f"Failed to send message to Sentry: {e}")
    
    def set_user_context(self, user_id: Optional[str] = None, username: Optional[str] = None):
        """Set user context for error tracking"""
        if self.sentry_enabled and SENTRY_AVAILABLE:
            try:
                sentry_sdk.set_user({
                    "id": user_id,
                    "username": username
                })
            except Exception as e:
                logger.warning(f"Failed to set Sentry user context: {e}")
    
    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info", data: Optional[Dict[str, Any]] = None):
        """Add breadcrumb for debugging"""
        if self.sentry_enabled and SENTRY_AVAILABLE:
            try:
                sentry_sdk.add_breadcrumb(
                    message=message,
                    category=category,
                    level=getattr(sentry_sdk.Severity, level.upper(), sentry_sdk.Severity.INFO),
                    data=data or {}
                )
            except Exception as e:
                logger.warning(f"Failed to add Sentry breadcrumb: {e}")


# Global error tracker instance
error_tracker = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance"""
    return error_tracker

