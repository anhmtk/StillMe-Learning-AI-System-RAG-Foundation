#!/usr/bin/env python3
"""
Script to inspect foundational knowledge documents in ChromaDB.
Shows full content of all CRITICAL_FOUNDATION documents, especially about self-tracking.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.rag.chroma_client import ChromaClient
from stillme_core.rag.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_foundational_knowledge():
    """
    Inspect all foundational knowledge documents in ChromaDB.
    """
    logger.info("="*60)
    logger.info("Inspecting Foundational Knowledge Documents")
    logger.info("="*60)
    
    try:
        # Initialize services
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        
        # Get collection
        collection = chroma_client.knowledge_collection
        
        # Get all CRITICAL_FOUNDATION documents
        logger.info("\n1. Retrieving all CRITICAL_FOUNDATION documents...")
        results = collection.get(
            where={"source": "CRITICAL_FOUNDATION"},
            include=["documents", "metadatas", "ids"]
        )
        
        if not results or not results.get("ids"):
            logger.warning("   ⚠️  No CRITICAL_FOUNDATION documents found!")
            logger.warning("   💡 Run: python scripts/add_foundational_knowledge_remote.py")
            return
        
        foundational_docs = []
        for i, doc_id in enumerate(results["ids"]):
            foundational_docs.append({
                "id": doc_id,
                "content": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
        
        logger.info(f"   ✅ Found {len(foundational_docs)} CRITICAL_FOUNDATION documents")
        
        # Filter for self-tracking related documents
        logger.info("\n2. Filtering for self-tracking related documents...")
        self_tracking_keywords = [
            "track", "execution", "time", "task", "performance",
            "TaskTracker", "TimeEstimationEngine", "self-tracking",
            "thời gian", "thực thi", "theo dõi"
        ]
        
        self_tracking_docs = []
        for doc in foundational_docs:
            content_lower = doc["content"].lower()
            if any(keyword.lower() in content_lower for keyword in self_tracking_keywords):
                self_tracking_docs.append(doc)
        
        logger.info(f"   ✅ Found {len(self_tracking_docs)} documents mentioning self-tracking")
        
        # Display all self-tracking documents
        logger.info("\n3. Self-Tracking Foundational Knowledge Documents:")
        logger.info("="*60)
        
        for i, doc in enumerate(self_tracking_docs, 1):
            logger.info(f"\n--- Document {i}/{len(self_tracking_docs)} ---")
            logger.info(f"ID: {doc['id']}")
            logger.info(f"Title: {doc['metadata'].get('title', 'N/A')}")
            logger.info(f"Source: {doc['metadata'].get('source', 'N/A')}")
            logger.info(f"\nContent ({len(doc['content'])} chars):")
            logger.info("-" * 60)
            logger.info(doc['content'])
            logger.info("-" * 60)
        
        # Also show all foundational docs (for context)
        logger.info(f"\n4. All Foundational Knowledge Documents ({len(foundational_docs)} total):")
        logger.info("="*60)
        
        for i, doc in enumerate(foundational_docs, 1):
            logger.info(f"\n--- Document {i}/{len(foundational_docs)} ---")
            logger.info(f"ID: {doc['id']}")
            logger.info(f"Title: {doc['metadata'].get('title', 'N/A')}")
            logger.info(f"Source: {doc['metadata'].get('source', 'N/A')}")
            
            # Show first 500 chars
            content_preview = doc['content'][:500]
            logger.info(f"\nContent preview ({len(doc['content'])} chars total):")
            logger.info("-" * 60)
            logger.info(content_preview)
            if len(doc['content']) > 500:
                logger.info("... (truncated)")
            logger.info("-" * 60)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Summary:")
        logger.info(f"  - Total foundational documents: {len(foundational_docs)}")
        logger.info(f"  - Self-tracking related: {len(self_tracking_docs)}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    inspect_foundational_knowledge()

