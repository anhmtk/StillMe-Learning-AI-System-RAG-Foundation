#!/usr/bin/env python3
"""
Fix metadata for existing style guide documents in ChromaDB
This script updates content_type metadata for style guide documents that were added before Phase 2.
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


def fix_style_guide_metadata():
    """Fix content_type metadata for style guide documents"""
    try:
        logger.info("Initializing ChromaDB client...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Find style guide documents by title/source
        style_guide_titles = [
            "Anthropomorphism Guard - Experience-Free Communication Protocol",
            "StillMe Philosophical Style Guide v1.0",
        ]
        
        style_guide_sources = [
            "CRITICAL_FOUNDATION",
        ]
        
        logger.info("Searching for style guide documents to fix...")
        
        # Get all documents from knowledge collection
        try:
            all_docs = chroma_client.knowledge_collection.get()
            
            if not all_docs or not all_docs.get("ids"):
                logger.warning("No documents found in knowledge collection")
                return False
            
            logger.info(f"Found {len(all_docs['ids'])} total documents in knowledge collection")
            
            fixed_count = 0
            not_found_count = 0
            
            for i, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs.get("metadatas", [{}])[i] if i < len(all_docs.get("metadatas", [])) else {}
                document = all_docs.get("documents", [""])[i] if i < len(all_docs.get("documents", [])) else ""
                title = metadata.get("title", "")
                source = metadata.get("source", "")
                current_content_type = metadata.get("content_type", "")
                
                # Check if this is a style guide document
                is_style_guide = (
                    any(title_indicator in title for title_indicator in style_guide_titles) or
                    any(source_indicator in source for source_indicator in style_guide_sources)
                ) and (
                    "anthropomorphism" in title.lower() or
                    "style guide" in title.lower() or
                    "experience-free" in title.lower() or
                    "philosophical" in title.lower()
                )
                
                if is_style_guide:
                    # Check if content_type is wrong
                    if current_content_type != "style_guide":
                        logger.info(f"Found style guide document with wrong content_type:")
                        logger.info(f"  ID: {doc_id}")
                        logger.info(f"  Title: {title}")
                        logger.info(f"  Current content_type: '{current_content_type}'")
                        logger.info(f"  Source: {source}")
                        
                        # Delete old document
                        try:
                            chroma_client.knowledge_collection.delete(ids=[doc_id])
                            logger.info(f"  ✅ Deleted old document: {doc_id}")
                        except Exception as delete_error:
                            logger.error(f"  ❌ Failed to delete document {doc_id}: {delete_error}")
                            continue
                        
                        # Re-add with correct metadata
                        fixed_metadata = metadata.copy()
                        fixed_metadata["content_type"] = "style_guide"
                        fixed_metadata["domain"] = "style_guide"
                        
                        # Ensure all required fields are present
                        if "title" not in fixed_metadata:
                            fixed_metadata["title"] = title
                        if "source" not in fixed_metadata:
                            fixed_metadata["source"] = source or "CRITICAL_FOUNDATION"
                        
                        # Re-add using RAGRetrieval to ensure proper embedding
                        success = rag_retrieval.add_learning_content(
                            content=document,
                            source=fixed_metadata.get("source", "CRITICAL_FOUNDATION"),
                            content_type="style_guide",
                            metadata=fixed_metadata
                        )
                        
                        if success:
                            logger.info(f"  ✅ Re-added with correct metadata: content_type='style_guide'")
                            fixed_count += 1
                        else:
                            logger.error(f"  ❌ Failed to re-add document {doc_id}")
                    else:
                        logger.debug(f"  ✅ Document {doc_id} already has correct content_type='style_guide'")
            
            logger.info("=" * 80)
            logger.info("FIX SUMMARY")
            logger.info("=" * 80)
            logger.info(f"✅ Fixed {fixed_count} style guide document(s)")
            
            if fixed_count > 0:
                logger.info("\n🎉 Style guide metadata fixed successfully!")
                logger.info("   Run verify script to confirm: python scripts/verify_style_guide_tags.py")
                return True
            else:
                logger.info("\n💡 No style guide documents needed fixing (or not found)")
                return True
                
        except Exception as collection_error:
            logger.error(f"Error accessing knowledge collection: {collection_error}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"❌ Error fixing style guide metadata: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_style_guide_metadata()
    sys.exit(0 if success else 1)

