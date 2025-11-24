"""
Request Tracking Middleware for Metrics Collection and Structured Logging
Tracks HTTP requests and errors for Prometheus metrics export
Adds correlation IDs for request tracing
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import uuid
import time
from contextvars import ContextVar
from typing import Optional

logger = logging.getLogger(__name__)

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP requests and errors for metrics collection.
    Records request counts and error rates for Prometheus export.
    Adds correlation IDs for request tracing and structured logging.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Track request and response for metrics with correlation ID
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler
        """
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        
        # Add correlation ID to request state for access in handlers
        request.state.correlation_id = correlation_id
        
        method = request.method
        endpoint = request.url.path
        start_time = time.time()
        
        # Structured logging: Request start
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "endpoint": endpoint,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            duration_ms = (time.time() - start_time) * 1000
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Track request in metrics collector
            try:
                from backend.api.metrics_collector import get_metrics_collector
                metrics_collector = get_metrics_collector()
                metrics_collector.increment_request(method, endpoint, status_code)
            except Exception as metrics_error:
                logger.debug(f"Could not track request metrics: {metrics_error}")
            
            # Structured logging: Request completed
            log_level = logging.WARNING if status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Track error in metrics collector
            try:
                from backend.api.metrics_collector import get_metrics_collector
                metrics_collector = get_metrics_collector()
                metrics_collector.increment_request(method, endpoint, 500)
            except Exception:
                pass
            
            # Structured logging: Request error
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # Re-raise exception to be handled by error handlers
            raise


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context"""
    return correlation_id_var.get()

