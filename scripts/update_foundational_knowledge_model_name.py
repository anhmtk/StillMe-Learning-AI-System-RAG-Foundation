#!/usr/bin/env python3
"""
Script to update foundational knowledge with correct embedding model name

This script updates the foundational knowledge in RAG database to ensure
StillMe always mentions the correct embedding model: paraphrase-multilingual-MiniLM-L12-v2
(not all-MiniLM-L6-v2)
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
from stillme_core.rag.model_info import EMBEDDING_MODEL_NAME, get_embedding_model_display_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_foundational_knowledge():
    """Update foundational knowledge with correct model name"""
    
    logger.info("="*60)
    logger.info("Updating Foundational Knowledge - Model Name Fix")
    logger.info("="*60)
    
    # Initialize services
    logger.info("Initializing services...")
    embedding_service = EmbeddingService(model_name=EMBEDDING_MODEL_NAME)
    chroma_client = ChromaClient(embedding_service=embedding_service)
    rag_retrieval = RAGRetrieval(chroma_client=chroma_client, embedding_service=embedding_service)
    
    # Get current model info
    model_display = get_embedding_model_display_name()
    logger.info(f"Current embedding model: {EMBEDDING_MODEL_NAME}")
    logger.info(f"Model display: {model_display}")
    
    # Search for foundational knowledge documents with old model name
    logger.info("\nSearching for foundational knowledge with old model name...")
    
    # Search for documents containing old model name
    old_model_queries = [
        "all-MiniLM-L6-v2",
        "all MiniLM L6 v2",
        "embedding model all-MiniLM"
    ]
    
    found_docs = []
    for query in old_model_queries:
        results = rag_retrieval.retrieve_context(
            query=query,
            knowledge_limit=10,
            similarity_threshold=0.01  # Very low threshold to find any matches
        )
        
        knowledge_docs = results.get("knowledge_documents", [])
        for doc in knowledge_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            # Check if it's foundational knowledge and has old model name
            if (metadata.get("source") == "CRITICAL_FOUNDATION" and 
                ("all-MiniLM-L6-v2" in content or "all MiniLM L6" in content)):
                found_docs.append({
                    "id": doc.get("id"),
                    "content": content,
                    "metadata": metadata
                })
    
    logger.info(f"Found {len(found_docs)} foundational knowledge documents with old model name")
    
    if not found_docs:
        logger.info("✅ No documents found with old model name - foundational knowledge is up to date!")
        return
    
    # Update each document
    logger.info(f"\nUpdating {len(found_docs)} documents...")
    
    updated_count = 0
    for doc in found_docs:
        old_content = doc["content"]
        
        # Replace old model name with new one
        new_content = old_content.replace(
            "all-MiniLM-L6-v2",
            EMBEDDING_MODEL_NAME
        )
        new_content = new_content.replace(
            "all MiniLM L6 v2",
            EMBEDDING_MODEL_NAME
        )
        new_content = new_content.replace(
            "all-MiniLM-L6",
            EMBEDDING_MODEL_NAME
        )
        
        # Also add explicit note if not present
        if "KHÔNG phải all-MiniLM-L6-v2" not in new_content and "NOT all-MiniLM-L6-v2" not in new_content:
            # Add note in Vietnamese and English
            if "Embedding Model:" in new_content or "Mô hình embedding:" in new_content:
                new_content = new_content.replace(
                    f"`{EMBEDDING_MODEL_NAME}`",
                    f"`{EMBEDDING_MODEL_NAME}` (CRITICAL: This is the CURRENT model, NOT all-MiniLM-L6-v2)"
                )
        
        if new_content != old_content:
            # Update document in ChromaDB
            try:
                # Delete old document
                chroma_client.delete_documents(
                    collection_name="stillme_knowledge",
                    ids=[doc["id"]]
                )
                
                # Add updated document
                chroma_client.add_documents(
                    collection_name="stillme_knowledge",
                    documents=[new_content],
                    metadatas=[doc["metadata"]],
                    ids=[doc["id"]]
                )
                
                updated_count += 1
                logger.info(f"✅ Updated document {doc['id'][:8]}...")
            except Exception as e:
                logger.error(f"❌ Failed to update document {doc['id'][:8]}...: {e}")
    
    logger.info(f"\n✅ Updated {updated_count}/{len(found_docs)} documents")
    logger.info("\n" + "="*60)
    logger.info("Next steps:")
    logger.info("1. Clear LLM cache to force regeneration of responses")
    logger.info("2. Test StillMe response to verify correct model name")
    logger.info("="*60)

if __name__ == "__main__":
    update_foundational_knowledge()

