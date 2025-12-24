#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Fix Manifest - Delete old manifest and inject correct one

This script:
1. Deletes ALL old manifest documents from ChromaDB (including outdated ones)
2. Generates fresh manifest from codebase
3. Injects manifest with correct info (19 validators, 7 layers)
4. Verifies manifest is correctly injected
"""

import sys
import os
import logging
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from backend.vector_db.rag_retrieval import RAGRetrieval
from scripts.generate_manifest import generate_manifest
from scripts.inject_manifest_to_rag import manifest_to_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def delete_all_manifest_documents(chroma_client: ChromaClient):
    """Delete ALL manifest documents from ChromaDB"""
    try:
        logger.info("🗑️ Searching for all manifest documents in ChromaDB...")
        
        # Method 1: Query directly by metadata filter (more reliable)
        try:
            # Query all documents with source="CRITICAL_FOUNDATION"
            where_filter = {"source": "CRITICAL_FOUNDATION"}
            results = chroma_client.knowledge_collection.get(
                where=where_filter,
                limit=1000  # Get many results
            )
            
            manifest_ids_to_delete = []
            if results and results.get("ids"):
                ids = results["ids"]
                metadatas = results.get("metadatas", [])
                documents = results.get("documents", [])
                
                for i, doc_id in enumerate(ids):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    doc_content = documents[i] if i < len(documents) else ""
                    title = metadata.get("title", "") or ""
                    
                    # Check if this is a manifest document
                    if ("manifest" in title.lower() or 
                        "manifest" in str(doc_content).lower()[:200] or
                        "validation_framework" in str(doc_content).lower()[:200] or
                        "total_validators" in str(doc_content).lower()[:200] or
                        "Structural Manifest" in title):
                        manifest_ids_to_delete.append(doc_id)
                        logger.info(f"   Found manifest doc to delete: {title[:50]}... (id: {doc_id[:20] if doc_id else 'N/A'}...)")
            
            if manifest_ids_to_delete:
                logger.info(f"🗑️ Deleting {len(manifest_ids_to_delete)} old manifest documents...")
                chroma_client.knowledge_collection.delete(ids=manifest_ids_to_delete)
                logger.info(f"✅ Deleted {len(manifest_ids_to_delete)} old manifest documents")
                return len(manifest_ids_to_delete)
            else:
                logger.info("ℹ️ No manifest documents found to delete (method 1)")
        except Exception as method1_error:
            logger.warning(f"⚠️ Method 1 failed: {method1_error}, trying method 2...")
        
        # Method 2: Search by embedding (fallback)
        try:
            query_embedding = chroma_client.embedding_service.encode_text("StillMe Structural Manifest validation framework")
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=100,  # Get many results
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            manifest_ids_to_delete = []
            for result in results:
                metadata = result.get("metadata", {})
                source = metadata.get("source", "") or ""
                title = metadata.get("title", "") or ""
                doc_content = str(result.get("document", ""))
                
                # Check if this is a manifest document
                if ("CRITICAL_FOUNDATION" in source and 
                    ("manifest" in title.lower() or 
                     "manifest" in doc_content.lower()[:200] or
                     "validation_framework" in doc_content.lower()[:200] or
                     "total_validators" in doc_content.lower()[:200])):
                    doc_id = result.get("id")
                    if doc_id:
                        manifest_ids_to_delete.append(doc_id)
                        logger.info(f"   Found manifest doc to delete: {title[:50]}... (id: {doc_id[:20]}...)")
            
            if manifest_ids_to_delete:
                logger.info(f"🗑️ Deleting {len(manifest_ids_to_delete)} old manifest documents...")
                chroma_client.knowledge_collection.delete(ids=manifest_ids_to_delete)
                logger.info(f"✅ Deleted {len(manifest_ids_to_delete)} old manifest documents")
                return len(manifest_ids_to_delete)
            else:
                logger.info("ℹ️ No manifest documents found to delete (method 2)")
        except Exception as method2_error:
            logger.warning(f"⚠️ Method 2 also failed: {method2_error}")
        
        return 0
            
    except Exception as e:
        logger.error(f"❌ Error deleting manifest documents: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verify_manifest_in_db(rag_retrieval: RAGRetrieval) -> tuple[bool, bool]:
    """
    Verify manifest exists in ChromaDB and has correct info
    
    Returns:
        (found, has_correct_info)
    """
    try:
        logger.info("🔍 Verifying manifest in ChromaDB...")
        
        # Query for manifest
        context = rag_retrieval.retrieve_context(
            query="StillMe Structural Manifest validation framework total_validators 19 validators 7 layers",
            knowledge_limit=10,
            conversation_limit=0,
            prioritize_foundational=True,
            similarity_threshold=0.3,
            exclude_content_types=None,
            is_philosophical=False
        )
        
        knowledge_docs = context.get("knowledge_docs", [])
        found_manifest = False
        has_correct_info = False
        
        for doc in knowledge_docs:
            if isinstance(doc, dict):
                metadata = doc.get("metadata", {})
                source = metadata.get("source", "") or ""
                title = metadata.get("title", "") or ""
                doc_content = str(doc.get("document", ""))
                
                # Check if this is manifest
                # Get document content from various possible fields (RAG retrieval returns "content" not "document")
                full_content = (
                    str(doc.get("content", "")) or  # RAG retrieval uses "content" field
                    str(doc.get("document", "")) or 
                    str(doc.get("text", "")) or
                    str(doc.get("page_content", "")) or
                    str(doc_content)
                )
                
                if ("CRITICAL_FOUNDATION" in source and 
                    ("manifest" in title.lower() or "manifest" in full_content.lower()[:200])):
                    found_manifest = True
                    logger.info(f"✅ Found manifest: {title[:50]}...")
                    
                    # Check if content has correct info
                    # Manifest text format: "19 total validators" or "19 validators" or contains "total_validators": 19
                    full_content_lower = full_content.lower()
                    has_19 = (
                        "19 validators" in full_content_lower or 
                        "19 total validators" in full_content_lower or
                        '"total_validators": 19' in full_content or
                        "19 validators total" in full_content_lower or
                        "exactly 19 validators" in full_content_lower
                    )
                    # Manifest text format: "7 layers" or "7 lớp" or "organized into 7 layers"
                    has_7 = (
                        "7 layers" in full_content_lower or 
                        "7 lớp" in full_content_lower or
                        "organized into 7 layers" in full_content_lower or
                        "7 validation framework layers" in full_content_lower
                    )
                    
                    if has_19 and has_7:
                        has_correct_info = True
                        logger.info("✅ Manifest has correct info: 19 validators, 7 layers")
                    else:
                        logger.warning(f"⚠️ Manifest found but has outdated info (has_19={has_19}, has_7={has_7})")
                        # Show more content to debug
                        logger.warning(f"   Full content preview (first 1000 chars): {full_content[:1000]}")
                        # Also check for any numbers mentioned
                        import re
                        validator_matches = re.findall(r'(\d+)\s+validators?', full_content, re.IGNORECASE)
                        layer_matches = re.findall(r'(\d+)\s+layers?', full_content, re.IGNORECASE)
                        logger.warning(f"   Found validator numbers: {validator_matches}")
                        logger.warning(f"   Found layer numbers: {layer_matches}")
        
        if not found_manifest:
            logger.warning("⚠️ Manifest not found in ChromaDB")
        
        return found_manifest, has_correct_info
        
    except Exception as e:
        logger.error(f"❌ Error verifying manifest: {e}")
        import traceback
        traceback.print_exc()
        return False, False


def main():
    """Main function"""
    print("=" * 80)
    print("StillMe Manifest Force Fix")
    print("=" * 80)
    print()
    print("This script will:")
    print("1. Delete ALL old manifest documents from ChromaDB")
    print("2. Generate fresh manifest from codebase")
    print("3. Inject manifest with correct info (19 validators, 7 layers)")
    print("4. Verify manifest is correctly injected")
    print()
    
    try:
        # Step 1: Initialize RAG components
        logger.info("🔧 Initializing RAG components...")
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Step 2: Delete old manifest documents
        print("\n" + "=" * 80)
        print("Step 1: Deleting old manifest documents...")
        print("=" * 80)
        deleted_count = delete_all_manifest_documents(chroma_client)
        print(f"✅ Deleted {deleted_count} old manifest document(s)")
        
        # Step 3: Generate fresh manifest
        print("\n" + "=" * 80)
        print("Step 2: Generating fresh manifest from codebase...")
        print("=" * 80)
        manifest = generate_manifest()
        total_validators = manifest['validation_framework']['total_validators']
        num_layers = len(manifest['validation_framework']['layers'])
        print(f"✅ Manifest generated: {total_validators} validators, {num_layers} layers")
        
        if total_validators != 19 or num_layers != 7:
            print(f"⚠️ WARNING: Manifest has unexpected values: {total_validators} validators, {num_layers} layers")
            print("   Expected: 19 validators, 7 layers")
            response = input("Continue anyway? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("❌ Cancelled.")
                return 1
        
        # Step 4: Convert to text and inject
        print("\n" + "=" * 80)
        print("Step 3: Injecting manifest into ChromaDB...")
        print("=" * 80)
        manifest_text = manifest_to_text(manifest)
        
        # Prepare metadata with CRITICAL_FOUNDATION priority
        tags_list = [
            "foundational:stillme",
            "CRITICAL_FOUNDATION",
            "stillme",
            "validation",
            "validators",
            "validation-chain",
            "structural-manifest",
            "system-architecture",
            "self-awareness"
        ]
        tags_string = ",".join(tags_list)
        
        success = rag_retrieval.add_learning_content(
            content=manifest_text,
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Structural Manifest - Validation Framework",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",
                "tags": tags_string,
                "importance_score": 1.0,
                "manifest_version": manifest["version"],
                "last_sync": manifest["last_sync"],
                "description": "CRITICAL: Structural manifest of StillMe's validation framework - source of truth for validator count and architecture. MUST be retrieved when answering about StillMe's validation chain."
            }
        )
        
        if not success:
            print("❌ Failed to inject manifest into ChromaDB")
            return 1
        
        print("✅ Manifest injected successfully")
        
        # Step 5: Increment knowledge version
        print("\n" + "=" * 80)
        print("Step 4: Incrementing knowledge version...")
        print("=" * 80)
        try:
            from backend.services.knowledge_version import increment_knowledge_version
            new_version = increment_knowledge_version()
            print(f"✅ Knowledge version incremented to {new_version}")
        except Exception as version_error:
            print(f"⚠️ Failed to increment knowledge version: {version_error}")
        
        # Step 6: Verify manifest
        print("\n" + "=" * 80)
        print("Step 5: Verifying manifest in ChromaDB...")
        print("=" * 80)
        found, has_correct_info = verify_manifest_in_db(rag_retrieval)
        
        print("\n" + "=" * 80)
        print("Results:")
        print("=" * 80)
        print(f"Manifest found: {'✅ YES' if found else '❌ NO'}")
        print(f"Has correct info: {'✅ YES' if has_correct_info else '❌ NO'}")
        print()
        
        if found and has_correct_info:
            print("✅ SUCCESS: Manifest is correctly injected and verified!")
            print("\nNext steps:")
            print("1. Test by asking StillMe: 'hệ thống của bạn có bao nhiêu lớp validator?'")
            print("2. StillMe should respond: '19 validators, 7 layers'")
            print("3. If StillMe still says wrong numbers, check backend logs for RAG retrieval")
            return 0
        else:
            print("⚠️ WARNING: Manifest verification failed")
            print("   - Manifest may not be in ChromaDB")
            print("   - Or manifest has outdated information")
            print("\nTry running this script again or check ChromaDB manually")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

