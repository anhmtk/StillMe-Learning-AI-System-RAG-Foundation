#!/usr/bin/env python3
"""
Verify that style guide documents have been correctly tagged with content_type: style_guide
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


def verify_style_guide_tags():
    """Verify style guide documents are tagged correctly"""
    try:
        logger.info("Initializing ChromaDB client...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        # Search for style guide documents
        query = "anthropomorphism guard experience free templates style guide"
        query_embedding = embedding_service.encode_text(query)
        
        logger.info("Searching for style guide documents in ChromaDB...")
        
        # Get documents (without filter to see all)
        all_results = chroma_client.search_knowledge(
            query_embedding=query_embedding,
            limit=20
        )
        
        style_guide_docs = []
        other_docs = []
        
        for doc in all_results:
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "N/A")
            content_type = metadata.get("content_type", "")
            source = metadata.get("source", "")
            
            # Check if it's a style guide document
            style_guide_indicators = [
                "anthropomorphism_guard",
                "experience_free_templates",
                "StillMe_StyleGuide",
                "style_guide",
            ]
            
            is_style_guide = any(
                indicator.lower() in str(title).lower() or 
                indicator.lower() in str(source).lower()
                for indicator in style_guide_indicators
            )
            
            if is_style_guide:
                style_guide_docs.append({
                    "title": title,
                    "content_type": content_type,
                    "source": source,
                    "id": doc.get("id", "N/A")
                })
            else:
                other_docs.append({
                    "title": title,
                    "content_type": content_type,
                    "source": source
                })
        
        # Report results
        logger.info("=" * 80)
        logger.info("VERIFICATION RESULTS")
        logger.info("=" * 80)
        
        if style_guide_docs:
            logger.info(f"\n✅ Found {len(style_guide_docs)} style guide document(s):")
            all_correct = True
            for doc in style_guide_docs:
                status = "✅" if doc["content_type"] == "style_guide" else "❌"
                if doc["content_type"] != "style_guide":
                    all_correct = False
                logger.info(f"  {status} {doc['title']}")
                logger.info(f"     content_type: {doc['content_type']}")
                logger.info(f"     source: {doc['source']}")
                logger.info(f"     id: {doc['id']}")
            
            if all_correct:
                logger.info("\n🎉 All style guide documents are correctly tagged with content_type='style_guide'!")
                return True
            else:
                logger.warning("\n⚠️ Some style guide documents are NOT correctly tagged!")
                logger.warning("   Please re-run the add scripts:")
                logger.warning("   python scripts/add_anthropomorphism_guard_rag.py")
                logger.warning("   python scripts/add_philosophical_style_guide_rag.py")
                return False
        else:
            logger.warning("\n⚠️ No style guide documents found in ChromaDB!")
            logger.warning("   Please run the add scripts:")
            logger.warning("   python scripts/add_anthropomorphism_guard_rag.py")
            logger.warning("   python scripts/add_philosophical_style_guide_rag.py")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error verifying style guide tags: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_style_guide_tags()
    sys.exit(0 if success else 1)

