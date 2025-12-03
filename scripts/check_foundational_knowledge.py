#!/usr/bin/env python3
"""
Script to check if foundational knowledge exists in RAG and can be retrieved.

This helps diagnose why foundational knowledge is not being retrieved.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.rag.chroma_client import ChromaClient
from stillme_core.rag.embeddings import EmbeddingService
from stillme_core.rag.rag_retrieval import RAGRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_foundational_knowledge():
    """
    Check if foundational knowledge exists and can be retrieved.
    """
    logger.info("="*60)
    logger.info("Foundational Knowledge Check")
    logger.info("="*60)
    
    try:
        # Initialize RAG components
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Test query
        test_query = "Do you track your own execution time?"
        logger.info(f"\nTest Query: '{test_query}'")
        
        # Generate query embedding
        query_embedding = embedding_service.encode_text(test_query)
        logger.info(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
        
        # Search for CRITICAL_FOUNDATION documents
        logger.info("\n1. Searching for CRITICAL_FOUNDATION documents...")
        try:
            critical_results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=10,
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            if critical_results:
                logger.info(f"   ✅ Found {len(critical_results)} CRITICAL_FOUNDATION documents")
                
                # Check distances
                distances = [r.get("distance", 1.0) for r in critical_results]
                avg_distance = sum(distances) / len(distances) if distances else 1.0
                min_distance = min(distances) if distances else 1.0
                max_distance = max(distances) if distances else 1.0
                
                logger.info(f"\n2. Distance Analysis:")
                logger.info(f"   Average distance: {avg_distance:.3f}")
                logger.info(f"   Min distance: {min_distance:.3f}")
                logger.info(f"   Max distance: {max_distance:.3f}")
                
                # Convert distance to similarity (cosine similarity = 1 - distance)
                avg_similarity = 1.0 - avg_distance
                min_similarity = 1.0 - min_distance
                
                logger.info(f"\n3. Similarity Analysis:")
                logger.info(f"   Average similarity: {avg_similarity:.3f}")
                logger.info(f"   Max similarity: {min_similarity:.3f}")
                
                # Check if any pass threshold
                threshold = 0.1
                passing = [r for r in critical_results if (1.0 - r.get("distance", 1.0)) >= threshold]
                
                logger.info(f"\n4. Threshold Check (threshold={threshold}):")
                logger.info(f"   Documents passing threshold: {len(passing)}/{len(critical_results)}")
                
                if passing:
                    logger.info("   ✅ Some documents pass threshold - should be retrievable")
                else:
                    logger.warning("   ⚠️  No documents pass threshold - may not be retrieved")
                    logger.warning("   💡 Consider lowering threshold or checking embedding model")
                
                # Show top result
                if critical_results:
                    top_result = critical_results[0]
                    top_distance = top_result.get("distance", 1.0)
                    top_similarity = 1.0 - top_distance
                    top_content = top_result.get("content", "")[:200]
                    top_metadata = top_result.get("metadata", {})
                    
                    logger.info(f"\n5. Top Result:")
                    logger.info(f"   Distance: {top_distance:.3f}")
                    logger.info(f"   Similarity: {top_similarity:.3f}")
                    logger.info(f"   Source: {top_metadata.get('source', 'N/A')}")
                    logger.info(f"   Title: {top_metadata.get('title', 'N/A')}")
                    logger.info(f"   Content preview: {top_content}...")
                    
                    # Check if content mentions self-tracking
                    if "self-tracking" in top_content.lower() or "track.*execution" in top_content.lower():
                        logger.info("   ✅ Content mentions self-tracking - should be relevant!")
                    else:
                        logger.warning("   ⚠️  Content doesn't mention self-tracking - may not be relevant")
            else:
                logger.warning("   ⚠️  No CRITICAL_FOUNDATION documents found!")
                logger.warning("   💡 Run: python scripts/add_foundational_knowledge_remote.py --backend-url <url>")
        
        except Exception as e:
            logger.error(f"   ❌ Error searching for CRITICAL_FOUNDATION: {e}")
            logger.error("   💡 This might mean ChromaDB filter syntax is not supported")
        
        # Also try general search
        logger.info("\n6. General knowledge search (no filter)...")
        try:
            general_results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=10
            )
            
            if general_results:
                logger.info(f"   ✅ Found {len(general_results)} documents in general search")
                
                # Check if any are foundational
                foundational_in_results = [
                    r for r in general_results 
                    if r.get("metadata", {}).get("source") == "CRITICAL_FOUNDATION"
                ]
                
                if foundational_in_results:
                    logger.info(f"   ✅ Found {len(foundational_in_results)} CRITICAL_FOUNDATION in general results")
                    
                    # Check their positions
                    positions = [general_results.index(r) for r in foundational_in_results]
                    logger.info(f"   Positions in results: {positions}")
                    
                    if min(positions) < 3:
                        logger.info("   ✅ Foundational knowledge is in top 3 - should be retrieved!")
                    else:
                        logger.warning(f"   ⚠️  Foundational knowledge is at position {min(positions)} - may not be retrieved")
                else:
                    logger.warning("   ⚠️  No CRITICAL_FOUNDATION found in general search")
            else:
                logger.warning("   ⚠️  No documents found in general search")
        
        except Exception as e:
            logger.error(f"   ❌ Error in general search: {e}")
        
        # Check database stats
        logger.info("\n7. Database Statistics:")
        try:
            stats = chroma_client.get_collection_stats()
            logger.info(f"   Total documents: {stats.get('total_documents', 0)}")
            logger.info(f"   Knowledge documents: {stats.get('knowledge_documents', 0)}")
            logger.info(f"   Conversation documents: {stats.get('conversation_documents', 0)}")
        except Exception as e:
            logger.error(f"   ❌ Error getting stats: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("Check complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    check_foundational_knowledge()

