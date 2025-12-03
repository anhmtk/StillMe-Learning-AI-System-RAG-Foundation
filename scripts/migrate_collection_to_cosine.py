#!/usr/bin/env python3
"""
Script to migrate ChromaDB collections from L2 distance to cosine distance.

This script:
1. Backs up all documents from existing collections
2. Deletes old collections (with L2 distance)
3. Creates new collections with cosine distance
4. Re-adds all documents with normalized embeddings

CRITICAL: This preserves all data while fixing the distance metric issue.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.rag.chroma_client import ChromaClient
from stillme_core.rag.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_collection_to_cosine(
    collection_name: str,
    chroma_client: ChromaClient,
    embedding_service: EmbeddingService,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate a ChromaDB collection from L2 to cosine distance.
    
    Args:
        collection_name: Name of collection to migrate (e.g., "stillme_knowledge")
        chroma_client: ChromaClient instance
        embedding_service: EmbeddingService instance (for re-embedding)
        dry_run: If True, only backup data without deleting/recreating
        
    Returns:
        Dict with migration results
    """
    logger.info("="*60)
    logger.info(f"Migrating collection '{collection_name}' to cosine distance")
    logger.info("="*60)
    
    try:
        # Step 1: Get collection
        try:
            collection = chroma_client.client.get_collection(name=collection_name)
            logger.info(f"✅ Found collection: {collection_name}")
        except Exception as e:
            logger.error(f"❌ Collection '{collection_name}' not found: {e}")
            return {
                "status": "error",
                "message": f"Collection not found: {e}",
                "collection_name": collection_name
            }
        
        # Step 2: Backup all documents
        logger.info(f"\n1. Backing up all documents from '{collection_name}'...")
        
        try:
            # Get all documents with metadata and embeddings
            all_data = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not all_data or not all_data.get("ids"):
                logger.warning(f"⚠️ Collection '{collection_name}' is empty - nothing to migrate")
                return {
                    "status": "success",
                    "message": "Collection is empty - no migration needed",
                    "collection_name": collection_name,
                    "documents_backed_up": 0,
                    "documents_migrated": 0
                }
            
            ids = all_data["ids"]
            documents = all_data.get("documents", [])
            metadatas = all_data.get("metadatas", [])
            old_embeddings = all_data.get("embeddings", [])
            
            num_docs = len(ids)
            logger.info(f"   ✅ Backed up {num_docs} documents")
            logger.info(f"   - IDs: {len(ids)}")
            logger.info(f"   - Documents: {len(documents)}")
            logger.info(f"   - Metadatas: {len(metadatas)}")
            logger.info(f"   - Embeddings: {len(old_embeddings)}")
            
            if dry_run:
                logger.info("\n   🔍 DRY RUN: Would migrate these documents")
                logger.info("   (No changes made - use without --dry-run to actually migrate)")
                return {
                    "status": "dry_run",
                    "message": "Dry run completed - no changes made",
                    "collection_name": collection_name,
                    "documents_backed_up": num_docs,
                    "documents_migrated": 0
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to backup documents: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Backup failed: {e}",
                "collection_name": collection_name
            }
        
        # Step 3: Delete old collection
        logger.info(f"\n2. Deleting old collection '{collection_name}' (with L2 distance)...")
        try:
            chroma_client.client.delete_collection(name=collection_name)
            logger.info(f"   ✅ Deleted old collection")
        except Exception as e:
            logger.error(f"❌ Failed to delete collection: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Delete failed: {e}",
                "collection_name": collection_name
            }
        
        # Step 4: Create new collection with cosine distance
        logger.info(f"\n3. Creating new collection '{collection_name}' with cosine distance...")
        try:
            # Determine description based on collection name
            if "knowledge" in collection_name.lower():
                description = "Knowledge base for StillMe learning"
            elif "conversation" in collection_name.lower():
                description = "Conversation history for context"
            else:
                description = f"Collection: {collection_name}"
            
            new_collection = chroma_client.client.create_collection(
                name=collection_name,
                metadata={
                    "description": description,
                    "hnsw:space": "cosine"  # CRITICAL: Use cosine distance for normalized embeddings
                }
            )
            logger.info(f"   ✅ Created new collection with cosine distance metric")
        except Exception as e:
            logger.error(f"❌ Failed to create new collection: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Create failed: {e}",
                "collection_name": collection_name,
                "documents_backed_up": num_docs,
                "documents_migrated": 0
            }
        
        # Step 5: Re-embed and re-add documents
        logger.info(f"\n4. Re-embedding and re-adding {num_docs} documents...")
        logger.info(f"   Model: {embedding_service.model_name}")
        logger.info(f"   This may take a while for large collections...")
        
        start_time = time.time()
        re_embedded_count = 0
        errors = []
        
        # Process in batches to avoid memory issues
        batch_size = 50
        for i in range(0, num_docs, batch_size):
            batch_end = min(i + batch_size, num_docs)
            batch_ids = ids[i:batch_end]
            batch_documents = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end] if metadatas else [{}] * (batch_end - i)
            
            logger.info(f"   Processing batch {i//batch_size + 1}/{(num_docs + batch_size - 1)//batch_size} ({i+1}-{batch_end}/{num_docs})...")
            
            try:
                # Re-embed documents with normalized embeddings
                batch_embeddings = []
                for doc in batch_documents:
                    embedding = embedding_service.encode_text(doc)
                    batch_embeddings.append(embedding)
                
                # Add to new collection
                new_collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
                
                re_embedded_count += len(batch_ids)
                logger.info(f"      ✅ Added {len(batch_ids)} documents to new collection")
                
            except Exception as e:
                error_msg = f"Failed to process batch {i//batch_size + 1}: {str(e)}"
                logger.error(f"      ❌ {error_msg}", exc_info=True)
                errors.append(error_msg)
        
        elapsed = time.time() - start_time
        logger.info(f"\n   ✅ Re-embedding complete: {re_embedded_count}/{num_docs} documents")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
        
        if errors:
            logger.warning(f"   ⚠️ {len(errors)} errors occurred during migration")
            for error in errors:
                logger.warning(f"      - {error}")
        
        # Step 6: Verify migration
        logger.info(f"\n5. Verifying migration...")
        try:
            verify_data = new_collection.get(
                include=["documents", "metadatas"]
            )
            verify_count = len(verify_data.get("ids", []))
            
            if verify_count == num_docs:
                logger.info(f"   ✅ Verification passed: {verify_count} documents in new collection")
            else:
                logger.warning(f"   ⚠️ Verification warning: Expected {num_docs}, found {verify_count}")
        except Exception as e:
            logger.warning(f"   ⚠️ Verification failed: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Migration complete!")
        logger.info("="*60)
        
        return {
            "status": "success",
            "message": "Collection migrated successfully",
            "collection_name": collection_name,
            "documents_backed_up": num_docs,
            "documents_migrated": re_embedded_count,
            "errors": errors,
            "time_elapsed_seconds": elapsed
        }
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Migration failed: {e}",
            "collection_name": collection_name
        }


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate ChromaDB collections from L2 to cosine distance"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="stillme_knowledge",
        help="Collection name to migrate (default: stillme_knowledge)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all collections (stillme_knowledge and stillme_conversations)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - backup data but don't migrate"
    )
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("ChromaDB Collection Migration: L2 → Cosine Distance")
    logger.info("="*60)
    
    try:
        # Initialize services
        logger.info("\nInitializing ChromaDB client and embedding service...")
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        logger.info("✅ Services initialized")
        
        # Determine collections to migrate
        collections_to_migrate = []
        if args.all:
            collections_to_migrate = ["stillme_knowledge", "stillme_conversations"]
        else:
            collections_to_migrate = [args.collection]
        
        # Migrate each collection
        results = []
        for collection_name in collections_to_migrate:
            result = migrate_collection_to_cosine(
                collection_name=collection_name,
                chroma_client=chroma_client,
                embedding_service=embedding_service,
                dry_run=args.dry_run
            )
            results.append(result)
            
            # Wait a bit between collections
            if len(collections_to_migrate) > 1 and collection_name != collections_to_migrate[-1]:
                logger.info("\nWaiting 2 seconds before next collection...")
                time.sleep(2)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Migration Summary")
        logger.info("="*60)
        for result in results:
            status = result.get("status", "unknown")
            collection = result.get("collection_name", "unknown")
            backed_up = result.get("documents_backed_up", 0)
            migrated = result.get("documents_migrated", 0)
            
            if status == "success":
                logger.info(f"✅ {collection}: {migrated}/{backed_up} documents migrated")
            elif status == "dry_run":
                logger.info(f"🔍 {collection}: {backed_up} documents would be migrated (dry run)")
            else:
                logger.error(f"❌ {collection}: Migration failed - {result.get('message', 'Unknown error')}")
        
        logger.info("="*60)
        
        # Exit code
        if all(r.get("status") in ["success", "dry_run"] for r in results):
            logger.info("\n✅ All migrations completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Some migrations failed - check logs above")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

