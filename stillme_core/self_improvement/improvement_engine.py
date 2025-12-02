"""
Improvement Engine - Automated improvement loop

This module provides an automated improvement engine that:
1. Monitors metrics continuously
2. Detects patterns and issues
3. Suggests improvements
4. Can optionally apply improvements automatically (with safeguards)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .analyzer import get_self_improvement_analyzer
from stillme_core.monitoring import get_metrics_collector, MetricCategory

logger = logging.getLogger(__name__)


class ImprovementEngine:
    """
    Automated improvement engine that monitors metrics and suggests/apply improvements
    """
    
    def __init__(self, auto_apply: bool = False):
        """
        Initialize improvement engine
        
        Args:
            auto_apply: Whether to automatically apply improvements (default: False for safety)
        """
        self.analyzer = get_self_improvement_analyzer()
        self.metrics = get_metrics_collector()
        self.auto_apply = auto_apply
        logger.info(f"ImprovementEngine initialized (auto_apply={auto_apply})")
    
    def run_improvement_cycle(self, days: int = 7) -> Dict[str, Any]:
        """
        Run a single improvement cycle
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with improvement results
        """
        logger.info(f"Running improvement cycle (analyzing last {days} days)...")
        
        # Get analysis from analyzer
        analysis = self.analyzer.analyze_and_suggest(days=days)
        
        # Get knowledge gaps
        knowledge_gaps = self.analyzer.get_knowledge_gaps_from_failures(days=days)
        
        # Record improvement cycle in metrics
        self.metrics.record(
            MetricCategory.SYSTEM,
            "improvement_cycle",
            {
                "patterns_detected": analysis.get("patterns_detected", 0),
                "knowledge_gaps": len(knowledge_gaps),
                "suggestions": len(analysis.get("learning_suggestions", [])),
                "recommendations": len(analysis.get("improvement_recommendations", []))
            }
        )
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_days": days,
            "patterns": analysis.get("patterns", []),
            "failure_rates": analysis.get("failure_rates_by_category", {}),
            "learning_suggestions": analysis.get("learning_suggestions", []),
            "improvement_recommendations": analysis.get("improvement_recommendations", []),
            "knowledge_gaps": knowledge_gaps,
            "auto_apply": self.auto_apply
        }
        
        # If auto_apply is enabled, apply improvements (with safeguards)
        if self.auto_apply:
            applied = self._apply_improvements(result)
            result["applied_improvements"] = applied
        
        logger.info(f"Improvement cycle completed: {len(result.get('learning_suggestions', []))} suggestions, {len(result.get('improvement_recommendations', []))} recommendations")
        
        return result
    
    def _apply_improvements(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Apply improvements automatically (with safeguards)
        
        This is a placeholder for future implementation.
        For now, it only logs what would be applied.
        
        Args:
            result: Improvement result dictionary
            
        Returns:
            List of applied improvements
        """
        applied = []
        
        # TODO: Implement safe auto-application of improvements
        # For now, just log what would be applied
        for suggestion in result.get("learning_suggestions", []):
            logger.info(f"Would apply learning suggestion: {suggestion.get('topic')} from {suggestion.get('source')}")
            applied.append({
                "type": "learning_suggestion",
                "topic": suggestion.get("topic"),
                "status": "logged_only"  # Not actually applied yet
            })
        
        return applied


# Global instance
_improvement_engine: Optional[ImprovementEngine] = None


def get_improvement_engine(auto_apply: bool = False) -> ImprovementEngine:
    """Get global improvement engine instance"""
    global _improvement_engine
    if _improvement_engine is None or _improvement_engine.auto_apply != auto_apply:
        _improvement_engine = ImprovementEngine(auto_apply=auto_apply)
    return _improvement_engine

