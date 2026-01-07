"""
Cache Utilities for StillMe

Provides utilities for caching validation results and other expensive operations.
Uses Redis if available, falls back to in-memory cache.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Redis cache
try:
    from backend.services.redis_cache import get_cache_service
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    get_cache_service = None

# In-memory fallback cache
_in_memory_cache: Dict[str, Dict[str, Any]] = {}


def hash_query(query: str) -> str:
    """
    Generate hash for query (normalized)
    
    Args:
        query: User query text
    
    Returns:
        MD5 hash (first 16 chars)
    """
    if not query:
        return "empty"
    
    # Normalize: lowercase, strip whitespace
    normalized = query.lower().strip()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:16]


def hash_context(context: Dict[str, Any]) -> str:
    """
    Generate hash for context (document IDs + similarities)
    
    Args:
        context: RAG context dictionary
    
    Returns:
        MD5 hash (first 16 chars)
    """
    if not context:
        return "no_context"
    
    # Extract document IDs and similarities
    docs = context.get("knowledge_docs", [])
    if not docs:
        return "no_docs"
    
    # Sort for consistent hashing
    doc_ids = sorted([str(doc.get("id", "")) for doc in docs if doc.get("id")])
    similarities = sorted([round(doc.get("similarity", 0.0), 3) for doc in docs])
    
    # Create hash from IDs and similarities
    context_str = json.dumps({"ids": doc_ids, "sims": similarities}, sort_keys=True)
    return hashlib.md5(context_str.encode('utf-8')).hexdigest()[:16]


def get_cache_key(prefix: str, query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate cache key from query and context
    
    Args:
        prefix: Cache key prefix (e.g., "validation")
        query: User query
        context: Optional RAG context
    
    Returns:
        Cache key string
    """
    query_hash = hash_query(query)
    context_hash = hash_context(context) if context else "no_context"
    return f"{prefix}:{query_hash}:{context_hash}"


def get_from_cache(cache_key: str) -> Optional[Any]:
    """
    Get value from cache (Redis or in-memory)
    
    Args:
        cache_key: Cache key
    
    Returns:
        Cached value or None if not found
    """
    # Try Redis first
    if REDIS_AVAILABLE:
        try:
            cache_service = get_cache_service()
            if cache_service:
                cached = cache_service.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT (Redis): {cache_key[:50]}...")
                    return cached
        except Exception as e:
            logger.debug(f"Redis cache error (falling back to memory): {e}")
    
    # Fallback to in-memory
    if cache_key in _in_memory_cache:
        cached_data = _in_memory_cache[cache_key]
        # Check TTL (simple implementation)
        import time
        if time.time() < cached_data.get("expires_at", 0):
            logger.debug(f"Cache HIT (Memory): {cache_key[:50]}...")
            return cached_data.get("value")
        else:
            # Expired, remove it
            del _in_memory_cache[cache_key]
    
    logger.debug(f"Cache MISS: {cache_key[:50]}...")
    return None


def set_to_cache(cache_key: str, value: Any, ttl: int = 3600) -> None:
    """
    Set value to cache (Redis or in-memory)
    
    Args:
        cache_key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 1 hour)
    """
    # Try Redis first
    if REDIS_AVAILABLE:
        try:
            cache_service = get_cache_service()
            if cache_service:
                cache_service.set(cache_key, value, ttl=ttl)
                logger.debug(f"Cached (Redis): {cache_key[:50]}... (TTL: {ttl}s)")
                return
        except Exception as e:
            logger.debug(f"Redis cache error (falling back to memory): {e}")
    
    # Fallback to in-memory
    import time
    _in_memory_cache[cache_key] = {
        "value": value,
        "expires_at": time.time() + ttl
    }
    logger.debug(f"Cached (Memory): {cache_key[:50]}... (TTL: {ttl}s)")


def clear_cache(cache_key: Optional[str] = None) -> None:
    """
    Clear cache (specific key or all)
    
    Args:
        cache_key: Specific key to clear, or None to clear all
    """
    if cache_key:
        # Clear specific key
        if REDIS_AVAILABLE:
            try:
                cache_service = get_cache_service()
                if cache_service:
                    cache_service.delete(cache_key)
            except Exception:
                pass
        
        if cache_key in _in_memory_cache:
            del _in_memory_cache[cache_key]
    else:
        # Clear all
        if REDIS_AVAILABLE:
            try:
                cache_service = get_cache_service()
                if cache_service:
                    cache_service.clear()
            except Exception:
                pass
        
        _in_memory_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache stats
    """
    stats = {
        "redis_available": REDIS_AVAILABLE,
        "in_memory_size": len(_in_memory_cache),
        "in_memory_keys": list(_in_memory_cache.keys())[:10]  # First 10 keys
    }
    
    if REDIS_AVAILABLE:
        try:
            cache_service = get_cache_service()
            if cache_service:
                redis_stats = cache_service.get_stats()
                stats.update(redis_stats)
        except Exception as e:
            stats["redis_error"] = str(e)
    
    return stats

