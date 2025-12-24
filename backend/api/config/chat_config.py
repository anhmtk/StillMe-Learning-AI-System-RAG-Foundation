"""Chat router configuration constants.

This module centralizes all configuration values used in chat_router.py
to improve maintainability and enable easy tuning.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SimilarityThresholds:
    """Similarity score thresholds for RAG retrieval."""
    DEFAULT: float = 0.4
    VALIDATOR_COUNT_QUESTION: float = 0.01
    FOUNDATIONAL_KNOWLEDGE: float = 0.3
    LOW_CONTEXT_QUALITY: float = 0.1
    HIGH_CONTEXT_QUALITY: float = 0.5
    VERY_LOW: float = 0.05


@dataclass
class TokenLimits:
    """Token limits for various text truncation operations."""
    MAX_USER_MESSAGE: int = 3000
    MAX_CONVERSATION_HISTORY: int = 1000
    MAX_PHILOSOPHY_QUESTION: int = 512
    MAX_CONTEXT_TEXT: int = 8000  # Approximate, for context truncation


@dataclass
class Timeouts:
    """Timeout values for async operations."""
    SOURCE_CONSENSUS: float = 3.0
    RAG_RETRIEVAL: float = 10.0
    LLM_CALL: float = 60.0


@dataclass
class ConfidenceThresholds:
    """Confidence score thresholds."""
    LOW: float = 0.3
    MEDIUM: float = 0.5
    HIGH: float = 0.7
    VERY_HIGH: float = 0.9
    DEFAULT_NO_CONTEXT: float = 0.3
    PHILOSOPHICAL_DEFAULT: float = 0.8
    PHILOSOPHICAL_FAILED_VALIDATION: float = 0.7


@dataclass
class RewriteConfig:
    """Post-processing rewrite configuration."""
    MAX_ATTEMPTS: int = 3
    MIN_QUALITY_FOR_REWRITE: float = 0.6
    QUALITY_IMPROVEMENT_THRESHOLD: float = 0.1  # Minimum improvement to keep rewrite


@dataclass
class CacheConfig:
    """Cache TTL and key configuration."""
    RAG_CACHE_TTL: int = 3600  # 1 hour
    LLM_RESPONSE_CACHE_TTL: int = 3600  # 1 hour
    KNOWLEDGE_VERSION_KEY: str = "knowledge_version"


@dataclass
class ValidationConfig:
    """Validation chain configuration."""
    ADAPTIVE_CITATION_OVERLAP_DEFAULT: float = 0.1
    ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT: float = 0.01
    MIN_SOURCES_FOR_CONSENSUS: int = 2
    CIRCUIT_BREAKER_THRESHOLD: int = 2
    CIRCUIT_BREAKER_DURATION: int = 3600  # 1 hour
    EVIDENCE_THRESHOLD_ENV_DEFAULT: str = "0.01"


@dataclass
class FPSConfig:
    """Factual Plausibility Scanner configuration."""
    BLOCK_THRESHOLD: float = 0.3
    EXPLICIT_FAKE_ENTITIES: List[str] = None  # Will be initialized in __post_init__


@dataclass
class ValidatorInfo:
    """Validator information defaults."""
    DEFAULT_VI: str = "19 validators total, chia thành 7 lớp (layers)"
    DEFAULT_EN: str = "19 validators total, organized into 7 layers"
    DEFAULT_LAYERS: str = "7 layers"


@dataclass
class ChatConfig:
    """Main configuration class aggregating all config sections."""
    
    similarity: SimilarityThresholds = None
    tokens: TokenLimits = None
    timeouts: Timeouts = None
    confidence: ConfidenceThresholds = None
    rewrite: RewriteConfig = None
    cache: CacheConfig = None
    validation: ValidationConfig = None
    fps: FPSConfig = None
    validator_info: ValidatorInfo = None
    
    def __post_init__(self):
        """Initialize nested config objects."""
        if self.similarity is None:
            self.similarity = SimilarityThresholds()
        if self.tokens is None:
            self.tokens = TokenLimits()
        if self.timeouts is None:
            self.timeouts = Timeouts()
        if self.confidence is None:
            self.confidence = ConfidenceThresholds()
        if self.rewrite is None:
            self.rewrite = RewriteConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.validation is None:
            self.validation = ValidationConfig()
        if self.fps is None:
            self.fps = FPSConfig()
            self.fps.EXPLICIT_FAKE_ENTITIES = [
                "veridian", "lumeria", "emerald", "daxonia"
            ]
        if self.validator_info is None:
            self.validator_info = ValidatorInfo()


# Global config instance (singleton pattern)
_config_instance: ChatConfig = None


def get_chat_config() -> ChatConfig:
    """Get global chat configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ChatConfig()
    return _config_instance

