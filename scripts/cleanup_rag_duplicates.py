"""
RAG Duplicate Cleanup Script
Xóa duplicate documents từ RAG database để cải thiện chất lượng
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from typing import List, Dict, Any
from collections import defaultdict
import hashlib
import re

def get_content_hash(content: str) -> str:
    """Generate hash for content to detect duplicates"""
    # Normalize: lowercase, remove extra whitespace
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()

def find_duplicates(chroma_client: ChromaClient) -> Dict[str, List[str]]:
    """Find duplicate document IDs"""
    knowledge_collection = chroma_client.knowledge_collection
    
    # Get all documents
    result = knowledge_collection.get(limit=10000)
    
    if not result or not result.get("ids"):
        return {}
    
    ids = result.get("ids", [])
    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])
    
    # Group by content hash
    content_map = defaultdict(list)
    
    for i, doc_id in enumerate(ids):
        content = documents[i] if i < len(documents) else ""
        if content:
            content_hash = get_content_hash(content)
            content_map[content_hash].append({
                "id": doc_id,
                "content": content,
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })
    
    # Find duplicates (keep first, mark others for deletion)
    duplicates_to_delete = []
    duplicates_to_keep = {}
    
    for content_hash, docs in content_map.items():
        if len(docs) > 1:
            # Sort by source priority: CRITICAL_FOUNDATION > PROVENANCE > others
            def get_priority(doc):
                source = doc.get("metadata", {}).get("source", "")
                if source == "CRITICAL_FOUNDATION":
                    return 0
                elif source == "PROVENANCE":
                    return 1
                else:
                    return 2
            
            docs_sorted = sorted(docs, key=get_priority)
            
            # Keep the first one (highest priority)
            keep_doc = docs_sorted[0]
            duplicates_to_keep[content_hash] = keep_doc
            
            # Mark others for deletion
            for doc in docs_sorted[1:]:
                duplicates_to_delete.append({
                    "id": doc["id"],
                    "content_hash": content_hash,
                    "source": doc.get("metadata", {}).get("source", "unknown"),
                    "keep_id": keep_doc["id"]
                })
    
    return {
        "to_delete": duplicates_to_delete,
        "to_keep": duplicates_to_keep
    }

def cleanup_duplicates(dry_run: bool = True):
    """Clean up duplicate documents"""
    print("🧹 StillMe RAG Duplicate Cleanup")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    else:
        print("⚠️  LIVE MODE - Duplicates will be DELETED")
    
    try:
        chroma_client = ChromaClient()
        
        print("\n📊 Step 1: Finding duplicates...")
        duplicates_info = find_duplicates(chroma_client)
        
        to_delete = duplicates_info["to_delete"]
        to_keep = duplicates_info["to_keep"]
        
        if not to_delete:
            print("✅ No duplicates found!")
            return
        
        print(f"⚠️  Found {len(to_delete)} duplicate documents to delete")
        print(f"✅ Will keep {len(to_keep)} unique documents")
        
        # Group by content hash for display
        by_hash = defaultdict(list)
        for doc in to_delete:
            by_hash[doc["content_hash"]].append(doc)
        
        print(f"\n📋 Duplicate Groups ({len(by_hash)} groups):")
        for i, (content_hash, docs) in enumerate(by_hash.items(), 1):
            keep_doc = to_keep[content_hash]
            print(f"\n   Group {i}: {len(docs)} duplicates")
            print(f"      ✅ Keeping: {keep_doc['id']} (source: {keep_doc.get('metadata', {}).get('source', 'unknown')})")
            print(f"      ❌ Deleting:")
            for doc in docs[:5]:  # Show first 5
                print(f"         - {doc['id']} (source: {doc['source']})")
            if len(docs) > 5:
                print(f"         ... and {len(docs) - 5} more")
        
        if dry_run:
            print("\n💡 This was a DRY RUN. To actually delete duplicates, run:")
            print("   python scripts/cleanup_rag_duplicates.py --delete")
        else:
            print("\n🗑️  Step 2: Deleting duplicates...")
            knowledge_collection = chroma_client.knowledge_collection
            
            # Delete in batches to avoid memory issues
            batch_size = 50
            deleted_count = 0
            
            for i in range(0, len(to_delete), batch_size):
                batch = to_delete[i:i + batch_size]
                ids_to_delete = [doc["id"] for doc in batch]
                
                try:
                    knowledge_collection.delete(ids=ids_to_delete)
                    deleted_count += len(ids_to_delete)
                    print(f"   ✅ Deleted batch {i//batch_size + 1}: {len(ids_to_delete)} documents")
                except Exception as e:
                    print(f"   ⚠️  Error deleting batch {i//batch_size + 1}: {e}")
            
            print(f"\n✅ Cleanup complete! Deleted {deleted_count} duplicate documents")
            print(f"✅ Kept {len(to_keep)} unique documents")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean up duplicate RAG documents")
    parser.add_argument("--delete", action="store_true", help="Actually delete duplicates (default: dry run)")
    args = parser.parse_args()
    
    cleanup_duplicates(dry_run=not args.delete)

