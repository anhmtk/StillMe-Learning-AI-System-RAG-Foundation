"""
Index Full StillMe Codebase (Phase 1.2)

Indexes all Python files in:
- backend/
- stillme_core/
- frontend/ (Python files only)

This script can be run standalone or integrated into the backend.
"""

import sys
import os
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


def index_full_codebase():
    """Index entire StillMe codebase"""
    
    logger.info("🚀 Starting full codebase indexing (Phase 1.2)...")
    
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
        except Exception as e:
            logger.warning(f"⚠️ Could not get final count: {e}")
        
        logger.info("\n✅ Full codebase indexing completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Indexing failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = index_full_codebase()
    sys.exit(0 if success else 1)

