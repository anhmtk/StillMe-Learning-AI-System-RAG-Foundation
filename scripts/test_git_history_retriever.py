"""
Test Git History Retriever

Tests:
1. Initialize GitHistoryRetriever
2. Get commits from repository
3. Index commits into ChromaDB
4. Query Git history
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass
except Exception:
    pass

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_git_history_retriever():
    """Test Git History Retriever"""
    logger.info("🧪 Testing Git History Retriever")
    logger.info("="*80)
    
    try:
        from backend.services.git_history_retriever import get_git_history_retriever
        
        # Get retriever
        retriever = get_git_history_retriever()
        
        # Test 1: Get commits
        logger.info("\n📝 Test 1: Get commits from repository")
        commits = retriever.get_commits(limit=10)
        logger.info(f"✅ Retrieved {len(commits)} commits")
        
        if commits:
            logger.info(f"   Sample commit: {commits[0]['subject'][:60]}...")
            logger.info(f"   Author: {commits[0]['author_name']}")
            logger.info(f"   Date: {commits[0]['date']}")
            logger.info(f"   Files changed: {len(commits[0]['files_changed'])}")
        
        # Test 2: Index commits
        logger.info("\n📝 Test 2: Index commits into ChromaDB")
        result = retriever.index_commits(limit=50, force=False)
        logger.info(f"✅ Indexing result: {result['status']}")
        logger.info(f"   Count: {result.get('count', 0)}")
        
        # Test 3: Query history
        logger.info("\n📝 Test 3: Query Git history")
        queries = [
            "Why did we choose Redis for caching?",
            "When was the validation chain implemented?",
            "What changes were made to the RAG system?",
        ]
        
        for query in queries:
            results = retriever.query_history(query, n_results=3)
            logger.info(f"✅ Query: '{query}'")
            logger.info(f"   Found {len(results)} relevant commits")
            if results:
                logger.info(f"   Top result: {results[0]['subject'][:60]}...")
                logger.info(f"   Similarity: {results[0].get('similarity', 'N/A')}")
        
        # Test 4: Collection stats
        logger.info("\n📝 Test 4: Collection statistics")
        stats = retriever.get_collection_stats()
        logger.info(f"✅ Collection: {stats['collection_name']}")
        logger.info(f"   Document count: {stats['document_count']}")
        logger.info(f"   Status: {stats['status']}")
        
        logger.info("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_git_history_retriever()
    sys.exit(0 if success else 1)

