"""
Cache Service for StillMe
Provides caching for LLM responses, RAG retrievals, and HTTP responses
Supports Redis (preferred) and in-memory fallback
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class CacheService:
    """
    Unified cache service for StillMe
    Supports Redis (persistent, distributed) and in-memory (fallback)
    """
    
    def __init__(self):
        """Initialize cache service with Redis or in-memory fallback"""
        self.redis_client = None
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }
        
        # Try to connect to Redis
        if REDIS_AVAILABLE:
            try:
                # CRITICAL FIX: Use REDIS_URL if available, otherwise fallback to REDIS_HOST/REDIS_PORT
                redis_url = os.getenv("REDIS_URL")
                
                if redis_url:
                    # Use redis.from_url() to parse REDIS_URL properly
                    # This handles redis://user:password@host:port/db format
                    self.redis_client = redis.from_url(
                        redis_url,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                    logger.info(f"✅ Connecting to Redis using REDIS_URL")
                else:
                    # Fallback to individual variables if REDIS_URL not set
                    redis_host = os.getenv("REDIS_HOST", "localhost")
                    redis_port = int(os.getenv("REDIS_PORT", "6379"))
                    redis_password = os.getenv("REDIS_PASSWORD", None)
                    
                    self.redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        password=redis_password,
                        decode_responses=True,
                        socket_connect_timeout=2,
                        socket_timeout=2
                    )
                    logger.info(f"✅ Connecting to Redis using REDIS_HOST/REDIS_PORT: {redis_host}:{redis_port}")
                
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available, using in-memory cache: {e}")
                logger.warning(f"   REDIS_URL: {os.getenv('REDIS_URL', 'NOT SET')}")
                logger.warning(f"   REDIS_HOST: {os.getenv('REDIS_HOST', 'NOT SET')}")
                logger.warning(f"   REDIS_PORT: {os.getenv('REDIS_PORT', 'NOT SET')}")
                self.redis_client = None
        
        if not self.redis_client:
            logger.info("📦 Using in-memory cache (not persistent)")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        # Create a deterministic string from args and kwargs
        key_parts = [prefix]
        
        # Add args
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add kwargs (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(dict(sorted_kwargs), sort_keys=True))
        
        # Create hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                # Try Redis first
                try:
                    value = self.redis_client.get(key)
                    if value:
                        self.cache_stats["hits"] += 1
                        return json.loads(value)
                    else:
                        self.cache_stats["misses"] += 1
                        return None
                except Exception as redis_error:
                    logger.warning(f"Redis get error, falling back to in-memory: {redis_error}")
                    # Fallback to in-memory
                    self.redis_client = None
            
            # In-memory cache
            if key in self.in_memory_cache:
                entry = self.in_memory_cache[key]
                # Check TTL
                if entry.get("expires_at") and time.time() > entry["expires_at"]:
                    # Expired, remove it
                    del self.in_memory_cache[key]
                    self.cache_stats["misses"] += 1
                    return None
                
                self.cache_stats["hits"] += 1
                return entry["value"]
            else:
                self.cache_stats["misses"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                # Try Redis first
                try:
                    serialized = json.dumps(value, default=str)
                    self.redis_client.setex(key, ttl_seconds, serialized)
                    self.cache_stats["sets"] += 1
                    return True
                except Exception as redis_error:
                    logger.warning(f"Redis set error, falling back to in-memory: {redis_error}")
                    # Fallback to in-memory
                    self.redis_client = None
            
            # In-memory cache
            self.in_memory_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl_seconds,
                "created_at": time.time()
            }
            
            # Limit in-memory cache size (remove oldest entries if needed)
            max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
            if len(self.in_memory_cache) > max_size:
                # Remove oldest entries (by created_at)
                sorted_entries = sorted(
                    self.in_memory_cache.items(),
                    key=lambda x: x[1].get("created_at", 0)
                )
                # Remove 20% of oldest entries
                remove_count = max_size // 5
                for key_to_remove, _ in sorted_entries[:remove_count]:
                    del self.in_memory_cache[key_to_remove]
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                    return True
                except Exception:
                    self.redis_client = None
            
            # In-memory cache
            if key in self.in_memory_cache:
                del self.in_memory_cache[key]
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern (Redis only)"""
        if not self.redis_client:
            # For in-memory, we'd need to iterate (expensive)
            # Only clear if pattern matches exactly
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            **self.cache_stats,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "backend": "redis" if self.redis_client else "memory",
            "memory_size": len(self.in_memory_cache) if not self.redis_client else None
        }
        
        return stats
    
    def cache_query_result(self, query: str, context_limit: int, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache RAG query result
        
        Args:
            query: User query
            context_limit: Context limit used
            result: RAG retrieval result
            ttl: Time to live in seconds (default: 1 hour for queries)
            
        Returns:
            True if cached successfully
        """
        key = self._generate_key("rag_query", query, context_limit)
        ttl = ttl or self.default_ttl  # 1 hour default
        return self.set(key, result, ttl)
    
    def get_query_result(self, query: str, context_limit: int) -> Optional[Dict[str, Any]]:
        """Get cached RAG query result
        
        Args:
            query: User query
            context_limit: Context limit used
            
        Returns:
            Cached result or None
        """
        key = self._generate_key("rag_query", query, context_limit)
        return self.get(key)


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get global cache service instance (singleton)"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# Cache key prefixes
CACHE_PREFIX_LLM = "llm:response"
CACHE_PREFIX_RAG = "rag:retrieval"
CACHE_PREFIX_HTTP = "http:response"

# Default TTLs (in seconds)
TTL_LLM_RESPONSE = int(os.getenv("CACHE_TTL_LLM", "3600"))  # 1 hour default
TTL_RAG_RETRIEVAL = int(os.getenv("CACHE_TTL_RAG", "21600"))  # 6 hours default
TTL_HTTP_RESPONSE = int(os.getenv("CACHE_TTL_HTTP", "300"))  # 5 minutes default

