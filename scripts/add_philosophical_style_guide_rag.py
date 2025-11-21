#!/usr/bin/env python3
"""
Script to add StillMe Philosophical Style Guide to RAG
This ensures StillMe can reference the style guide when answering philosophical questions
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

# Read the style guide content
STYLE_GUIDE_PATH = project_root / "docs" / "style" / "StillMe_StyleGuide_Philosophy_v1.0.md"

def add_philosophical_style_guide_rag():
    """Add Philosophical Style Guide to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Read the style guide content
        if not STYLE_GUIDE_PATH.exists():
            logger.error(f"❌ Style guide not found: {STYLE_GUIDE_PATH}")
            return False
        
        with open(STYLE_GUIDE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.info("Adding Philosophical Style Guide to RAG...")
        
        # Add with special metadata - CRITICAL FOUNDATION tag
        tags_list = ["foundational:style", "CRITICAL_FOUNDATION", "philosophical", "style_guide", "philosophy", "ethics", "transparency"]
        tags_string = ",".join(tags_list)
        
        # Phase 2: Tag as style_guide (not knowledge) - will be filtered from user chat
        success = rag_retrieval.add_learning_content(
            content=content,
            source="CRITICAL_FOUNDATION",
            content_type="style_guide",  # Phase 2: Changed from "knowledge" to "style_guide"
            metadata={
                "title": "StillMe Philosophical Style Guide v1.0",
                "foundational": "style",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",
                "tags": tags_string,
                "importance_score": 1.0,
                "content_type": "style_guide",  # Phase 2: Explicitly tag as style_guide
                "domain": "style_guide",
                "description": "CRITICAL: Philosophical style guide for StillMe. NOTE: This is a style guide, not knowledge - filtered from user chat queries. Used internally for formatting/philosophical structure, not returned to users."
            }
        )
        
        if success:
            logger.info("✅ Philosophical Style Guide added successfully!")
            return True
        else:
            logger.error("❌ Failed to add Philosophical Style Guide")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding Philosophical Style Guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_philosophical_style_guide_rag()
    sys.exit(0 if success else 1)

