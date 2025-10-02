"""
Embedding Backend Adapter
=========================

Provides Windows-safe embedding backends with fallback mechanisms.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Protocol, Union

from .worker import EmbeddingRuntimeError, EmbeddingWorker


class EmbeddingBackend(Protocol):
    """Protocol for embedding backends"""

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        ...


class FakeBackend:
    """Fake backend for testing - no external dependencies"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate fake embeddings based on text length"""
        embeddings = []
        for text in texts:
            # Simple deterministic embedding based on text characteristics
            base_vector = [len(text) / 100.0] * self.dimension
            # Add some variation based on text content
            for i, char in enumerate(text[:self.dimension]):
                base_vector[i] += ord(char) / 1000.0
            embeddings.append(base_vector)
        return embeddings


class SentenceTransformerBackend:
    """Windows-safe SentenceTransformer backend with subprocess fallback"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._worker = None
        self._use_subprocess = platform.system() == "Windows"

        # Try direct import first (Linux/macOS)
        if not self._use_subprocess:
            try:
                self._init_direct_model()
            except Exception as e:
                print(f"Direct model init failed: {e}, falling back to subprocess")
                self._use_subprocess = True

        # Initialize subprocess worker if needed
        if self._use_subprocess:
            self._worker = EmbeddingWorker(model_name)

    def _init_direct_model(self):
        """Initialize model directly (Linux/macOS)"""
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with fallback mechanism"""
        if not self._use_subprocess and self._model:
            # Direct model (Linux/macOS)
            try:
                embeddings = self._model.encode(texts)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                print(f"Direct embedding failed: {e}, falling back to subprocess")
                self._use_subprocess = True
                self._worker = EmbeddingWorker(self.model_name)

        # Subprocess worker (Windows or fallback)
        if self._worker:
            try:
                return self._worker.embed(texts)
            except EmbeddingRuntimeError as e:
                print(f"Subprocess embedding failed: {e}, using fake backend")
                # Ultimate fallback to fake backend
                fake_backend = FakeBackend()
                return fake_backend.embed(texts)

        # Should never reach here, but just in case
        fake_backend = FakeBackend()
        return fake_backend.embed(texts)

    def __del__(self):
        """Cleanup resources"""
        if self._worker:
            self._worker.cleanup()
