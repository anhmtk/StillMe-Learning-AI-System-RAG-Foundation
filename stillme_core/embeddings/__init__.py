"""
Embeddings Module for StillMe Core
==================================

Provides embedding backends with Windows-safe fallback mechanisms.
"""

from .adapter import EmbeddingBackend, SentenceTransformerBackend, FakeBackend
from .worker import EmbeddingWorker, EmbeddingRuntimeError

__all__ = [
    "EmbeddingBackend",
    "SentenceTransformerBackend", 
    "FakeBackend",
    "EmbeddingWorker",
    "EmbeddingRuntimeError"
]
