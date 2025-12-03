#!/usr/bin/env python3
"""
Script to re-embed foundational knowledge with the current embedding model.

This ensures foundational knowledge uses the same embedding model as queries,
fixing high distance/similarity issues.
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


def re_embed_foundational_knowledge():
    """
    Re-embed all CRITICAL_FOUNDATION documents with the current embedding model.
    """
    logger.info("="*60)
    logger.info("Re-embedding Foundational Knowledge")
    logger.info("="*60)
    
    try:
        # Initialize RAG components
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Get all CRITICAL_FOUNDATION documents
        logger.info("\n1. Finding all CRITICAL_FOUNDATION documents...")
        
        # Search with a very generic query to get all foundational docs
        # We'll use a dummy embedding to search, then filter by metadata
        try:
            # Get collection
            collection = chroma_client.knowledge_collection
            
            # Query all documents with CRITICAL_FOUNDATION source
            # ChromaDB doesn't support direct metadata filtering in query, so we'll get all and filter
            results = collection.get(
                where={"source": "CRITICAL_FOUNDATION"},
                include=["documents", "metadatas", "embeddings"]
            )
            
            foundational_docs = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"]):
                    foundational_docs.append({
                        "id": doc_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        "old_embedding": results["embeddings"][i] if results["embeddings"] else None
                    })
            
            logger.info(f"   ✅ Found {len(foundational_docs)} CRITICAL_FOUNDATION documents")
            
            if not foundational_docs:
                logger.warning("   ⚠️  No CRITICAL_FOUNDATION documents found!")
                logger.warning("   💡 Run: python scripts/add_foundational_knowledge.py first")
                return
            
            # Re-embed each document
            logger.info(f"\n2. Re-embedding {len(foundational_docs)} documents with current model...")
            logger.info(f"   Model: {embedding_service.model_name}")
            logger.info(f"   Dimensions: {embedding_service.embedding_dimensions}")
            
            re_embedded_count = 0
            for i, doc in enumerate(foundational_docs, 1):
                logger.info(f"\n   [{i}/{len(foundational_docs)}] Re-embedding: {doc['metadata'].get('title', doc['id'])}")
                
                # Generate new embedding
                new_embedding = embedding_service.encode_text(doc["content"])
                logger.info(f"      ✅ Generated new embedding: {len(new_embedding)} dimensions")
                
                # Delete old document
                try:
                    collection.delete(ids=[doc["id"]])
                    logger.info(f"      ✅ Deleted old document")
                except Exception as e:
                    logger.warning(f"      ⚠️  Could not delete old document: {e}")
                
                # Add new document with new embedding
                try:
                    collection.add(
                        ids=[doc["id"]],
                        documents=[doc["content"]],
                        metadatas=[doc["metadata"]],
                        embeddings=[new_embedding]
                    )
                    logger.info(f"      ✅ Added document with new embedding")
                    re_embedded_count += 1
                except Exception as e:
                    logger.error(f"      ❌ Failed to add document: {e}")
                    # Try to restore old document if possible
                    if doc.get("old_embedding"):
                        try:
                            collection.add(
                                ids=[doc["id"]],
                                documents=[doc["content"]],
                                metadatas=[doc["metadata"]],
                                embeddings=[doc["old_embedding"]]
                            )
                            logger.info(f"      ✅ Restored old document")
                        except Exception as restore_error:
                            logger.error(f"      ❌ Failed to restore old document: {restore_error}")
            
            logger.info(f"\n3. Re-embedding complete!")
            logger.info(f"   ✅ Successfully re-embedded: {re_embedded_count}/{len(foundational_docs)} documents")
            
            # Test retrieval
            logger.info(f"\n4. Testing retrieval with re-embedded documents...")
            test_query = "Do you track your own execution time?"
            test_embedding = embedding_service.encode_text(test_query)
            
            test_results = collection.query(
                query_embeddings=[test_embedding],
                n_results=5,
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            if test_results and test_results.get("distances") and test_results["distances"][0]:
                distances = test_results["distances"][0]
                min_distance = min(distances)
                max_distance = max(distances)
                avg_distance = sum(distances) / len(distances)
                
                logger.info(f"   ✅ Test query: '{test_query}'")
                logger.info(f"   Distance range: {min_distance:.3f} - {max_distance:.3f}")
                logger.info(f"   Average distance: {avg_distance:.3f}")
                
                # Convert to similarity (assuming L2 distance, approximate cosine similarity)
                # For normalized vectors: cosine_sim ≈ 1 - (L2^2 / 2)
                # But this is approximate - actual similarity depends on normalization
                min_similarity = 1.0 - (min_distance ** 2 / 2) if min_distance < 2.0 else -1.0
                logger.info(f"   Estimated similarity: {min_similarity:.3f}")
                
                if min_distance < 1.0:
                    logger.info("   ✅ Distance looks good! Documents should be retrievable")
                elif min_distance < 2.0:
                    logger.warning("   ⚠️  Distance is moderate - may need lower threshold")
                else:
                    logger.warning("   ⚠️  Distance is still high - may need to check embedding model or normalization")
            else:
                logger.warning("   ⚠️  No test results returned")
            
            logger.info("\n" + "="*60)
            logger.info("Re-embedding complete!")
            logger.info("Next steps:")
            logger.info("1. Clear LLM cache: python scripts/clear_cache_railway.ps1 -Pattern llm:response:*")
            logger.info("2. Test StillMe response: python scripts/test_self_tracking_query.py --backend-url <url>")
            logger.info("="*60)
        
        except Exception as e:
            logger.error(f"❌ Error re-embedding foundational knowledge: {e}", exc_info=True)
            raise
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    re_embed_foundational_knowledge()

