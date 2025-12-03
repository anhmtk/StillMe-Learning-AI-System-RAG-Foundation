#!/usr/bin/env python3
"""
Script to diagnose why embedding distance is high after re-embedding.

This helps understand if the issue is:
1. Embeddings not normalized
2. Query doesn't semantically match content
3. ChromaDB distance metric issue
"""

import sys
import logging
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.rag.chroma_client import ChromaClient
from stillme_core.rag.embeddings import EmbeddingService
from stillme_core.rag.rag_retrieval import RAGRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def diagnose_embedding_distance():
    """
    Diagnose why embedding distance is high.
    """
    logger.info("="*60)
    logger.info("Embedding Distance Diagnosis")
    logger.info("="*60)
    
    try:
        # Initialize RAG components
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Get all CRITICAL_FOUNDATION documents
        logger.info("\n1. Getting CRITICAL_FOUNDATION documents...")
        collection = chroma_client.knowledge_collection
        
        results = collection.get(
            where={"source": "CRITICAL_FOUNDATION"},
            include=["documents", "metadatas", "embeddings"]
        )
        
        if not results or not results.get("ids"):
            logger.error("   ❌ No CRITICAL_FOUNDATION documents found!")
            return
        
        logger.info(f"   ✅ Found {len(results['ids'])} CRITICAL_FOUNDATION documents")
        
        # Test query
        test_query = "Do you track your own execution time?"
        logger.info(f"\n2. Test Query: '{test_query}'")
        
        # Generate query embedding
        query_embedding = np.array(embedding_service.encode_text(test_query))
        logger.info(f"   ✅ Query embedding: {len(query_embedding)} dimensions")
        
        # Check if query embedding is normalized
        query_norm = np.linalg.norm(query_embedding)
        logger.info(f"   Query embedding norm: {query_norm:.6f}")
        if abs(query_norm - 1.0) < 0.01:
            logger.info("   ✅ Query embedding is normalized (unit vector)")
        else:
            logger.warning(f"   ⚠️  Query embedding is NOT normalized (norm={query_norm:.6f})")
        
        # Check document embeddings
        logger.info(f"\n3. Analyzing document embeddings...")
        embeddings_list = results.get("embeddings", [])
        
        if embeddings_list:
            doc_embedding = np.array(embeddings_list[0])
            doc_norm = np.linalg.norm(doc_embedding)
            logger.info(f"   Document embedding norm: {doc_norm:.6f}")
            if abs(doc_norm - 1.0) < 0.01:
                logger.info("   ✅ Document embedding is normalized (unit vector)")
            else:
                logger.warning(f"   ⚠️  Document embedding is NOT normalized (norm={doc_norm:.6f})")
            
            # Calculate cosine similarity manually
            if query_norm > 0 and doc_norm > 0:
                # Normalize both for cosine similarity
                query_normalized = query_embedding / query_norm
                doc_normalized = doc_embedding / doc_norm
                
                cosine_sim = np.dot(query_normalized, doc_normalized)
                cosine_distance = 1.0 - cosine_sim
                
                logger.info(f"\n4. Manual Similarity Calculation:")
                logger.info(f"   Cosine similarity: {cosine_sim:.6f}")
                logger.info(f"   Cosine distance: {cosine_distance:.6f}")
                
                # Calculate L2 distance
                l2_distance = np.linalg.norm(query_embedding - doc_embedding)
                logger.info(f"   L2 distance: {l2_distance:.6f}")
                
                # Compare with ChromaDB result
                logger.info(f"\n5. ChromaDB Query Result:")
                test_results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=1,
                    where={"source": "CRITICAL_FOUNDATION"}
                )
                
                if test_results and test_results.get("distances") and test_results["distances"][0]:
                    chroma_distance = test_results["distances"][0][0]
                    logger.info(f"   ChromaDB distance: {chroma_distance:.6f}")
                    
                    # Determine which metric ChromaDB is using
                    if abs(chroma_distance - l2_distance) < 0.1:
                        logger.info("   ✅ ChromaDB is using L2 distance")
                    elif abs(chroma_distance - cosine_distance) < 0.1:
                        logger.info("   ✅ ChromaDB is using cosine distance")
                    else:
                        logger.warning(f"   ⚠️  ChromaDB distance doesn't match L2 ({l2_distance:.6f}) or cosine ({cosine_distance:.6f})")
                        logger.warning(f"   ChromaDB distance: {chroma_distance:.6f}")
                
                # Check content relevance
                logger.info(f"\n6. Content Relevance Check:")
                doc_content = results["documents"][0] if results.get("documents") else ""
                logger.info(f"   Document length: {len(doc_content)} characters")
                logger.info(f"   Contains 'track': {'track' in doc_content.lower()}")
                logger.info(f"   Contains 'execution time': {'execution time' in doc_content.lower()}")
                logger.info(f"   Contains 'self-tracking': {'self-tracking' in doc_content.lower()}")
                
                # Show content preview
                logger.info(f"\n7. Document Content Preview:")
                preview = doc_content[:500] if len(doc_content) > 500 else doc_content
                logger.info(f"   {preview}...")
                
                # Recommendations
                logger.info(f"\n8. Recommendations:")
                if cosine_sim < 0.3:
                    logger.warning("   ⚠️  Cosine similarity is very low (< 0.3)")
                    logger.warning("   💡 Query may not semantically match document content")
                    logger.warning("   💡 Try using query variants or expanding foundational knowledge")
                
                if not (abs(query_norm - 1.0) < 0.01 and abs(doc_norm - 1.0) < 0.01):
                    logger.warning("   ⚠️  Embeddings are not normalized")
                    logger.warning("   💡 Consider normalizing embeddings before storing in ChromaDB")
                    logger.warning("   💡 This will improve cosine similarity calculations")
                
                if chroma_distance > 2.0:
                    logger.warning("   ⚠️  ChromaDB distance is very high (> 2.0)")
                    logger.warning("   💡 This suggests embeddings don't match semantically")
                    logger.warning("   💡 Or ChromaDB is using L2 distance on unnormalized vectors")
        
        logger.info("\n" + "="*60)
        logger.info("Diagnosis complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    diagnose_embedding_distance()

