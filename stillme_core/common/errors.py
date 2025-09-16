#!/usr/bin/env python3
"""
⚠️ ERROR HANDLING - UNIFIED EXCEPTION SYSTEM
⚠️ XỬ LÝ LỖI - HỆ THỐNG EXCEPTION THỐNG NHẤT

PURPOSE / MỤC ĐÍCH:
- Unified exception handling system for StillMe modules
- Hệ thống xử lý exception thống nhất cho các modules StillMe
- Structured error responses with context
- Phản hồi lỗi có cấu trúc với context
- Error categorization and recovery strategies
- Phân loại lỗi và chiến lược phục hồi

FUNCTIONALITY / CHỨC NĂNG:
- Custom exception hierarchy
- Hệ thống phân cấp exception tùy chỉnh
- Error context and metadata
- Context và metadata lỗi
- Recovery strategy suggestions
- Gợi ý chiến lược phục hồi
- Integration with logging system
- Tích hợp với hệ thống logging

RELATED FILES / FILES LIÊN QUAN:
- common/logging.py - Error logging integration
- modules/* - Module error handling
- framework.py - Framework error handling
- stable_ai_server.py - Server error handling

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Exception chaining for better debugging
- Error codes for programmatic handling
- Structured error responses for APIs
- Integration with monitoring systems
"""

import traceback
import uuid
from datetime import datetime
from typing import Any, Dict


class StillMeException(Exception):
    """
    Base exception class for StillMe framework
    Lớp exception cơ sở cho framework StillMe
    """

    def __init__(
        self,
        message: str,
        error_code: str = None,
        context: Dict[str, Any] = None,
        recoverable: bool = True,
        suggested_action: str = None,
    ):
        """
        Initialize StillMe exception

        Args:
            message: Error message
            error_code: Unique error code for programmatic handling
            context: Additional context information
            recoverable: Whether this error is recoverable
            suggested_action: Suggested action for recovery
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.recoverable = recoverable
        self.suggested_action = suggested_action
        self.timestamp = datetime.now()
        self.error_id = str(uuid.uuid4())
        self.traceback = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "exception_type": self.__class__.__name__,
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message} (Code: {self.error_code})"


class StillMeError(StillMeException):
    """General StillMe error"""

    pass


class StillMeWarning(StillMeException):
    """StillMe warning (non-fatal)"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, recoverable=True, **kwargs)


class ConfigurationError(StillMeError):
    """Configuration-related errors"""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        context = kwargs.get("context", {})
        if config_key:
            context["config_key"] = config_key
        kwargs["context"] = context
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class ModuleError(StillMeError):
    """Module-related errors"""

    def __init__(self, message: str, module_name: str = None, **kwargs):
        context = kwargs.get("context", {})
        if module_name:
            context["module_name"] = module_name
        kwargs["context"] = context
        super().__init__(message, error_code="MODULE_ERROR", **kwargs)


class APIError(StillMeError):
    """API-related errors"""

    def __init__(
        self, message: str, status_code: int = None, endpoint: str = None, **kwargs
    ):
        context = kwargs.get("context", {})
        if status_code:
            context["status_code"] = status_code
        if endpoint:
            context["endpoint"] = endpoint
        kwargs["context"] = context
        super().__init__(message, error_code="API_ERROR", **kwargs)


class SecurityError(StillMeError):
    """Security-related errors"""

    def __init__(self, message: str, security_level: str = None, **kwargs):
        context = kwargs.get("context", {})
        if security_level:
            context["security_level"] = security_level
        kwargs["context"] = context
        kwargs["recoverable"] = False  # Security errors are typically not recoverable
        super().__init__(message, error_code="SECURITY_ERROR", **kwargs)


class ValidationError(StillMeError):
    """Data validation errors"""

    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        context = kwargs.get("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)
        kwargs["context"] = context
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class NetworkError(StillMeError):
    """Network-related errors"""

    def __init__(self, message: str, url: str = None, timeout: float = None, **kwargs):
        context = kwargs.get("context", {})
        if url:
            context["url"] = url
        if timeout:
            context["timeout"] = timeout
        kwargs["context"] = context
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class TimeoutError(StillMeError):
    """Timeout-related errors"""

    def __init__(self, message: str, timeout_duration: float = None, **kwargs):
        context = kwargs.get("context", {})
        if timeout_duration:
            context["timeout_duration"] = timeout_duration
        kwargs["context"] = context
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)


class ResourceError(StillMeError):
    """Resource-related errors (memory, disk, etc.)"""

    def __init__(
        self,
        message: str,
        resource_type: str = None,
        current_usage: float = None,
        limit: float = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if resource_type:
            context["resource_type"] = resource_type
        if current_usage is not None:
            context["current_usage"] = current_usage
        if limit is not None:
            context["limit"] = limit
        kwargs["context"] = context
        super().__init__(message, error_code="RESOURCE_ERROR", **kwargs)


class AuthenticationError(SecurityError):
    """Authentication-related errors"""

    def __init__(self, message: str, user_id: str = None, **kwargs):
        context = kwargs.get("context", {})
        if user_id:
            context["user_id"] = user_id
        kwargs["context"] = context
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class AuthorizationError(SecurityError):
    """Authorization-related errors"""

    def __init__(
        self,
        message: str,
        user_id: str = None,
        required_permission: str = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if user_id:
            context["user_id"] = user_id
        if required_permission:
            context["required_permission"] = required_permission
        kwargs["context"] = context
        super().__init__(message, error_code="AUTHZ_ERROR", **kwargs)


class CircuitBreakerError(StillMeError):
    """Circuit breaker related errors"""

    def __init__(
        self,
        message: str,
        service_name: str = None,
        failure_count: int = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if service_name:
            context["service_name"] = service_name
        if failure_count is not None:
            context["failure_count"] = failure_count
        kwargs["context"] = context
        super().__init__(message, error_code="CIRCUIT_BREAKER_ERROR", **kwargs)


class ErrorHandler:
    """
    Centralized error handling and recovery
    Xử lý lỗi tập trung và phục hồi
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.error_counts = {}
        self.recovery_strategies = {}

    def handle_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle error and return structured response

        Args:
            error: Exception to handle
            context: Additional context

        Returns:
            Structured error response
        """
        if context is None:
            context = {}

        # Log error
        if self.logger:
            if isinstance(error, StillMeException):
                self.logger.error(
                    f"StillMe Error: {error.message}",
                    error_code=error.error_code,
                    error_id=error.error_id,
                    context=error.context,
                    **context,
                )
            else:
                self.logger.error(
                    f"Unexpected Error: {error!s}",
                    exception_type=type(error).__name__,
                    **context,
                )

        # Track error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Generate response
        if isinstance(error, StillMeException):
            response = error.to_dict()
        else:
            response = {
                "error_id": str(uuid.uuid4()),
                "error_code": "UNKNOWN_ERROR",
                "message": str(error),
                "context": context,
                "recoverable": True,
                "suggested_action": "Check logs for more details",
                "timestamp": datetime.now().isoformat(),
                "exception_type": error_type,
            }

        return response

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "unique_error_types": len(self.error_counts),
        }

    def reset_error_counts(self):
        """Reset error counts"""
        self.error_counts.clear()


class ErrorRecovery:
    """
    Error recovery strategies
    Chiến lược phục hồi lỗi
    """

    @staticmethod
    def retry_with_backoff(
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        exceptions: tuple = (Exception,),
    ):
        """
        Retry function with exponential backoff

        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            exceptions: Exceptions to catch and retry
        """
        import time

        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    raise e

    @staticmethod
    def fallback_response(
        error: StillMeException, fallback_data: Any = None
    ) -> Dict[str, Any]:
        """
        Generate fallback response for API errors

        Args:
            error: StillMe exception
            fallback_data: Fallback data to return

        Returns:
            Fallback response
        """
        return {
            "status": "error",
            "error": error.to_dict(),
            "fallback_data": fallback_data,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def suggest_recovery_action(error: StillMeException) -> str:
        """
        Suggest recovery action based on error type

        Args:
            error: StillMe exception

        Returns:
            Suggested recovery action
        """
        if error.suggested_action:
            return error.suggested_action

        # Default suggestions based on error type
        suggestions = {
            "CONFIG_ERROR": "Check configuration file and environment variables",
            "MODULE_ERROR": "Restart the module or check module dependencies",
            "API_ERROR": "Check API endpoint availability and authentication",
            "NETWORK_ERROR": "Check network connectivity and retry",
            "TIMEOUT_ERROR": "Increase timeout or optimize operation",
            "RESOURCE_ERROR": "Free up system resources or increase limits",
            "SECURITY_ERROR": "Review security policies and access controls",
            "VALIDATION_ERROR": "Check input data format and constraints",
        }

        return suggestions.get(error.error_code, "Check logs for more details")


# Convenience functions
def handle_error(
    error: Exception, logger=None, context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Handle error with default error handler"""
    handler = ErrorHandler(logger)
    return handler.handle_error(error, context)


def create_error_response(
    error: Exception, fallback_data: Any = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    if isinstance(error, StillMeException):
        return ErrorRecovery.fallback_response(error, fallback_data)
    else:
        return {
            "status": "error",
            "error": {
                "error_code": "UNKNOWN_ERROR",
                "message": str(error),
                "exception_type": type(error).__name__,
            },
            "fallback_data": fallback_data,
            "timestamp": datetime.now().isoformat(),
        }
