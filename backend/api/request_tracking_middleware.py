"""
Request Tracking Middleware for Metrics Collection
Tracks HTTP requests and errors for Prometheus metrics export
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP requests and errors for metrics collection.
    Records request counts and error rates for Prometheus export.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Track request and response for metrics
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler
        """
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Track request in metrics collector
            try:
                from backend.api.metrics_collector import get_metrics_collector
                metrics_collector = get_metrics_collector()
                metrics_collector.increment_request(method, endpoint, status_code)
            except Exception as metrics_error:
                logger.debug(f"Could not track request metrics: {metrics_error}")
            
            return response
            
        except Exception:
            # Track error in metrics collector
            try:
                from backend.api.metrics_collector import get_metrics_collector
                metrics_collector = get_metrics_collector()
                metrics_collector.increment_request(method, endpoint, 500)
            except Exception:
                pass
            
            # Re-raise exception to be handled by error handlers
            raise

