#!/usr/bin/env python3
"""
Script to add StillMe Provenance knowledge to RAG
This ensures StillMe can answer questions about its origin/founder ONLY when asked directly
CRITICAL: This knowledge should ONLY be retrieved when user asks about origin/founder
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

# Read PROVENANCE.md content
PROVENANCE_FILE = project_root / "docs" / "about" / "PROVENANCE.md"

if not PROVENANCE_FILE.exists():
    logger.error(f"❌ PROVENANCE.md not found at {PROVENANCE_FILE}")
    sys.exit(1)

with open(PROVENANCE_FILE, 'r', encoding='utf-8') as f:
    PROVENANCE_CONTENT = f.read()


def add_provenance_knowledge():
    """Add StillMe provenance knowledge to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Adding StillMe provenance knowledge to RAG...")
        
        # Add provenance knowledge with special metadata - INTENT-BASED RETRIEVAL
        # CRITICAL: Only retrieve when user asks about origin/founder
        tags_list = [
            "provenance", "about", "origin", "founder", "stillme_history",
            "intent:origin", "intent:founder", "intent:about"
        ]
        tags_string = ",".join(tags_list)
        
        # Intent keywords for retrieval filtering
        intent_keywords = [
            "ai đứng sau", "founder", "origin", "who built", "nguồn gốc", 
            "tác giả", "who created", "who made", "creator", "sáng lập", 
            "người tạo ra", "about stillme", "stillme history"
        ]
        intent_keywords_string = ",".join(intent_keywords)
        
        success = rag_retrieval.add_learning_content(
            content=PROVENANCE_CONTENT,
            source="PROVENANCE",
            content_type="knowledge",
            metadata={
                "title": "StillMe Origin & Provenance",
                "type": "provenance",
                "source": "PROVENANCE",
                "tags": tags_string,
                "intent_keywords": intent_keywords_string,  # For intent-based filtering
                "importance_score": 0.8,  # High but not critical (only when asked)
                "description": "StillMe origin and founder information - ONLY retrieve when user asks about origin/founder/about StillMe",
                "retrieval_policy": "intent_based",  # Critical: only retrieve on specific intent
                "guardrail": "never_mention_unless_asked"  # Never mention founder unless explicitly asked
            }
        )
        
        if success:
            logger.info("✅ Provenance knowledge added successfully!")
            logger.info("⚠️  CRITICAL: This knowledge will ONLY be retrieved when user asks about origin/founder")
            logger.info("⚠️  CRITICAL: StillMe will NEVER mention founder in other contexts")
            return True
        else:
            logger.error("❌ Failed to add provenance knowledge")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding provenance knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Fix encoding for Windows console
    import sys
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    
    success = add_provenance_knowledge()
    sys.exit(0 if success else 1)

