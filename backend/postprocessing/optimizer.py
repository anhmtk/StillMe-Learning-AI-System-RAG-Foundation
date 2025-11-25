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
        validation_result: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Determine if rewrite is really needed (Phase 3: Only rewrite critical issues)
        
        Phase 3 Optimization: "Less is More"
        - Chỉ rewrite khi có CRITICAL issues:
          1. Missing citation (critical) - khi có context nhưng không có citation
          2. Anthropomorphic language (critical) - "in my experience", "tôi cảm thấy"
          3. Language mismatch (critical) - trả lời sai ngôn ngữ
        - KHÔNG rewrite cho:
          - Minor formatting issues (thiếu emoji, markdown format)
          - Style preferences (paragraph structure khác nhau)
          - Natural variation (cùng câu hỏi nhưng cách diễn đạt khác)
          - Depth, unpacking (optional - không phải critical)
        
        Args:
            quality_result: Quality evaluation result
            is_philosophical: Whether question is philosophical
            response_length: Length of response
            validation_result: Optional validation result from validator chain
            
        Returns:
            Tuple of (should_rewrite, reason)
        """
        quality = quality_result.get("quality", "good")
        overall_score = quality_result.get("overall_score", 1.0)
        reasons = quality_result.get("reasons", [])
        
        # Phase 3: Check for CRITICAL issues only
        critical_issues = []
        
        # 1. Check for anthropomorphic language (CRITICAL)
        has_anthropomorphic = any(
            "anthropomorphic" in r.lower() or 
            "contains anthropomorphic" in r.lower() or
            "claims experience" in r.lower() or
            "claims feelings" in r.lower()
            for r in reasons
        )
        if has_anthropomorphic:
            critical_issues.append("anthropomorphic_language")
        
        # 2. Check for missing citation (CRITICAL) - from validation_result if available
        if validation_result:
            validation_reasons = validation_result.get("reasons", [])
            has_missing_citation = any("missing_citation" in r for r in validation_reasons)
            if has_missing_citation:
                critical_issues.append("missing_citation")
        
        # 3. Check for language mismatch (CRITICAL) - from validation_result if available
        if validation_result:
            validation_reasons = validation_result.get("reasons", [])
            has_language_mismatch = any("language_mismatch" in r for r in validation_reasons)
            if has_language_mismatch:
                critical_issues.append("language_mismatch")
        
        # 4. Check for topic drift (CRITICAL - StillMe talking about consciousness/LLM when not asked)
        has_topic_drift = any("topic drift" in r.lower() for r in reasons)
        if has_topic_drift:
            critical_issues.append("topic_drift")
        
        # 5. Check for template-like response (CRITICAL - too mechanical)
        has_template_like = any("template-like" in r.lower() for r in reasons)
        if has_template_like:
            critical_issues.append("template_like")
        
        # Phase 3: Only rewrite if there are CRITICAL issues
        if critical_issues:
            logger.info(
                f"🔄 Phase 3: Rewriting due to CRITICAL issues: {critical_issues}, "
                f"quality={quality}, score={overall_score:.2f}, "
                f"philosophical={is_philosophical}, length={response_length}"
            )
            return True, f"critical_issues: {', '.join(critical_issues)}"
        
        # No critical issues - skip rewrite (allow natural variation)
        logger.info(
            f"⏭️ Phase 3: Skipping rewrite - no critical issues, "
            f"quality={quality}, score={overall_score:.2f}, "
            f"philosophical={is_philosophical}, length={response_length}, "
            f"non_critical_reasons={reasons[:2] if reasons else 'none'}"
        )
        return False, "no_critical_issues"


def get_postprocessing_optimizer() -> PostProcessingOptimizer:
    """Get singleton instance of PostProcessingOptimizer"""
    if not hasattr(get_postprocessing_optimizer, '_instance'):
        get_postprocessing_optimizer._instance = PostProcessingOptimizer()
    return get_postprocessing_optimizer._instance


