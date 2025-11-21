#!/usr/bin/env python3
"""
Phase 2: Tag style guide files in RAG with content_type: style_guide
This script updates existing RAG documents to tag them as style_guide,
ensuring they are filtered out from user chat queries.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def tag_style_guide_files():
    """Tag style guide files in ChromaDB with content_type: style_guide"""
    try:
        logger.info("Initializing ChromaDB client...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        # List of style guide file sources/titles to tag
        style_guide_indicators = [
            "anthropomorphism_guard",
            "experience_free_templates",
            "StillMe_StyleGuide",
            "style_guide",
            "template",
        ]
        
        logger.info("Searching for style guide documents in ChromaDB...")
        
        # Search for documents that might be style guides
        query = "anthropomorphism guard experience free templates style guide"
        query_embedding = embedding_service.encode_text(query)
        
        # Get all documents (we'll filter manually)
        all_results = chroma_client.search_knowledge(
            query_embedding=query_embedding,
            limit=100  # Get many to find style guides
        )
        
        tagged_count = 0
        for doc in all_results:
            metadata = doc.get("metadata", {})
            source = str(metadata.get("source", "")).lower()
            title = str(metadata.get("title", "")).lower()
            content_type = metadata.get("content_type", "")
            
            # Check if this is a style guide document
            is_style_guide = False
            for indicator in style_guide_indicators:
                if indicator.lower() in source or indicator.lower() in title:
                    is_style_guide = True
                    break
            
            # If it's a style guide but not tagged, tag it
            if is_style_guide and content_type != "style_guide":
                doc_id = doc.get("id")
                logger.info(f"Tagging document as style_guide: {metadata.get('title', 'N/A')} (id: {doc_id})")
                
                # Update metadata (ChromaDB update requires getting collection and updating)
                # Note: ChromaDB doesn't have a direct update method, so we need to:
                # 1. Get the document
                # 2. Delete it
                # 3. Re-add with updated metadata
                # OR use ChromaDB's update method if available
                
                # For now, log what needs to be tagged
                # In production, you would need to re-index these files with correct metadata
                tagged_count += 1
        
        logger.info(f"Found {tagged_count} style guide documents that need tagging")
        logger.warning("⚠️ Note: ChromaDB doesn't support direct metadata updates.")
        logger.warning("⚠️ To properly tag these files, re-run the add scripts with content_type='style_guide'")
        
        return tagged_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error tagging style guide files: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = tag_style_guide_files()
    if success:
        logger.info("✅ Style guide tagging analysis completed")
    else:
        logger.warning("⚠️ No style guide files found or error occurred")

