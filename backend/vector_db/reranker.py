"""
Cross-Encoder Re-ranker for StillMe RAG System

Implements BGE-Reranker or similar cross-encoder models to improve relevance
of retrieved documents after similarity search.

This addresses the limitation where ChromaDB similarity search can be fooled
by keyword matches with different semantics. Cross-encoder provides more accurate
semantic relevance scoring.
"""

import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Try to import reranker libraries
RERANKER_AVAILABLE = False
RERANKER_MODEL = None

try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
    logger.info("✅ FlagReranker (BGE-Reranker) available")
except ImportError:
    try:
        from sentence_transformers import CrossEncoder
        RERANKER_AVAILABLE = True
        logger.info("✅ SentenceTransformers CrossEncoder available")
    except ImportError:
        logger.warning("⚠️ No reranker library available. Install 'FlagEmbedding' or 'sentence-transformers' for reranking support.")


class Reranker:
    """
    Cross-encoder re-ranker for improving RAG retrieval relevance.
    
    Uses BGE-Reranker (FlagReranker) or SentenceTransformers CrossEncoder
    to re-rank documents after similarity search.
    """
    
    def __init__(self, model_name: Optional[str] = None, use_gpu: bool = False):
        """
        Initialize reranker.
        
        Args:
            model_name: Model name (default: BGE-Reranker-Base or ms-marco-MiniLM)
            use_gpu: Whether to use GPU (if available)
        """
        self.model = None
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.is_initialized = False
        
        if RERANKER_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize reranker model"""
        if self.is_initialized:
            return
        
        try:
            # Default to BGE-Reranker if available, otherwise use CrossEncoder
            if 'FlagReranker' in globals():
                # Use BGE-Reranker (recommended by Gemini)
                model_name = self.model_name or "BAAI/bge-reranker-base"
                logger.info(f"🔧 Initializing BGE-Reranker: {model_name}")
                self.model = FlagReranker(model_name, use_fp16=True)
                logger.info(f"✅ BGE-Reranker initialized: {model_name}")
            elif 'CrossEncoder' in globals():
                # Fallback to SentenceTransformers CrossEncoder
                model_name = self.model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
                logger.info(f"🔧 Initializing CrossEncoder: {model_name}")
                self.model = CrossEncoder(model_name)
                logger.info(f"✅ CrossEncoder initialized: {model_name}")
            
            self.is_initialized = True
        except Exception as e:
            logger.error(f"❌ Failed to initialize reranker: {e}")
            logger.warning("⚠️ Reranking will be disabled. Install 'FlagEmbedding' for BGE-Reranker support.")
            self.model = None
            self.is_initialized = False
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query: User query
            documents: List of document dicts with 'document' (text) and 'metadata' keys
            top_k: Number of top documents to return (None = return all)
        
        Returns:
            Re-ranked list of documents (sorted by relevance, highest first)
        """
        if not self.is_initialized or self.model is None:
            logger.debug("Reranker not available, returning original order")
            return documents[:top_k] if top_k else documents
        
        if not documents:
            return documents
        
        try:
            # Extract document texts
            doc_texts = []
            for doc in documents:
                # Try to get text from various possible keys
                text = doc.get("document", "")
                if not text:
                    text = doc.get("text", "")
                if not text:
                    # Try to construct from metadata
                    metadata = doc.get("metadata", {})
                    text = metadata.get("content", "") or metadata.get("summary", "") or metadata.get("title", "")
                
                if not text:
                    logger.warning(f"⚠️ Document has no text content, skipping: {doc.get('id', 'unknown')}")
                    continue
                
                doc_texts.append(text)
            
            if not doc_texts:
                logger.warning("⚠️ No document texts found for reranking")
                return documents[:top_k] if top_k else documents
            
            # Re-rank using cross-encoder
            if hasattr(self.model, 'compute_score'):
                # FlagReranker API
                pairs = [[query, text] for text in doc_texts]
                scores = self.model.compute_score(pairs)
                if isinstance(scores, list):
                    pass  # Already a list
                else:
                    scores = [scores] if len(doc_texts) == 1 else scores.tolist()
            else:
                # CrossEncoder API
                pairs = [[query, text] for text in doc_texts]
                scores = self.model.predict(pairs)
                if not isinstance(scores, list):
                    scores = scores.tolist()
            
            # Create list of (index, score) tuples
            scored_docs = list(zip(range(len(doc_texts)), scores))
            
            # Sort by score (descending)
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Re-order documents based on new scores
            reranked_docs = []
            for idx, score in scored_docs:
                doc = documents[idx].copy()
                # Add rerank score to metadata
                if "metadata" not in doc:
                    doc["metadata"] = {}
                doc["metadata"]["rerank_score"] = float(score)
                doc["metadata"]["original_rank"] = idx
                reranked_docs.append(doc)
            
            logger.info(f"✅ Re-ranked {len(reranked_docs)} documents (top score: {scored_docs[0][1]:.4f})")
            
            # Return top_k if specified
            if top_k:
                return reranked_docs[:top_k]
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"❌ Reranking failed: {e}", exc_info=True)
            logger.warning("⚠️ Returning original document order")
            return documents[:top_k] if top_k else documents


# Global reranker instance (lazy initialization)
_reranker_instance: Optional[Reranker] = None


def get_reranker() -> Optional[Reranker]:
    """
    Get global reranker instance (singleton pattern).
    
    Returns:
        Reranker instance if available, None otherwise
    """
    global _reranker_instance
    
    if _reranker_instance is None:
        # Check if reranking is enabled
        enable_reranker = os.getenv("ENABLE_RERANKER", "false").lower() == "true"
        
        if enable_reranker and RERANKER_AVAILABLE:
            model_name = os.getenv("RERANKER_MODEL_NAME", None)
            use_gpu = os.getenv("USE_GPU_FOR_RERANKER", "false").lower() == "true"
            _reranker_instance = Reranker(model_name=model_name, use_gpu=use_gpu)
        else:
            if not enable_reranker:
                logger.info("ℹ️ Reranker disabled (set ENABLE_RERANKER=true to enable)")
            else:
                logger.info("ℹ️ Reranker libraries not available")
    
    return _reranker_instance


def is_reranker_available() -> bool:
    """Check if reranker is available and enabled"""
    reranker = get_reranker()
    return reranker is not None and reranker.is_initialized

