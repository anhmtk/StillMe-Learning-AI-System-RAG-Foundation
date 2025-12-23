#!/usr/bin/env python3
"""
Verify and Re-inject Validator Information to ChromaDB

This script:
1. Checks if foundational_technical.md is in ChromaDB with correct content (19 validators, 7 layers)
2. Checks if manifest is in ChromaDB with correct content (19 validators, 7 layers)
3. Re-injects both if missing or incorrect
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


def check_foundational_technical_in_db(rag_retrieval: RAGRetrieval) -> bool:
    """Check if foundational_technical.md exists in ChromaDB with correct content"""
    try:
        logger.info("🔍 Checking foundational_technical.md in ChromaDB...")
        
        # Query for foundational technical knowledge
        context = rag_retrieval.retrieve_context(
            query="StillMe validation framework 19 validators 7 layers",
            knowledge_limit=10,
            conversation_limit=0,
            prioritize_foundational=True,
            similarity_threshold=0.3,
            exclude_content_types=None,
            is_philosophical=False
        )
        
        knowledge_docs = context.get("knowledge_docs", [])
        found_foundational = False
        has_correct_info = False
        
        for doc in knowledge_docs:
            if isinstance(doc, dict):
                metadata = doc.get("metadata", {})
                source = metadata.get("source", "") or ""
                title = metadata.get("title", "") or ""
                doc_content = str(doc.get("document", ""))
                
                # Check if this is foundational technical
                if ("CRITICAL_FOUNDATION" in source and 
                    "Technical Architecture" in title):
                    found_foundational = True
                    logger.info(f"✅ Found foundational_technical.md: {title[:50]}")
                    
                    # Check if content has correct info
                    has_19 = "19 validators" in doc_content or "19 validators total" in doc_content
                    has_7 = "7 layers" in doc_content or "7 lớp" in doc_content
                    
                    if has_19 and has_7:
                        has_correct_info = True
                        logger.info("✅ Content verified: Contains '19 validators' and '7 layers'")
                    else:
                        logger.warning(f"⚠️ Content may be outdated: has_19={has_19}, has_7={has_7}")
                        logger.warning(f"   Content preview: {doc_content[:200]}...")
        
        if not found_foundational:
            logger.warning("⚠️ foundational_technical.md not found in ChromaDB")
            return False
        
        if not has_correct_info:
            logger.warning("⚠️ foundational_technical.md found but content may be outdated")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking foundational_technical.md: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_manifest_in_db(rag_retrieval: RAGRetrieval) -> bool:
    """Check if manifest exists in ChromaDB with correct content"""
    try:
        logger.info("🔍 Checking manifest in ChromaDB...")
        
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
                if ("CRITICAL_FOUNDATION" in source and 
                    ("manifest" in title.lower() or "manifest" in doc_content.lower()[:100])):
                    found_manifest = True
                    logger.info(f"✅ Found manifest: {title[:50]}")
                    
                    # Check if content has correct info
                    has_19 = "19 validators" in doc_content or "total_validators" in doc_content
                    has_7 = "7 layers" in doc_content or len([l for l in doc_content.split("\n") if "Layer" in l]) >= 7
                    
                    if has_19 and has_7:
                        has_correct_info = True
                        logger.info("✅ Content verified: Contains '19 validators' and '7 layers'")
                    else:
                        logger.warning(f"⚠️ Content may be outdated: has_19={has_19}, has_7={has_7}")
                        logger.warning(f"   Content preview: {doc_content[:200]}...")
        
        if not found_manifest:
            logger.warning("⚠️ Manifest not found in ChromaDB")
            return False
        
        if not has_correct_info:
            logger.warning("⚠️ Manifest found but content may be outdated")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking manifest: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("StillMe Validator Information Verification & Re-injection")
    print("=" * 60)
    print()
    
    try:
        # Initialize RAG components
        logger.info("🔧 Initializing RAG components...")
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Check foundational_technical.md
        foundational_ok = check_foundational_technical_in_db(rag_retrieval)
        
        # Check manifest
        manifest_ok = check_manifest_in_db(rag_retrieval)
        
        print()
        print("=" * 60)
        print("Verification Results:")
        print("=" * 60)
        print(f"Foundational Technical: {'✅ OK' if foundational_ok else '❌ MISSING/OUTDATED'}")
        print(f"Manifest: {'✅ OK' if manifest_ok else '❌ MISSING/OUTDATED'}")
        print()
        
        if not foundational_ok or not manifest_ok:
            print("⚠️ Some information is missing or outdated. Re-injecting...")
            print()
            
            # Re-inject foundational_technical.md
            if not foundational_ok:
                logger.info("📥 Re-injecting foundational_technical.md...")
                from scripts.add_foundational_knowledge import add_foundational_knowledge
                success = add_foundational_knowledge()
                if success:
                    print("✅ foundational_technical.md re-injected successfully")
                else:
                    print("❌ Failed to re-inject foundational_technical.md")
            
            # Re-inject manifest
            if not manifest_ok:
                logger.info("📥 Re-injecting manifest...")
                from scripts.inject_manifest_to_rag import inject_manifest_to_rag
                success = inject_manifest_to_rag()
                if success:
                    print("✅ Manifest re-injected successfully")
                else:
                    print("❌ Failed to re-inject manifest")
            
            print()
            print("✅ Re-injection complete!")
            print()
            print("Next steps:")
            print("1. Test by asking: 'hệ thống của bạn có bao nhiêu lớp validator?'")
            print("2. Expected answer: '19 validators total, chia thành 7 lớp'")
        else:
            print("✅ All validator information is up-to-date in ChromaDB!")
            print()
            print("StillMe should now correctly report:")
            print("- 19 validators total")
            print("- 7 layers")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Fix encoding for Windows console
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    sys.exit(main())

