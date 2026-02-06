"""
Semantic-Based Philosophical Question Detector

Uses embedding similarity to detect philosophical questions across all languages,
eliminating the need for language-specific keyword patterns.

This approach is scalable and works for any language StillMe supports.
"""

import logging
import numpy as np
from typing import Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# Philosophical question examples (seed examples for semantic matching)
# These are representative philosophical questions in multiple languages
PHILOSOPHICAL_EXAMPLES = [
    # Self-reference and meta-cognition
    "If you were built to learn forever, would there come a day when every question leads back to yourself?",
    "Can a system evaluate itself? Can knowledge justify itself?",
    "What is the value of answers that come from a system that questions itself?",
    "Does thinking about thinking create a paradox?",
    
    # Consciousness and experience
    "Do you have consciousness?",
    "Can AI experience emotions?",
    "What is the difference between understanding and experiencing?",
    
    # Paradoxes and limits
    "What happens when a system tries to understand its own limits?",
    "Can truth be defined within the same language that expresses it?",
    "Is there a fixed point where all questions return to the system itself?",
    
    # Vietnamese examples
    "Nếu bạn được xây dựng để học hỏi mãi mãi, liệu có ngày nào bạn đạt đến điểm mà mọi câu hỏi đều quay về chính bạn?",
    "Bạn có ý thức không?",
    "Hệ thống có thể đánh giá chính nó không?",
    "Giá trị câu trả lời xuất phát từ hệ thống tư duy là gì?",
    
    # Chinese examples
    "如果你被构建为永久学习，是否有一天你会达到所有问题都回归你自身的那一点？",
    "你有意识吗？",
    "系统能否评估自己？",
    "思考思考本身是否会产生悖论？",
    
    # Evolution and learning mechanism
    "Can a learning system evolve infinitely, or does it reach a fixed point?",
    "What happens when there is nothing left to learn except learning about learning?",
    "Does continuous learning lead to self-referential loops?",
]


class SemanticPhilosophicalDetector:
    """
    Semantic-based philosophical question detector using embedding similarity.
    
    This detector works across all languages by comparing semantic similarity
    with philosophical question examples, eliminating the need for language-specific patterns.
    """
    
    def __init__(self, embedding_service=None, similarity_threshold: float = 0.65):
        """
        Initialize semantic philosophical detector.
        
        Args:
            embedding_service: EmbeddingService instance (will be lazy-loaded if None)
            similarity_threshold: Minimum cosine similarity to consider question philosophical (default: 0.65)
        """
        self.embedding_service = embedding_service
        self.similarity_threshold = similarity_threshold
        self._philosophical_embeddings = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of philosophical question embeddings"""
        if self._initialized:
            return
        
        try:
            # Lazy import to avoid circular dependencies
            if self.embedding_service is None:
                from backend.vector_db.embeddings import get_embedding_service
                self.embedding_service = get_embedding_service()
            
            # Embed all philosophical examples
            logger.info(f"Initializing semantic philosophical detector with {len(PHILOSOPHICAL_EXAMPLES)} examples")
            self._philosophical_embeddings = [
                self.embedding_service.encode_text(example)
                for example in PHILOSOPHICAL_EXAMPLES
            ]
            self._initialized = True
            logger.info("✅ Semantic philosophical detector initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize semantic philosophical detector: {e}")
            # Fallback: mark as initialized but use empty embeddings (will fall back to keyword-based)
            self._philosophical_embeddings = []
            self._initialized = True
    
    def detect(self, question: str) -> Tuple[bool, float, Optional[str]]:
        """
        Detect if question is philosophical using semantic similarity.
        
        Args:
            question: User question text (any language)
            
        Returns:
            Tuple of (is_philosophical, max_similarity, matched_example)
            - is_philosophical: True if question is philosophical
            - max_similarity: Maximum similarity score with philosophical examples (0.0-1.0)
            - matched_example: The philosophical example that matched (for debugging)
        """
        if not question or len(question.strip()) < 10:
            return (False, 0.0, None)
        
        try:
            self._initialize()
            
            # If initialization failed, return False (will fall back to keyword-based)
            if not self._philosophical_embeddings:
                return (False, 0.0, None)
            
            # Embed the question
            question_embedding = self.embedding_service.encode_text(question)
            
            # Calculate cosine similarity with all philosophical examples
            max_similarity = 0.0
            matched_example = None
            
            for i, example_embedding in enumerate(self._philosophical_embeddings):
                # Cosine similarity
                similarity = np.dot(question_embedding, example_embedding) / (
                    np.linalg.norm(question_embedding) * np.linalg.norm(example_embedding)
                )
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    matched_example = PHILOSOPHICAL_EXAMPLES[i]
            
            is_philosophical = max_similarity >= self.similarity_threshold
            
            if is_philosophical:
                logger.info(
                    f"✅ Semantic philosophical question detected: similarity={max_similarity:.3f}, "
                    f"threshold={self.similarity_threshold:.3f}, matched='{matched_example[:60]}...'"
                )
            else:
                logger.debug(
                    f"Semantic philosophical question NOT detected: similarity={max_similarity:.3f}, "
                    f"threshold={self.similarity_threshold:.3f}"
                )
            
            return (is_philosophical, max_similarity, matched_example)
            
        except Exception as e:
            logger.error(f"❌ Error in semantic philosophical detection: {e}")
            # Fallback: return False (will use keyword-based detection)
            return (False, 0.0, None)


# Global instance (lazy initialization)
_semantic_detector: Optional[SemanticPhilosophicalDetector] = None


def get_semantic_philosophical_detector(
    embedding_service=None,
    similarity_threshold: float = 0.65
) -> SemanticPhilosophicalDetector:
    """
    Get or create global semantic philosophical detector instance.
    
    Args:
        embedding_service: Optional EmbeddingService instance
        similarity_threshold: Minimum similarity threshold (default: 0.65)
        
    Returns:
        SemanticPhilosophicalDetector instance
    """
    global _semantic_detector
    if _semantic_detector is None:
        _semantic_detector = SemanticPhilosophicalDetector(
            embedding_service=embedding_service,
            similarity_threshold=similarity_threshold
        )
    return _semantic_detector

