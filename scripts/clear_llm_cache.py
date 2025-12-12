#!/usr/bin/env python3
"""
Script to clear LLM response cache

This script clears the LLM response cache to force StillMe to regenerate
responses with updated foundational knowledge (e.g., correct model name).

IMPORTANT: If you're running this locally but cache is on Railway:
- Use scripts/clear_cache_railway.py instead (clears via API)
- Or set REDIS_URL/REDIS_HOST environment variables to connect to Railway Redis
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_llm_cache():
    """Clear LLM response cache"""
    
    logger.info("="*60)
    logger.info("Clearing LLM Response Cache")
    logger.info("="*60)
    
    # Check if we're trying to clear local cache but cache is on Railway
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST")
    
    if not redis_url and not redis_host:
        logger.warning("⚠️  No Redis connection configured (REDIS_URL or REDIS_HOST not set)")
        logger.warning("   This script will only clear LOCAL in-memory cache.")
        logger.warning("   If your cache is on Railway, use one of these methods:")
        logger.warning("   1. python scripts/clear_cache_railway.py (recommended)")
        logger.warning("   2. Set REDIS_URL environment variable to Railway Redis URL")
        logger.warning("   3. Use Railway CLI: railway run python scripts/clear_llm_cache.py")
        logger.warning("")
        logger.warning("   Continuing with local cache clear...")
        logger.warning("")
    
    try:
        from backend.services.cache_service import get_cache_service, CACHE_PREFIX_LLM
        
        cache_service = get_cache_service()
        
        # Check if we're using in-memory cache
        cache_type = type(cache_service).__name__
        if "Memory" in cache_type or "InMemory" in cache_type:
            logger.warning("⚠️  Using in-memory cache (not persistent)")
            logger.warning("   This will only clear cache in this process.")
            logger.warning("   To clear Railway cache, use: python scripts/clear_cache_railway.py")
            logger.warning("")
        
        # Clear all LLM cache keys
        if hasattr(cache_service, 'clear_pattern'):
            # Redis cache - clear by pattern
            pattern = f"{CACHE_PREFIX_LLM}:*"
            cleared = cache_service.clear_pattern(pattern)
            logger.info(f"✅ Cleared {cleared} LLM cache entries (pattern: {pattern})")
            
            if cleared == 0:
                logger.warning("⚠️  No cache entries cleared. Possible reasons:")
                logger.warning("   1. Cache is on Railway, not local (use clear_cache_railway.py)")
                logger.warning("   2. Cache keys don't match pattern (check pattern)")
                logger.warning("   3. Cache was already empty")
        elif hasattr(cache_service, 'clear_all'):
            # Clear all cache (if no pattern support)
            cache_service.clear_all()
            logger.info("✅ Cleared all cache entries")
        else:
            logger.warning("⚠️ Cache service doesn't support clearing - cache may persist")
            logger.info("   You may need to wait for cache TTL to expire or restart the service")
        
        logger.info("\n" + "="*60)
        logger.info("Cache cleared successfully!")
        logger.info("Next steps:")
        logger.info("1. Test StillMe response to verify correct model name")
        logger.info("2. Response should now be regenerated with updated foundational knowledge")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        logger.error("   You may need to manually clear cache or wait for TTL to expire")
        logger.error("   For Railway cache, use: python scripts/clear_cache_railway.py")
        raise

if __name__ == "__main__":
    clear_llm_cache()

