"""
AutoTuner for Meta-Learning (Stage 2, Phase 3)

Automatically tunes similarity thresholds and keywords based on strategy effectiveness.
This enables continuous optimization of RAG retrieval strategies.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from backend.learning.strategy_tracker import get_strategy_tracker

logger = logging.getLogger(__name__)


class AutoTuner:
    """
    Automatically tunes parameters based on strategy effectiveness.
    
    Tunes:
    - Similarity thresholds (0.05, 0.1, 0.15, 0.2, etc.)
    - Keyword combinations
    - Source selection strategies
    """
    
    def __init__(self):
        self.strategy_tracker = get_strategy_tracker()
        logger.info("AutoTuner initialized")
    
    def optimize_similarity_threshold(
        self,
        days: int = 30,
        candidate_thresholds: Optional[List[float]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Find optimal similarity threshold based on strategy effectiveness
        
        Args:
            days: Number of days to analyze
            candidate_thresholds: List of thresholds to test (default: [0.05, 0.1, 0.15, 0.2, 0.25])
        
        Returns:
            Tuple of (optimal_threshold, analysis_results)
        """
        if candidate_thresholds is None:
            candidate_thresholds = [0.05, 0.1, 0.15, 0.2, 0.25]
        
        logger.info(f"🔧 Optimizing similarity threshold from candidates: {candidate_thresholds}")
        
        # Get effectiveness for each threshold
        effectiveness_dict = self.strategy_tracker.calculate_strategy_effectiveness(days=days)
        
        # Filter to similarity threshold strategies
        threshold_effectiveness = {}
        for strategy_name, effectiveness in effectiveness_dict.items():
            if "similarity_threshold" in strategy_name:
                # Extract threshold from strategy name
                try:
                    threshold_str = strategy_name.split("_")[-1]
                    threshold = float(threshold_str)
                    threshold_effectiveness[threshold] = effectiveness
                except (ValueError, IndexError):
                    continue
        
        if not threshold_effectiveness:
            logger.warning("No similarity threshold strategies found, using default 0.1")
            return 0.1, {
                "optimal_threshold": 0.1,
                "reason": "No strategy data available, using default",
                "candidates_tested": candidate_thresholds
            }
        
        # Score each candidate threshold
        # Score = weighted combination of validation_pass_rate, retention_rate, avg_confidence
        scored_thresholds = []
        for threshold in candidate_thresholds:
            if threshold in threshold_effectiveness:
                effectiveness = threshold_effectiveness[threshold]
                # Weighted score: 50% pass_rate, 30% retention, 20% confidence
                score = (
                    effectiveness.validation_pass_rate * 0.5 +
                    effectiveness.retention_rate * 0.3 +
                    effectiveness.avg_confidence * 0.2
                )
                scored_thresholds.append((threshold, score, effectiveness))
            else:
                # Threshold not tested yet - assign default score
                scored_thresholds.append((threshold, 0.5, None))
        
        # Sort by score (descending)
        scored_thresholds.sort(key=lambda x: x[1], reverse=True)
        
        optimal_threshold = scored_thresholds[0][0]
        optimal_effectiveness = scored_thresholds[0][2]
        
        logger.info(f"✅ Optimal similarity threshold: {optimal_threshold:.2f} (score: {scored_thresholds[0][1]:.2f})")
        
        return optimal_threshold, {
            "optimal_threshold": optimal_threshold,
            "optimal_score": scored_thresholds[0][1],
            "candidates_tested": candidate_thresholds,
            "effectiveness": {
                threshold: {
                    "pass_rate": eff.validation_pass_rate if eff else None,
                    "retention_rate": eff.retention_rate if eff else None,
                    "avg_confidence": eff.avg_confidence if eff else None,
                    "score": score
                }
                for threshold, score, eff in scored_thresholds
            },
            "recommendation": f"Use threshold {optimal_threshold:.2f} for best performance"
        }
    
    def optimize_keywords(
        self,
        days: int = 30,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Optimize keyword combinations based on strategy effectiveness
        
        Args:
            days: Number of days to analyze
            domain: Optional domain to focus on (e.g., "ai", "ethics")
        
        Returns:
            List of optimized keyword combinations with effectiveness scores
        """
        logger.info(f"🔧 Optimizing keywords for domain: {domain or 'all'}")
        
        # Get effectiveness for keyword strategies
        effectiveness_dict = self.strategy_tracker.calculate_strategy_effectiveness(days=days)
        
        # Filter to keyword strategies
        keyword_strategies = {}
        for strategy_name, effectiveness in effectiveness_dict.items():
            if "keyword" in strategy_name.lower():
                keyword_strategies[strategy_name] = effectiveness
        
        if not keyword_strategies:
            logger.warning("No keyword strategies found")
            return []
        
        # Sort by effectiveness
        sorted_keywords = sorted(
            keyword_strategies.items(),
            key=lambda x: x[1].validation_pass_rate,
            reverse=True
        )
        
        optimized = []
        for strategy_name, effectiveness in sorted_keywords[:10]:  # Top 10
            optimized.append({
                "strategy_name": strategy_name,
                "keywords": strategy_name.replace("keyword_", "").split("_"),
                "pass_rate": effectiveness.validation_pass_rate,
                "retention_rate": effectiveness.retention_rate,
                "avg_confidence": effectiveness.avg_confidence
            })
        
        logger.info(f"✅ Found {len(optimized)} optimized keyword combinations")
        return optimized
    
    def get_recommended_strategy(
        self,
        days: int = 30,
        strategy_type: str = "similarity_threshold"
    ) -> Optional[Dict[str, Any]]:
        """
        Get recommended strategy based on effectiveness
        
        Args:
            days: Number of days to analyze
            strategy_type: Type of strategy ("similarity_threshold", "keyword", "source")
        
        Returns:
            Recommended strategy configuration, or None if no data
        """
        best_strategy_name = self.strategy_tracker.get_best_strategy(
            days=days,
            metric="validation_pass_rate"
        )
        
        if not best_strategy_name:
            return None
        
        effectiveness_dict = self.strategy_tracker.calculate_strategy_effectiveness(days=days)
        effectiveness = effectiveness_dict.get(best_strategy_name)
        
        if not effectiveness:
            return None
        
        return {
            "strategy_name": best_strategy_name,
            "strategy_type": strategy_type,
            "effectiveness": {
                "pass_rate": effectiveness.validation_pass_rate,
                "retention_rate": effectiveness.retention_rate,
                "avg_confidence": effectiveness.avg_confidence,
                "total_uses": effectiveness.total_uses
            },
            "recommendation": f"Use {best_strategy_name} for best performance"
        }


# Global tuner instance
_auto_tuner_instance: Optional[AutoTuner] = None


def get_auto_tuner() -> AutoTuner:
    """Get global AutoTuner instance"""
    global _auto_tuner_instance
    if _auto_tuner_instance is None:
        _auto_tuner_instance = AutoTuner()
    return _auto_tuner_instance

