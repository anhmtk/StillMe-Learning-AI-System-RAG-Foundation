#!/usr/bin/env python3
"""
EMERGENCY: Embedding Model Migration Tool
Re-embeds all documents in ChromaDB with the current embedding model

This script is used when the embedding model is upgraded and all existing
embeddings become incompatible (high distance, no retrieval results).

Usage:
    python scripts/migrate_embeddings.py [--dry-run] [--collection COLLECTION]

Options:
    --dry-run: Show what would be migrated without actually doing it
    --collection: Migrate specific collection (stillme_knowledge or stillme_conversations)
                  If not specified, migrates both collections
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from backend.vector_db.rag_retrieval import RAGRetrieval

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_collection(
    chroma_client: ChromaClient,
    embedding_service: EmbeddingService,
    collection_name: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Migrate a single collection to new embedding model
    
    Args:
        chroma_client: ChromaDB client
        embedding_service: Embedding service with current model
        collection_name: Name of collection to migrate
        dry_run: If True, only show what would be migrated
        
    Returns:
        Dict with migration statistics
    """
    stats = {
        "collection": collection_name,
        "total_documents": 0,
        "migrated": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Get collection
        if collection_name == "stillme_knowledge":
            collection = chroma_client.knowledge_collection
        elif collection_name == "stillme_conversations":
            collection = chroma_client.conversation_collection
        else:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        # Get all documents
        logger.info(f"📊 Fetching all documents from {collection_name}...")
        all_docs = collection.get()
        
        if not all_docs or not all_docs.get("ids"):
            logger.info(f"✅ {collection_name} is empty - nothing to migrate")
            return stats
        
        total_docs = len(all_docs["ids"])
        stats["total_documents"] = total_docs
        logger.info(f"📊 Found {total_docs} documents in {collection_name}")
        
        if dry_run:
            logger.info(f"🔍 DRY RUN: Would migrate {total_docs} documents")
            logger.info(f"🔍 Current embedding model: {embedding_service.model_name}")
            return stats
        
        # Migrate documents in batches
        batch_size = 10
        documents = all_docs.get("documents", [])
        metadatas = all_docs.get("metadatas", [])
        ids = all_docs.get("ids", [])
        
        logger.info(f"🔄 Starting migration of {total_docs} documents...")
        logger.info(f"   Model: {embedding_service.model_name}")
        logger.info(f"   Batch size: {batch_size}")
        
        for i in range(0, total_docs, batch_size):
            batch_end = min(i + batch_size, total_docs)
            batch_ids = ids[i:batch_end]
            batch_docs = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end] if metadatas else [{}] * len(batch_ids)
            
            try:
                # Generate new embeddings
                logger.info(f"🔄 Processing batch {i//batch_size + 1} ({i+1}-{batch_end}/{total_docs})...")
                new_embeddings = [embedding_service.encode_text(doc) for doc in batch_docs]
                
                # Delete old documents
                collection.delete(ids=batch_ids)
                
                # Add with new embeddings
                collection.add(
                    embeddings=new_embeddings,
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                stats["migrated"] += len(batch_ids)
                logger.info(f"✅ Migrated batch {i//batch_size + 1}: {len(batch_ids)} documents")
                
            except Exception as batch_error:
                stats["failed"] += len(batch_ids)
                error_msg = f"Batch {i//batch_size + 1} failed: {batch_error}"
                stats["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
                continue
        
        logger.info(f"✅ Migration complete for {collection_name}:")
        logger.info(f"   - Total: {stats['total_documents']}")
        logger.info(f"   - Migrated: {stats['migrated']}")
        logger.info(f"   - Failed: {stats['failed']}")
        
    except Exception as e:
        error_msg = f"Migration failed for {collection_name}: {e}"
        stats["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}", exc_info=True)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate ChromaDB embeddings to new model")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually doing it"
    )
    parser.add_argument(
        "--collection",
        choices=["stillme_knowledge", "stillme_conversations"],
        help="Migrate specific collection (default: both)"
    )
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚨 EMERGENCY: Embedding Model Migration Tool")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE: No changes will be made")
    
    try:
        # Initialize components
        logger.info("Initializing RAG components...")
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        logger.info(f"✅ Current embedding model: {embedding_service.model_name}")
        
        # Determine which collections to migrate
        collections_to_migrate = []
        if args.collection:
            collections_to_migrate = [args.collection]
        else:
            collections_to_migrate = ["stillme_knowledge", "stillme_conversations"]
        
        # Migrate each collection
        all_stats = []
        for collection_name in collections_to_migrate:
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Migrating collection: {collection_name}")
            logger.info("=" * 60)
            
            stats = migrate_collection(
                chroma_client,
                embedding_service,
                collection_name,
                dry_run=args.dry_run
            )
            all_stats.append(stats)
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("=" * 60)
        for stats in all_stats:
            logger.info(f"Collection: {stats['collection']}")
            logger.info(f"  Total documents: {stats['total_documents']}")
            if not args.dry_run:
                logger.info(f"  Migrated: {stats['migrated']}")
                logger.info(f"  Failed: {stats['failed']}")
                if stats['errors']:
                    logger.warning(f"  Errors: {len(stats['errors'])}")
                    for error in stats['errors'][:5]:  # Show first 5 errors
                        logger.warning(f"    - {error}")
        
        if args.dry_run:
            logger.info("")
            logger.info("🔍 DRY RUN complete - no changes were made")
            logger.info("💡 Run without --dry-run to perform actual migration")
        else:
            logger.info("")
            logger.info("✅ Migration complete!")
            logger.info("💡 Restart the backend service to use migrated embeddings")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

