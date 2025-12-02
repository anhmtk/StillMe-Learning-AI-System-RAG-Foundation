"""
Vector Database Module for StillMe
Provides ChromaDB integration for RAG (Retrieval-Augmented Generation)

⚠️ MIGRATION NOTE: This module is being migrated to stillme_core.rag.
During migration, imports are forwarded from stillme_core.rag for backward compatibility.
"""

# During migration: Forward imports from stillme_core.rag
try:
    from stillme_core.rag import (
        ChromaClient,
        EmbeddingService,
        RAGRetrieval,
    )
except ImportError:
    # Fallback to local imports if stillme_core is not available yet
    from .chroma_client import ChromaClient
    from .embeddings import EmbeddingService
    from .rag_retrieval import RAGRetrieval

__all__ = ["ChromaClient", "EmbeddingService", "RAGRetrieval"]
