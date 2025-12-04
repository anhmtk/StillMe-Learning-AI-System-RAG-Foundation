"""
Time Estimation Engine

Estimates task completion time based on StillMe's historical performance data.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from statistics import median, mean
from stillme_core.monitoring import get_metrics_collector, MetricCategory
from stillme_core.monitoring.task_tracker import get_task_tracker, TaskRecord

logger = logging.getLogger(__name__)


@dataclass
class TimeEstimate:
    """Time estimate with confidence interval"""
    estimated_minutes: float
    confidence: float  # 0.0-1.0
    range_min: float
    range_max: float
    based_on_n_tasks: int
    explanation: str  # Human-readable explanation


class TimeEstimationEngine:
    """
    Estimates task completion time based on historical performance.
    
    Uses:
    - Historical task records
    - Similarity matching
    - Complexity adjustment
    - Confidence intervals
    """
    
    def __init__(self):
        self.metrics = get_metrics_collector()
        self.task_tracker = get_task_tracker()
        
        # Complexity multipliers (conservative bias)
        self.complexity_multipliers = {
            "simple": 0.7,
            "moderate": 1.0,
            "complex": 1.5,
            "very_complex": 2.5
        }
    
    def estimate(
        self,
        task_description: str,
        task_type: str,
        complexity: str,
        size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TimeEstimate:
        """
        Estimate task completion time.
        
        Args:
            task_description: Description of the task
            task_type: Type of task ("coding", "review", "migration", etc.)
            complexity: Task complexity ("simple", "moderate", "complex", "very_complex")
            size: Task size (lines of code, files changed, etc.)
            metadata: Additional metadata
            
        Returns:
            TimeEstimate with estimate, confidence, and range
        """
        # Find similar historical tasks
        similar_tasks = self._find_similar_tasks(task_type, complexity, size)
        
        # Calculate base estimate
        if similar_tasks:
            base_estimate = self._calculate_base_estimate(similar_tasks)
            confidence = self._calculate_confidence(similar_tasks)
            n_tasks = len(similar_tasks)
            explanation = f"Based on {n_tasks} similar tasks"
        else:
            # No historical data - use complexity-based estimate
            base_estimate = self._estimate_from_complexity(complexity, size)
            confidence = 0.3  # Low confidence for novel tasks
            n_tasks = 0
            explanation = "No similar historical tasks found, using complexity-based estimate"
        
        # Adjust for complexity (apply multiplier)
        adjusted_estimate = base_estimate * self.complexity_multipliers.get(complexity, 1.0)
        
        # Add conservative bias (slightly overestimate)
        conservative_estimate = adjusted_estimate * 1.2  # 20% buffer
        
        # Calculate confidence interval (range)
        if similar_tasks:
            # Use historical variance
            actual_times = [t.actual_time_minutes for t in similar_tasks]
            std_dev = self._calculate_std_dev(actual_times)
            range_min = max(0.1, conservative_estimate - std_dev)
            range_max = conservative_estimate + std_dev * 1.5
        else:
            # Use percentage-based range for novel tasks
            range_min = conservative_estimate * 0.5
            range_max = conservative_estimate * 2.0
        
        return TimeEstimate(
            estimated_minutes=conservative_estimate,
            confidence=confidence,
            range_min=range_min,
            range_max=range_max,
            based_on_n_tasks=n_tasks,
            explanation=explanation
        )
    
    def _find_similar_tasks(
        self,
        task_type: str,
        complexity: str,
        size: int
    ) -> List[TaskRecord]:
        """Find similar historical tasks"""
        # Get historical tasks
        historical = self.task_tracker.get_historical_tasks(
            task_type=task_type,
            days=90  # Last 90 days
        )
        
        # Filter by complexity
        similar = [t for t in historical if t.complexity == complexity]
        
        # Filter by size (within 50% range)
        if similar:
            size_range = (size * 0.5, size * 1.5)
            similar = [
                t for t in similar
                if size_range[0] <= t.size <= size_range[1]
            ]
        
        # If no similar complexity, use same task_type
        if not similar:
            similar = [t for t in historical if t.task_type == task_type]
        
        return similar
    
    def _calculate_base_estimate(self, similar_tasks: List[TaskRecord]) -> float:
        """Calculate base estimate from similar tasks"""
        if not similar_tasks:
            return 30.0  # Default 30 minutes
        
        # Use median (more robust to outliers)
        actual_times = [t.actual_time_minutes for t in similar_tasks]
        return median(actual_times)
    
    def _estimate_from_complexity(self, complexity: str, size: int) -> float:
        """Estimate from complexity when no historical data"""
        # Base estimates per complexity (in minutes)
        base_estimates = {
            "simple": 10,
            "moderate": 30,
            "complex": 90,
            "very_complex": 240
        }
        
        base = base_estimates.get(complexity, 30)
        
        # Adjust for size (rough estimate: 1 minute per 10 lines of code)
        size_adjustment = size / 10
        
        return base + size_adjustment
    
    def _calculate_confidence(self, similar_tasks: List[TaskRecord]) -> float:
        """Calculate confidence based on number of similar tasks"""
        n = len(similar_tasks)
        
        if n >= 10:
            return 0.9
        elif n >= 5:
            return 0.7
        elif n >= 2:
            return 0.5
        elif n == 1:
            return 0.3
        else:
            return 0.1
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return values[0] * 0.3 if values else 10.0
        
        mean_val = mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def format_estimate(self, estimate: TimeEstimate, language: str = "en") -> str:
        """
        Format estimate for user communication.
        
        Args:
            estimate: TimeEstimate object
            language: Language code ("en" or "vi")
        
        Returns:
            Human-readable estimate string in specified language
        """
        if language == "vi":
            # Vietnamese formatting
            if estimate.confidence >= 0.7:
                confidence_text = "độ tin cậy cao"
            elif estimate.confidence >= 0.5:
                confidence_text = "độ tin cậy trung bình"
            else:
                confidence_text = "độ tin cậy thấp"
            
            # Translate explanation
            explanation_vi = estimate.explanation
            if "No similar historical tasks found" in explanation_vi:
                explanation_vi = "Không tìm thấy tác vụ lịch sử tương tự, sử dụng ước tính dựa trên độ phức tạp"
            elif "Based on" in explanation_vi and "similar tasks" in explanation_vi:
                # Extract number if present
                import re
                match = re.search(r'Based on (\d+) similar tasks', explanation_vi)
                if match:
                    n = match.group(1)
                    explanation_vi = f"Dựa trên {n} tác vụ tương tự"
                else:
                    explanation_vi = "Dựa trên các tác vụ lịch sử tương tự"
            
            return (
                f"Dựa trên hiệu suất lịch sử của mình, mình ước tính điều này sẽ mất "
                f"{estimate.range_min:.0f}-{estimate.range_max:.0f} phút "
                f"({confidence_text}, {estimate.confidence:.0%}). "
                f"{explanation_vi}."
            )
        else:
            # English formatting (default)
            if estimate.confidence >= 0.7:
                confidence_text = "high confidence"
            elif estimate.confidence >= 0.5:
                confidence_text = "moderate confidence"
            else:
                confidence_text = "low confidence"
            
            return (
                f"Based on my historical performance, I estimate this will take "
                f"{estimate.range_min:.0f}-{estimate.range_max:.0f} minutes "
                f"({confidence_text}, {estimate.confidence:.0%}). "
                f"{estimate.explanation}."
            )


# Global instance
_estimation_engine: Optional[TimeEstimationEngine] = None


def get_estimation_engine() -> TimeEstimationEngine:
    """Get global time estimation engine instance"""
    global _estimation_engine
    if _estimation_engine is None:
        _estimation_engine = TimeEstimationEngine()
    return _estimation_engine

