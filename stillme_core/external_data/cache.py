"""
Cache for external data results

Supports Redis (if available) with in-memory fallback.
Uses existing CacheService for consistency.
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .providers.base import ExternalDataResult

logger = logging.getLogger(__name__)

# Try to use CacheService if available
try:
    from backend.services.cache_service import get_cache_service
    CACHE_SERVICE_AVAILABLE = True
except ImportError:
    CACHE_SERVICE_AVAILABLE = False
    logger.debug("CacheService not available, using in-memory cache only")


class ExternalDataCache:
    """
    Cache for external data results
    
    Uses CacheService (Redis) if available, falls back to in-memory cache.
    """
    
    def __init__(self):
        """Initialize cache"""
        self._cache: Dict[str, tuple[ExternalDataResult, float]] = {}
        self._max_size = 1000  # Max cache entries
        self.logger = logging.getLogger(__name__)
        
        # Try to use CacheService if available
        self._cache_service = None
        if CACHE_SERVICE_AVAILABLE:
            try:
                self._cache_service = get_cache_service()
                self.logger.info("Using CacheService (Redis) for external data cache")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CacheService: {e}. Using in-memory cache.")
                self._cache_service = None
    
    def get(self, key: str) -> Optional[ExternalDataResult]:
        """
        Get cached result
        
        Args:
            key: Cache key
            
        Returns:
            Cached result if exists and not expired, None otherwise
        """
        # Try CacheService first (Redis)
        if self._cache_service:
            try:
                cached_data = self._cache_service.get(f"external_data:{key}")
                if cached_data:
                    # Deserialize ExternalDataResult
                    import json
                    from datetime import datetime
                    data = json.loads(cached_data)
                    result = ExternalDataResult(
                        data=data["data"],
                        source=data["source"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        cached=True,
                        cache_ttl=data.get("cache_ttl"),
                        raw_response=data.get("raw_response"),
                        success=data.get("success", True),
                        error_message=data.get("error_message")
                    )
                    self.logger.debug(f"Cache hit from CacheService: {key}")
                    return result
            except Exception as e:
                self.logger.warning(f"Error getting from CacheService: {e}. Falling back to in-memory.")
        
        # Fallback to in-memory cache
        if key not in self._cache:
            return None
        
        result, expiry_time = self._cache[key]
        
        # Check if expired
        if time.time() > expiry_time:
            del self._cache[key]
            return None
        
        # Mark as cached
        result.cached = True
        return result
    
    def set(self, key: str, result: ExternalDataResult, ttl: int):
        """
        Cache result with TTL
        
        Args:
            key: Cache key
            result: Result to cache
            ttl: Time to live in seconds
        """
        # Try CacheService first (Redis)
        if self._cache_service:
            try:
                import json
                # Serialize ExternalDataResult
                data = {
                    "data": result.data,
                    "source": result.source,
                    "timestamp": result.timestamp.isoformat(),
                    "cache_ttl": result.cache_ttl,
                    "raw_response": result.raw_response,
                    "success": result.success,
                    "error_message": result.error_message,
                }
                self._cache_service.set(
                    f"external_data:{key}",
                    json.dumps(data),
                    ttl=ttl
                )
                self.logger.debug(f"Cached result in CacheService: {key}, TTL: {ttl}s")
                return
            except Exception as e:
                self.logger.warning(f"Error setting in CacheService: {e}. Falling back to in-memory.")
        
        # Fallback to in-memory cache
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        expiry_time = time.time() + ttl
        self._cache[key] = (result, expiry_time)
        
        self.logger.debug(f"Cached result in-memory: {key}, TTL: {ttl}s")
    
    def _evict_oldest(self):
        """Evict oldest cache entry"""
        if not self._cache:
            return
        
        # Find oldest entry (lowest expiry time)
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
        self.logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        # Clean expired entries first
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        for key in expired_keys:
            del self._cache[key]
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "usage_percent": (len(self._cache) / self._max_size) * 100
        }

