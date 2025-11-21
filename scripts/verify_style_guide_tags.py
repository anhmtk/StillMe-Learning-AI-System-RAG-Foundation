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
        
        logger.info("Searching for style guide documents in ChromaDB...")
        
        # Method 1: Search with metadata filter for content_type="style_guide"
        # Search in BOTH knowledge and conversation collections
        filtered_results = []
        try:
            logger.info("Method 1: Searching with metadata filter content_type='style_guide'...")
            query_embedding = embedding_service.encode_text("style guide anthropomorphism")
            
            # Search in knowledge collection
            try:
                knowledge_results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=50,
                    where={"content_type": "style_guide"}
                )
                filtered_results.extend(knowledge_results)
                logger.info(f"Found {len(knowledge_results)} style guide documents in knowledge collection")
            except Exception as knowledge_error:
                logger.warning(f"Knowledge collection filter error: {knowledge_error}")
            
            # Search in conversation collection
            try:
                conversation_results = chroma_client.search_conversations(
                    query_embedding=query_embedding,
                    limit=50,
                    where={"content_type": "style_guide"}
                )
                filtered_results.extend(conversation_results)
                logger.info(f"Found {len(conversation_results)} style guide documents in conversation collection")
            except Exception as conversation_error:
                logger.warning(f"Conversation collection filter error: {conversation_error}")
                
        except Exception as filter_error:
            logger.warning(f"Metadata filter not supported: {filter_error}")
        
        # Method 2: Search broadly and filter by metadata
        logger.info("Method 2: Searching broadly and filtering by metadata...")
        query = "anthropomorphism guard experience free templates style guide"
        query_embedding = embedding_service.encode_text(query)
        
        all_results = []
        
        # Search in knowledge collection
        try:
            knowledge_results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=100
            )
            all_results.extend(knowledge_results)
            logger.info(f"Found {len(knowledge_results)} documents from knowledge collection")
        except Exception as knowledge_error:
            logger.warning(f"Knowledge collection search error: {knowledge_error}")
        
        # Search in conversation collection
        try:
            conversation_results = chroma_client.search_conversations(
                query_embedding=query_embedding,
                limit=100
            )
            all_results.extend(conversation_results)
            logger.info(f"Found {len(conversation_results)} documents from conversation collection")
        except Exception as conversation_error:
            logger.warning(f"Conversation collection search error: {conversation_error}")
        
        logger.info(f"Found {len(all_results)} total documents from semantic search")
        
        # Combine results (avoid duplicates)
        all_docs = {}
        for doc in filtered_results:
            doc_id = doc.get("id", "unknown")
            all_docs[doc_id] = doc
        
        for doc in all_results:
            doc_id = doc.get("id", "unknown")
            if doc_id not in all_docs:
                all_docs[doc_id] = doc
        
        style_guide_docs = []
        other_docs = []
        
        for doc in all_docs.values():
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "N/A")
            content_type = metadata.get("content_type", "")
            source = metadata.get("source", "")
            
            # Check if it's a style guide document
            # Priority 1: Check content_type metadata
            if content_type == "style_guide":
                is_style_guide = True
            else:
                # Priority 2: Check title/source for style guide indicators
                style_guide_indicators = [
                    "anthropomorphism_guard",
                    "experience_free_templates",
                    "StillMe_StyleGuide",
                    "style_guide",
                    "Anthropomorphism Guard",
                    "Experience-Free",
                    "Philosophical Style Guide",
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
            logger.info(f"\n📊 Debug info:")
            logger.info(f"   Total documents searched: {len(all_docs)}")
            if other_docs:
                logger.info(f"   Sample of other documents found:")
                for doc in other_docs[:5]:
                    logger.info(f"     - {doc['title']} (content_type: {doc.get('content_type', 'N/A')}, source: {doc.get('source', 'N/A')})")
            
            logger.warning("\n   Possible reasons:")
            logger.warning("   1. Scripts chạy trên local nhưng ChromaDB path khác với production")
            logger.warning("   2. Documents chưa được add vào ChromaDB (check logs của add scripts)")
            logger.warning("   3. ChromaDB path không đúng (check persist_directory)")
            logger.warning("\n   Please verify:")
            logger.warning("   - Check logs của add scripts có báo '✅ added successfully' không?")
            logger.warning("   - Check ChromaDB path: scripts dùng 'data/vector_db', production có thể khác")
            logger.warning("   - Re-run add scripts nếu cần:")
            logger.warning("     python scripts/add_anthropomorphism_guard_rag.py")
            logger.warning("     python scripts/add_philosophical_style_guide_rag.py")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error verifying style guide tags: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_style_guide_tags()
    sys.exit(0 if success else 1)

