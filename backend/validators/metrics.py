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
        self.recent_logs: List[Dict[str, Any]] = []
        self.max_logs = 100
        
    def record_validation(
        self,
        passed: bool,
        reasons: List[str],
        overlap_score: float = 0.0
    ) -> None:
        """
        Record a validation result
        
        Args:
            passed: Whether validation passed
            reasons: List of reasons
            overlap_score: Evidence overlap score (if available)
        """
        self.total_validations += 1
        
        if passed:
            self.passed_count += 1
        else:
            self.failed_count += 1
        
        # Record reasons
        for reason in reasons:
            self.reasons_histogram[reason] += 1
        
        # Record overlap score
        if overlap_score > 0:
            self.overlap_scores.append(overlap_score)
        
        # Log recent validation
        self.recent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "reasons": reasons,
            "overlap_score": overlap_score
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
        
        return {
            "total_validations": self.total_validations,
            "pass_rate": pass_rate,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "avg_overlap_score": avg_overlap,
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
        self.recent_logs.clear()


# Global metrics instance
_metrics = ValidationMetrics()


def get_metrics() -> ValidationMetrics:
    """Get global metrics instance"""
    return _metrics

