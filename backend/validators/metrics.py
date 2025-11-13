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
    
    def get_metrics(self, days: int = None) -> Dict[str, Any]:
        """
        Get current metrics
        
        Args:
            days: Optional number of days to filter logs (e.g., 3 for last 3 days)
        
        Returns:
            Dictionary with metrics
        """
        # Filter logs by time if days specified
        filtered_logs = self.recent_logs
        if days is not None:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            filtered_logs = [
                log for log in self.recent_logs
                if datetime.fromisoformat(log["timestamp"]) >= cutoff_time
            ]
        
        # Calculate metrics from filtered logs
        if days is not None and filtered_logs:
            # Recalculate from filtered logs
            filtered_total = len(filtered_logs)
            filtered_passed = sum(1 for log in filtered_logs if log.get("passed", False))
            filtered_failed = filtered_total - filtered_passed
            
            # Extract overlap and confidence scores from filtered logs
            filtered_overlaps = [log.get("overlap_score", 0.0) for log in filtered_logs if log.get("overlap_score", 0.0) > 0]
            filtered_confidences = [log.get("confidence_score") for log in filtered_logs if log.get("confidence_score") is not None]
            
            # Count reasons from filtered logs
            filtered_reasons_histogram = defaultdict(int)
            filtered_fallback_count = 0
            filtered_hallucination_prevented = 0
            filtered_uncertainty_count = 0
            
            for log in filtered_logs:
                reasons = log.get("reasons", [])
                for reason in reasons:
                    filtered_reasons_histogram[reason] += 1
                    if reason == "missing_uncertainty_no_context":
                        filtered_hallucination_prevented += 1
                    if "uncertainty" in reason.lower() or "don't know" in reason.lower():
                        filtered_uncertainty_count += 1
                if log.get("used_fallback", False):
                    filtered_fallback_count += 1
                    filtered_hallucination_prevented += 1
            
            pass_rate = filtered_passed / filtered_total if filtered_total > 0 else 0.0
            avg_overlap = sum(filtered_overlaps) / len(filtered_overlaps) if filtered_overlaps else 0.0
            avg_confidence = sum(filtered_confidences) / len(filtered_confidences) if filtered_confidences else 0.0
            hallucination_reduction_rate = filtered_hallucination_prevented / filtered_total if filtered_total > 0 else 0.0
            
            return {
                "total_validations": filtered_total,
                "pass_rate": pass_rate,
                "passed_count": filtered_passed,
                "failed_count": filtered_failed,
                "avg_overlap_score": avg_overlap,
                "avg_confidence_score": avg_confidence,
                "fallback_usage_count": filtered_fallback_count,
                "fallback_usage_rate": filtered_fallback_count / filtered_total if filtered_total > 0 else 0.0,
                "hallucination_prevented_count": filtered_hallucination_prevented,
                "hallucination_reduction_rate": hallucination_reduction_rate,
                "uncertainty_expressed_count": filtered_uncertainty_count,
                "uncertainty_expression_rate": filtered_uncertainty_count / filtered_total if filtered_total > 0 else 0.0,
                "reasons_histogram": dict(filtered_reasons_histogram),
                "recent_logs": filtered_logs[-10:],  # Last 10 logs from filtered set
                "filter_days": days
            }
        
        # Default: return all-time metrics
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

