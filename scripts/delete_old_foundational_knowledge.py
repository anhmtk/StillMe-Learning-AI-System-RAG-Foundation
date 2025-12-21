#!/usr/bin/env python3
"""
Delete old foundational knowledge from ChromaDB

This script deletes the old "StillMe Core Mechanism - Technical Architecture" 
document from ChromaDB so that the new version can be injected on next server restart.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_old_foundational_knowledge():
    """Delete old foundational knowledge documents from ChromaDB"""
    try:
        logger.info("🔧 Initializing ChromaDB client...")
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        
        logger.info("🔍 Searching for old foundational knowledge documents...")
        
        # Use the same method as in backend/api/main.py
        # Search for documents with source="CRITICAL_FOUNDATION" and title="StillMe Core Mechanism - Technical Architecture"
        old_title = "StillMe Core Mechanism - Technical Architecture"
        
        # Generate a query embedding to search for foundational knowledge
        from backend.vector_db.embeddings import EmbeddingService
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        query_text = "StillMe Core Mechanism Technical Architecture"
        query_embedding = embedding_service.encode_text(query_text)
        
        logger.info("🔍 Searching for foundational knowledge documents...")
        
        # Search for documents (this will find all foundational knowledge)
        all_results = chroma_client.search_knowledge(
            query_embedding=query_embedding,
            limit=100  # Get many results to find all foundational docs
        )
        
        foundational_ids_to_delete = []
        for result in all_results:
            metadata = result.get("metadata", {})
            title = metadata.get("title", "")
            source = metadata.get("source", "")
            
            # Delete if it matches the old title
            if title == old_title or (source == "CRITICAL_FOUNDATION" and "Technical Architecture" in title):
                doc_id = result.get("id")
                if doc_id:
                    foundational_ids_to_delete.append(doc_id)
                    logger.info(f"   Found document to delete: ID={doc_id}, title={title}")
        
        if not foundational_ids_to_delete:
            logger.info("✅ No old foundational knowledge documents found. Nothing to delete.")
            return True
        
        logger.info(f"🗑️  Deleting {len(foundational_ids_to_delete)} old foundational knowledge document(s)...")
        
        # Delete documents by IDs
        chroma_client.knowledge_collection.delete(ids=foundational_ids_to_delete)
        
        logger.info(f"✅ Successfully deleted {len(foundational_ids_to_delete)} old foundational knowledge document(s)")
        logger.info("")
        logger.info("💡 Next steps:")
        logger.info("   1. Restart server to inject new foundational knowledge")
        logger.info("   2. The new version will be automatically injected on startup")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to delete old foundational knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = delete_old_foundational_knowledge()
    sys.exit(0 if success else 1)

