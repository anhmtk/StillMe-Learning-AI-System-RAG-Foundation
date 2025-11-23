#!/usr/bin/env python3
"""
Script to add historical facts knowledge to RAG
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


def add_historical_facts():
    """Add historical facts knowledge to RAG"""
    
    # Read historical facts file
    historical_file = project_root / "docs" / "rag" / "historical_facts.md"
    
    if not historical_file.exists():
        logger.error(f"❌ Historical facts file not found: {historical_file}")
        return False
    
    with open(historical_file, 'r', encoding='utf-8') as f:
        historical_content = f.read()
    
    logger.info("Initializing RAG components...")
    
    # Initialize components
    embedding_service = EmbeddingService()
    chroma_client = ChromaClient(embedding_service=embedding_service)
    rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
    
    logger.info("Adding historical facts knowledge to RAG...")
    
    # Add historical knowledge
    try:
        import uuid
        doc_id = f"historical_facts_{uuid.uuid4().hex[:8]}"
        
        chroma_client.add_knowledge(
            documents=[historical_content],
            metadatas=[{
                "source": "Wikipedia, Academic Sources, Historical Records",
                "content_type": "historical",
                "domain": "world_history",
                "title": "Historical Facts and Events",
                "is_foundational": True
            }],
            ids=[doc_id]
        )
        logger.info("✅ Historical facts knowledge added successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to add historical facts: {e}")
        return False


if __name__ == "__main__":
    success = add_historical_facts()
    if success:
        print("\n✅ Historical facts added to RAG!")
        print("StillMe can now answer questions about historical events using RAG knowledge.")
        print("Coverage includes: Vietnam history, world economic history, political history,")
        print("scientific history, Asian history, Middle East, Africa, modern history, ancient history,")
        print("religious history, economic history, and space history.")
    else:
        print("\n❌ Failed to add historical facts")
        sys.exit(1)

