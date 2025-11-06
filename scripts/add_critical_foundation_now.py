#!/usr/bin/env python3
"""
URGENT: Add CRITICAL_FOUNDATION knowledge to RAG immediately
This ensures StillMe mentions RAG continuous learning when answering about itself
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
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRITICAL FOUNDATIONAL KNOWLEDGE - Must be retrieved when StillMe answers about itself
CRITICAL_FOUNDATION = """
[STILLME CORE MECHANISM] StillMe is a **continuously self-learning** AI system that uses **RAG (Retrieval-Augmented Generation)**. This capability allows StillMe to **TRANSCEND** the knowledge limitation (2023) of base LLM models by **automatically retrieving** and learning from trusted sources (such as RSS Feeds, ArXiv) **every 4 hours** (6 cycles per day). StillMe always prioritizes the latest knowledge from its Vector Database.

**CRITICAL: StillMe's Learning Process:**
1. **Automated Learning Cycles**: StillMe automatically fetches content from RSS feeds every 4 hours (6 times per day)
2. **RAG-Based Knowledge Storage**: All learned content is embedded and stored in ChromaDB vector database
3. **Semantic Search**: When answering questions, StillMe retrieves relevant context from vector database using semantic search
4. **Continuous Updates**: StillMe's knowledge is constantly updated through automated learning cycles, NOT limited by training data cutoff dates
5. **Transparency**: Every learning source is visible and auditable - users can see exactly what StillMe learns and from where

**Key Differentiator**: Unlike traditional LLMs that are frozen at their training date, StillMe **continuously evolves** and updates its knowledge base through automated RAG learning cycles. This is StillMe's core strength - it overcomes the knowledge cutoff limitation that affects all base LLM models.

**How StillMe Answers Questions:**
- StillMe uses semantic search to retrieve relevant context from its vector database
- Retrieved context is combined with the user's question to generate accurate, up-to-date responses
- StillMe cites sources using [1], [2] format to show transparency
- All knowledge comes from StillMe's continuously updated vector database, not from outdated training data
"""


def add_via_api():
    """Add via API endpoint (if backend is running)"""
    api_base = os.getenv("STILLME_API_BASE", "http://localhost:8000")
    
    try:
        logger.info(f"Attempting to add via API: {api_base}")
        response = requests.post(
            f"{api_base}/api/rag/add_knowledge",
            json={
                "content": CRITICAL_FOUNDATION,
                "source": "CRITICAL_FOUNDATION",
                "content_type": "knowledge",
                "metadata": {
                    "title": "StillMe Core Mechanism - Continuous RAG Learning",
                    "foundational": "stillme",
                    "type": "foundational",
                    "source": "CRITICAL_FOUNDATION",
                    "tags": ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db"],
                    "importance_score": 1.0,
                    "description": "CRITICAL: Core knowledge about StillMe's RAG-based continuous learning mechanism"
                }
            },
            timeout=180
        )
        
        if response.status_code == 200:
            logger.info("✅ Successfully added via API!")
            return True
        else:
            logger.warning(f"API returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.warning(f"API method failed: {e}")
        return False


def add_directly():
    """Add directly to ChromaDB (if API not available)"""
    try:
        logger.info("Initializing RAG components for direct addition...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Adding CRITICAL_FOUNDATION knowledge to RAG...")
        
        # Add foundational knowledge with special metadata - CRITICAL FOUNDATION tag
        success = rag_retrieval.add_learning_content(
            content=CRITICAL_FOUNDATION,
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Core Mechanism - Continuous RAG Learning",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",  # Critical tag for priority retrieval
                "tags": ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db"],
                "importance_score": 1.0,  # Maximum importance
                "description": "CRITICAL: Core knowledge about StillMe's RAG-based continuous learning mechanism - MUST be retrieved when answering about StillMe"
            }
        )
        
        if success:
            logger.info("✅ CRITICAL_FOUNDATION knowledge added successfully!")
            return True
        else:
            logger.error("❌ Failed to add CRITICAL_FOUNDATION knowledge")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding CRITICAL_FOUNDATION knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("URGENT: Add CRITICAL_FOUNDATION Knowledge to RAG")
    print("=" * 70)
    print()
    print("This script adds critical foundational knowledge about StillMe's")
    print("RAG-based continuous learning mechanism to ensure StillMe mentions")
    print("this capability when answering questions about itself.")
    print()
    
    # Try API first (if backend is running)
    success = add_via_api()
    
    # If API fails, try direct method
    if not success:
        print("API method failed, trying direct method...")
        print()
        success = add_directly()
    
    if success:
        print()
        print("✅ Setup complete!")
        print()
        print("Next steps:")
        print("1. Test by asking: 'Bạn học tập như thế nào?' or 'How do you learn?'")
        print("2. Verify that StillMe mentions:")
        print("   - Automated learning cycles every 4 hours")
        print("   - RAG-based knowledge storage in vector database")
        print("   - Continuous updates through RSS feeds")
        print("   - StillMe is NOT limited by training data cutoff dates")
        print("3. Check that responses include RAG citations [1], [2]")
    else:
        print()
        print("❌ Setup failed. Check logs above for details.")
        sys.exit(1)

