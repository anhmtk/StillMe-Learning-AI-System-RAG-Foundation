#!/usr/bin/env python3
"""
Script to clear LLM response cache

This script clears the LLM response cache to force StillMe to regenerate
responses with updated foundational knowledge (e.g., correct model name).
"""

import sys
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
    
    try:
        from backend.services.cache_service import get_cache_service, CACHE_PREFIX_LLM
        
        cache_service = get_cache_service()
        
        # Clear all LLM cache keys
        if hasattr(cache_service, 'clear_pattern'):
            # Redis cache - clear by pattern
            pattern = f"{CACHE_PREFIX_LLM}:*"
            cleared = cache_service.clear_pattern(pattern)
            logger.info(f"✅ Cleared {cleared} LLM cache entries (pattern: {pattern})")
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
        raise

if __name__ == "__main__":
    clear_llm_cache()

