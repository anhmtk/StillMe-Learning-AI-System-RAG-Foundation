#!/usr/bin/env python3
"""
Web Cache System - LRU + TTL for Short-term Caching
Provides efficient caching for web requests with TTL and LRU eviction
"""
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import OrderedDict
import time

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int
    last_accessed: datetime
    size_bytes: int
    etag: Optional[str] = None
    last_modified: Optional[str] = None

@dataclass
class CacheStats:
    """Cache statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    evictions: int
    total_size_bytes: int
    hit_ratio: float
    average_latency_ms: float

class WebCache:
    """LRU + TTL cache for web requests"""
    
    def __init__(self, max_size: int = 100, max_memory_mb: int = 50):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = CacheStats(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            evictions=0,
            total_size_bytes=0,
            hit_ratio=0.0,
            average_latency_ms=0.0
        )
        
        # TTL configurations for different content types
        self.ttl_configs = {
            'news': timedelta(seconds=120),      # 2 minutes
            'hackernews': timedelta(seconds=60), # 1 minute
            'github_trending': timedelta(seconds=300), # 5 minutes
            'google_trends': timedelta(seconds=600),   # 10 minutes
            'default': timedelta(seconds=180)    # 3 minutes
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
        
        logger.info(f"🗄️ Web Cache initialized: max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def get(self, key: str, content_type: str = "default") -> Tuple[Optional[Any], bool]:
        """Get cached data with cache hit/miss indication"""
        with self._lock:
            self._stats.total_requests += 1
            
            if key not in self._cache:
                self._stats.cache_misses += 1
                self._update_hit_ratio()
                return None, False
            
            entry = self._cache[key]
            
            # Check if expired
            if datetime.now() > entry.expires_at:
                del self._cache[key]
                self._stats.cache_misses += 1
                self._stats.evictions += 1
                self._update_hit_ratio()
                return None, False
            
            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats.cache_hits += 1
            self._update_hit_ratio()
            
            logger.debug(f"🗄️ Cache HIT for key: {key}")
            return entry.data, True
    
    def put(self, key: str, data: Any, content_type: str = "default", 
            etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
        """Store data in cache"""
        with self._lock:
            # Calculate TTL
            ttl = self.ttl_configs.get(content_type, self.ttl_configs['default'])
            now = datetime.now()
            
            # Calculate data size
            data_size = self._calculate_size(data)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=now,
                expires_at=now + ttl,
                access_count=1,
                last_accessed=now,
                size_bytes=data_size,
                etag=etag,
                last_modified=last_modified
            )
            
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache[key]
                self._stats.total_size_bytes -= old_entry.size_bytes
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            self._stats.total_size_bytes += data_size
            
            # Evict if necessary
            self._evict_if_needed()
            
            logger.debug(f"🗄️ Cache PUT for key: {key}, size: {data_size} bytes")
    
    def invalidate(self, key: str) -> bool:
        """Invalidate cache entry"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self._stats.total_size_bytes -= entry.size_bytes
                del self._cache[key]
                logger.debug(f"🗄️ Cache INVALIDATED for key: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats.total_size_bytes = 0
            self._stats.evictions += len(self._cache)
            logger.info("🗄️ Cache cleared")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            return CacheStats(
                total_requests=self._stats.total_requests,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                evictions=self._stats.evictions,
                total_size_bytes=self._stats.total_size_bytes,
                hit_ratio=self._stats.hit_ratio,
                average_latency_ms=self._stats.average_latency_ms
            )
    
    def _evict_if_needed(self) -> None:
        """Evict entries if cache limits are exceeded"""
        # Check size limit
        while len(self._cache) > self.max_size:
            # Remove least recently used
            oldest_key = next(iter(self._cache))
            oldest_entry = self._cache[oldest_key]
            self._stats.total_size_bytes -= oldest_entry.size_bytes
            del self._cache[oldest_key]
            self._stats.evictions += 1
            logger.debug(f"🗄️ Evicted LRU entry: {oldest_key}")
        
        # Check memory limit
        while self._stats.total_size_bytes > self.max_memory_bytes:
            if not self._cache:
                break
            
            # Remove least recently used
            oldest_key = next(iter(self._cache))
            oldest_entry = self._cache[oldest_key]
            self._stats.total_size_bytes -= oldest_entry.size_bytes
            del self._cache[oldest_key]
            self._stats.evictions += 1
            logger.debug(f"🗄️ Evicted memory entry: {oldest_key}")
    
    def _cleanup_expired(self) -> None:
        """Background thread to clean up expired entries"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                with self._lock:
                    expired_keys = []
                    now = datetime.now()
                    
                    for key, entry in self._cache.items():
                        if now > entry.expires_at:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        entry = self._cache[key]
                        self._stats.total_size_bytes -= entry.size_bytes
                        del self._cache[key]
                        self._stats.evictions += 1
                    
                    if expired_keys:
                        logger.debug(f"🗄️ Cleaned up {len(expired_keys)} expired entries")
                
            except Exception as e:
                logger.error(f"❌ Cache cleanup error: {e}")
    
    def _calculate_size(self, data: Any) -> int:
        """Calculate approximate size of data in bytes"""
        try:
            if isinstance(data, (str, bytes)):
                return len(data)
            elif isinstance(data, (dict, list)):
                return len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except Exception:
            return 1024  # Default size estimate
    
    def _update_hit_ratio(self) -> None:
        """Update cache hit ratio"""
        if self._stats.total_requests > 0:
            self._stats.hit_ratio = self._stats.cache_hits / self._stats.total_requests
    
    def generate_cache_key(self, tool_name: str, **params) -> str:
        """Generate cache key from tool name and parameters"""
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True, ensure_ascii=False)
        
        # Create hash
        key_data = f"{tool_name}:{param_str}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed cache entry information"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            return {
                "key": entry.key,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat(),
                "size_bytes": entry.size_bytes,
                "etag": entry.etag,
                "last_modified": entry.last_modified,
                "is_expired": datetime.now() > entry.expires_at
            }
    
    def get_all_keys(self) -> List[str]:
        """Get all cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def export_cache_data(self) -> Dict[str, Any]:
        """Export cache data for debugging"""
        with self._lock:
            return {
                "stats": asdict(self._stats),
                "entries": {
                    key: {
                        "created_at": entry.created_at.isoformat(),
                        "expires_at": entry.expires_at.isoformat(),
                        "access_count": entry.access_count,
                        "size_bytes": entry.size_bytes,
                        "etag": entry.etag
                    }
                    for key, entry in self._cache.items()
                },
                "config": {
                    "max_size": self.max_size,
                    "max_memory_bytes": self.max_memory_bytes,
                    "ttl_configs": {k: str(v) for k, v in self.ttl_configs.items()}
                }
            }

# Global cache instance
web_cache = WebCache()

# Export functions
def get_cached_data(key: str, content_type: str = "default") -> Tuple[Optional[Any], bool]:
    """Get cached data with cache hit/miss indication"""
    return web_cache.get(key, content_type)

def cache_data(key: str, data: Any, content_type: str = "default", 
               etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
    """Cache data with TTL"""
    web_cache.put(key, data, content_type, etag, last_modified)

def invalidate_cache(key: str) -> bool:
    """Invalidate cache entry"""
    return web_cache.invalidate(key)

def clear_cache() -> None:
    """Clear all cache"""
    web_cache.clear()

def get_cache_stats() -> CacheStats:
    """Get cache statistics"""
    return web_cache.get_stats()

def generate_cache_key(tool_name: str, **params) -> str:
    """Generate cache key"""
    return web_cache.generate_cache_key(tool_name, **params)

def get_cache_info(key: str) -> Optional[Dict[str, Any]]:
    """Get cache entry info"""
    return web_cache.get_cache_info(key)

if __name__ == "__main__":
    # Test cache functionality
    print("🗄️ Testing Web Cache...")
    
    # Test basic operations
    key1 = generate_cache_key("web.search_news", query="AI", window="24h")
    data1 = {"articles": [{"title": "AI News", "content": "Test content"}]}
    
    # Put data
    cache_data(key1, data1, "news")
    print(f"Cached data for key: {key1}")
    
    # Get data
    cached_data, hit = get_cached_data(key1, "news")
    print(f"Cache hit: {hit}, Data: {cached_data is not None}")
    
    # Test cache stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats.total_requests} requests, {stats.cache_hits} hits, {stats.hit_ratio:.2%} hit ratio")
    
    # Test cache info
    info = get_cache_info(key1)
    print(f"Cache info: {info}")
    
    # Test invalidation
    invalidated = invalidate_cache(key1)
    print(f"Invalidated: {invalidated}")
    
    # Test miss after invalidation
    cached_data, hit = get_cached_data(key1, "news")
    print(f"Cache hit after invalidation: {hit}")
    
    print("✅ Web Cache test completed")
