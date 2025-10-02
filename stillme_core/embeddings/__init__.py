"""
Embeddings Module for StillMe Core
==================================

Provides embedding backends with Windows-safe fallback mechanisms.
"""

from .adapter import EmbeddingBackend, FakeBackend, SentenceTransformerBackend
from .worker import EmbeddingRuntimeError, EmbeddingWorker

__all__ = [
    "EmbeddingBackend",
    "SentenceTransformerBackend",
    "FakeBackend",
    "EmbeddingWorker",
    "EmbeddingRuntimeError",
]
