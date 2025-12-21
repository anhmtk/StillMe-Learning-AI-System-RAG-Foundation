#!/usr/bin/env python3
"""
Script to delete ALL old foundational knowledge from ChromaDB

This script:
1. Deletes all documents with source="CRITICAL_FOUNDATION"
2. Deletes all documents with type="foundational"
3. Deletes all documents with foundational="stillme" in metadata
4. This ensures clean slate before re-injecting correct foundational knowledge
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


def delete_all_foundational_knowledge():
    """Delete all foundational knowledge documents from ChromaDB"""
    try:
        logger.info("🔍 Searching for all foundational knowledge documents...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        # Search for all foundational documents using multiple queries
        search_queries = [
            "StillMe RAG continuous learning",
            "StillMe validation framework",
            "StillMe technical architecture",
            "StillMe validators layers"
        ]
        
        all_foundational_ids = set()
        
        for query in search_queries:
            logger.info(f"🔍 Searching with query: '{query}'...")
            query_embedding = embedding_service.encode_text(query)
            
            # Search with very low threshold to find all matches
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=100,  # Get many results
                where=None  # No filter, search all
            )
            
            # Check each result for foundational markers
            for result in results:
                metadata = result.get("metadata", {})
                source = metadata.get("source", "")
                doc_type = metadata.get("type", "")
                foundational = metadata.get("foundational", "")
                title = metadata.get("title", "")
                
                # Check if this is a foundational document
                is_foundational = (
                    "CRITICAL_FOUNDATION" in source or
                    source == "CRITICAL_FOUNDATION" or
                    doc_type == "foundational" or
                    foundational == "stillme" or
                    "foundational" in str(title).lower() or
                    "StillMe Core Mechanism" in str(title) or
                    "StillMe Core Principles" in str(title) or
                    "Technical Architecture" in str(title)
                )
                
                if is_foundational:
                    doc_id = result.get("id")
                    if doc_id:
                        all_foundational_ids.add(doc_id)
                        logger.info(f"   Found foundational document: ID={doc_id}, Title={title[:50]}")
        
        # Also try direct metadata filter if supported
        try:
            logger.info("🔍 Trying direct metadata filter search...")
            # Try to get all documents with CRITICAL_FOUNDATION source
            # Note: This may not work if ChromaDB doesn't support complex filters
            direct_results = chroma_client.search_knowledge(
                query_embedding=embedding_service.encode_text("StillMe"),
                limit=200,  # Get many results
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            for result in direct_results:
                doc_id = result.get("id")
                if doc_id:
                    all_foundational_ids.add(doc_id)
                    logger.info(f"   Found via direct filter: ID={doc_id}")
        except Exception as filter_error:
            logger.debug(f"Direct filter not supported: {filter_error}")
        
        # Delete all found foundational documents
        if all_foundational_ids:
            logger.info(f"🗑️ Deleting {len(all_foundational_ids)} foundational knowledge document(s)...")
            
            # Convert set to list for deletion
            ids_to_delete = list(all_foundational_ids)
            
            # Delete in batches (ChromaDB may have limits)
            batch_size = 50
            deleted_count = 0
            
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                try:
                    chroma_client.knowledge_collection.delete(ids=batch)
                    deleted_count += len(batch)
                    logger.info(f"✅ Deleted batch {i//batch_size + 1}: {len(batch)} documents")
                except Exception as delete_error:
                    logger.error(f"❌ Failed to delete batch {i//batch_size + 1}: {delete_error}")
            
            logger.info(f"✅ Successfully deleted {deleted_count} foundational knowledge document(s)")
            return deleted_count
        else:
            logger.info("ℹ️ No foundational knowledge documents found to delete")
            return 0
        
    except Exception as e:
        logger.error(f"❌ Error deleting foundational knowledge: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    # Fix encoding for Windows console
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    print("=" * 80)
    print("StillMe - Delete Old Foundational Knowledge")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This will delete ALL foundational knowledge from ChromaDB!")
    print("   This includes:")
    print("   - All documents with source='CRITICAL_FOUNDATION'")
    print("   - All documents with type='foundational'")
    print("   - All documents with foundational='stillme'")
    print()
    print("   After deletion, you should run:")
    print("   python scripts/add_foundational_knowledge.py")
    print("   to re-inject correct foundational knowledge from foundational_technical.md")
    print()
    
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("❌ Cancelled.")
        sys.exit(0)
    
    print()
    deleted_count = delete_all_foundational_knowledge()
    
    print()
    print("=" * 80)
    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} foundational knowledge document(s)")
        print()
        print("Next steps:")
        print("1. Run: python scripts/add_foundational_knowledge.py")
        print("2. This will inject correct foundational knowledge from foundational_technical.md")
        print("3. Test by asking: 'How many validators does StillMe have?'")
    else:
        print("ℹ️ No foundational knowledge documents found (may already be deleted)")
    print("=" * 80)
