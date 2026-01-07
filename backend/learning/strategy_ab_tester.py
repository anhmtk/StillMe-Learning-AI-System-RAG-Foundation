"""
A/B Testing Framework for Meta-Learning (Stage 2, Phase 3)

Enables A/B testing of different strategies to find the best one.
This is the foundation for strategy optimization.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from backend.learning.strategy_tracker import get_strategy_tracker

logger = logging.getLogger(__name__)


@dataclass
class ABTestConfig:
    """Configuration for an A/B test"""
    test_name: str
    strategy_a: Dict[str, Any]  # Strategy A configuration
    strategy_b: Dict[str, Any]  # Strategy B configuration
    traffic_split: float = 0.5  # 0.5 = 50/50 split
    min_samples: int = 100  # Minimum samples before declaring winner
    metric: str = "validation_pass_rate"  # Metric to optimize


@dataclass
class ABTestResult:
    """Result of an A/B test"""
    test_name: str
    strategy_a_name: str
    strategy_b_name: str
    strategy_a_effectiveness: Dict[str, Any]
    strategy_b_effectiveness: Dict[str, Any]
    winner: Optional[str]  # "A", "B", or None (inconclusive)
    confidence: float  # Statistical confidence (0.0-1.0)
    recommendation: str


class StrategyABTester:
    """
    A/B testing framework for strategies.
    
    Tests different strategies and selects the best one based on metrics.
    """
    
    def __init__(self):
        self.strategy_tracker = get_strategy_tracker()
        self.active_tests: Dict[str, ABTestConfig] = {}
        logger.info("StrategyABTester initialized")
    
    def start_ab_test(self, config: ABTestConfig) -> None:
        """
        Start an A/B test
        
        Args:
            config: A/B test configuration
        """
        self.active_tests[config.test_name] = config
        logger.info(f"🧪 Started A/B test: {config.test_name} (A: {config.strategy_a}, B: {config.strategy_b})")
    
    def select_strategy(self, test_name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Select strategy for current request (A or B based on traffic split)
        
        Args:
            test_name: Name of A/B test
        
        Returns:
            Tuple of (strategy_name, strategy_config)
        """
        if test_name not in self.active_tests:
            # No active test, return default
            return "default", {}
        
        config = self.active_tests[test_name]
        
        # Random selection based on traffic split
        if random.random() < config.traffic_split:
            return "A", config.strategy_a
        else:
            return "B", config.strategy_b
    
    def evaluate_ab_test(
        self,
        test_name: str,
        days: int = 7
    ) -> Optional[ABTestResult]:
        """
        Evaluate A/B test and determine winner
        
        Args:
            test_name: Name of A/B test
            days: Number of days to analyze
        
        Returns:
            ABTestResult with winner and confidence, or None if test not found
        """
        if test_name not in self.active_tests:
            logger.warning(f"A/B test '{test_name}' not found")
            return None
        
        config = self.active_tests[test_name]
        
        # Get effectiveness for both strategies
        effectiveness_dict = self.strategy_tracker.calculate_strategy_effectiveness(days=days)
        
        strategy_a_name = config.strategy_a.get("name", "strategy_a")
        strategy_b_name = config.strategy_b.get("name", "strategy_b")
        
        strategy_a_eff = effectiveness_dict.get(strategy_a_name)
        strategy_b_eff = effectiveness_dict.get(strategy_b_name)
        
        if not strategy_a_eff or not strategy_b_eff:
            logger.warning(f"Insufficient data for A/B test '{test_name}'")
            return ABTestResult(
                test_name=test_name,
                strategy_a_name=strategy_a_name,
                strategy_b_name=strategy_b_name,
                strategy_a_effectiveness={},
                strategy_b_effectiveness={},
                winner=None,
                confidence=0.0,
                recommendation="Insufficient data - need more samples"
            )
        
        # Compare based on metric
        if config.metric == "validation_pass_rate":
            a_metric = strategy_a_eff.validation_pass_rate
            b_metric = strategy_b_eff.validation_pass_rate
        elif config.metric == "retention_rate":
            a_metric = strategy_a_eff.retention_rate
            b_metric = strategy_b_eff.retention_rate
        elif config.metric == "avg_confidence":
            a_metric = strategy_a_eff.avg_confidence
            b_metric = strategy_b_eff.avg_confidence
        else:
            a_metric = strategy_a_eff.validation_pass_rate
            b_metric = strategy_b_eff.validation_pass_rate
        
        # Determine winner (simple comparison - can be enhanced with statistical tests)
        winner = None
        confidence = 0.0
        
        if a_metric > b_metric:
            winner = "A"
            # Simple confidence: difference / max
            confidence = (a_metric - b_metric) / max(a_metric, 0.01)
        elif b_metric > a_metric:
            winner = "B"
            confidence = (b_metric - a_metric) / max(b_metric, 0.01)
        else:
            winner = None
            confidence = 0.0
        
        # Check if we have enough samples
        total_samples = strategy_a_eff.total_uses + strategy_b_eff.total_uses
        if total_samples < config.min_samples:
            winner = None
            confidence = 0.0
            recommendation = f"Insufficient samples ({total_samples}/{config.min_samples}) - continue testing"
        elif winner:
            recommendation = f"Strategy {winner} is better ({config.metric}: {a_metric:.2f} vs {b_metric:.2f}, confidence: {confidence:.2f})"
        else:
            recommendation = "No clear winner - strategies are equivalent"
        
        return ABTestResult(
            test_name=test_name,
            strategy_a_name=strategy_a_name,
            strategy_b_name=strategy_b_name,
            strategy_a_effectiveness={
                "pass_rate": strategy_a_eff.validation_pass_rate,
                "retention_rate": strategy_a_eff.retention_rate,
                "avg_confidence": strategy_a_eff.avg_confidence,
                "total_uses": strategy_a_eff.total_uses
            },
            strategy_b_effectiveness={
                "pass_rate": strategy_b_eff.validation_pass_rate,
                "retention_rate": strategy_b_eff.retention_rate,
                "avg_confidence": strategy_b_eff.avg_confidence,
                "total_uses": strategy_b_eff.total_uses
            },
            winner=winner,
            confidence=confidence,
            recommendation=recommendation
        )
    
    def get_active_tests(self) -> List[str]:
        """Get list of active A/B test names"""
        return list(self.active_tests.keys())


# Global tester instance
_ab_tester_instance: Optional[StrategyABTester] = None


def get_strategy_ab_tester() -> StrategyABTester:
    """Get global StrategyABTester instance"""
    global _ab_tester_instance
    if _ab_tester_instance is None:
        _ab_tester_instance = StrategyABTester()
    return _ab_tester_instance

