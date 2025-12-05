#!/usr/bin/env python3
"""
Index StillMe Codebase on Railway

This script indexes the StillMe codebase into ChromaDB on Railway.
It can be run:
1. Locally (to index Railway's remote ChromaDB)
2. On Railway via Railway CLI or one-off command

Usage:
    # Local (connect to Railway backend)
    python scripts/index_codebase_railway.py https://stillme-backend-production.up.railway.app
    
    # On Railway (via Railway CLI)
    railway run python scripts/index_codebase_railway.py
"""

import sys
import os
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def index_via_api(backend_url: str):
    """
    Index codebase via Railway API endpoint (if available).
    
    This requires an API endpoint that triggers indexing.
    """
    logger.info(f"🌐 Attempting to index via API: {backend_url}")
    
    # Check if endpoint exists
    try:
        # First, check if codebase router is available
        response = requests.get(f"{backend_url}/api/codebase/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"📊 Current stats: {stats}")
            
            # If there's an index endpoint, use it
            # For now, we'll use the direct method below
            logger.info("ℹ️ No auto-index endpoint found, using direct indexing method")
            return False
        else:
            logger.warning(f"⚠️ Stats endpoint returned {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to API: {e}")
        return False


def index_directly():
    """
    Index codebase directly (when running on Railway).
    
    This method works when the script runs on Railway itself,
    where it has direct access to ChromaDB.
    """
    logger.info("🚀 Starting direct codebase indexing...")
    
    try:
        from backend.services.codebase_indexer import get_codebase_indexer
        
        # Initialize indexer
        logger.info("📦 Initializing CodebaseIndexer...")
        indexer = get_codebase_indexer()
        logger.info("✅ CodebaseIndexer initialized")
        
        # Check current collection status
        try:
            current_count = indexer.codebase_collection.count()
            logger.info(f"📊 Current collection has {current_count} chunks")
            
            if current_count > 0:
                logger.info("⚠️ Collection already has chunks. Re-indexing will add duplicates.")
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    logger.info("❌ Indexing cancelled by user")
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Could not get current count: {e}")
        
        # Index entire codebase
        logger.info("\n📁 Indexing full codebase...")
        stats = indexer.index_codebase()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 INDEXING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files indexed: {stats['files_indexed']}")
        logger.info(f"Total chunks created: {stats['chunks_created']}")
        logger.info("\nBreakdown by directory:")
        for dir_stat in stats['directories']:
            logger.info(f"  - {dir_stat['directory']}: {dir_stat['files']} files, {dir_stat['chunks']} chunks")
        
        # Verify collection
        try:
            final_count = indexer.codebase_collection.count()
            logger.info(f"\n✅ Final collection count: {final_count} chunks")
            
            if final_count >= stats['chunks_created']:
                logger.info("✅ Indexing successful!")
                return True
            else:
                logger.warning(f"⚠️ Expected {stats['chunks_created']} chunks but found {final_count}")
                return False
        except Exception as e:
            logger.error(f"❌ Could not verify collection: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to index codebase: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("📚 StillMe Codebase Indexing for Railway")
    logger.info("="*60)
    
    # Check if running on Railway
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_NAME")
    
    if is_railway:
        logger.info("✅ Railway environment detected - using direct indexing")
        success = index_directly()
    else:
        # Running locally - try to use API or direct method
        backend_url = sys.argv[1] if len(sys.argv) > 1 else None
        
        if backend_url:
            logger.info(f"🌐 Local execution with Railway URL: {backend_url}")
            # Try API first, fallback to direct (if we can connect to Railway's ChromaDB)
            if not index_via_api(backend_url):
                logger.info("⚠️ API method not available, attempting direct indexing...")
                logger.info("   Note: Direct indexing requires access to Railway's ChromaDB")
                success = index_directly()
            else:
                success = True
        else:
            logger.info("ℹ️ Local execution - using direct indexing (assumes local ChromaDB)")
            logger.info("   To index Railway, provide Railway URL as argument:")
            logger.info("   python scripts/index_codebase_railway.py https://your-railway-url.railway.app")
            success = index_directly()
    
    if success:
        logger.info("\n🎉 Codebase indexing completed successfully!")
        logger.info("✅ StillMe Codebase Assistant is now ready to answer questions about the codebase")
        return 0
    else:
        logger.error("\n❌ Codebase indexing failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

