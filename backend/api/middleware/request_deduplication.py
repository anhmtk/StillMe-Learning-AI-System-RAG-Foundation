"""
Request Deduplication Middleware
Prevents duplicate requests within a short time window
"""

import hashlib
import time
import logging
from typing import Dict, Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Deduplication window (seconds)
DEDUP_WINDOW = 5.0  # 5 seconds

# Track recent requests
_recent_requests: Dict[str, Tuple[float, dict]] = {}


class RequestDeduplicationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to deduplicate identical requests within a time window.
    Only applies to GET requests to specific endpoints.
    """
    
    def __init__(self, app, dedup_enabled: bool = True):
        super().__init__(app)
        self.dedup_enabled = dedup_enabled
        self.dedup_window = DEDUP_WINDOW
        
        # Endpoints to apply deduplication
        self.dedup_paths = [
            "/api/learning/scheduler/status",
            "/api/learning/metrics/daily",
            "/api/learning/metrics/range",
            "/api/learning/metrics/summary",
            "/api/rag/stats",
            "/api/system/status",
            "/api/validators/metrics"
        ]
    
    def _is_dedup_target(self, request: Request) -> bool:
        """Check if request should be deduplicated"""
        if not self.dedup_enabled:
            return False
        
        # Only deduplicate GET requests
        if request.method != "GET":
            return False
        
        path = request.url.path
        return any(path.startswith(dedup_path) for dedup_path in self.dedup_paths)
    
    def _generate_request_key(self, request: Request) -> str:
        """Generate unique key for request"""
        path = request.url.path
        query_string = str(request.url.query)
        key_string = f"{request.method}:{path}?{query_string}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _cleanup_old_requests(self):
        """Remove requests older than dedup window"""
        current_time = time.time()
        keys_to_remove = [
            key for key, (timestamp, _) in _recent_requests.items()
            if current_time - timestamp > self.dedup_window
        ]
        for key in keys_to_remove:
            _recent_requests.pop(key, None)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with deduplication"""
        
        if not self._is_dedup_target(request):
            return await call_next(request)
        
        # Cleanup old requests
        self._cleanup_old_requests()
        
        # Generate request key
        request_key = self._generate_request_key(request)
        current_time = time.time()
        
        # Check if we have a recent identical request
        if request_key in _recent_requests:
            timestamp, cached_response = _recent_requests[request_key]
            age = current_time - timestamp
            
            if age < self.dedup_window:
                logger.info(f"🔄 Request deduplicated: {request.url.path} (age: {age:.2f}s)")
                return JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers={
                        **cached_response.get("headers", {}),
                        "X-Deduplicated": "true",
                        "X-Request-Age": f"{age:.2f}"
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Cache response if successful
        if 200 <= response.status_code < 300:
            try:
                # Get response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Try to parse as JSON
                try:
                    import json
                    response_content = json.loads(response_body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, don't cache
                    from starlette.responses import Response as StarletteResponse
                    return StarletteResponse(
                        content=response_body,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                
                # Store in deduplication cache
                _recent_requests[request_key] = (
                    current_time,
                    {
                        "content": response_content,
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
                )
                
                # Return response
                return JSONResponse(
                    content=response_content,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Deduplicated": "false"
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to cache response for deduplication: {e}")
        
        return response

