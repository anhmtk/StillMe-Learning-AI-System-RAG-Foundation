"""Tests for chat configuration."""

import pytest
from backend.api.config.chat_config import (
    get_chat_config,
    ChatConfig,
    SimilarityThresholds,
    TokenLimits,
    Timeouts,
    ConfidenceThresholds,
    RewriteConfig,
    CacheConfig,
    ValidationConfig,
    FPSConfig
)


def test_get_chat_config_returns_singleton():
    """Test that get_chat_config returns the same instance."""
    config1 = get_chat_config()
    config2 = get_chat_config()
    assert config1 is config2


def test_config_has_all_sections():
    """Test that config has all required sections."""
    config = get_chat_config()
    assert config.similarity is not None
    assert config.tokens is not None
    assert config.timeouts is not None
    assert config.confidence is not None
    assert config.rewrite is not None
    assert config.cache is not None
    assert config.validation is not None
    assert config.fps is not None


def test_similarity_thresholds():
    """Test similarity threshold values."""
    config = get_chat_config()
    assert config.similarity.DEFAULT == 0.4
    assert config.similarity.VALIDATOR_COUNT_QUESTION == 0.01
    assert config.similarity.FOUNDATIONAL_KNOWLEDGE == 0.3
    assert config.similarity.LOW_CONTEXT_QUALITY == 0.1
    assert config.similarity.HIGH_CONTEXT_QUALITY == 0.5
    assert config.similarity.VERY_LOW == 0.05


def test_token_limits():
    """Test token limit values."""
    config = get_chat_config()
    assert config.tokens.MAX_USER_MESSAGE == 3000
    assert config.tokens.MAX_CONVERSATION_HISTORY == 1000
    assert config.tokens.MAX_PHILOSOPHY_QUESTION == 512
    assert config.tokens.MAX_CONTEXT_TEXT == 8000


def test_timeouts():
    """Test timeout values."""
    config = get_chat_config()
    assert config.timeouts.SOURCE_CONSENSUS == 3.0
    assert config.timeouts.RAG_RETRIEVAL == 10.0
    assert config.timeouts.LLM_CALL == 60.0


def test_confidence_thresholds():
    """Test confidence threshold values."""
    config = get_chat_config()
    assert config.confidence.LOW == 0.3
    assert config.confidence.MEDIUM == 0.5
    assert config.confidence.HIGH == 0.7
    assert config.confidence.VERY_HIGH == 0.9
    assert config.confidence.DEFAULT_NO_CONTEXT == 0.3
    assert config.confidence.PHILOSOPHICAL_DEFAULT == 0.8
    assert config.confidence.PHILOSOPHICAL_FAILED_VALIDATION == 0.7


def test_rewrite_config():
    """Test rewrite configuration values."""
    config = get_chat_config()
    assert config.rewrite.MAX_ATTEMPTS == 3
    assert config.rewrite.MIN_QUALITY_FOR_REWRITE == 0.6
    assert config.rewrite.QUALITY_IMPROVEMENT_THRESHOLD == 0.1


def test_cache_config():
    """Test cache configuration values."""
    config = get_chat_config()
    assert config.cache.RAG_CACHE_TTL == 3600
    assert config.cache.LLM_RESPONSE_CACHE_TTL == 3600
    assert config.cache.KNOWLEDGE_VERSION_KEY == "knowledge_version"


def test_validation_config():
    """Test validation configuration values."""
    config = get_chat_config()
    assert config.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT == 0.1
    assert config.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT == 0.01
    assert config.validation.MIN_SOURCES_FOR_CONSENSUS == 2
    assert config.validation.CIRCUIT_BREAKER_THRESHOLD == 2
    assert config.validation.CIRCUIT_BREAKER_DURATION == 3600
    assert config.validation.EVIDENCE_THRESHOLD_ENV_DEFAULT == "0.01"


def test_fps_explicit_fake_entities():
    """Test FPS explicit fake entities list."""
    config = get_chat_config()
    assert "veridian" in config.fps.EXPLICIT_FAKE_ENTITIES
    assert "lumeria" in config.fps.EXPLICIT_FAKE_ENTITIES
    assert "emerald" in config.fps.EXPLICIT_FAKE_ENTITIES
    assert "daxonia" in config.fps.EXPLICIT_FAKE_ENTITIES
    assert len(config.fps.EXPLICIT_FAKE_ENTITIES) == 4


def test_fps_block_threshold():
    """Test FPS block threshold."""
    config = get_chat_config()
    assert config.fps.BLOCK_THRESHOLD == 0.3


def test_config_initialization():
    """Test that config initializes nested objects correctly."""
    config = ChatConfig()
    assert isinstance(config.similarity, SimilarityThresholds)
    assert isinstance(config.tokens, TokenLimits)
    assert isinstance(config.timeouts, Timeouts)
    assert isinstance(config.confidence, ConfidenceThresholds)
    assert isinstance(config.rewrite, RewriteConfig)
    assert isinstance(config.cache, CacheConfig)
    assert isinstance(config.validation, ValidationConfig)
    assert isinstance(config.fps, FPSConfig)


def test_config_values_are_positive():
    """Test that all numeric config values are positive."""
    config = get_chat_config()
    
    # Similarity thresholds should be between 0 and 1
    assert 0 < config.similarity.DEFAULT <= 1
    assert 0 < config.similarity.VALIDATOR_COUNT_QUESTION <= 1
    assert 0 < config.similarity.FOUNDATIONAL_KNOWLEDGE <= 1
    
    # Token limits should be positive
    assert config.tokens.MAX_USER_MESSAGE > 0
    assert config.tokens.MAX_CONVERSATION_HISTORY > 0
    assert config.tokens.MAX_PHILOSOPHY_QUESTION > 0
    
    # Timeouts should be positive
    assert config.timeouts.SOURCE_CONSENSUS > 0
    assert config.timeouts.RAG_RETRIEVAL > 0
    assert config.timeouts.LLM_CALL > 0
    
    # Confidence thresholds should be between 0 and 1
    assert 0 <= config.confidence.LOW <= 1
    assert 0 <= config.confidence.MEDIUM <= 1
    assert 0 <= config.confidence.HIGH <= 1
    
    # Rewrite config
    assert config.rewrite.MAX_ATTEMPTS > 0
    assert 0 <= config.rewrite.MIN_QUALITY_FOR_REWRITE <= 1
    
    # Cache TTLs should be positive
    assert config.cache.RAG_CACHE_TTL > 0
    assert config.cache.LLM_RESPONSE_CACHE_TTL > 0
    
    # Validation config
    assert 0 <= config.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT <= 1
    assert 0 <= config.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT <= 1
    assert config.validation.MIN_SOURCES_FOR_CONSENSUS > 0
    
    # FPS config
    assert 0 <= config.fps.BLOCK_THRESHOLD <= 1

