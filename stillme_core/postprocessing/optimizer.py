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
        response_length: int,
        validation_result: Optional[Dict] = None,
        rewrite_count: int = 0
    ) -> Tuple[bool, str, int]:
        """
        Determine if rewrite should be performed using cost-benefit policy
        
        Phase 4: Cost-Benefit Logic
        - Uses RewriteDecisionPolicy for intelligent rewrite decisions
        - Respects SELF_CORRECTION_MODE (off/light/aggressive)
        - Tracks rewrite count to prevent excessive rewrites
        - Considers quality score thresholds
        
        Args:
            quality_result: Quality evaluation result
            is_philosophical: Whether question is philosophical
            response_length: Length of response
            validation_result: Optional validation result from validator chain
            rewrite_count: Number of rewrites already performed (default: 0)
            
        Returns:
            Tuple of (should_rewrite, reason, max_attempts)
        """
        from backend.postprocessing.rewrite_decision_policy import get_rewrite_decision_policy
        
        policy = get_rewrite_decision_policy()
        overall_score = quality_result.get("overall_score", 1.0)
        
        # Use policy to make decision
        decision = policy.should_rewrite(
            quality_score=overall_score,
            quality_result=quality_result,
            rewrite_count=rewrite_count,
            validation_result=validation_result
        )
        
        # Log decision
        if decision.should_rewrite:
            logger.info(
                f"🔄 Cost-Benefit: Rewrite decision - {decision.reason}, "
                f"quality_before={decision.quality_before:.2f}, "
                f"rewrite_count={rewrite_count}/{decision.max_attempts}, "
                f"mode={decision.mode}"
            )
        else:
            logger.info(
                f"⏭️ Cost-Benefit: Skip rewrite - {decision.reason}, "
                f"quality_before={decision.quality_before:.2f}, "
                f"rewrite_count={rewrite_count}/{decision.max_attempts}, "
                f"mode={decision.mode}"
            )
        
        return decision.should_rewrite, decision.reason, decision.max_attempts


def get_postprocessing_optimizer() -> PostProcessingOptimizer:
    """Get singleton instance of PostProcessingOptimizer"""
    if not hasattr(get_postprocessing_optimizer, '_instance'):
        get_postprocessing_optimizer._instance = PostProcessingOptimizer()
    return get_postprocessing_optimizer._instance


