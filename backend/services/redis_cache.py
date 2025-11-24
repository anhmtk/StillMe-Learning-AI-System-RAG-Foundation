"""
Redis Cache Service for StillMe
Provides caching for embeddings, queries, and RAG results to reduce latency and costs
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

# Try to import redis, fallback to None if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching will be disabled. Install with: pip install redis")


class RedisCacheService:
    """Redis cache service for StillMe"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        """Initialize Redis cache service
        
        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var or localhost)
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self.redis_client = None
        self.enabled = False
        
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis not installed - caching disabled")
            return
        
        try:
            # Get Redis URL from environment or use default
            if redis_url is None:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            # Parse Redis URL
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,  # Auto-decode strings
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"✅ Redis cache enabled: {redis_url}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed - caching disabled: {e}")
            logger.warning("   Caching will be disabled. System will work without cache.")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments
        
        Args:
            prefix: Key prefix (e.g., "embedding", "query", "rag")
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Cache key string
        """
        # Create key from prefix and arguments
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, (list, dict)):
                # Hash complex objects
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest()[:16])
            else:
                key_parts.append(str(hash(arg))[:16])
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:16])
        
        return ":".join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
                
        except Exception as e:
            logger.warning(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (defaults to default_ttl)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (str, int, float, bool)):
                serialized = value if isinstance(value, str) else json.dumps(value)
            else:
                serialized = json.dumps(value)
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, serialized)
            return True
            
        except Exception as e:
            logger.warning(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete error for key {key}: {e}")
            return False
    
    def cache_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """Cache embedding result
        
        Args:
            text: Input text
            embedding: Embedding vector
            ttl: Time to live in seconds (default: 24 hours for embeddings)
            
        Returns:
            True if cached successfully
        """
        key = self._generate_key("embedding", text)
        ttl = ttl or (24 * 3600)  # 24 hours default for embeddings
        return self.set(key, embedding, ttl)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding
        
        Args:
            text: Input text
            
        Returns:
            Cached embedding or None
        """
        key = self._generate_key("embedding", text)
        return self.get(key)
    
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
    
    def cache_frequent_query(self, query: str, response: str, ttl: Optional[int] = None) -> bool:
        """Cache frequent query response (for common questions)
        
        Args:
            query: User query
            response: LLM response
            ttl: Time to live in seconds (default: 6 hours for frequent queries)
            
        Returns:
            True if cached successfully
        """
        key = self._generate_key("frequent_query", query)
        ttl = ttl or (6 * 3600)  # 6 hours default
        return self.set(key, response, ttl)
    
    def get_frequent_query(self, query: str) -> Optional[str]:
        """Get cached frequent query response
        
        Args:
            query: User query
            
        Returns:
            Cached response or None
        """
        key = self._generate_key("frequent_query", query)
        return self.get(key)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "embedding:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis invalidate_pattern error for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "error": "Redis not available"
            }
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": sum(
                    int(count) for count in info.get("db0", {}).get("keys", "0").split(",")
                    if count.isdigit()
                ) if "db0" in info else 0,
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) * 100 if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) > 0 else 0
            }
        except Exception as e:
            logger.warning(f"Redis stats error: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    def clear_all(self) -> bool:
        """Clear all cache (use with caution!)
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("🗑️ All Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"Redis clear_all error: {e}")
            return False


# Global cache service instance
_cache_service: Optional[RedisCacheService] = None


def get_cache_service() -> Optional[RedisCacheService]:
    """Get global cache service instance
    
    Returns:
        RedisCacheService instance or None if Redis not available
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = RedisCacheService()
    return _cache_service if _cache_service.enabled else None

