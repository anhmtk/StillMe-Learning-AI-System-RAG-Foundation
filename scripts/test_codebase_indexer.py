"""
Test script for Codebase Indexer (Phase 1.1)

Tests:
1. CodebaseIndexer initialization
2. File indexing
3. Codebase querying
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_codebase_indexer():
    """Test CodebaseIndexer functionality"""
    
    logger.info("🧪 Testing CodebaseIndexer (Phase 1.1)...")
    
    try:
        # Import after path setup
        from backend.services.codebase_indexer import get_codebase_indexer
        
        # Initialize indexer (will use main_module instances)
        logger.info("📦 Initializing CodebaseIndexer...")
        indexer = get_codebase_indexer()
        logger.info("✅ CodebaseIndexer initialized")
        
        # Test 1: Index a single file
        logger.info("\n📄 Test 1: Indexing single file...")
        test_file = project_root / "backend" / "services" / "codebase_indexer.py"
        if test_file.exists():
            chunks = indexer.index_file(test_file)
            logger.info(f"✅ Indexed {chunks} chunks from {test_file.name}")
        else:
            logger.warning(f"⚠️ Test file not found: {test_file}")
        
        # Test 2: Index a small directory
        logger.info("\n📁 Test 2: Indexing small directory...")
        test_dir = project_root / "backend" / "services"
        stats = indexer.index_directory(test_dir)
        logger.info(f"✅ Directory indexing stats: {stats}")
        
        # Test 3: Query codebase
        logger.info("\n🔍 Test 3: Querying codebase...")
        test_queries = [
            "How does CodebaseIndexer work?",
            "What is the chunking strategy?",
            "How to index a file?"
        ]
        
        for query in test_queries:
            logger.info(f"\n  Query: {query}")
            results = indexer.query_codebase(query, n_results=3)
            logger.info(f"  Found {len(results)} results")
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                file_path = metadata.get("file_path", "unknown")
                line_range = f"{metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}"
                code_type = metadata.get("code_type", "unknown")
                logger.info(f"    {i}. {file_path}:{line_range} ({code_type})")
                if metadata.get("function_name"):
                    logger.info(f"       Function: {metadata['function_name']}")
                if metadata.get("class_name"):
                    logger.info(f"       Class: {metadata['class_name']}")
        
        # Test 4: Check collection stats
        logger.info("\n📊 Test 4: Collection statistics...")
        try:
            count = indexer.codebase_collection.count()
            logger.info(f"✅ Total chunks in collection: {count}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get collection count: {e}")
        
        logger.info("\n✅ All tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_codebase_indexer()
    sys.exit(0 if success else 1)

