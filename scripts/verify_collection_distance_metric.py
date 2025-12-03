#!/usr/bin/env python3
"""
Script to verify ChromaDB collection distance metric.

This script checks if collections are using cosine distance metric
and tests retrieval to verify distance values are correct.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def verify_collection_distance_metric(collection_name: str = "stillme_knowledge"):
    """
    Verify collection distance metric and test retrieval.
    
    Args:
        collection_name: Name of collection to verify
    """
    logger.info("="*60)
    logger.info(f"Verifying Collection Distance Metric: {collection_name}")
    logger.info("="*60)
    
    try:
        # Initialize services
        logger.info("\n1. Initializing services...")
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        logger.info("✅ Services initialized")
        
        # Get collection
        logger.info(f"\n2. Getting collection '{collection_name}'...")
        try:
            collection = chroma_client.client.get_collection(name=collection_name)
            logger.info("✅ Collection found")
        except Exception as e:
            logger.error(f"❌ Collection not found: {e}")
            return
        
        # Check collection metadata
        logger.info(f"\n3. Checking collection metadata...")
        metadata = collection.metadata or {}
        logger.info(f"   Metadata: {metadata}")
        
        # Check for distance metric configuration
        distance_metric = metadata.get("hnsw:space", "unknown")
        if distance_metric == "cosine":
            logger.info("   ✅ Collection uses COSINE distance metric")
        elif distance_metric == "l2":
            logger.warning("   ⚠️ Collection uses L2 distance metric (should be cosine)")
        else:
            logger.warning(f"   ⚠️ Collection distance metric: {distance_metric} (expected: cosine)")
        
        # Get collection info
        count = collection.count()
        logger.info(f"\n4. Collection info:")
        logger.info(f"   Documents: {count}")
        
        if count == 0:
            logger.warning("   ⚠️ Collection is empty - no documents to test")
            return
        
        # Test retrieval with foundational knowledge query
        logger.info(f"\n5. Testing retrieval with foundational knowledge query...")
        test_query = "Do you track your own execution time?"
        logger.info(f"   Query: '{test_query}'")
        
        # Generate query embedding
        query_embedding = embedding_service.encode_text(test_query)
        query_norm = sum(x**2 for x in query_embedding)**0.5
        logger.info(f"   Query embedding norm: {query_norm:.6f}")
        if abs(query_norm - 1.0) < 0.01:
            logger.info("   ✅ Query embedding is normalized (unit vector)")
        else:
            logger.warning(f"   ⚠️ Query embedding is NOT normalized (norm={query_norm:.6f})")
        
        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where={"source": "CRITICAL_FOUNDATION"} if "knowledge" in collection_name.lower() else None
        )
        
        if results and results.get("distances") and results["distances"][0]:
            distances = results["distances"][0]
            min_distance = min(distances)
            max_distance = max(distances)
            avg_distance = sum(distances) / len(distances)
            
            logger.info(f"\n6. Retrieval Results:")
            logger.info(f"   Documents retrieved: {len(distances)}")
            logger.info(f"   Distance range: {min_distance:.6f} - {max_distance:.6f}")
            logger.info(f"   Average distance: {avg_distance:.6f}")
            
            # Interpret distance based on metric
            if distance_metric == "cosine":
                # Cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
                # For normalized vectors, cosine distance = 1 - cosine_similarity
                # Good similarity: distance < 0.5 (similarity > 0.5)
                # Moderate similarity: distance 0.5-0.8 (similarity 0.2-0.5)
                # Poor similarity: distance > 0.8 (similarity < 0.2)
                
                if min_distance < 0.5:
                    logger.info("   ✅ Distance looks good! (cosine distance < 0.5)")
                    logger.info("   ✅ Documents should be retrievable with good similarity")
                elif min_distance < 0.8:
                    logger.warning("   ⚠️ Distance is moderate (cosine distance 0.5-0.8)")
                    logger.info("   💡 May need lower similarity threshold for retrieval")
                else:
                    logger.warning("   ⚠️ Distance is high (cosine distance > 0.8)")
                    logger.info("   💡 Documents may not be retrievable effectively")
                
                # Convert to similarity for clarity
                min_similarity = 1.0 - min_distance
                logger.info(f"   Estimated cosine similarity: {min_similarity:.6f}")
                
            elif distance_metric == "l2":
                # L2 distance: varies with vector magnitude
                # For normalized vectors (norm=1), L2 distance range: 0 to 2
                # Good similarity: distance < 0.5
                # Moderate similarity: distance 0.5-1.0
                # Poor similarity: distance > 1.0
                
                if min_distance < 0.5:
                    logger.info("   ✅ Distance looks good! (L2 distance < 0.5)")
                elif min_distance < 1.0:
                    logger.warning("   ⚠️ Distance is moderate (L2 distance 0.5-1.0)")
                else:
                    logger.warning("   ⚠️ Distance is high (L2 distance > 1.0)")
                    logger.warning("   ⚠️ Collection should use cosine distance for normalized embeddings!")
                
            else:
                logger.warning(f"   ⚠️ Unknown distance metric: {distance_metric}")
                logger.info("   💡 Cannot interpret distance values")
            
            # Show document previews
            if results.get("documents") and results["documents"][0]:
                logger.info(f"\n7. Retrieved Documents Preview:")
                for i, (doc, dist) in enumerate(zip(results["documents"][0][:3], distances[:3]), 1):
                    preview = doc[:200] + "..." if len(doc) > 200 else doc
                    logger.info(f"\n   [{i}] Distance: {dist:.6f}")
                    logger.info(f"       Preview: {preview}")
        else:
            logger.warning("   ⚠️ No results returned from query")
        
        logger.info("\n" + "="*60)
        logger.info("Verification complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}", exc_info=True)
        raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify ChromaDB collection distance metric"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="stillme_knowledge",
        help="Collection name to verify (default: stillme_knowledge)"
    )
    args = parser.parse_args()
    
    verify_collection_distance_metric(args.collection)


if __name__ == "__main__":
    main()

