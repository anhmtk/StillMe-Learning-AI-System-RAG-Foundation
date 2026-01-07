"""
Strategy Tracker for Meta-Learning (Stage 2, Phase 3)

Tracks effectiveness of different strategies (similarity thresholds, keywords, sources).
This enables strategy optimization through A/B testing.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class StrategyRecord:
    """Single record of strategy usage"""
    timestamp: str  # ISO format
    strategy_name: str  # e.g., "similarity_threshold_0.1", "keyword_rag_optimization"
    strategy_params: Dict[str, Any]  # Strategy parameters
    query: str  # User query
    validation_passed: bool  # Whether validation passed
    confidence_score: float  # Response confidence
    retention_used: bool  # Whether retrieved documents were used in response
    execution_time_ms: Optional[float] = None  # Strategy execution time


@dataclass
class StrategyEffectiveness:
    """Effectiveness of a strategy"""
    strategy_name: str
    total_uses: int
    validation_pass_rate: float
    avg_confidence: float
    retention_rate: float  # How often retrieved documents were used
    avg_execution_time_ms: Optional[float] = None
    improvement_over_baseline: Optional[float] = None  # Compared to baseline strategy


class StrategyTracker:
    """
    Tracks strategy effectiveness for optimization.
    
    Strategies tracked:
    - Similarity thresholds (0.1, 0.15, 0.2, etc.)
    - Keyword combinations
    - Source selection strategies
    - RAG retrieval strategies
    """
    
    def __init__(self, persist_to_file: bool = True, strategy_file: Optional[str] = None):
        """
        Initialize strategy tracker
        
        Args:
            persist_to_file: Whether to persist records to file
            strategy_file: Path to strategy file (default: data/strategy_metrics.jsonl)
        """
        self.persist_to_file = persist_to_file
        self.strategy_file = strategy_file or "data/strategy_metrics.jsonl"
        
        # In-memory storage
        self._records: List[StrategyRecord] = []
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.strategy_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_records()
        
        logger.info(f"StrategyTracker initialized (persist={persist_to_file}, file={self.strategy_file})")
    
    def _load_records(self):
        """Load strategy records from file"""
        try:
            if Path(self.strategy_file).exists():
                with open(self.strategy_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            record = StrategyRecord(**data)
                            self._records.append(record)
                logger.info(f"Loaded {len(self._records)} strategy records from {self.strategy_file}")
        except Exception as e:
            logger.warning(f"Failed to load strategy records from {self.strategy_file}: {e}")
    
    def _save_record(self, record: StrategyRecord):
        """Save a single record to file"""
        if self.persist_to_file:
            try:
                with open(self.strategy_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to save strategy record to {self.strategy_file}: {e}")
    
    def record_strategy_usage(
        self,
        strategy_name: str,
        strategy_params: Dict[str, Any],
        query: str,
        validation_passed: bool,
        confidence_score: float,
        retention_used: bool = True,
        execution_time_ms: Optional[float] = None
    ) -> None:
        """
        Record strategy usage
        
        Args:
            strategy_name: Name of strategy (e.g., "similarity_threshold_0.1")
            strategy_params: Strategy parameters
            query: User query
            validation_passed: Whether validation passed
            confidence_score: Response confidence
            retention_used: Whether retrieved documents were used
            execution_time_ms: Execution time in milliseconds
        """
        record = StrategyRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            strategy_name=strategy_name,
            strategy_params=strategy_params,
            query=query[:500],  # Truncate
            validation_passed=validation_passed,
            confidence_score=confidence_score,
            retention_used=retention_used,
            execution_time_ms=execution_time_ms
        )
        
        self._records.append(record)
        self._save_record(record)
        
        logger.debug(f"Recorded strategy usage: {strategy_name}, passed={validation_passed}, confidence={confidence_score:.2f}")
    
    def calculate_strategy_effectiveness(
        self,
        days: int = 30,
        baseline_strategy: Optional[str] = None
    ) -> Dict[str, StrategyEffectiveness]:
        """
        Calculate effectiveness of each strategy
        
        Args:
            days: Number of days to analyze
            baseline_strategy: Baseline strategy to compare against (optional)
        
        Returns:
            Dictionary mapping strategy_name to StrategyEffectiveness
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
        ]
        
        if not recent_records:
            return {}
        
        # Aggregate by strategy
        strategy_stats: Dict[str, Dict[str, Any]] = {}
        
        for record in recent_records:
            strategy_name = record.strategy_name
            
            if strategy_name not in strategy_stats:
                strategy_stats[strategy_name] = {
                    "total_uses": 0,
                    "validation_passed_count": 0,
                    "confidence_scores": [],
                    "retention_used_count": 0,
                    "execution_times": []
                }
            
            stats = strategy_stats[strategy_name]
            stats["total_uses"] += 1
            
            if record.validation_passed:
                stats["validation_passed_count"] += 1
            
            stats["confidence_scores"].append(record.confidence_score)
            
            if record.retention_used:
                stats["retention_used_count"] += 1
            
            if record.execution_time_ms is not None:
                stats["execution_times"].append(record.execution_time_ms)
        
        # Calculate effectiveness
        effectiveness_dict = {}
        baseline_pass_rate = None
        
        if baseline_strategy and baseline_strategy in strategy_stats:
            baseline_stats = strategy_stats[baseline_strategy]
            baseline_pass_rate = baseline_stats["validation_passed_count"] / baseline_stats["total_uses"] if baseline_stats["total_uses"] > 0 else 0.0
        
        for strategy_name, stats in strategy_stats.items():
            total_uses = stats["total_uses"]
            pass_rate = stats["validation_passed_count"] / total_uses if total_uses > 0 else 0.0
            avg_confidence = sum(stats["confidence_scores"]) / len(stats["confidence_scores"]) if stats["confidence_scores"] else 0.0
            retention_rate = stats["retention_used_count"] / total_uses if total_uses > 0 else 0.0
            avg_execution_time = sum(stats["execution_times"]) / len(stats["execution_times"]) if stats["execution_times"] else None
            
            improvement = None
            if baseline_pass_rate is not None:
                improvement = pass_rate - baseline_pass_rate
            
            effectiveness = StrategyEffectiveness(
                strategy_name=strategy_name,
                total_uses=total_uses,
                validation_pass_rate=pass_rate,
                avg_confidence=avg_confidence,
                retention_rate=retention_rate,
                avg_execution_time_ms=avg_execution_time,
                improvement_over_baseline=improvement
            )
            
            effectiveness_dict[strategy_name] = effectiveness
        
        return effectiveness_dict
    
    def get_best_strategy(
        self,
        days: int = 30,
        metric: str = "validation_pass_rate"
    ) -> Optional[str]:
        """
        Get best strategy based on metric
        
        Args:
            days: Number of days to analyze
            metric: Metric to optimize ("validation_pass_rate", "retention_rate", "avg_confidence")
        
        Returns:
            Strategy name with best metric, or None if no data
        """
        effectiveness_dict = self.calculate_strategy_effectiveness(days=days)
        
        if not effectiveness_dict:
            return None
        
        # Sort by metric
        if metric == "validation_pass_rate":
            sorted_strategies = sorted(
                effectiveness_dict.items(),
                key=lambda x: x[1].validation_pass_rate,
                reverse=True
            )
        elif metric == "retention_rate":
            sorted_strategies = sorted(
                effectiveness_dict.items(),
                key=lambda x: x[1].retention_rate,
                reverse=True
            )
        elif metric == "avg_confidence":
            sorted_strategies = sorted(
                effectiveness_dict.items(),
                key=lambda x: x[1].avg_confidence,
                reverse=True
            )
        else:
            return None
        
        if sorted_strategies:
            return sorted_strategies[0][0]
        
        return None


# Global tracker instance
_strategy_tracker_instance: Optional[StrategyTracker] = None


def get_strategy_tracker() -> StrategyTracker:
    """Get global StrategyTracker instance"""
    global _strategy_tracker_instance
    if _strategy_tracker_instance is None:
        _strategy_tracker_instance = StrategyTracker()
    return _strategy_tracker_instance

