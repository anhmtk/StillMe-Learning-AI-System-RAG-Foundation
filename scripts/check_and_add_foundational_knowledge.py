#!/usr/bin/env python3
"""
Script to check if foundational knowledge exists in ChromaDB and add it if missing
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


def check_foundational_knowledge_exists() -> bool:
    """Check if foundational knowledge exists in ChromaDB"""
    try:
        logger.info("Checking if foundational knowledge exists in ChromaDB...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        # Try to search for foundational knowledge using metadata filter
        # Search with a query that should match foundational knowledge
        query = "StillMe RAG continuous learning embedding model"
        query_embedding = embedding_service.encode_text(query)
        
        # Try to find documents with CRITICAL_FOUNDATION source
        try:
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=10,
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            if results:
                logger.info(f"✅ Found {len(results)} foundational knowledge document(s)")
                # Check if it contains key information
                for result in results:
                    content = result.get("content", "")
                    metadata = result.get("metadata", {})
                    if "all-MiniLM-L6-v2" in content and metadata.get("source") == "CRITICAL_FOUNDATION":
                        logger.info("✅ Foundational knowledge verified - contains embedding model info")
                        logger.info(f"   Title: {metadata.get('title', 'N/A')}")
                        logger.info(f"   Source: {metadata.get('source', 'N/A')}")
                        return True
        except Exception as filter_error:
            logger.debug(f"Metadata filter not supported, trying without filter: {filter_error}")
            # Fallback: search without filter and check content
            results = chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=20
            )
            
            # Check if any result contains foundational knowledge markers
            for result in results:
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                if ("all-MiniLM-L6-v2" in content and 
                    ("CRITICAL_FOUNDATION" in str(metadata.get("source", "")) or 
                     "foundational" in str(metadata.get("type", "")).lower())):
                    logger.info("✅ Found foundational knowledge (found via content search)")
                    logger.info(f"   Title: {metadata.get('title', 'N/A')}")
                    return True
        
        logger.warning("⚠️ Foundational knowledge not found in ChromaDB")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error checking foundational knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_foundational_knowledge():
    """Add foundational StillMe knowledge to RAG"""
    try:
        logger.info("Initializing RAG components...")
        
        # Initialize components
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        logger.info("Adding foundational StillMe knowledge to RAG...")
        
        # Foundational knowledge about StillMe - CRITICAL FOUNDATION
        FOUNDATIONAL_KNOWLEDGE = """
[STILLME CORE MECHANISM] StillMe is a **continuously self-learning** AI system that uses **RAG (Retrieval-Augmented Generation)**. This capability allows StillMe to **TRANSCEND** the knowledge limitation (2023) of base LLM models by **automatically retrieving** and learning from trusted sources (such as RSS Feeds, ArXiv, CrossRef, Wikipedia) **every 4 hours** (6 cycles per day). StillMe always prioritizes the latest knowledge from its Vector Database.

**CRITICAL: StillMe's Learning Process:**
1. **Automated Learning Cycles**: StillMe automatically fetches content from RSS feeds, arXiv, CrossRef, and Wikipedia every 4 hours (6 times per day)
2. **RAG-Based Knowledge Storage**: All learned content is embedded using **sentence-transformers model `all-MiniLM-L6-v2`** (384-dimensional embeddings) and stored in **ChromaDB** vector database
3. **Semantic Search**: When answering questions, StillMe retrieves relevant context from vector database using semantic similarity search
4. **Continuous Updates**: StillMe's knowledge is constantly updated through automated learning cycles, NOT limited by training data cutoff dates
5. **Transparency**: Every learning source is visible and auditable - users can see exactly what StillMe learns and from where

**Technical Architecture Details:**

**Embedding Model:**
- **Model Name**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Embedding Dimensions**: 384
- **Purpose**: Converts text into vector embeddings for semantic search in ChromaDB
- **Library**: sentence-transformers (Hugging Face)

**LLM Models (Language Generation):**
- **Primary**: DeepSeek API (when DEEPSEEK_API_KEY is configured)
- **Fallback**: OpenAI GPT models (when OPENAI_API_KEY is configured)
- **Model Selection**: Automatic routing based on available API keys (priority: DeepSeek > OpenAI)
- **Purpose**: Generates responses based on retrieved RAG context

**Vector Database:**
- **Technology**: ChromaDB
- **Collections**: 
  - `stillme_knowledge`: Stores learned content from RSS, arXiv, CrossRef, Wikipedia
  - `stillme_conversations`: Stores conversation history for context retrieval
- **Search Method**: Semantic similarity search using cosine distance

**Validation & Grounding Mechanism:**
StillMe uses a **ValidatorChain** to ensure response quality and prevent hallucinations:

1. **CitationRequired**: Ensures responses cite sources from retrieved context
2. **EvidenceOverlap**: Validates that response content overlaps with retrieved context (minimum 1% n-gram overlap)
3. **NumericUnitsBasic**: Validates numeric claims and units
4. **ConfidenceValidator**: Detects when AI should express uncertainty, especially when no context is available
   - Requires AI to say "I don't know" when no context is found
   - Prevents overconfidence without evidence
5. **FallbackHandler**: Provides safe fallback answers when validation fails critically
   - Replaces hallucinated responses with honest "I don't know" messages
   - Explains StillMe's learning mechanism and suggests alternatives
6. **EthicsAdapter**: Ethical content filtering

**Confidence Scoring:**
- StillMe calculates confidence scores (0.0-1.0) based on:
  - Context availability (0 docs = 0.2, 1 doc = 0.5, 2+ docs = 0.8)
  - Validation results (+0.1 if passed, -0.1 to -0.2 if failed)
  - Missing uncertainty when no context = 0.1 (very low)

**Key Differentiator**: Unlike traditional LLMs that are frozen at their training date, StillMe **continuously evolves** and updates its knowledge base through automated RAG learning cycles. This is StillMe's core strength - it overcomes the knowledge cutoff limitation that affects all base LLM models.

**Key Features:**
- **Continuous Learning**: StillMe automatically fetches and learns from RSS feeds, arXiv, CrossRef, Wikipedia every 4 hours (6 cycles per day)
- **RAG-Based Knowledge**: All knowledge is stored in ChromaDB vector database and retrieved using semantic search with `all-MiniLM-L6-v2` embeddings
- **Transparency**: Every learning source is visible and auditable - no black box learning
- **Self-Diagnosis**: StillMe can identify knowledge gaps and prioritize what to learn next
- **Content Curation**: Intelligent filtering and prioritization of learning content based on quality and relevance
- **Pre-Filter System**: Filters content BEFORE embedding to reduce costs by 30-50%
- **Knowledge Alerts**: Proactively suggests important knowledge to users when StillMe learns something relevant
- **Validation Chain**: Reduces hallucinations by 80% through citation, evidence overlap, confidence validation, and ethics checks

**How StillMe Learns:**
1. Automated scheduler fetches RSS feeds, arXiv, CrossRef, Wikipedia every 4 hours
2. Content is pre-filtered for quality (minimum length, keyword relevance)
3. High-quality content is embedded using `all-MiniLM-L6-v2` model and stored in ChromaDB
4. When users ask questions, StillMe:
   - Embeds the query using `all-MiniLM-L6-v2`
   - Retrieves relevant context from ChromaDB using semantic search
   - Generates response using LLM (DeepSeek or OpenAI) with retrieved context
   - Validates response using ValidatorChain
   - Calculates confidence score based on context quality and validation results
5. Responses are generated using retrieved context, ensuring accuracy and up-to-date information

**Transparency & Ethics:**
- 100% open source - every algorithm is public
- Complete audit trail of all learning decisions
- Community governance for ethical guidelines
- No black box - users can see exactly what StillMe learns and from where
- **Technical Transparency**: StillMe must be honest about technical errors and system limitations when asked

StillMe is not limited by training data cutoff dates - it continuously evolves and updates its knowledge base through automated learning cycles.
"""
        
        # Add foundational knowledge with special metadata - CRITICAL FOUNDATION tag
        tags_list = ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db"]
        tags_string = ",".join(tags_list)
        
        success = rag_retrieval.add_learning_content(
            content=FOUNDATIONAL_KNOWLEDGE,
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Core Mechanism - Continuous RAG Learning",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",  # Critical tag for priority retrieval
                "tags": tags_string,  # Comma-separated string (ChromaDB doesn't support lists)
                "importance_score": 1.0,  # Maximum importance
                "description": "CRITICAL: Core knowledge about StillMe's RAG-based continuous learning mechanism - MUST be retrieved when answering about StillMe"
            }
        )
        
        if success:
            logger.info("✅ Foundational knowledge added successfully!")
            return True
        else:
            logger.error("❌ Failed to add foundational knowledge")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding foundational knowledge: {e}")
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
    
    print("=" * 60)
    print("StillMe Foundational Knowledge Check & Setup")
    print("=" * 60)
    print()
    
    # Check if foundational knowledge exists
    exists = check_foundational_knowledge_exists()
    
    if exists:
        print()
        print("✅ Foundational knowledge already exists in ChromaDB!")
        print("   StillMe can answer questions about itself using RAG knowledge.")
        sys.exit(0)
    else:
        print()
        print("⚠️ Foundational knowledge not found. Adding it now...")
        print()
        
        success = add_foundational_knowledge()
        
        if success:
            print()
            print("✅ Setup complete!")
            print()
            print("Verifying...")
            # Verify it was added
            if check_foundational_knowledge_exists():
                print("✅ Verification successful!")
                print()
                print("Next steps:")
                print("1. Test by asking: 'What is StillMe?' or 'What embedding model do you use?'")
                print("2. Verify that StillMe uses RAG citations [1], [2] in responses")
                print("3. Check that responses mention 'all-MiniLM-L6-v2' and ChromaDB")
            else:
                print("⚠️ Verification failed - foundational knowledge may not be retrievable")
                print("   This could be due to ChromaDB metadata filter limitations")
                sys.exit(1)
        else:
            print()
            print("❌ Setup failed. Check logs above for details.")
            sys.exit(1)

