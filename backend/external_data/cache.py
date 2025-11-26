"""
Simple in-memory cache for external data

For Phase 1 MVP, we use in-memory cache. Can be upgraded to Redis later.
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .providers.base import ExternalDataResult

logger = logging.getLogger(__name__)


class ExternalDataCache:
    """In-memory cache for external data results"""
    
    def __init__(self):
        """Initialize cache"""
        self._cache: Dict[str, tuple[ExternalDataResult, float]] = {}
        self._max_size = 1000  # Max cache entries
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[ExternalDataResult]:
        """
        Get cached result
        
        Args:
            key: Cache key
            
        Returns:
            Cached result if exists and not expired, None otherwise
        """
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
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        expiry_time = time.time() + ttl
        self._cache[key] = (result, expiry_time)
        
        self.logger.debug(f"Cached result for key: {key}, TTL: {ttl}s")
    
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

