"""
Rewrite Decision Policy - Cost-Benefit Logic for RewriteLLM

Manages rewrite decisions based on:
- Quality score thresholds
- Self-correction mode (off/light/aggressive)
- Maximum rewrite attempts per request
- Cost-benefit analysis

This is a rule-based policy that can be upgraded to ML-based in the future.
"""

import logging
import os
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SelfCorrectionMode(str, Enum):
    """Self-correction modes"""
    OFF = "off"  # No rewrites
    LIGHT = "light"  # Conservative: max 1 rewrite for medium quality
    AGGRESSIVE = "aggressive"  # More rewrites: max 2 for medium quality


@dataclass
class RewriteDecision:
    """Decision result for rewrite"""
    should_rewrite: bool
    reason: str
    max_attempts: int  # Maximum rewrite attempts allowed for this request
    quality_before: float
    mode: str


class RewriteDecisionPolicy:
    """
    Cost-benefit policy for rewrite decisions
    
    Rules:
    - quality_score >= 0.8 → NO rewrite (good enough)
    - 0.5 <= quality_score < 0.8:
      - "light": max 1 rewrite
      - "aggressive": max 2 rewrites
    - quality_score < 0.5:
      - max 2 rewrites, but stop if quality still low after rewrite
    """
    
    def __init__(self):
        """Initialize rewrite decision policy"""
        # Read config from environment
        mode_str = os.getenv("SELF_CORRECTION_MODE", "light").lower()
        try:
            self.mode = SelfCorrectionMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid SELF_CORRECTION_MODE '{mode_str}', defaulting to 'light'")
            self.mode = SelfCorrectionMode.LIGHT
        
        # Quality thresholds
        self.high_quality_threshold = 0.8  # >= 0.8: no rewrite
        self.medium_quality_threshold = 0.5  # 0.5-0.8: conditional rewrite
        
        # Max rewrite attempts by mode and quality
        self.max_attempts_light_medium = 1  # Light mode: max 1 for medium quality
        self.max_attempts_aggressive_medium = 2  # Aggressive mode: max 2 for medium quality
        self.max_attempts_low_quality = 2  # Low quality (<0.5): max 2 attempts
        
        logger.info(f"RewriteDecisionPolicy initialized: mode={self.mode.value}")
    
    def should_rewrite(
        self,
        quality_score: float,
        quality_result: Dict,
        rewrite_count: int = 0,
        validation_result: Optional[Dict] = None
    ) -> RewriteDecision:
        """
        Determine if rewrite should be performed based on cost-benefit analysis
        
        Args:
            quality_score: Overall quality score (0.0-1.0)
            quality_result: Full quality evaluation result dict
            rewrite_count: Number of rewrites already performed for this request
            validation_result: Optional validation result (for critical issues)
            
        Returns:
            RewriteDecision with should_rewrite flag, reason, and max_attempts
        """
        # Mode OFF: Never rewrite
        if self.mode == SelfCorrectionMode.OFF:
            return RewriteDecision(
                should_rewrite=False,
                reason="SELF_CORRECTION_MODE=off",
                max_attempts=0,
                quality_before=quality_score,
                mode=self.mode.value
            )
        
        # High quality (>= 0.8): No rewrite needed
        if quality_score >= self.high_quality_threshold:
            return RewriteDecision(
                should_rewrite=False,
                reason=f"quality_score ({quality_score:.2f}) >= {self.high_quality_threshold} (high quality threshold)",
                max_attempts=0,
                quality_before=quality_score,
                mode=self.mode.value
            )
        
        # Check for critical issues that should always trigger rewrite (if not exceeded max attempts)
        has_critical_issues = self._has_critical_issues(quality_result, validation_result)
        
        # Medium quality (0.5 <= score < 0.8): Conditional rewrite
        if self.medium_quality_threshold <= quality_score < self.high_quality_threshold:
            max_attempts = (
                self.max_attempts_aggressive_medium 
                if self.mode == SelfCorrectionMode.AGGRESSIVE 
                else self.max_attempts_light_medium
            )
            
            # Check if we've exceeded max attempts
            if rewrite_count >= max_attempts:
                return RewriteDecision(
                    should_rewrite=False,
                    reason=f"exceeded_max_attempts (rewrite_count={rewrite_count} >= max={max_attempts}) for medium quality",
                    max_attempts=max_attempts,
                    quality_before=quality_score,
                    mode=self.mode.value
                )
            
            # Only rewrite if there are critical issues or mode is aggressive
            if has_critical_issues or self.mode == SelfCorrectionMode.AGGRESSIVE:
                return RewriteDecision(
                    should_rewrite=True,
                    reason=f"medium_quality ({quality_score:.2f}) with {'critical_issues' if has_critical_issues else 'aggressive_mode'}",
                    max_attempts=max_attempts,
                    quality_before=quality_score,
                    mode=self.mode.value
                )
            else:
                return RewriteDecision(
                    should_rewrite=False,
                    reason=f"medium_quality ({quality_score:.2f}) but no critical issues and mode=light",
                    max_attempts=max_attempts,
                    quality_before=quality_score,
                    mode=self.mode.value
                )
        
        # Low quality (< 0.5): Allow rewrite but check if we've exceeded max attempts
        if quality_score < self.medium_quality_threshold:
            max_attempts = self.max_attempts_low_quality
            
            if rewrite_count >= max_attempts:
                return RewriteDecision(
                    should_rewrite=False,
                    reason=f"exceeded_max_attempts (rewrite_count={rewrite_count} >= max={max_attempts}) for low quality",
                    max_attempts=max_attempts,
                    quality_before=quality_score,
                    mode=self.mode.value
                )
            
            return RewriteDecision(
                should_rewrite=True,
                reason=f"low_quality ({quality_score:.2f}) < {self.medium_quality_threshold}",
                max_attempts=max_attempts,
                quality_before=quality_score,
                mode=self.mode.value
            )
        
        # Fallback (should not reach here)
        return RewriteDecision(
            should_rewrite=False,
            reason="unknown_quality_range",
            max_attempts=0,
            quality_before=quality_score,
            mode=self.mode.value
        )
    
    def _has_critical_issues(
        self,
        quality_result: Dict,
        validation_result: Optional[Dict] = None
    ) -> bool:
        """
        Check if there are critical issues that should always trigger rewrite
        
        Critical issues:
        - Anthropomorphic language
        - Missing citation (when context available)
        - Language mismatch
        - Template-like response
        - Topic drift
        
        Args:
            quality_result: Quality evaluation result
            validation_result: Optional validation result
            
        Returns:
            True if critical issues found
        """
        reasons = quality_result.get("reasons", [])
        
        # Check for critical issues in quality_result
        critical_patterns = [
            "anthropomorphic",
            "template-like",
            "topic drift",
            "too short"
        ]
        
        for reason in reasons:
            reason_lower = reason.lower()
            if any(pattern in reason_lower for pattern in critical_patterns):
                return True
        
        # Check for critical issues in validation_result
        if validation_result:
            validation_reasons = validation_result.get("reasons", [])
            critical_validation_patterns = [
                "missing_citation",
                "language_mismatch"
            ]
            
            for reason in validation_reasons:
                if any(pattern in reason.lower() for pattern in critical_validation_patterns):
                    return True
        
        return False
    
    def should_continue_rewrite(
        self,
        quality_before: float,
        quality_after: float,
        rewrite_count: int,
        max_attempts: int
    ) -> Tuple[bool, str]:
        """
        Determine if rewrite should continue after a rewrite attempt
        
        This is called after each rewrite to decide if another rewrite is needed.
        
        Args:
            quality_before: Quality score before rewrite
            quality_after: Quality score after rewrite
            rewrite_count: Current rewrite count (1-indexed, so 1 = first rewrite done)
            max_attempts: Maximum allowed attempts
            
        Returns:
            Tuple of (should_continue, reason)
        """
        # Check if we've exceeded max attempts
        if rewrite_count >= max_attempts:
            return False, f"exceeded_max_attempts (rewrite_count={rewrite_count} >= max={max_attempts})"
        
        # If quality improved significantly (>= 0.2 improvement), continue if still below threshold
        quality_improvement = quality_after - quality_before
        if quality_improvement >= 0.2:
            # Good improvement, but check if still needs more work
            if quality_after < self.high_quality_threshold:
                return True, f"quality_improved ({quality_improvement:.2f}) but still below threshold ({quality_after:.2f} < {self.high_quality_threshold})"
            else:
                return False, f"quality_improved ({quality_improvement:.2f}) and reached threshold ({quality_after:.2f} >= {self.high_quality_threshold})"
        
        # If quality didn't improve much (< 0.1) and still low, stop to avoid wasting tokens
        if quality_improvement < 0.1 and quality_after < self.medium_quality_threshold:
            return False, f"quality_not_improving (improvement={quality_improvement:.2f}, after={quality_after:.2f}) - stopping to avoid waste"
        
        # If quality improved slightly (0.1-0.2), allow one more attempt if still below threshold
        if 0.1 <= quality_improvement < 0.2:
            if quality_after < self.high_quality_threshold and rewrite_count < max_attempts:
                return True, f"quality_improved_slightly ({quality_improvement:.2f}), allowing one more attempt"
            else:
                return False, f"quality_improved_slightly ({quality_improvement:.2f}) but {'reached threshold' if quality_after >= self.high_quality_threshold else 'max attempts reached'}"
        
        # Default: continue if below threshold and haven't exceeded max attempts
        if quality_after < self.high_quality_threshold:
            return True, f"quality_still_below_threshold ({quality_after:.2f} < {self.high_quality_threshold})"
        else:
            return False, f"quality_reached_threshold ({quality_after:.2f} >= {self.high_quality_threshold})"


# Global policy instance
_policy = None


def get_rewrite_decision_policy() -> RewriteDecisionPolicy:
    """Get global rewrite decision policy instance"""
    global _policy
    if _policy is None:
        _policy = RewriteDecisionPolicy()
    return _policy

