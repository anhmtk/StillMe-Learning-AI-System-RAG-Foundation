"""
Verify Codebase Indexing (Phase 1.2)

Tests:
1. Query accuracy across different directories
2. Metadata completeness
3. File:line references correctness
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


def verify_codebase_indexing():
    """Verify codebase indexing quality"""
    
    logger.info("🔍 Verifying codebase indexing (Phase 1.2)...")
    
    try:
        from backend.services.codebase_indexer import get_codebase_indexer
        
        # Initialize indexer
        indexer = get_codebase_indexer()
        
        # Check collection stats
        try:
            count = indexer.codebase_collection.count()
            logger.info(f"📊 Collection has {count} chunks")
        except Exception as e:
            logger.warning(f"⚠️ Could not get count: {e}")
        
        # Test queries across different areas
        test_queries = [
            # Backend queries
            ("How does the validation chain work?", "backend"),
            ("What is the RAG retrieval process?", "stillme_core"),
            ("How does the chat router handle requests?", "backend"),
            # StillMe core queries
            ("How does StillMe track task execution time?", "stillme_core"),
            ("What validators are in the validation chain?", "stillme_core"),
            # Frontend queries
            ("How does the floating chat component work?", "frontend"),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🔍 QUERY VERIFICATION")
        logger.info("="*60)
        
        all_passed = True
        for query, expected_area in test_queries:
            logger.info(f"\n📝 Query: {query}")
            logger.info(f"   Expected area: {expected_area}")
            
            results = indexer.query_codebase(query, n_results=3)
            
            if not results:
                logger.warning(f"   ⚠️ No results found!")
                all_passed = False
                continue
            
            logger.info(f"   ✅ Found {len(results)} results")
            
            # Check if results are from expected area
            found_expected = False
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                file_path = metadata.get("file_path", "")
                code_type = metadata.get("code_type", "unknown")
                line_range = f"{metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}"
                
                # Check if from expected area
                if expected_area in file_path:
                    found_expected = True
                
                logger.info(f"      {i}. {Path(file_path).name}:{line_range} ({code_type})")
                
                # Verify metadata completeness
                required_fields = ["file_path", "line_start", "line_end", "code_type"]
                missing_fields = [f for f in required_fields if f not in metadata]
                if missing_fields:
                    logger.warning(f"         ⚠️ Missing metadata: {missing_fields}")
                    all_passed = False
                else:
                    logger.info(f"         ✅ Metadata complete")
                
                # Show additional metadata if available
                if metadata.get("function_name"):
                    logger.info(f"         Function: {metadata['function_name']}")
                if metadata.get("class_name"):
                    logger.info(f"         Class: {metadata['class_name']}")
                if metadata.get("docstring"):
                    doc_preview = metadata['docstring'][:100] + "..." if len(metadata['docstring']) > 100 else metadata['docstring']
                    logger.info(f"         Docstring: {doc_preview}")
            
            if found_expected:
                logger.info(f"   ✅ Found results from expected area ({expected_area})")
            else:
                logger.warning(f"   ⚠️ No results from expected area ({expected_area})")
                all_passed = False
        
        logger.info("\n" + "="*60)
        if all_passed:
            logger.info("✅ All verification tests passed!")
        else:
            logger.warning("⚠️ Some verification tests had issues")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = verify_codebase_indexing()
    sys.exit(0 if success else 1)

