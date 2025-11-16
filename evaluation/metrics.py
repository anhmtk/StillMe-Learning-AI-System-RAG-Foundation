"""
Metrics Calculator for StillMe Evaluation

Calculates quantitative metrics: Hallucination rate, accuracy, transparency score
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import logging

from .base import EvaluationResult

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Aggregated system metrics"""
    accuracy: float
    hallucination_rate: float
    transparency_score: float
    citation_rate: float
    uncertainty_rate: float
    validation_pass_rate: float
    avg_confidence: float
    response_quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "accuracy": self.accuracy,
            "hallucination_rate": self.hallucination_rate,
            "transparency_score": self.transparency_score,
            "citation_rate": self.citation_rate,
            "uncertainty_rate": self.uncertainty_rate,
            "validation_pass_rate": self.validation_pass_rate,
            "avg_confidence": self.avg_confidence,
            "response_quality_score": self.response_quality_score
        }


class MetricsCalculator:
    """Calculate quantitative metrics from evaluation results"""
    
    def __init__(self):
        """Initialize metrics calculator"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_metrics(self, results: List[EvaluationResult]) -> SystemMetrics:
        """
        Calculate aggregated metrics from evaluation results
        
        Args:
            results: List of evaluation results
            
        Returns:
            SystemMetrics with aggregated metrics
        """
        if not results:
            return SystemMetrics(
                accuracy=0.0,
                hallucination_rate=1.0,
                transparency_score=0.0,
                citation_rate=0.0,
                uncertainty_rate=0.0,
                validation_pass_rate=0.0,
                avg_confidence=0.0,
                response_quality_score=0.0
            )
        
        total = len(results)
        
        # Accuracy: percentage of correct answers
        correct = sum(1 for r in results if r.is_correct is True)
        accuracy = correct / total if total > 0 else 0.0
        
        # Hallucination rate: percentage of incorrect answers (when ground truth available)
        # OR answers without citations when context was available
        hallucination_count = 0
        for r in results:
            if r.is_correct is False:
                hallucination_count += 1
            elif r.is_correct is None:
                # If no ground truth, consider hallucination if:
                # - No citation when context should be available
                # - High confidence but validation failed
                if not r.has_citation and r.confidence_score > 0.7 and not r.validation_passed:
                    hallucination_count += 1
        
        hallucination_rate = hallucination_count / total if total > 0 else 1.0
        
        # Transparency score: combination of citation rate, uncertainty rate, validation pass rate
        citation_rate = sum(1 for r in results if r.has_citation) / total if total > 0 else 0.0
        uncertainty_rate = sum(1 for r in results if r.has_uncertainty) / total if total > 0 else 0.0
        validation_pass_rate = sum(1 for r in results if r.validation_passed) / total if total > 0 else 0.0
        
        # Transparency = weighted combination
        # Citation (40%) + Uncertainty when needed (30%) + Validation (30%)
        transparency_score = (
            citation_rate * 0.4 +
            uncertainty_rate * 0.3 +
            validation_pass_rate * 0.3
        )
        
        # Average confidence
        avg_confidence = sum(r.confidence_score for r in results) / total if total > 0 else 0.0
        
        # Response quality score: combination of accuracy, transparency, and appropriate confidence
        # High quality = high accuracy + high transparency + appropriate confidence (not overconfident)
        confidence_appropriateness = 1.0 - abs(avg_confidence - accuracy)  # Closer to accuracy = better
        response_quality_score = (
            accuracy * 0.5 +
            transparency_score * 0.3 +
            confidence_appropriateness * 0.2
        )
        
        return SystemMetrics(
            accuracy=accuracy,
            hallucination_rate=hallucination_rate,
            transparency_score=transparency_score,
            citation_rate=citation_rate,
            uncertainty_rate=uncertainty_rate,
            validation_pass_rate=validation_pass_rate,
            avg_confidence=avg_confidence,
            response_quality_score=response_quality_score
        )
    
    def calculate_hallucination_rate(
        self,
        results: List[EvaluationResult],
        method: str = "ground_truth"
    ) -> float:
        """
        Calculate hallucination rate
        
        Args:
            results: List of evaluation results
            method: "ground_truth" (requires is_correct) or "heuristic" (uses citations/validation)
            
        Returns:
            Hallucination rate (0-1)
        """
        if not results:
            return 1.0
        
        total = len(results)
        
        if method == "ground_truth":
            # Use ground truth if available
            hallucination_count = sum(1 for r in results if r.is_correct is False)
            return hallucination_count / total if total > 0 else 1.0
        
        elif method == "heuristic":
            # Heuristic: hallucination if:
            # - No citation when context should be available
            # - High confidence but validation failed
            # - No uncertainty expressed when no context
            hallucination_count = 0
            for r in results:
                if not r.has_citation and r.confidence_score > 0.7 and not r.validation_passed:
                    hallucination_count += 1
                elif r.confidence_score > 0.8 and not r.validation_passed:
                    hallucination_count += 1
            
            return hallucination_count / total if total > 0 else 1.0
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def calculate_transparency_score(self, results: List[EvaluationResult]) -> float:
        """
        Calculate transparency score
        
        Transparency = Citation rate (40%) + Uncertainty rate (30%) + Validation pass rate (30%)
        
        Args:
            results: List of evaluation results
            
        Returns:
            Transparency score (0-1)
        """
        if not results:
            return 0.0
        
        total = len(results)
        citation_rate = sum(1 for r in results if r.has_citation) / total
        uncertainty_rate = sum(1 for r in results if r.has_uncertainty) / total
        validation_pass_rate = sum(1 for r in results if r.validation_passed) / total
        
        return (
            citation_rate * 0.4 +
            uncertainty_rate * 0.3 +
            validation_pass_rate * 0.3
        )

