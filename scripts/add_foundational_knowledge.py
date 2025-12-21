#!/usr/bin/env python3
"""
Script to add StillMe foundational knowledge to RAG
This ensures StillMe can answer questions about itself using RAG, not outdated LLM knowledge

CRITICAL: This script ALWAYS reads from docs/rag/foundational_technical.md
NEVER uses hardcoded content - ensures we always have latest validator info (19 validators, 7 layers)
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


def add_foundational_knowledge():
    """Add foundational StillMe knowledge to RAG - ALWAYS reads from file, NEVER hardcoded"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Loading foundational knowledge from file...")
        
        # CRITICAL: Always read from file, never use hardcoded content
        technical_path = project_root / "docs" / "rag" / "foundational_technical.md"
        
        if not technical_path.exists():
            logger.error(f"❌ File not found: {technical_path}")
            logger.error("❌ Cannot inject foundational knowledge - file does not exist!")
            return False
        
        # Read content from file
        with open(technical_path, "r", encoding="utf-8") as f:
            technical_content = f.read()
        
        # Remove frontmatter if present
        if technical_content.startswith("---"):
            parts = technical_content.split("---", 2)
            if len(parts) >= 3:
                technical_content = parts[2].strip()
        
        logger.info(f"📊 Loaded {len(technical_content)} characters from {technical_path}")
        
        # Verify content contains correct validator info
        has_19_validators = "19 validators" in technical_content or "19 validators total" in technical_content
        has_7_layers = "7 layers" in technical_content or "7 lớp" in technical_content
        
        if not has_19_validators:
            logger.warning("⚠️ Content does not contain '19 validators' - may be outdated")
        if not has_7_layers:
            logger.warning("⚠️ Content does not contain '7 layers' - may be outdated")
        
        if not has_19_validators or not has_7_layers:
            logger.error("❌ File foundational_technical.md does not contain correct validator info!")
            logger.error("   Expected: '19 validators' and '7 layers'")
            return False
        
        logger.info("✅ Content verified: Contains correct validator count (19 validators, 7 layers)")
        
        # Add foundational knowledge with special metadata - CRITICAL FOUNDATION tag
        # Note: ChromaDB metadata must be str, int, float, bool, or None (not lists)
        # Convert tags list to comma-separated string
        tags_list = [
            "foundational:stillme",
            "CRITICAL_FOUNDATION",
            "stillme",
            "rag",
            "self-evolving",
            "continuous-learning",
            "automated-learning",
            "rss",
            "vector-db",
            "technical",
            "core_logic",
            "priority_high"
        ]
        tags_string = ",".join(tags_list)
        
        success = rag_retrieval.add_learning_content(
            content=technical_content,  # Use content from file, not hardcoded
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Core Mechanism - Technical Architecture",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",  # Critical tag for priority retrieval
                "tags": tags_string,  # Comma-separated string (ChromaDB doesn't support lists)
                "importance_score": 1.0,  # Maximum importance
                "priority": "high",  # Explicit priority field
                "category": "core_logic",  # Explicit category for filtering
                "content_type": "technical",
                "domain": "stillme_architecture",
                "description": "CRITICAL: Technical knowledge about StillMe's RAG-based continuous learning mechanism and validation framework (19 validators, 7 layers) - MUST be retrieved when answering about StillMe's architecture"
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
    # Fix encoding for Windows console
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Fallback if reconfigure fails
    
    print("=" * 60)
    print("StillMe Foundational Knowledge Setup")
    print("=" * 60)
    print()
    print("This script adds foundational knowledge about StillMe to the RAG system.")
    print("This ensures StillMe can answer questions about itself using up-to-date")
    print("RAG knowledge, not outdated LLM training data.")
    print()
    print("CRITICAL: This script ALWAYS reads from docs/rag/foundational_technical.md")
    print("NEVER uses hardcoded content - ensures we always have latest validator info")
    print()
    
    success = add_foundational_knowledge()
    
    if success:
        print()
        print("Setup complete!")
        print()
        print("Next steps:")
        print("1. Test by asking: 'What is StillMe?' or 'How does StillMe learn?'")
        print("2. Verify that StillMe uses RAG citations [1], [2] in responses")
        print("3. Check that responses mention continuous learning and RAG capabilities")
        print("4. Test validator count: 'How many validators does StillMe have?'")
        print("   Expected: '19 validators total, chia thành 7 lớp (layers)'")
    else:
        print()
        print("Setup failed. Check logs above for details.")
        sys.exit(1)
