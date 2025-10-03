"""
Test Token Optimizer Integration (Windows-safe)
==============================================

Integration tests for TokenOptimizer with Windows subprocess fallback.
"""

from unittest.mock import Mock, patch

import pytest

from stillme_core.embeddings import EmbeddingRuntimeError
from stillme_core.modules.token_optimizer_v1 import TokenOptimizer, TokenOptimizerConfig


class TestTokenOptimizerIntegration:
    """Test TokenOptimizer integration with Windows safety"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return TokenOptimizerConfig(
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            max_cache_size=100,
            semantic_threshold=0.8,
            token_limit=1000,
        )

    def test_worker_success(self, config):
        """Test successful worker execution"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock successful worker
            mock_instance = Mock()
            mock_instance.embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Test that optimizer works
            assert optimizer is not None
            assert optimizer.cache is not None

            # Test embedding generation
            embeddings = optimizer.cache._get_embedding("test text")
            assert len(embeddings) > 0

    def test_worker_failure_fallback(self, config):
        """Test worker failure with fallback to fake backend"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock worker failure
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError("Worker failed")
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should not crash
            assert optimizer is not None

            # Should still work with fallback
            embeddings = optimizer.cache._get_embedding("test text")
            assert len(embeddings) > 0

    def test_worker_timeout_handling(self, config):
        """Test worker timeout handling"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock timeout
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError("Worker timeout")
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should not crash
            assert optimizer is not None

            # Should degrade gracefully
            embeddings = optimizer.cache._get_embedding("test text")
            assert len(embeddings) > 0

    def test_worker_json_error_handling(self, config):
        """Test worker JSON parsing error handling"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock JSON error
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError(
                "Invalid JSON output"
            )
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should not crash
            assert optimizer is not None

            # Should use fallback
            embeddings = optimizer.cache._get_embedding("test text")
            assert len(embeddings) > 0

    def test_worker_subprocess_error(self, config):
        """Test subprocess execution error handling"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock subprocess error
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError("Subprocess failed")
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should not crash
            assert optimizer is not None

            # Should use fallback
            embeddings = optimizer.cache._get_embedding("test text")
            assert len(embeddings) > 0

    def test_optimizer_degraded_mode(self, config):
        """Test optimizer in degraded mode"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock degraded mode
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError(
                "All backends failed"
            )
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should still function
            assert optimizer is not None

            # Test cache operations still work
            optimizer.cache.add_item("test query", "test response", 10)
            match = optimizer.cache.get_exact_match("test query")
            assert match is not None

    def test_optimizer_consistency_under_failure(self, config):
        """Test optimizer consistency under various failure modes"""
        failure_modes = [
            EmbeddingRuntimeError("Worker failed"),
            EmbeddingRuntimeError("Timeout"),
            EmbeddingRuntimeError("JSON error"),
            EmbeddingRuntimeError("Subprocess error"),
            Exception("Unexpected error"),
        ]

        for failure in failure_modes:
            with patch(
                "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
            ) as mock_backend:
                mock_instance = Mock()
                mock_instance.embed.side_effect = failure
                mock_backend.return_value = mock_instance

                optimizer = TokenOptimizer(config)

                # Should not crash
                assert optimizer is not None

                # Should produce consistent results
                embeddings1 = optimizer.cache._get_embedding("test text")
                embeddings2 = optimizer.cache._get_embedding("test text")

                assert len(embeddings1) == len(embeddings2)
                assert all(
                    abs(a - b) < 1e-10
                    for a, b in zip(embeddings1, embeddings2, strict=False)
                )

    def test_optimizer_deterministic_fallback(self, config):
        """Test that fallback produces deterministic results"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock consistent failure
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError(
                "Consistent failure"
            )
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Multiple calls should produce same results
            text = "deterministic test text"
            emb1 = optimizer.cache._get_embedding(text)
            emb2 = optimizer.cache._get_embedding(text)
            emb3 = optimizer.cache._get_embedding(text)

            assert all(abs(a - b) < 1e-10 for a, b in zip(emb1, emb2, strict=False))
            assert all(abs(a - b) < 1e-10 for a, b in zip(emb2, emb3, strict=False))

    def test_optimizer_performance_under_failure(self, config):
        """Test optimizer performance under failure conditions"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock slow failure
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError("Slow failure")
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should still be reasonably fast
            import time

            start_time = time.time()

            for i in range(10):
                optimizer.cache._get_embedding(f"test text {i}")

            end_time = time.time()
            duration = end_time - start_time

            # Should complete within reasonable time (1 second for 10 embeddings)
            assert duration < 1.0

    def test_optimizer_memory_usage_under_failure(self, config):
        """Test optimizer memory usage under failure conditions"""
        with patch(
            "stillme_core.modules.token_optimizer_v1.SentenceTransformerBackend"
        ) as mock_backend:
            # Mock memory-intensive failure
            mock_instance = Mock()
            mock_instance.embed.side_effect = EmbeddingRuntimeError("Memory failure")
            mock_backend.return_value = mock_instance

            optimizer = TokenOptimizer(config)

            # Should not leak memory
            initial_cache_size = len(optimizer.cache.cache)

            # Add many items
            for i in range(1000):
                optimizer.cache.add_item(f"query {i}", f"response {i}", 10)

            # Cache should respect size limit
            assert len(optimizer.cache.cache) <= config.max_cache_size

            # Should not grow indefinitely
            assert (
                len(optimizer.cache.cache) <= initial_cache_size + config.max_cache_size
            )
