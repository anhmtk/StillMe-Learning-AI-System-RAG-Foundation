import time
from datetime import timedelta
from typing import Callable
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from modules.token_optimizer_v1 import (
    QualityMonitor,
    TokenLimitExceededError,
    TokenOptimizer,
    TokenOptimizerConfig,
    TokenRateLimiter,
)


# ============================
# FIXTURES
# ============================
@pytest.fixture
def sample_config() -> TokenOptimizerConfig:
    return TokenOptimizerConfig(
        min_similarity_threshold=0.8,
        max_prompt_tokens=200,
        cache_ttl=timedelta(minutes=10),
        max_cache_size=100,
    )


@pytest.fixture
def mock_embedding() -> np.ndarray:
    return np.random.rand(384)


@pytest.fixture
def optimizer(sample_config: TokenOptimizerConfig) -> TokenOptimizer:
    with patch("sentence_transformers.SentenceTransformer"):
        return TokenOptimizer(sample_config)


# ============================
# TEST CACHE
# ============================
def test_cache_operations(optimizer: TokenOptimizer) -> None:
    test_query = "Xin chào, bạn khỏe không?"
    test_response = "Tôi khỏe, cảm ơn bạn!"

    optimizer.cache.add_item(
        query=test_query,
        response=test_response,
        token_count=10,
        ttl=timedelta(minutes=5),
    )

    cached_item = optimizer.cache.get_exact_match(test_query)
    assert cached_item is not None
    assert cached_item.response == test_response

    similar_query = "Chào bạn, bạn có khỏe không?"
    result = optimizer.cache.get_semantic_match(similar_query, 0.8)
    assert result is not None
    item, similarity = result
    assert item.response == test_response
    assert similarity >= 0.8


def test_cache_expiration(optimizer: TokenOptimizer) -> None:
    test_query = "Câu hỏi tạm thời"
    optimizer.cache.add_item(
        query=test_query,
        response="Trả lời tạm",
        token_count=5,
        ttl=timedelta(milliseconds=10),
    )
    time.sleep(0.05)
    assert optimizer.cache.get_exact_match(test_query) is None
    cleared = optimizer.cache.clear_expired()
    assert cleared >= 1


# ============================
# TEST TOKEN COUNTING
# ============================
def test_token_counting(optimizer: TokenOptimizer) -> None:
    text = "Xin chào thế giới"
    token_count = optimizer._count_tokens(text)
    assert token_count > 0
    assert isinstance(token_count, int)


# ============================
# TEST PROMPT OPTIMIZATION
# ============================
def test_prompt_optimization(optimizer: TokenOptimizer) -> None:
    query = "Giải thích về AI"
    context = [
        "Chúng ta đang nói về công nghệ",
        "AI là trí tuệ nhân tạo",
        "Nó đang phát triển rất nhanh",
    ]
    optimized = optimizer._optimize_prompt(query, context)
    assert "AI là trí tuệ nhân tạo" in optimized
    assert (
        len(optimizer.tokenizer.encode(optimized)) <= optimizer.config.max_prompt_tokens
    )


# ============================
# TEST VIETNAMESE NORMALIZATION
# ============================
def test_vietnamese_normalization(optimizer: TokenOptimizer) -> None:
    normalized = optimizer._normalize_query("Tôi ko biết")
    assert "không" in normalized
    assert "ko" not in normalized


# ============================
# TEST RATE LIMITER
# ============================
def test_rate_limiting() -> None:
    limiter = TokenRateLimiter(max_tokens_per_minute=100)
    limiter.check_limit(50)
    limiter.check_limit(49)
    with pytest.raises(TokenLimitExceededError):
        limiter.check_limit(2)


def test_rate_limiter_reset() -> None:
    limiter = TokenRateLimiter(max_tokens_per_minute=100)
    limiter.check_limit(60)
    time.sleep(1.2)  # Chờ reset
    limiter.last_reset -= 61
    limiter.check_limit(50)
    assert limiter.token_count <= 50


# ============================
# TEST QUALITY MONITOR
# ============================
def test_quality_monitoring() -> None:
    monitor = QualityMonitor()
    monitor.log_quality("Câu hỏi dài", "Trả lời ngắn")
    assert len(monitor.comparisons) == 1
    diff = monitor.comparisons[0]["length_diff"]
    assert isinstance(diff, int)
    assert diff >= 0


# ============================
# FULL PROCESS FLOW
# ============================
def test_full_process_flow(optimizer: TokenOptimizer) -> None:
    mock_api: Callable[[str], str] = MagicMock(return_value="Câu trả lời mẫu")

    response, cached = optimizer.process_request(
        query="Câu hỏi mới", context=[], api_callback=mock_api
    )
    assert not cached
    mock_api.assert_called_once()

    mock_api.reset_mock()
    response2, cached2 = optimizer.process_request(
        query="Câu hỏi mới", context=[], api_callback=mock_api
    )
    assert cached2
    mock_api.assert_not_called()


# ============================
# TEST CONFIG LOADING
# ============================
@patch("modules.token_optimizer_v1.tiktoken.get_encoding")
def test_config_loading(mock_encoding: MagicMock) -> None:
    config = TokenOptimizerConfig(
        language="en",
        max_prompt_tokens=500,
        min_similarity_threshold=0.8,
        max_cache_size=100,
    )
    optimizer = TokenOptimizer(config)
    assert optimizer.config.language == "en"
    assert optimizer.config.max_prompt_tokens == 500


# ============================
# SEMANTIC MATCH ACCURACY
# ============================
def test_semantic_match_accuracy(optimizer: TokenOptimizer) -> None:
    query = "Xin chào"
    response = "Chào bạn"
    optimizer.cache.add_item(query, response, token_count=5, ttl=timedelta(minutes=1))
    result = optimizer.cache.get_semantic_match("Xin chào", 0.5)
    assert result is not None
    item, similarity = result
    assert item.response == response
    assert similarity >= 0.5
