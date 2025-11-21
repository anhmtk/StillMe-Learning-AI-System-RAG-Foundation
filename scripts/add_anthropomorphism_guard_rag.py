#!/usr/bin/env python3
"""
Script to add Anthropomorphism Guard knowledge to RAG
This ensures StillMe can answer questions about experience-free communication using RAG
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

# Read the RAG module content
RAG_MODULE_PATH = project_root / "docs" / "rag" / "anthropomorphism_guard.md"

def add_anthropomorphism_guard_rag():
    """Add Anthropomorphism Guard knowledge to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Read the RAG module content
        if not RAG_MODULE_PATH.exists():
            logger.error(f"❌ RAG module not found: {RAG_MODULE_PATH}")
            return False
        
        with open(RAG_MODULE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.info("Adding Anthropomorphism Guard knowledge to RAG...")
        
        # Add with special metadata - CRITICAL FOUNDATION tag
        tags_list = ["foundational:ethics", "CRITICAL_FOUNDATION", "anthropomorphism", "experience-free", "ethics", "transparency", "ego-neutrality"]
        tags_string = ",".join(tags_list)
        
        # Phase 2: Tag as style_guide (not knowledge) - will be filtered from user chat
        success = rag_retrieval.add_learning_content(
            content=content,
            source="CRITICAL_FOUNDATION",
            content_type="style_guide",  # Phase 2: Changed from "knowledge" to "style_guide"
            metadata={
                "title": "Anthropomorphism Guard - Experience-Free Communication Protocol",
                "foundational": "ethics",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",
                "tags": tags_string,
                "importance_score": 1.0,
                "content_type": "style_guide",  # Phase 2: Explicitly tag as style_guide
                "description": "CRITICAL: StillMe's Ethical Charter - Điều 5: Cấm Mô Phỏng Trải Nghiệm Cá Nhân. Experience-Free communication protocol to prevent 'Hallucination of Experience'. NOTE: This is a style guide, not knowledge - filtered from user chat queries."
            }
        )
        
        if success:
            logger.info("✅ Anthropomorphism Guard knowledge added successfully!")
            logger.info("StillMe can now answer questions about experience-free communication using RAG knowledge.")
            return True
        else:
            logger.error("❌ Failed to add Anthropomorphism Guard knowledge")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding Anthropomorphism Guard knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Fix encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    success = add_anthropomorphism_guard_rag()
    sys.exit(0 if success else 1)

