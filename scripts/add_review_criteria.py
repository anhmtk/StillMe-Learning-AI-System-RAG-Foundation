#!/usr/bin/env python3
"""
Script to add StillMe Review Criteria to RAG
This ensures StillMe can retrieve review criteria when evaluating proposals
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

# Review Criteria Document
REVIEW_CRITERIA = """
# StillMe Peer Review Criteria

## Core Evaluation Criteria

### 1. Novelty (Tính Mới)
- High (8-10): Introduces genuinely new concepts, methods, or perspectives not commonly found in StillMe's knowledge base
- Medium (5-7): Presents known concepts but with new applications, combinations, or interpretations
- Low (0-4): Purely repetitive of existing knowledge without new insights

### 2. Feasibility (Tính Khả Thi)
- High (8-10): Clearly implementable, well-defined, with concrete steps
- Medium (5-7): Generally feasible but may require clarification or additional resources
- Low (0-4): Vague, unrealistic, or requires resources beyond StillMe's capabilities

### 3. Relevance (Tính Liên Quan)
- High (8-10): Directly relevant to StillMe's mission (AI transparency, ethics, RAG, learning systems)
- Medium (5-7): Related to AI/tech but not core to StillMe's mission
- Low (0-4): Unrelated to AI, technology, or StillMe's domain

### 4. Clarity (Độ Rõ Ràng)
- High (8-10): Well-structured, clear, unambiguous
- Medium (5-7): Generally clear but may need minor clarification
- Low (0-4): Confusing, ambiguous, or poorly structured

### 5. Evidence Base (Cơ Sở Bằng Chứng)
- High (8-10): Well-supported by credible sources, verifiable claims
- Medium (5-7): Some evidence but may need more support
- Low (0-4): Lacks evidence, unverifiable, or from unreliable sources

## Scoring Guidelines

- Score Range: 0.0 to 10.0
- Threshold for Acceptance: >= 5.0
- Threshold for High Quality: >= 7.0

### Weighted Criteria:
- Novelty: 25%
- Feasibility: 30%
- Relevance: 25%
- Clarity: 10%
- Evidence Base: 10%

### Quick Evaluation (for pre-filtering):
1. Relevance check: Is this related to AI/tech/StillMe's mission? (Yes/No)
2. Feasibility check: Can StillMe learn this? (Yes/No)
3. Quality check: Is this well-structured and clear? (Yes/No)

If all three are "Yes" → Score >= 5.0 (pass)
If any are "No" → Score < 5.0 (reject)

## StillMe's Mission Alignment
Proposals should align with StillMe's core values:
- Transparency: Does this promote transparency in AI?
- Ethics: Does this relate to ethical AI development?
- Open Source: Does this support open source AI?
- Community Governance: Does this enable community control?

## Learning Source Quality
- High Quality Sources: arXiv, peer-reviewed papers, Wikipedia, established tech blogs
- Medium Quality: General tech news, blog posts
- Low Quality: Unverified claims, spam, irrelevant content
"""


def add_review_criteria():
    """Add StillMe Review Criteria to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Adding StillMe Review Criteria to RAG...")
        
        # Check if already exists by trying to retrieve
        try:
            existing = rag_retrieval.retrieve_context(
                query="StillMe Peer Review Criteria",
                knowledge_limit=5
            )
            
            # Check if review criteria already exists in retrieved documents
            criteria_exists = False
            for doc in existing.get("knowledge_docs", []):
                content = doc.get("content", "")
                if "StillMe Peer Review Criteria" in content or "Core Evaluation Criteria" in content:
                    criteria_exists = True
                    break
            
            if criteria_exists:
                logger.info("✅ Review Criteria already exists in RAG, skipping...")
                return True
        except Exception as check_error:
            logger.debug(f"Could not check for existing criteria: {check_error}. Proceeding to add...")
        
        # Add review criteria with special metadata
        tags_list = ["review_criteria", "foundational:stillme", "evaluation", "peer_review"]
        tags_string = ",".join(tags_list)
        
        success = rag_retrieval.add_learning_content(
            content=REVIEW_CRITERIA,
            source="StillMe_Review_Criteria",
            content_type="knowledge",
            metadata={
                "tags": tags_string,
                "category": "review_criteria",
                "version": "1.0",
                "critical": "true"
            }
        )
        
        if success:
            logger.info("✅ Successfully added Review Criteria to RAG")
            return True
        else:
            logger.error("❌ Failed to add Review Criteria to RAG")
            return False
            
    except Exception as e:
        logger.error(f"Error adding Review Criteria: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = add_review_criteria()
    sys.exit(0 if success else 1)

