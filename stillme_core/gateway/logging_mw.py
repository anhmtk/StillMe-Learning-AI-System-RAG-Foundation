"""
Logging Middleware for Enterprise Audit & Privacy
================================================

Provides structured JSON logging with PII redaction, correlation IDs,
and comprehensive audit trails for enterprise compliance.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import hashlib
import json
import logging
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from ..privacy.pii_redactor import PIIRedactor

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id')
user_id_var: ContextVar[str] = ContextVar('user_id')
trace_id_var: ContextVar[str] = ContextVar('trace_id')
span_id_var: ContextVar[str] = ContextVar('span_id')


@dataclass
class LogEntry:
    """Structured log entry with all required fields"""
    timestamp: str
    level: str
    trace_id: str
    span_id: str
    user_id_hash: str
    event: str
    pii_redacted: bool
    message: str
    metadata: Optional[dict[str, Any]] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


class StructuredLogger:
    """
    Enterprise-grade structured logger with PII redaction

    Features:
    - JSON structured logging
    - PII redaction for all log content
    - Correlation ID tracking
    - User ID hashing
    - Performance metrics
    - Audit trail compliance
    """

    def __init__(self, name: str, config: Optional[dict] = None):
        """Initialize structured logger"""
        self.name = name
        self.config = config or {}
        self.pii_redactor = PIIRedactor(self.config.get('pii_config', {}))
        self.logger = logging.getLogger(name)

        # Configure logging level
        log_level = self.config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Add console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _get_context(self) -> dict[str, str]:
        """Get current request context"""
        return {
            'request_id': request_id_var.get(''),
            'user_id': user_id_var.get(''),
            'trace_id': trace_id_var.get(''),
            'span_id': span_id_var.get(''),
        }

    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy"""
        if not user_id:
            return ''
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    def _redact_content(self, content: str) -> tuple[str, bool]:
        """Redact PII from content and return (redacted_content, was_redacted)"""
        if not content:
            return content, False

        redacted, matches = self.pii_redactor.redact(content)
        was_redacted = len(matches) > 0
        return redacted, was_redacted

    def _create_log_entry(
        self,
        level: str,
        event: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> LogEntry:
        """Create structured log entry"""
        context = self._get_context()

        # Redact message content
        redacted_message, pii_redacted = self._redact_content(message)

        # Redact metadata if present
        redacted_metadata = None
        if metadata:
            redacted_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, str):
                    redacted_value, _ = self._redact_content(value)
                    redacted_metadata[key] = redacted_value
                else:
                    redacted_metadata[key] = value

        # Redact error if present
        redacted_error = None
        if error:
            redacted_error, _ = self._redact_content(error)

        return LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            trace_id=context['trace_id'],
            span_id=context['span_id'],
            user_id_hash=self._hash_user_id(context['user_id']),
            event=event,
            pii_redacted=pii_redacted,
            message=redacted_message,
            metadata=redacted_metadata,
            duration_ms=duration_ms,
            status_code=status_code,
            error=redacted_error
        )

    def _log(self, log_entry: LogEntry):
        """Output structured log entry"""
        log_dict = asdict(log_entry)
        # Remove None values
        log_dict = {k: v for k, v in log_dict.items() if v is not None}

        self.logger.info(json.dumps(log_dict, ensure_ascii=False))

    def info(self, event: str, message: str, **kwargs):
        """Log info level message"""
        log_entry = self._create_log_entry('INFO', event, message, **kwargs)
        self._log(log_entry)

    def warning(self, event: str, message: str, **kwargs):
        """Log warning level message"""
        log_entry = self._create_log_entry('WARNING', event, message, **kwargs)
        self._log(log_entry)

    def error(self, event: str, message: str, **kwargs):
        """Log error level message"""
        log_entry = self._create_log_entry('ERROR', event, message, **kwargs)
        self._log(log_entry)

    def debug(self, event: str, message: str, **kwargs):
        """Log debug level message"""
        log_entry = self._create_log_entry('DEBUG', event, message, **kwargs)
        self._log(log_entry)


class LoggingMiddleware:
    """
    Middleware for HTTP request/response logging with PII redaction

    Features:
    - Request/response logging
    - PII redaction for query params and body
    - Performance metrics
    - Error tracking
    - Correlation ID management
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize logging middleware"""
        self.config = config or {}
        self.logger = StructuredLogger('gateway.middleware', config)
        self.pii_redactor = PIIRedactor(self.config.get('pii_config', {}))

    def _generate_correlation_ids(self) -> dict[str, str]:
        """Generate correlation IDs for request tracking"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:8]
        request_id = str(uuid.uuid4())

        return {
            'trace_id': trace_id,
            'span_id': span_id,
            'request_id': request_id
        }

    def _redact_query_params(self, query_params: dict[str, Any]) -> dict[str, Any]:
        """Redact PII from query parameters"""
        redacted = {}
        for key, value in query_params.items():
            if isinstance(value, str):
                redacted_value, _ = self.pii_redactor.redact(value)
                redacted[key] = redacted_value
            else:
                redacted[key] = value
        return redacted

    def _redact_request_body(self, body: str) -> str:
        """Redact PII from request body"""
        if not body:
            return body

        redacted, _ = self.pii_redactor.redact(body)
        return redacted

    def _redact_response_body(self, body: str) -> str:
        """Redact PII from response body"""
        if not body:
            return body

        redacted, _ = self.pii_redactor.redact(body)
        return redacted

    def log_request(
        self,
        method: str,
        path: str,
        query_params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        body: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log incoming request and return request ID

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body
            user_id: User identifier

        Returns:
            Request ID for correlation
        """
        # Generate correlation IDs
        ids = self._generate_correlation_ids()

        # Set context variables
        request_id_var.set(ids['request_id'])
        trace_id_var.set(ids['trace_id'])
        span_id_var.set(ids['span_id'])
        if user_id:
            user_id_var.set(user_id)

        # Redact sensitive data
        redacted_query = self._redact_query_params(query_params or {})
        redacted_body = self._redact_request_body(body or '')

        # Prepare metadata
        metadata = {
            'method': method,
            'path': path,
            'query_params': redacted_query,
            'headers': headers or {},
            'body': redacted_body,
            'body_size': len(body or ''),
        }

        # Log request
        self.logger.info(
            event='request_received',
            message=f'{method} {path}',
            metadata=metadata
        )

        return ids['request_id']

    def log_response(
        self,
        request_id: str,
        status_code: int,
        headers: Optional[dict[str, str]] = None,
        body: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Log outgoing response

        Args:
            request_id: Request ID for correlation
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            duration_ms: Request duration in milliseconds
            error: Error message if any
        """
        # Redact sensitive data
        redacted_body = self._redact_response_body(body or '')

        # Prepare metadata
        metadata = {
            'status_code': status_code,
            'headers': headers or {},
            'body': redacted_body,
            'body_size': len(body or ''),
        }

        # Determine log level
        if status_code >= 500:
            level = 'error'
        elif status_code >= 400:
            level = 'warning'
        else:
            level = 'info'

        # Log response
        log_method = getattr(self.logger, level)
        log_method(
            event='response_sent',
            message=f'Response {status_code}',
            metadata=metadata,
            duration_ms=duration_ms,
            status_code=status_code,
            error=error
        )

    def log_access(
        self,
        method: str,
        path: str,
        status_code: int,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        query_params: Optional[dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log access event (simplified version for high-volume logging)

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            user_id: User identifier
            duration_ms: Request duration
            query_params: Query parameters
            error: Error message if any
        """
        # Set context
        if user_id:
            user_id_var.set(user_id)

        # Redact query params
        redacted_query = self._redact_query_params(query_params or {})

        # Prepare metadata
        metadata = {
            'method': method,
            'path': path,
            'query_params': redacted_query,
        }

        # Determine log level
        if status_code >= 500:
            level = 'error'
        elif status_code >= 400:
            level = 'warning'
        else:
            level = 'info'

        # Log access
        log_method = getattr(self.logger, level)
        log_method(
            event='access',
            message=f'{method} {path} -> {status_code}',
            metadata=metadata,
            duration_ms=duration_ms,
            status_code=status_code,
            error=error
        )


# Global middleware instance
default_middleware = LoggingMiddleware()


def set_request_context(
    request_id: str,
    trace_id: str,
    span_id: str,
    user_id: Optional[str] = None
):
    """Set request context for logging"""
    request_id_var.set(request_id)
    trace_id_var.set(trace_id)
    span_id_var.set(span_id)
    if user_id:
        user_id_var.set(user_id)


def get_request_context() -> dict[str, str]:
    """Get current request context"""
    return {
        'request_id': request_id_var.get(''),
        'trace_id': trace_id_var.get(''),
        'span_id': span_id_var.get(''),
        'user_id': user_id_var.get(''),
    }
