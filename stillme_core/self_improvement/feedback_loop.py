"""
Feedback Loop - Connects validation → learning

This module provides a feedback loop that:
1. Monitors validation failures
2. Identifies knowledge gaps
3. Suggests learning content
4. Can trigger learning cycles with specific content
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .analyzer import get_self_improvement_analyzer
from stillme_core.monitoring import get_metrics_collector, MetricCategory

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """
    Feedback loop that connects validation metrics to learning system
    """
    
    def __init__(self):
        """Initialize feedback loop"""
        self.analyzer = get_self_improvement_analyzer()
        self.metrics = get_metrics_collector()
        logger.info("FeedbackLoop initialized")
    
    def get_learning_suggestions_from_failures(
        self,
        days: int = 7,
        min_failure_rate: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Get learning suggestions based on validation failures
        
        Args:
            days: Number of days to analyze
            min_failure_rate: Minimum failure rate to trigger suggestion (0.0-1.0)
            
        Returns:
            List of learning suggestions with topics and sources
        """
        # Get knowledge gaps from failures
        knowledge_gaps = self.analyzer.get_knowledge_gaps_from_failures(days=days)
        
        # Get failure rates by category
        failure_rates = self.analyzer.tracker.get_failure_rate_by_category(days=days)
        
        suggestions = []
        
        # Add suggestions from knowledge gaps
        for gap in knowledge_gaps:
            suggestions.append({
                "type": "knowledge_gap",
                "topics": gap.get("topics", []),
                "suggested_sources": gap.get("suggested_sources", []),
                "priority": gap.get("priority", "medium"),
                "reason": f"Knowledge gap detected: {gap.get('question', '')[:100]}"
            })
        
        # Add suggestions from high failure rates
        for category, rate in failure_rates.items():
            if rate >= min_failure_rate:
                suggestions.append({
                    "type": "high_failure_rate",
                    "category": category,
                    "failure_rate": rate,
                    "topics": [f"Knowledge about {category} topics"],
                    "suggested_sources": ["Wikipedia", "arXiv", "Domain-specific sources"],
                    "priority": "high" if rate > 0.3 else "medium",
                    "reason": f"High failure rate ({rate:.1%}) for {category} questions"
                })
        
        # Record feedback loop activity
        self.metrics.record(
            MetricCategory.SYSTEM,
            "feedback_loop_suggestions",
            {
                "suggestions_count": len(suggestions),
                "knowledge_gaps": len(knowledge_gaps),
                "high_failure_categories": len([c for c, r in failure_rates.items() if r >= min_failure_rate])
            }
        )
        
        logger.info(f"Feedback loop generated {len(suggestions)} learning suggestions")
        
        return suggestions
    
    def should_trigger_learning_cycle(self, days: int = 7) -> bool:
        """
        Determine if a learning cycle should be triggered based on validation failures
        
        Args:
            days: Number of days to analyze
            
        Returns:
            True if learning cycle should be triggered
        """
        # Get recent validation metrics
        metrics = self.metrics.get_metrics(
            category=MetricCategory.VALIDATION,
            days=days
        )
        
        # Check if failure rate is high
        counters = metrics.get("counters", {}).get("validation", {})
        total = counters.get("total_validations", 0)
        failed = counters.get("failed_count", 0)
        
        if total == 0:
            return False
        
        failure_rate = failed / total
        
        # Trigger if failure rate > 20%
        should_trigger = failure_rate > 0.2
        
        logger.debug(f"Feedback loop check: failure_rate={failure_rate:.1%}, should_trigger={should_trigger}")
        
        return should_trigger


# Global instance
_feedback_loop: Optional[FeedbackLoop] = None


def get_feedback_loop() -> FeedbackLoop:
    """Get global feedback loop instance"""
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = FeedbackLoop()
    return _feedback_loop

