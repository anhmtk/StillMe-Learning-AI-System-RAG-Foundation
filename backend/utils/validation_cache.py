"""
Validation Cache Wrapper

Wraps validation execution with caching to reduce redundant LLM calls.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from backend.utils.cache_utils import get_cache_key, get_from_cache, set_to_cache

logger = logging.getLogger(__name__)


async def get_cached_validation_or_run(
    query: str,
    context: Dict[str, Any],
    raw_response: str,
    validation_func,
    ttl: int = 3600,
    **validation_kwargs
) -> Tuple[Any, bool]:
    """
    Get cached validation result or run validation and cache it.
    
    Args:
        query: User query
        context: RAG context
        raw_response: Response to validate
        validation_func: Async function that runs validation
        ttl: Cache TTL in seconds
        **validation_kwargs: Additional kwargs for validation function
    
    Returns:
        Tuple of (validation_result, was_cached)
    """
    # Generate cache key from query and context
    cache_key = get_cache_key("validation", query, context)
    
    # Check cache
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        logger.info(f"✅ Validation cache HIT for query: {query[:50]}...")
        return cached_result, True
    
    # Cache miss - run validation
    logger.debug(f"⏳ Validation cache MISS, running validation for: {query[:50]}...")
    validation_result = await validation_func(raw_response, context, **validation_kwargs)
    
    # Cache result
    set_to_cache(cache_key, validation_result, ttl=ttl)
    logger.debug(f"💾 Cached validation result (TTL: {ttl}s)")
    
    return validation_result, False

