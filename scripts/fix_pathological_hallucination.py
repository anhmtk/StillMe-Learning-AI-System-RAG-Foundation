#!/usr/bin/env python3
"""
Script to fix pathological hallucination in RAG system

This script:
1. Deletes noisy data about "Nature Machine Intelligence" and "A psychometric framework"
2. Ensures foundational_technical.md is properly injected with correct metadata
3. Verifies that foundational knowledge is retrievable
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


def delete_noisy_documents():
    """Delete documents containing noisy keywords from ChromaDB"""
    try:
        logger.info("🔍 Searching for noisy documents...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        # Search for documents containing noisy keywords
        noisy_keywords = [
            "Nature Machine Intelligence",
            "A psychometric framework",
            "psychometric framework",
            "CitationRelevance, FactualAccuracy, AntiHallucination, LogicConsistency"  # Fake validator list
        ]
        
        deleted_count = 0
        
        for keyword in noisy_keywords:
            logger.info(f"🔍 Searching for documents containing: '{keyword}'...")
            query_embedding = embedding_service.encode_text(keyword)
            
            # Search with very low threshold to find all matches
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=50,
                where=None  # No filter, search all
            )
            
            # Check each result for noisy content
            for result in results:
                content = str(result.get("document", "")).lower()
                metadata = result.get("metadata", {})
                source = metadata.get("source", "")
                
                # Skip CRITICAL_FOUNDATION documents (we want to keep those)
                if "CRITICAL_FOUNDATION" in source:
                    continue
                
                # Check if this document contains noisy keywords
                is_noisy = False
                if "nature machine intelligence" in content.lower():
                    is_noisy = True
                elif "psychometric framework" in content.lower():
                    is_noisy = True
                elif "factualaccuracy" in content.lower() and "antihallucination" in content.lower():
                    # This is the fake validator list
                    is_noisy = True
                
                if is_noisy:
                    doc_id = result.get("id")
                    if doc_id:
                        try:
                            # Delete from ChromaDB
                            chroma_client.knowledge_collection.delete(ids=[doc_id])
                            deleted_count += 1
                            logger.info(f"✅ Deleted noisy document: ID={doc_id}, Title={metadata.get('title', 'N/A')[:50]}")
                        except Exception as delete_error:
                            logger.warning(f"⚠️ Failed to delete document {doc_id}: {delete_error}")
        
        logger.info(f"✅ Deleted {deleted_count} noisy document(s)")
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error deleting noisy documents: {e}")
        import traceback
        traceback.print_exc()
        return 0


def ensure_foundational_technical_injected():
    """Ensure foundational_technical.md is properly injected with correct metadata"""
    try:
        logger.info("📖 Loading foundational_technical.md...")
        
        technical_path = project_root / "docs" / "rag" / "foundational_technical.md"
        
        if not technical_path.exists():
            logger.error(f"❌ File not found: {technical_path}")
            return False
        
        with open(technical_path, "r", encoding="utf-8") as f:
            technical_content = f.read()
        
        # Remove frontmatter if present
        if technical_content.startswith("---"):
            parts = technical_content.split("---", 2)
            if len(parts) >= 3:
                technical_content = parts[2].strip()
        
        logger.info(f"📊 Content length: {len(technical_content)} characters")
        
        # Verify content contains correct validator info
        if "19 validators" not in technical_content and "19 validators total" not in technical_content:
            logger.warning("⚠️ Content does not contain '19 validators' - may be outdated")
        if "7 layers" not in technical_content and "7 lớp" not in technical_content:
            logger.warning("⚠️ Content does not contain '7 layers' - may be outdated")
        
        # Initialize RAG components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Check if foundational technical already exists
        logger.info("🔍 Checking if foundational technical already exists...")
        query_embedding = embedding_service.encode_text("StillMe validation framework 19 validators 7 layers")
        existing_results = chroma_client.search_knowledge(
            query_embedding=query_embedding,
            limit=5,
            where={"source": "CRITICAL_FOUNDATION"}
        )
        
        # Check if any existing result contains correct validator info
        has_correct_content = False
        for result in existing_results:
            content = str(result.get("document", ""))
            if "19 validators" in content or "19 validators total" in content:
                if "7 layers" in content or "7 lớp" in content:
                    has_correct_content = True
                    logger.info("✅ Found existing foundational technical with correct validator info")
                    break
        
        if not has_correct_content:
            logger.info("📝 Injecting foundational technical knowledge...")
            
            # Prepare metadata with maximum priority
            tags_list = [
                "foundational:stillme",
                "CRITICAL_FOUNDATION",
                "stillme",
                "rag",
                "validation",
                "validators",
                "validation-chain",
                "technical",
                "core_logic",
                "priority_high"
            ]
            tags_string = ",".join(tags_list)
            
            success = rag_retrieval.add_learning_content(
                content=technical_content,
                source="CRITICAL_FOUNDATION",
                content_type="knowledge",
                metadata={
                    "title": "StillMe Core Mechanism - Technical Architecture",
                    "foundational": "stillme",
                    "type": "foundational",
                    "source": "CRITICAL_FOUNDATION",
                    "tags": tags_string,
                    "importance_score": 1.0,  # Maximum importance
                    "priority": "high",  # Explicit priority field
                    "category": "core_logic",  # Explicit category for filtering
                    "content_type": "technical",
                    "domain": "stillme_architecture",
                    "description": "CRITICAL: Technical knowledge about StillMe's RAG-based continuous learning mechanism and validation framework (19 validators, 7 layers) - MUST be retrieved when answering about StillMe's architecture"
                }
            )
            
            if success:
                logger.info("✅ Foundational technical knowledge injected successfully!")
                return True
            else:
                logger.error("❌ Failed to inject foundational technical knowledge")
                return False
        else:
            logger.info("✅ Foundational technical already exists with correct content")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error ensuring foundational technical injection: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_retrieval():
    """Verify that foundational knowledge can be retrieved"""
    try:
        logger.info("🔍 Verifying retrieval of foundational knowledge...")
        
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        
        # Test queries that should retrieve foundational knowledge
        test_queries = [
            "How many validators does StillMe have?",
            "hệ thống của bạn có bao nhiêu lớp validator?",
            "StillMe validation framework layers",
            "19 validators 7 layers"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 Testing query: '{query}'...")
            query_embedding = embedding_service.encode_text(query)
            
            # Search with low threshold to ensure we get results
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=5,
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            if results:
                logger.info(f"✅ Found {len(results)} result(s) for query: '{query}'")
                for i, result in enumerate(results, 1):
                    content = str(result.get("document", ""))[:200]
                    metadata = result.get("metadata", {})
                    title = metadata.get("title", "N/A")
                    similarity = result.get("distance", "N/A")
                    logger.info(f"   Result {i}: Title={title}, Similarity={similarity}")
                    logger.info(f"   Content preview: {content}...")
                    
                    # Check if it contains correct info
                    if "19 validators" in content or "19 validators total" in content:
                        logger.info(f"   ✅ Contains correct validator count!")
                    if "7 layers" in content or "7 lớp" in content:
                        logger.info(f"   ✅ Contains correct layer count!")
            else:
                logger.warning(f"⚠️ No results found for query: '{query}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Fix encoding for Windows console
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    print("=" * 80)
    print("StillMe Pathological Hallucination Fix Script")
    print("=" * 80)
    print()
    
    # Step 1: Delete noisy documents
    print("Step 1: Deleting noisy documents...")
    deleted_count = delete_noisy_documents()
    print(f"✅ Deleted {deleted_count} noisy document(s)")
    print()
    
    # Step 2: Ensure foundational technical is injected
    print("Step 2: Ensuring foundational_technical.md is properly injected...")
    success = ensure_foundational_technical_injected()
    if success:
        print("✅ Foundational technical knowledge is properly injected")
    else:
        print("❌ Failed to inject foundational technical knowledge")
        sys.exit(1)
    print()
    
    # Step 3: Verify retrieval
    print("Step 3: Verifying retrieval...")
    verify_retrieval()
    print()
    
    print("=" * 80)
    print("✅ Fix script completed!")
    print()
    print("Next steps:")
    print("1. Test by asking: 'How many validators does StillMe have?'")
    print("2. Verify that StillMe responds with '19 validators, 7 layers'")
    print("3. Check that StillMe cites actual ChromaDB document IDs, not fake IDs like 12345")
    print("=" * 80)

