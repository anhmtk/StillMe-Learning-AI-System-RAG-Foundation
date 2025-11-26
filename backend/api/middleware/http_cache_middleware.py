"""
HTTP Response Cache Middleware for StillMe
Phase 3: Cache HTTP responses to reduce database load and latency
"""

import hashlib
import json
import logging
import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.services.cache_service import (
    get_cache_service,
    CACHE_PREFIX_HTTP,
    TTL_HTTP_RESPONSE
)
import os

logger = logging.getLogger(__name__)


class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache HTTP responses
    Only caches GET requests to specific endpoints
    """
    
    def __init__(self, app, cache_enabled: bool = True):
        super().__init__(app)
        self.cache_enabled = cache_enabled and (os.getenv("ENABLE_HTTP_CACHE", "true").lower() == "true")
        self.cache_service = get_cache_service()
        
        # Endpoints to cache (only GET requests)
        self.cacheable_paths = [
            "/api/learning/metrics/daily",
            "/api/learning/metrics/range",
            "/api/learning/metrics/summary",
            "/api/learning/scheduler/status",  # Added for performance
            "/api/learning/sources/current",
            "/api/learning/sources/stats",
            "/api/rag/stats",  # Added for performance
            "/api/validators/metrics",
            "/api/system/status",
            "/api/system/health"
        ]
        
        # Endpoints to never cache
        self.never_cache_paths = [
            "/api/chat/",
            "/api/learning/cycle",
            "/api/learning/trigger"
        ]
    
    def _is_cacheable(self, request: Request) -> bool:
        """Check if request is cacheable"""
        if not self.cache_enabled:
            return False
        
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        path = request.url.path
        
        # Never cache these paths
        for never_path in self.never_cache_paths:
            if path.startswith(never_path):
                return False
        
        # Check if path is in cacheable list
        for cacheable_path in self.cacheable_paths:
            if path.startswith(cacheable_path):
                return True
        
        return False
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include path and query parameters
        path = request.url.path
        query_string = str(request.url.query)
        
        # Include headers that affect response (if any)
        # For now, just use path + query
        key_string = f"{path}?{query_string}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"{CACHE_PREFIX_HTTP}:{key_hash}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""
        
        # Check if request is cacheable
        if not self._is_cacheable(request):
            # Not cacheable, proceed normally
            response = await call_next(request)
            return response
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        cached_response = self.cache_service.get(cache_key)
        if cached_response:
            logger.info(f"✅ HTTP cache HIT: {request.url.path}")
            
            # Return cached response
            return JSONResponse(
                content=cached_response.get("content"),
                status_code=cached_response.get("status_code", 200),
                headers={
                    **cached_response.get("headers", {}),
                    "X-Cache": "HIT",
                    "X-Cache-Timestamp": str(cached_response.get("timestamp", 0))
                }
            )
        
        # Cache miss - process request
        logger.debug(f"❌ HTTP cache MISS: {request.url.path}")
        start_time = time.time()
        
        response = await call_next(request)
        
        # Only cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            try:
                # Get response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Try to parse as JSON
                try:
                    response_content = json.loads(response_body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, skip caching
                    logger.debug(f"Skipping cache for non-JSON response: {request.url.path}")
                    from starlette.responses import Response as StarletteResponse
                    return StarletteResponse(
                        content=response_body,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                
                # Cache the response
                cache_value = {
                    "content": response_content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "timestamp": time.time(),
                    "latency": time.time() - start_time
                }
                
                # Use endpoint-specific TTL if available (increased for performance)
                ttl = TTL_HTTP_RESPONSE
                if "/metrics/daily" in request.url.path:
                    ttl = 600  # 10 minutes for daily metrics (increased from 5)
                elif "/metrics/range" in request.url.path:
                    ttl = 900  # 15 minutes for range metrics (increased from 10)
                elif "/metrics/summary" in request.url.path:
                    ttl = 300  # 5 minutes for summary (increased from 3)
                elif "/scheduler/status" in request.url.path:
                    ttl = 60  # 1 minute for scheduler status
                elif "/rag/stats" in request.url.path:
                    ttl = 120  # 2 minutes for RAG stats
                
                self.cache_service.set(cache_key, cache_value, ttl=ttl)
                logger.debug(f"💾 HTTP response cached: {request.url.path}")
                
                # Return response with cache headers
                return JSONResponse(
                    content=response_content,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Cache": "MISS",
                        "X-Cache-TTL": str(ttl)
                    }
                )
                
            except Exception as cache_error:
                logger.warning(f"Failed to cache HTTP response: {cache_error}")
                # Return original response
                from starlette.responses import Response as StarletteResponse
                return StarletteResponse(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
        
        # Non-2xx response, don't cache
        return response

