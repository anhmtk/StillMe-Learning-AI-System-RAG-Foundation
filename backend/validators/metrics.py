"""
Validation metrics collector
"""

from typing import Dict, List, Any
from collections import defaultdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationMetrics:
    """Collects validation metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.total_validations = 0
        self.passed_count = 0
        self.failed_count = 0
        self.reasons_histogram: Dict[str, int] = defaultdict(int)
        self.overlap_scores: List[float] = []
        self.confidence_scores: List[float] = []  # NEW: Track confidence scores
        self.fallback_usage_count = 0  # NEW: Track fallback usage
        self.hallucination_prevented_count = 0  # NEW: Track prevented hallucinations
        self.uncertainty_expressed_count = 0  # NEW: Track when AI expressed uncertainty
        self.recent_logs: List[Dict[str, Any]] = []
        self.max_logs = 100
        
    def record_validation(
        self,
        passed: bool,
        reasons: List[str],
        overlap_score: float = 0.0,
        confidence_score: float = None,
        used_fallback: bool = False
    ) -> None:
        """
        Record a validation result
        
        Args:
            passed: Whether validation passed
            reasons: List of reasons
            overlap_score: Evidence overlap score (if available)
            confidence_score: AI confidence score (if available)
            used_fallback: Whether fallback answer was used
        """
        self.total_validations += 1
        
        if passed:
            self.passed_count += 1
        else:
            self.failed_count += 1
        
        # Record reasons
        for reason in reasons:
            self.reasons_histogram[reason] += 1
            # Track specific metrics
            if reason == "missing_uncertainty_no_context":
                self.hallucination_prevented_count += 1
            if "uncertainty" in reason.lower() or "don't know" in reason.lower():
                self.uncertainty_expressed_count += 1
        
        # Record overlap score
        if overlap_score > 0:
            self.overlap_scores.append(overlap_score)
        
        # Record confidence score
        if confidence_score is not None:
            self.confidence_scores.append(confidence_score)
        
        # Track fallback usage
        if used_fallback:
            self.fallback_usage_count += 1
            self.hallucination_prevented_count += 1  # Fallback prevents hallucination
        
        # Log recent validation
        self.recent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "reasons": reasons,
            "overlap_score": overlap_score,
            "confidence_score": confidence_score,
            "used_fallback": used_fallback
        })
        
        # Keep only recent logs
        if len(self.recent_logs) > self.max_logs:
            self.recent_logs = self.recent_logs[-self.max_logs:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics
        
        Returns:
            Dictionary with metrics
        """
        pass_rate = (
            self.passed_count / self.total_validations
            if self.total_validations > 0
            else 0.0
        )
        
        avg_overlap = (
            sum(self.overlap_scores) / len(self.overlap_scores)
            if self.overlap_scores
            else 0.0
        )
        
        avg_confidence = (
            sum(self.confidence_scores) / len(self.confidence_scores)
            if self.confidence_scores
            else 0.0
        )
        
        # Calculate hallucination reduction rate
        hallucination_reduction_rate = (
            self.hallucination_prevented_count / self.total_validations
            if self.total_validations > 0
            else 0.0
        )
        
        return {
            "total_validations": self.total_validations,
            "pass_rate": pass_rate,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "avg_overlap_score": avg_overlap,
            "avg_confidence_score": avg_confidence,
            "fallback_usage_count": self.fallback_usage_count,
            "fallback_usage_rate": (
                self.fallback_usage_count / self.total_validations
                if self.total_validations > 0
                else 0.0
            ),
            "hallucination_prevented_count": self.hallucination_prevented_count,
            "hallucination_reduction_rate": hallucination_reduction_rate,
            "uncertainty_expressed_count": self.uncertainty_expressed_count,
            "uncertainty_expression_rate": (
                self.uncertainty_expressed_count / self.total_validations
                if self.total_validations > 0
                else 0.0
            ),
            "reasons_histogram": dict(self.reasons_histogram),
            "recent_logs": self.recent_logs[-10:]  # Last 10 logs
        }
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.total_validations = 0
        self.passed_count = 0
        self.failed_count = 0
        self.reasons_histogram.clear()
        self.overlap_scores.clear()
        self.confidence_scores.clear()
        self.fallback_usage_count = 0
        self.hallucination_prevented_count = 0
        self.uncertainty_expressed_count = 0
        self.recent_logs.clear()


# Global metrics instance
_metrics = ValidationMetrics()


def get_metrics() -> ValidationMetrics:
    """Get global metrics instance"""
    return _metrics

