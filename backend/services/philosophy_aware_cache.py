"""
Philosophy-Aware Cache for StillMe

Smart caching that respects philosophical uniqueness while optimizing costs.
"""

import logging
import hashlib
import json
import time
from typing import Optional, Dict, Any, Tuple
from backend.services.cache_service import get_cache_service, CACHE_PREFIX_LLM, TTL_LLM_RESPONSE
from backend.core.question_classifier import is_philosophical_question

logger = logging.getLogger(__name__)


class PhilosophyAwareCache:
    """
    Cache system that respects philosophical uniqueness
    
    Strategy:
    - CACHE STRONGLY: Simple factual questions
    - CACHE SELECTIVELY: Philosophical questions with common themes
    - NEVER CACHE: Highly unique philosophical inquiries
    """
    
    def __init__(self):
        """Initialize philosophy-aware cache"""
        self.cache_service = get_cache_service()
        
        # Philosophical themes for selective caching
        self.philosophical_themes = {
            "cartesian_doubt": ["descartes", "cogito", "doubt", "nghi ngờ", "hoài nghi"],
            "existential_absurd": ["camus", "absurd", "meaningless", "vô nghĩa", "hiện sinh"],
            "kantian_phenomena": ["phenomena", "noumena", "kant", "hiện tượng", "vật tự thân"],
            "utilitarianism": ["utilitarian", "bentham", "mill", "hạnh phúc", "lợi ích"],
            "stoicism": ["stoic", "epictetus", "marcus aurelius", "khắc kỷ"],
            "buddhist_emptiness": ["emptiness", "śūnyatā", "anatta", "vô ngã", "không tính"],
            "daoist_wu_wei": ["wu wei", "dao", "tao", "vô vi", "đạo"],
        }
    
    def _extract_philosophical_theme(self, question: str, response: str) -> Optional[str]:
        """
        Extract philosophical theme from question/response
        
        Args:
            question: User question
            response: LLM response
            
        Returns:
            Theme name or None if unique
        """
        question_lower = question.lower()
        response_lower = response.lower()
        
        combined_text = question_lower + " " + response_lower
        
        # Check for theme matches
        for theme_name, keywords in self.philosophical_themes.items():
            # Need at least 2 keywords to match a theme
            matches = sum(1 for keyword in keywords if keyword in combined_text)
            if matches >= 2:
                logger.debug(f"🎯 Detected philosophical theme: {theme_name} (matches: {matches})")
                return theme_name
        
        return None
    
    def _is_simple_factual(self, question: str) -> bool:
        """Detect simple factual questions (safe to cache strongly)"""
        if not question:
            return False
        
        question_lower = question.lower()
        
        # Simple factual patterns
        simple_patterns = [
            r'what is the capital of',
            r'who wrote',
            r'when was',
            r'how many',
            r'what is 2\+2',
            r'capital of',
            r'thủ đô',
            r'ai viết',
            r'khi nào',
            r'bao nhiêu',
            r'what is the population of',
            r'what year',
            r'năm nào'
        ]
        
        import re
        return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in simple_patterns)
    
    def _is_general_philosophy(self, question: str) -> bool:
        """Detect general philosophical questions (can cache with theme)"""
        if not question:
            return False
        
        # Check if philosophical but not highly unique
        is_philo = is_philosophical_question(question)
        
        if not is_philo:
            return False
        
        # Check for unique indicators (don't cache these)
        unique_indicators = [
            "my", "your", "personal", "của tôi", "của bạn",
            "specific", "cụ thể", "particular", "riêng"
        ]
        
        question_lower = question.lower()
        has_unique = any(indicator in question_lower for indicator in unique_indicators)
        
        return not has_unique
    
    def should_cache(self, question: str, response: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if response should be cached
        
        Args:
            question: User question
            response: LLM response
            
        Returns:
            Tuple of (should_cache, cache_key_type)
            cache_key_type: "factual", "theme", or None
        """
        # 🎯 CACHE STRONGLY: Simple factual questions
        if self._is_simple_factual(question):
            return (True, "factual")
        
        # 🎯 CACHE SELECTIVELY: General philosophical questions with themes
        if self._is_general_philosophy(question):
            theme = self._extract_philosophical_theme(question, response)
            if theme:
                return (True, f"theme:{theme}")
        
        # 🚫 NEVER CACHE: Highly unique philosophical inquiries
        return (False, None)
    
    def get_cache_key(self, question: str, cache_key_type: str, context_hash: Optional[str] = None) -> str:
        """
        Generate cache key based on type
        
        Args:
            question: User question
            cache_key_type: Type of cache key ("factual", "theme:xxx", etc.)
            context_hash: Optional context hash for RAG queries
            
        Returns:
            Cache key string
        """
        # Normalize question for cache key
        question_normalized = question.lower().strip()
        
        if cache_key_type == "factual":
            # For factual, use question hash (exact match)
            question_hash = hashlib.md5(question_normalized.encode()).hexdigest()[:16]
            return f"{CACHE_PREFIX_LLM}:factual:{question_hash}"
        
        elif cache_key_type.startswith("theme:"):
            # For themes, use theme name + question hash
            theme = cache_key_type.split(":")[1]
            question_hash = hashlib.md5(question_normalized.encode()).hexdigest()[:16]
            return f"{CACHE_PREFIX_LLM}:theme:{theme}:{question_hash}"
        
        else:
            # Default: use question hash
            question_hash = hashlib.md5(question_normalized.encode()).hexdigest()[:16]
            return f"{CACHE_PREFIX_LLM}:default:{question_hash}"
    
    def get_cached_response(self, question: str, context_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available
        
        Args:
            question: User question
            context_hash: Optional context hash for RAG queries
            
        Returns:
            Cached response dict or None
        """
        # Check if should cache (to determine key type)
        # We need a dummy response to check theme, but for retrieval we'll try all types
        
        # Try factual cache first
        if self._is_simple_factual(question):
            cache_key = self.get_cache_key(question, "factual", context_hash)
            cached = self.cache_service.get(cache_key)
            if cached:
                logger.info(f"✅ Cache HIT (factual): {question[:50]}...")
                return cached
        
        # Try theme-based cache
        if self._is_general_philosophy(question):
            # Try each theme
            for theme_name in self.philosophical_themes.keys():
                cache_key = self.get_cache_key(question, f"theme:{theme_name}", context_hash)
                cached = self.cache_service.get(cache_key)
                if cached:
                    logger.info(f"✅ Cache HIT (theme:{theme_name}): {question[:50]}...")
                    return cached
        
        return None
    
    def cache_response(
        self,
        question: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        context_hash: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache response if appropriate
        
        Args:
            question: User question
            response: LLM response
            metadata: Optional metadata (latency, tokens, etc.)
            context_hash: Optional context hash for RAG queries
            ttl: Time to live in seconds
            
        Returns:
            True if cached, False otherwise
        """
        should_cache, cache_key_type = self.should_cache(question, response)
        
        if not should_cache:
            logger.debug(f"🚫 Not caching (unique philosophical): {question[:50]}...")
            return False
        
        # Generate cache key
        cache_key = self.get_cache_key(question, cache_key_type, context_hash)
        
        # Prepare cache value
        cache_value = {
            "response": response,
            "question": question,
            "cache_type": cache_key_type,
            "cached_at": time.time(),
            "metadata": metadata or {}
        }
        
        # Set TTL based on type
        if ttl is None:
            if cache_key_type == "factual":
                ttl = TTL_LLM_RESPONSE * 2  # 2 hours for factual
            else:
                ttl = TTL_LLM_RESPONSE  # 1 hour for themes
        
        # Cache it
        success = self.cache_service.set(cache_key, cache_value, ttl)
        
        if success:
            logger.info(f"💾 Cached ({cache_key_type}): {question[:50]}... (TTL: {ttl}s)")
        
        return success


# Global cache instance
_philosophy_cache: Optional[PhilosophyAwareCache] = None


def get_philosophy_aware_cache() -> PhilosophyAwareCache:
    """Get global philosophy-aware cache instance (singleton)"""
    global _philosophy_cache
    if _philosophy_cache is None:
        _philosophy_cache = PhilosophyAwareCache()
    return _philosophy_cache

