#!/usr/bin/env python3
"""
Script to test ChromaDB scalability with different document counts
Measures search latency as database size increases
"""

import sys
import os
import time
import statistics
from pathlib import Path
from typing import Dict, List, Any
import uuid

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_documents(count: int) -> List[str]:
    """Generate test documents"""
    documents = []
    for i in range(count):
        doc = f"Test document {i+1}. This is a sample document for scalability testing. " \
              f"It contains some text about artificial intelligence, machine learning, " \
              f"and natural language processing. Document ID: {uuid.uuid4().hex[:8]}"
        documents.append(doc)
    return documents


def measure_search_latency(
    chroma_client: ChromaClient,
    embedding_service: EmbeddingService,
    query: str,
    num_tests: int = 10
) -> Dict[str, float]:
    """Measure search latency"""
    query_embedding = embedding_service.encode_text(query)
    latencies = []
    
    for i in range(num_tests):
        start = time.time()
        results = chroma_client.search_knowledge(query_embedding, limit=5)
        elapsed = time.time() - start
        latencies.append(elapsed)
        time.sleep(0.05)
    
    return {
        "average": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "median": statistics.median(latencies),
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    }


def test_scalability(test_sizes: List[int] = [100, 500, 1000, 5000, 10000]) -> Dict[str, Any]:
    """Test ChromaDB scalability at different document counts"""
    logger.info("="*80)
    logger.info("ChromaDB Scalability Test")
    logger.info("="*80)
    
    # Use temporary directory for testing
    test_db_path = project_root / "data" / "test_vector_db"
    test_db_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize ChromaDB client and embedding service
    embedding_service = EmbeddingService()
    chroma_client = ChromaClient(
        persist_directory=str(test_db_path),
        reset_on_error=True,
        embedding_service=embedding_service
    )
    
    results = {}
    test_query = "What is artificial intelligence?"
    
    # Get initial stats
    initial_stats = chroma_client.get_collection_stats()
    logger.info(f"Initial database state: {initial_stats}")
    
    cumulative_docs = initial_stats.get("knowledge_documents", 0)
    
    for size in test_sizes:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing with {size} documents (cumulative: {cumulative_docs + size})")
        logger.info(f"{'='*80}")
        
        # Add documents to reach target size
        docs_to_add = size - cumulative_docs
        if docs_to_add > 0:
            logger.info(f"Adding {docs_to_add} documents...")
            test_docs = generate_test_documents(docs_to_add)
            start_add = time.time()
            
            # Add in batches of 100
            batch_size = 100
            for i in range(0, len(test_docs), batch_size):
                batch = test_docs[i:i+batch_size]
                ids = [f"test_doc_{cumulative_docs + i + j}" for j in range(len(batch))]
                metadatas = [{"source": "scalability_test", "index": cumulative_docs + i + j} for j in range(len(batch))]
                
                chroma_client.add_knowledge(
                    documents=batch,
                    metadatas=metadatas,
                    ids=ids
                )
                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"  Added {i + len(batch)}/{len(test_docs)} documents...")
            
            add_time = time.time() - start_add
            cumulative_docs += docs_to_add
            logger.info(f"✅ Added {docs_to_add} documents in {add_time:.2f}s")
        else:
            logger.info(f"Already have {cumulative_docs} documents, skipping addition")
        
        # Measure search latency
        logger.info(f"Measuring search latency...")
        latency = measure_search_latency(chroma_client, embedding_service, test_query, num_tests=10)
        
        # Get collection stats
        stats = chroma_client.get_collection_stats()
        
        # Calculate database size (rough estimate)
        # Each document: ~200 chars text + 384-dim embedding (4 bytes/float) = ~1.7KB
        estimated_size_mb = (cumulative_docs * 1.7) / 1024
        
        results[f"{size}_docs"] = {
            "document_count": cumulative_docs,
            "search_latency": latency,
            "add_time": add_time if docs_to_add > 0 else 0.0,
            "estimated_size_mb": round(estimated_size_mb, 2),
            "collection_stats": stats
        }
        
        logger.info(f"✅ Search latency: {latency['average']:.3f}s avg (min: {latency['min']:.3f}s, max: {latency['max']:.3f}s)")
        logger.info(f"✅ Estimated size: {estimated_size_mb:.2f} MB")
    
    # Cleanup
    logger.info(f"\n{'='*80}")
    logger.info("Cleaning up test database...")
    try:
        import shutil
        if test_db_path.exists():
            shutil.rmtree(test_db_path)
            logger.info("✅ Test database cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Could not clean up test database: {e}")
    
    return results


if __name__ == "__main__":
    # Test with smaller sizes for faster execution
    test_sizes = [100, 500, 1000, 2000]  # Reduced for faster testing
    
    results = test_scalability(test_sizes)
    
    print("\n" + "="*80)
    print("SCALABILITY TEST RESULTS")
    print("="*80)
    
    for size_key, data in results.items():
        print(f"\n{size_key}:")
        print(f"  Documents: {data['document_count']}")
        print(f"  Search Latency: {data['search_latency']['average']:.3f}s avg")
        print(f"  Estimated Size: {data['estimated_size_mb']} MB")
    
    # Save results
    import json
    output_file = project_root / "data" / "scalability_test_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_file}")

