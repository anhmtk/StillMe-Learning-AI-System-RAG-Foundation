"""
Post-processing Optimizer - Smart skip logic to reduce cost and latency

Optimizes post-processing pipeline by:
- Skipping post-processing for simple/factual questions
- Caching quality evaluation results
- Adaptive quality thresholds
- Pre-filtering to avoid unnecessary rewrites
"""

import logging
import hashlib
from typing import Dict, Optional, Tuple
from backend.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class PostProcessingOptimizer:
    """
    Optimizes post-processing pipeline to reduce cost and latency
    while maintaining quality
    """
    
    def __init__(self):
        """Initialize optimizer"""
        self.cache_service = get_cache_service()
        self.cache_prefix = "postproc_quality"
        
        # Simple question patterns (skip post-processing)
        self.simple_patterns = [
            r'^(what is|what are|what does|what do|what\'s)',
            r'^(là gì|gì là|định nghĩa)',
            r'^(how to|how do|how does|how can)',
            r'^(làm thế nào|cách làm|hướng dẫn)',
            r'^(yes|no|có|không)\s*\?',
            r'^(true|false|đúng|sai)\s*\?',
        ]
        
        # Short question threshold (skip if too short)
        self.min_question_length = 20  # Skip if question < 20 chars
        
        # Response length thresholds
        self.min_response_length_simple = 50   # Simple questions
        self.min_response_length_complex = 200  # Complex questions
    
    def should_skip_postprocessing(
        self,
        question: str,
        response: str,
        is_philosophical: bool
    ) -> Tuple[bool, str]:
        """
        Determine if post-processing should be skipped
        
        Args:
            question: User question
            response: LLM response
            is_philosophical: Whether question is philosophical
            
        Returns:
            Tuple of (should_skip, reason)
        """
        # Never skip philosophical questions - they need quality enforcement
        if is_philosophical:
            return False, "philosophical_question"
        
        # Skip if question is too short (likely simple)
        if len(question.strip()) < self.min_question_length:
            return True, "question_too_short"
        
        # Skip if response is too short (likely simple factual answer)
        if len(response.strip()) < self.min_response_length_simple:
            return True, "response_too_short"
        
        # Skip if question matches simple patterns
        import re
        question_lower = question.lower().strip()
        for pattern in self.simple_patterns:
            if re.match(pattern, question_lower):
                return True, "simple_question_pattern"
        
        # Don't skip - needs post-processing
        return False, "needs_processing"
    
    def get_cached_quality_result(
        self,
        question: str,
        response: str
    ) -> Optional[Dict]:
        """
        Get cached quality evaluation result
        
        Args:
            question: User question
            response: Sanitized response
            
        Returns:
            Cached quality result or None
        """
        try:
            # Generate cache key from question + response hash
            response_hash = hashlib.md5(response.encode()).hexdigest()[:16]
            cache_key = f"{self.cache_prefix}:{hashlib.md5(question.encode()).hexdigest()[:16]}:{response_hash}"
            
            cached = self.cache_service.get(cache_key)
            if cached:
                logger.debug(f"✅ Quality evaluation cache HIT")
                return cached.get("result")
        except Exception as e:
            logger.warning(f"Cache lookup error: {e}")
        
        return None
    
    def cache_quality_result(
        self,
        question: str,
        response: str,
        quality_result: Dict,
        ttl_seconds: int = 3600  # 1 hour
    ):
        """
        Cache quality evaluation result
        
        Args:
            question: User question
            response: Sanitized response
            quality_result: Quality evaluation result
            ttl_seconds: Time to live in seconds
        """
        try:
            response_hash = hashlib.md5(response.encode()).hexdigest()[:16]
            cache_key = f"{self.cache_prefix}:{hashlib.md5(question.encode()).hexdigest()[:16]}:{response_hash}"
            
            self.cache_service.set(
                cache_key,
                {"result": quality_result},
                ttl_seconds=ttl_seconds
            )
            logger.debug(f"💾 Quality evaluation result cached")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def should_rewrite(
        self,
        quality_result: Dict,
        is_philosophical: bool,
        response_length: int
    ) -> Tuple[bool, str]:
        """
        Determine if rewrite is really needed (pre-filter to avoid unnecessary rewrites)
        
        🚨🚨🚨 CRITICAL RULE D: BẬT LẠI REWRITE MỨC CAO NHẤT 🚨🚨🚨
        - For philosophical questions: ALWAYS rewrite if quality is not "good"
        - Accept trade-off: latency/cost increase, but quality increases significantly
        - If rewrite uses many tokens → let it run, do NOT disable
        
        Args:
            quality_result: Quality evaluation result
            is_philosophical: Whether question is philosophical
            response_length: Length of response
            
        Returns:
            Tuple of (should_rewrite, reason)
        """
        quality = quality_result.get("quality", "good")
        overall_score = quality_result.get("overall_score", 1.0)
        reasons = quality_result.get("reasons", [])
        
        # If quality is good, don't rewrite
        if quality == "good":
            return False, "quality_good"
        
        # CRITICAL: Critical issues always require rewrite
        critical_issues = [
            "Contains anthropomorphic language",
            "Output too short",
            "Topic drift detected",  # CRITICAL: Drift always requires rewrite
        ]
        has_critical = any(issue in reasons for issue in critical_issues)
        
        # 🚨🚨🚨 CRITICAL RULE D: For philosophical questions, ALWAYS rewrite if quality is not "good" 🚨🚨🚨
        # Accept trade-off: latency/cost increase, but quality increases significantly
        if is_philosophical:
            # ALWAYS rewrite philosophical questions if quality is not "good"
            # This ensures 3-tier analysis (Reframing, Conceptual Map, Boundary) is enforced
            logger.info(
                f"🔄 Philosophical question requires rewrite: quality={quality}, "
                f"score={overall_score:.2f}, reasons={reasons[:2]}"
            )
            return True, "philosophical_question_requires_rewrite"
        
        # For non-philosophical questions: only rewrite if score < 0.3 or has critical issues
        if not is_philosophical:
            if overall_score >= 0.3 and not has_critical:
                logger.info(
                    f"⏭️ Skipping rewrite: score={overall_score:.2f} >= 0.3 (threshold), "
                    f"length={response_length}, critical_issues={has_critical}"
                )
                return False, f"score_acceptable_non_philosophical_{overall_score:.2f}"
        
        # Rewrite needed
        return True, "quality_insufficient"


def get_postprocessing_optimizer() -> PostProcessingOptimizer:
    """Get singleton instance of PostProcessingOptimizer"""
    if not hasattr(get_postprocessing_optimizer, '_instance'):
        get_postprocessing_optimizer._instance = PostProcessingOptimizer()
    return get_postprocessing_optimizer._instance


