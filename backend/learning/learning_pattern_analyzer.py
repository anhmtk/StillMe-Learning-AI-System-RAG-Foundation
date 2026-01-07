"""
Learning Pattern Analyzer for Meta-Learning (Stage 2, Phase 2)

Analyzes the relationship between learned topics and validation improvement.
This enables curriculum learning - optimizing the order and priority of learning.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
import json

from backend.validators.validation_metrics_tracker import get_validation_tracker
from backend.learning.document_usage_tracker import get_document_usage_tracker

logger = logging.getLogger(__name__)


@dataclass
class LearningEffectiveness:
    """Effectiveness of learning a specific topic"""
    topic: str
    source: str
    before_learning_pass_rate: float  # Validation pass rate before learning
    after_learning_pass_rate: float   # Validation pass rate after learning
    improvement: float  # after - before
    questions_affected: int  # Number of questions this topic helped with
    learned_timestamp: str  # When this topic was learned
    validation_window_days: int  # Days analyzed before/after


@dataclass
class CurriculumItem:
    """Item in the learning curriculum"""
    topic: str
    source: str
    priority: float  # 0.0-1.0, higher = more important
    reason: str  # Why this topic is prioritized
    estimated_improvement: float  # Expected validation improvement
    knowledge_gap_urgency: float  # How urgent is this gap (0.0-1.0)


class LearningPatternAnalyzer:
    """
    Analyzes learning effectiveness to enable curriculum learning.
    
    Compares validation pass rates before and after learning specific topics
    to identify which topics provide the most improvement.
    """
    
    def __init__(self):
        self.validation_tracker = get_validation_tracker()
        self.usage_tracker = get_document_usage_tracker()
        logger.info("LearningPatternAnalyzer initialized")
    
    def analyze_learning_effectiveness(
        self,
        days: int = 30,
        validation_window_days: int = 7
    ) -> List[LearningEffectiveness]:
        """
        Analyze effectiveness of learning specific topics
        
        For each topic learned:
        1. Get validation pass rate BEFORE learning (in validation_window_days before)
        2. Get validation pass rate AFTER learning (in validation_window_days after)
        3. Calculate improvement = after - before
        
        Args:
            days: Number of days to analyze learning cycles
            validation_window_days: Days before/after learning to analyze validation
        
        Returns:
            List of LearningEffectiveness objects, sorted by improvement (descending)
        """
        logger.info(f"📊 Analyzing learning effectiveness over last {days} days...")
        
        # Get learning cycles from learning_metrics.jsonl
        learning_cycles = self._load_learning_cycles(days=days)
        
        if not learning_cycles:
            logger.warning("No learning cycles found in learning_metrics.jsonl")
            return []
        
        effectiveness_list = []
        
        for cycle in learning_cycles:
            cycle_timestamp = datetime.fromisoformat(cycle["timestamp"])
            source = cycle.get("source", "unknown")
            entries_added = cycle.get("entries_added", 0)
            
            if entries_added == 0:
                continue
            
            # Extract topics from cycle (simplified - can be improved)
            topics = self._extract_topics_from_cycle(cycle)
            
            for topic in topics:
                # Get validation pass rate BEFORE learning
                before_window_start = cycle_timestamp - timedelta(days=validation_window_days)
                before_window_end = cycle_timestamp
                before_pass_rate = self._get_validation_pass_rate_for_topic(
                    topic=topic,
                    start_time=before_window_start,
                    end_time=before_window_end
                )
                
                # Get validation pass rate AFTER learning
                after_window_start = cycle_timestamp
                after_window_end = cycle_timestamp + timedelta(days=validation_window_days)
                after_pass_rate = self._get_validation_pass_rate_for_topic(
                    topic=topic,
                    start_time=after_window_start,
                    end_time=after_window_end
                )
                
                # Calculate improvement
                improvement = after_pass_rate - before_pass_rate
                
                # Count questions affected (questions that used documents from this cycle)
                questions_affected = self._count_questions_affected(
                    topic=topic,
                    source=source,
                    start_time=after_window_start,
                    end_time=after_window_end
                )
                
                effectiveness = LearningEffectiveness(
                    topic=topic,
                    source=source,
                    before_learning_pass_rate=before_pass_rate,
                    after_learning_pass_rate=after_pass_rate,
                    improvement=improvement,
                    questions_affected=questions_affected,
                    learned_timestamp=cycle["timestamp"],
                    validation_window_days=validation_window_days
                )
                
                effectiveness_list.append(effectiveness)
        
        # Sort by improvement (descending)
        effectiveness_list.sort(key=lambda x: x.improvement, reverse=True)
        
        logger.info(f"✅ Analyzed {len(effectiveness_list)} learning effectiveness records")
        return effectiveness_list
    
    def _load_learning_cycles(self, days: int) -> List[Dict[str, Any]]:
        """Load learning cycles from learning_metrics.jsonl"""
        learning_metrics_file = Path("data/learning_metrics.jsonl")
        
        if not learning_metrics_file.exists():
            return []
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        cycles = []
        
        try:
            with open(learning_metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            cycle_timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                            if cycle_timestamp >= cutoff_time:
                                cycles.append(data)
                        except Exception as e:
                            logger.debug(f"Failed to parse learning cycle: {e}")
                            continue
        except Exception as e:
            logger.warning(f"Failed to load learning cycles: {e}")
        
        return cycles
    
    def _extract_topics_from_cycle(self, cycle: Dict[str, Any]) -> List[str]:
        """
        Extract topics from a learning cycle
        
        This is a simplified version - in production, would use NLP to extract
        topics from entry titles, summaries, or content.
        """
        topics = []
        
        # Try to extract from entries
        entries = cycle.get("entries", [])
        for entry in entries[:10]:  # Limit to first 10 entries
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Simple keyword extraction (can be improved)
            text = f"{title} {summary}".lower()
            
            # Extract common topic keywords
            topic_keywords = [
                "ai", "machine learning", "deep learning", "neural network",
                "rag", "retrieval", "embedding", "vector",
                "ethics", "governance", "transparency",
                "philosophy", "epistemology", "consciousness",
                "python", "programming", "algorithm",
                "research", "paper", "study"
            ]
            
            for keyword in topic_keywords:
                if keyword in text and keyword not in topics:
                    topics.append(keyword)
        
        # If no topics extracted, use source as topic
        if not topics:
            source = cycle.get("source", "unknown")
            topics.append(source.split("/")[-1] if "/" in source else source)
        
        return topics[:5]  # Limit to 5 topics per cycle
    
    def _get_validation_pass_rate_for_topic(
        self,
        topic: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """
        Get validation pass rate for questions related to a topic
        
        Args:
            topic: Topic keyword
            start_time: Start of time window
            end_time: End of time window
        
        Returns:
            Pass rate (0.0-1.0)
        """
        records = [
            r for r in self.validation_tracker._records
            if start_time <= datetime.fromisoformat(r.timestamp) <= end_time
            and topic.lower() in r.question.lower()
        ]
        
        if not records:
            return 0.5  # Default: assume 50% if no data
        
        passed = sum(1 for r in records if r.passed)
        return passed / len(records) if records else 0.5
    
    def _count_questions_affected(
        self,
        topic: str,
        source: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count questions that used documents from this topic/source"""
        usage_records = [
            r for r in self.usage_tracker._records
            if start_time <= datetime.fromisoformat(r.timestamp) <= end_time
            and source in r.source
            and topic.lower() in (r.title or "").lower()
        ]
        
        return len(usage_records)
    
    def get_top_effective_topics(self, days: int = 30, top_n: int = 10) -> List[LearningEffectiveness]:
        """
        Get top N most effective topics (highest improvement)
        
        Args:
            days: Number of days to analyze
            top_n: Number of top topics to return
        
        Returns:
            List of top effective topics
        """
        effectiveness_list = self.analyze_learning_effectiveness(days=days)
        return effectiveness_list[:top_n]
    
    def get_ineffective_topics(self, days: int = 30, threshold: float = 0.0) -> List[LearningEffectiveness]:
        """
        Get topics with negative or zero improvement
        
        Args:
            days: Number of days to analyze
            threshold: Maximum improvement to consider "ineffective" (default: 0.0)
        
        Returns:
            List of ineffective topics
        """
        effectiveness_list = self.analyze_learning_effectiveness(days=days)
        return [e for e in effectiveness_list if e.improvement <= threshold]


# Global analyzer instance
_analyzer_instance: Optional[LearningPatternAnalyzer] = None


def get_learning_pattern_analyzer() -> LearningPatternAnalyzer:
    """Get global LearningPatternAnalyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = LearningPatternAnalyzer()
    return _analyzer_instance

