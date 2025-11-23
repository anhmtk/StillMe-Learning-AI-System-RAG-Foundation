#!/usr/bin/env python3
"""
Script to add validation and self-improvement knowledge to RAG
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


def add_validation_knowledge():
    """Add validation and self-improvement knowledge to RAG"""
    
    # Read validation knowledge file
    validation_file = project_root / "docs" / "rag" / "validation_self_improvement.md"
    
    if not validation_file.exists():
        logger.error(f"❌ Validation knowledge file not found: {validation_file}")
        return False
    
    with open(validation_file, 'r', encoding='utf-8') as f:
        validation_content = f.read()
    
    logger.info("Initializing RAG components...")
    
    # Initialize components
    embedding_service = EmbeddingService()
    chroma_client = ChromaClient(embedding_service=embedding_service)
    rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
    
    logger.info("Adding validation and self-improvement knowledge to RAG...")
    
    # Add validation knowledge
    try:
        import uuid
        doc_id = f"validation_self_improvement_{uuid.uuid4().hex[:8]}"
        
        chroma_client.add_knowledge(
            documents=[validation_content],
            metadatas=[{
                "source": "StillMe Internal Documentation",
                "content_type": "technical",
                "domain": "stillme_validation_self_improvement",
                "title": "StillMe Validation & Self-Improvement Mechanism",
                "is_foundational": True
            }],
            ids=[doc_id]
        )
        logger.info("✅ Validation and self-improvement knowledge added successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to add validation knowledge: {e}")
        return False


if __name__ == "__main__":
    success = add_validation_knowledge()
    if success:
        print("\n✅ Validation knowledge added to RAG!")
        print("StillMe can now answer questions about validation and self-improvement using RAG knowledge.")
    else:
        print("\n❌ Failed to add validation knowledge")
        sys.exit(1)

