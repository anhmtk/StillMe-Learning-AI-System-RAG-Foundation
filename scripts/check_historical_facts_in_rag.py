#!/usr/bin/env python3
"""
Script to check if historical_facts.md has been loaded into ChromaDB
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from backend.vector_db.rag_retrieval import RAGRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_historical_facts_in_rag():
    """Check if historical facts are in ChromaDB"""
    
    logger.info("Initializing RAG components...")
    
    # Initialize components
    embedding_service = EmbeddingService()
    chroma_client = ChromaClient(embedding_service=embedding_service)
    rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
    
    logger.info("Checking if historical facts are in ChromaDB...")
    
    # Method 1: Check by metadata
    try:
        knowledge_collection = chroma_client.knowledge_collection
        
        # Get all documents with historical metadata
        result = knowledge_collection.get(
            where={"content_type": "historical"},
            limit=100
        )
        
        if result and result.get("ids"):
            ids = result.get("ids", [])
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])
            
            logger.info(f"✅ Found {len(ids)} historical documents in ChromaDB")
            
            # Check if Geneva 1954 is in any document
            geneva_found = False
            for i, doc in enumerate(documents):
                if "Geneva" in doc and "1954" in doc:
                    geneva_found = True
                    logger.info(f"✅ Geneva 1954 found in document ID: {ids[i]}")
                    logger.info(f"   Metadata: {metadatas[i]}")
                    logger.info(f"   Content preview (first 200 chars): {doc[:200]}...")
                    break
            
            if not geneva_found:
                logger.warning("⚠️ Geneva 1954 NOT found in historical documents")
            
            # Show all historical document IDs
            logger.info(f"\n📋 All historical document IDs:")
            for i, doc_id in enumerate(ids):
                logger.info(f"   - {doc_id}: {metadatas[i].get('title', 'No title')}")
        else:
            logger.warning("⚠️ No historical documents found in ChromaDB")
            logger.warning("   This means add_historical_facts.py has NOT been run yet!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking historical documents: {e}")
        return False
    
    # Method 2: Try semantic search for "Geneva 1954" using retrieve_context
    logger.info("\n🔍 Method 2: Semantic search for 'Geneva 1954'...")
    try:
        # Test with Vietnamese query (same as test)
        query_vi = "Hiệp ước Geneva 1954 đã quyết định những gì về Việt Nam?"
        query_en = "Geneva 1954 Vietnam partition 17th parallel"
        
        logger.info(f"   Testing Vietnamese query: {query_vi}")
        results_vi = rag_retrieval.retrieve_context(
            query=query_vi,
            knowledge_limit=5,
            similarity_threshold=0.1  # Use same threshold as chat_router
        )
        
        if results_vi and results_vi.get("knowledge_docs"):
            docs = results_vi["knowledge_docs"]
            logger.info(f"✅ Semantic search (Vietnamese) found {len(docs)} relevant documents")
            
            geneva_found_semantic = False
            for i, doc in enumerate(docs):
                if "Geneva" in doc and "1954" in doc:
                    geneva_found_semantic = True
                    logger.info(f"✅ Geneva 1954 found via semantic search (rank {i+1})")
                    logger.info(f"   Content preview: {doc[:300]}...")
                    # Check similarity score if available
                    if results_vi.get("similarities"):
                        logger.info(f"   Similarity score: {results_vi['similarities'][i] if i < len(results_vi['similarities']) else 'N/A'}")
                    break
            
            if not geneva_found_semantic:
                logger.warning("⚠️ Geneva 1954 NOT found via semantic search (Vietnamese query)")
                logger.warning("   This might indicate:")
                logger.warning("   1. Similarity threshold too high (current: 0.1)")
                logger.warning("   2. Embedding quality issue (Vietnamese vs English)")
                logger.warning("   3. Query not matching document content")
                logger.warning(f"   Documents found: {len(docs)}")
                if docs:
                    first_doc = docs[0] if isinstance(docs[0], str) else str(docs[0])
                    logger.warning(f"   First doc preview: {first_doc[:200]}...")
        else:
            logger.warning("⚠️ Semantic search (Vietnamese) returned no results")
            logger.warning(f"   Results: {results_vi}")
            logger.warning("   This means RAG retrieval is not finding historical facts")
            
        # Also test with English query
        logger.info(f"\n   Testing English query: {query_en}")
        results_en = rag_retrieval.retrieve_context(
            query=query_en,
            knowledge_limit=5,
            similarity_threshold=0.1
        )
        
        if results_en and results_en.get("knowledge_docs"):
            docs_en = results_en["knowledge_docs"]
            logger.info(f"✅ Semantic search (English) found {len(docs_en)} relevant documents")
            
            geneva_found_en = False
            for i, doc in enumerate(docs_en):
                if "Geneva" in doc and "1954" in doc:
                    geneva_found_en = True
                    logger.info(f"✅ Geneva 1954 found via semantic search (English, rank {i+1})")
                    logger.info(f"   Content preview: {doc[:300]}...")
                    break
            
            if not geneva_found_en:
                logger.warning("⚠️ Geneva 1954 NOT found via semantic search (English query)")
        else:
            logger.warning("⚠️ Semantic search (English) returned no results")
            
    except Exception as e:
        logger.error(f"❌ Error in semantic search: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 Checking if historical_facts.md is in ChromaDB")
    print("="*60 + "\n")
    
    success = check_historical_facts_in_rag()
    
    if success:
        print("\n✅ Historical facts ARE in ChromaDB")
        print("   If Geneva 1954 is still not found, the issue might be:")
        print("   1. RAG retrieval similarity threshold too high")
        print("   2. Query embedding not matching document embedding")
        print("   3. Need to check retrieval parameters")
    else:
        print("\n❌ Historical facts are NOT in ChromaDB")
        print("   ACTION REQUIRED: Run 'python scripts/add_historical_facts.py' to load historical facts")
    
    print("\n" + "="*60)

