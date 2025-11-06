#!/usr/bin/env python3
"""
Script to add StillMe foundational knowledge to RAG
This ensures StillMe can answer questions about itself using RAG, not outdated LLM knowledge
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from backend.vector_db.rag_retrieval import RAGRetrieval
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Foundational knowledge about StillMe
FOUNDATIONAL_KNOWLEDGE = """
[FOUNDATIONAL:STILLME] StillMe is a self-evolving AI system that **transcends the time limitations** of base LLM models. StillMe uses **RAG (Retrieval-Augmented Generation)** to learn from trusted sources (RSS feeds, arXiv, public APIs) **every few hours**, ensuring knowledge is always up-to-date. This continuous learning capability is the core differentiator of StillMe - it overcomes the knowledge cutoff limitation that affects traditional LLMs.

**Key Features:**
- **Continuous Learning**: StillMe automatically fetches and learns from RSS feeds every 4 hours (6 cycles per day)
- **RAG-Based Knowledge**: All knowledge is stored in a vector database (ChromaDB) and retrieved using semantic search
- **Transparency**: Every learning source is visible and auditable - no black box learning
- **Self-Diagnosis**: StillMe can identify knowledge gaps and prioritize what to learn next
- **Content Curation**: Intelligent filtering and prioritization of learning content based on quality and relevance
- **Pre-Filter System**: Filters content BEFORE embedding to reduce costs by 30-50%
- **Knowledge Alerts**: Proactively suggests important knowledge to users when StillMe learns something relevant

**How StillMe Learns:**
1. Automated scheduler fetches RSS feeds every 4 hours
2. Content is pre-filtered for quality (minimum length, keyword relevance)
3. High-quality content is embedded and stored in vector database
4. When users ask questions, StillMe retrieves relevant context from vector database
5. Responses are generated using retrieved context, ensuring accuracy and up-to-date information

**Transparency & Ethics:**
- 100% open source - every algorithm is public
- Complete audit trail of all learning decisions
- Community governance for ethical guidelines
- No black box - users can see exactly what StillMe learns and from where

StillMe is not limited by training data cutoff dates - it continuously evolves and updates its knowledge base through automated learning cycles.
"""


def add_foundational_knowledge():
    """Add foundational StillMe knowledge to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Adding foundational StillMe knowledge to RAG...")
        
        # Add foundational knowledge with special metadata
        success = rag_retrieval.add_learning_content(
            content=FOUNDATIONAL_KNOWLEDGE,
            source="foundational",
            content_type="knowledge",
            metadata={
                "title": "StillMe Foundational Knowledge - Self-Evolving AI System",
                "foundational": "stillme",
                "type": "foundational",
                "tags": ["foundational:stillme", "stillme", "rag", "self-evolving", "continuous-learning"],
                "importance_score": 1.0,  # Maximum importance
                "description": "Core knowledge about StillMe's architecture, learning process, and capabilities"
            }
        )
        
        if success:
            logger.info("✅ Foundational knowledge added successfully!")
            logger.info("StillMe can now answer questions about itself using RAG knowledge.")
            return True
        else:
            logger.error("❌ Failed to add foundational knowledge")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding foundational knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("StillMe Foundational Knowledge Setup")
    print("=" * 60)
    print()
    print("This script adds foundational knowledge about StillMe to the RAG system.")
    print("This ensures StillMe can answer questions about itself using up-to-date")
    print("RAG knowledge, not outdated LLM training data.")
    print()
    
    success = add_foundational_knowledge()
    
    if success:
        print()
        print("✅ Setup complete!")
        print()
        print("Next steps:")
        print("1. Test by asking: 'What is StillMe?' or 'How does StillMe learn?'")
        print("2. Verify that StillMe uses RAG citations [1], [2] in responses")
        print("3. Check that responses mention continuous learning and RAG capabilities")
    else:
        print()
        print("❌ Setup failed. Check logs above for details.")
        sys.exit(1)

