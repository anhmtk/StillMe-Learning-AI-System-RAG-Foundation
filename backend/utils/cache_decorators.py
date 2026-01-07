"""
Cache Decorators for StillMe

Provides decorators for caching expensive operations like validation.
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps

from backend.utils.cache_utils import get_cache_key, get_from_cache, set_to_cache

logger = logging.getLogger(__name__)


def cache_validation_result(ttl: int = 3600):
    """
    Decorator to cache validation results
    
    Caches validation results based on query hash and context hash.
    Skips validation if cached result exists.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
    
    Usage:
        @cache_validation_result(ttl=3600)
        async def validate_response(response: str, query: str, context: Dict):
            # Validation logic
            return validation_result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract query and context from kwargs
            query = kwargs.get('query', '')
            context = kwargs.get('context', {})
            
            # Generate cache key
            cache_key = get_cache_key("validation", query, context)
            
            # Check cache
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                logger.info(f"✅ Validation cache HIT for query: {query[:50]}...")
                return cached_result
            
            # Execute function
            logger.debug(f"⏳ Validation cache MISS, executing validation for: {query[:50]}...")
            result = await func(*args, **kwargs)
            
            # Cache result
            set_to_cache(cache_key, result, ttl=ttl)
            logger.debug(f"💾 Cached validation result (TTL: {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


def cache_expensive_operation(prefix: str, ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    Generic decorator to cache expensive operations
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from args/kwargs
    
    Usage:
        @cache_expensive_operation("llm_response", ttl=1800)
        async def generate_response(query: str):
            # Expensive operation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use first arg or query kwarg
                if args:
                    cache_key = get_cache_key(prefix, str(args[0]))
                elif 'query' in kwargs:
                    cache_key = get_cache_key(prefix, kwargs['query'])
                else:
                    # No cache key possible, skip caching
                    return await func(*args, **kwargs)
            
            # Check cache
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key[:50]}...")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            set_to_cache(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator

