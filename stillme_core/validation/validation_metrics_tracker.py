"""
Validation Metrics Tracker with Persistent Storage
Tracks validation metrics with timestamps for self-improvement and learning

This service tracks:
- Validation results per question/response
- Confidence scores
- Validation failure reasons
- Patterns in failures
- Historical performance for self-improvement
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationRecord:
    """Single validation record"""
    timestamp: str  # ISO format
    question: str
    answer: str
    passed: bool
    confidence_score: float
    validation_reasons: List[str]
    overlap_score: Optional[float] = None
    used_fallback: bool = False
    context_docs_count: int = 0
    has_citations: bool = False
    category: Optional[str] = None  # e.g., "philosophical", "factual", "technical"


@dataclass
class ValidationPattern:
    """Pattern detected from validation records"""
    pattern_type: str  # e.g., "missing_citation", "low_overlap", "missing_uncertainty"
    frequency: int
    affected_categories: List[str]
    suggested_improvement: str


class ValidationMetricsTracker:
    """
    Tracks validation metrics with persistent storage for self-improvement
    
    Stores metrics in-memory and persists to file (data/validation_metrics.jsonl).
    Analyzes patterns to suggest improvements.
    """
    
    def __init__(self, persist_to_file: bool = True, metrics_file: Optional[str] = None):
        """
        Initialize validation metrics tracker
        
        Args:
            persist_to_file: Whether to persist metrics to file
            metrics_file: Path to metrics file (default: data/validation_metrics.jsonl)
        """
        self.persist_to_file = persist_to_file
        self.metrics_file = metrics_file or "data/validation_metrics.jsonl"
        
        # In-memory storage: list of ValidationRecord
        self._records: List[ValidationRecord] = []
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.metrics_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_metrics()
        
        logger.info(f"ValidationMetricsTracker initialized (persist={persist_to_file}, file={self.metrics_file})")
    
    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            record = ValidationRecord(**data)
                            self._records.append(record)
                logger.info(f"Loaded {len(self._records)} validation records from {self.metrics_file}")
        except Exception as e:
            logger.warning(f"Failed to load validation metrics from {self.metrics_file}: {e}")
    
    def _save_record(self, record: ValidationRecord):
        """Save a single record to file"""
        if self.persist_to_file:
            try:
                with open(self.metrics_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to save validation record to {self.metrics_file}: {e}")
    
    def record_validation(
        self,
        question: str,
        answer: str,
        passed: bool,
        confidence_score: float,
        validation_reasons: List[str],
        overlap_score: Optional[float] = None,
        used_fallback: bool = False,
        context_docs_count: int = 0,
        has_citations: bool = False,
        category: Optional[str] = None
    ) -> None:
        """
        Record a validation result
        
        Args:
            question: User question
            answer: StillMe's answer
            passed: Whether validation passed
            confidence_score: Confidence score (0.0-1.0)
            validation_reasons: List of validation reasons
            overlap_score: Evidence overlap score (if available)
            used_fallback: Whether fallback answer was used
            context_docs_count: Number of context documents retrieved
            has_citations: Whether answer has citations
            category: Question category (e.g., "philosophical", "factual")
        """
        record = ValidationRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            question=question[:500],  # Truncate long questions
            answer=answer[:2000],  # Truncate long answers
            passed=passed,
            confidence_score=confidence_score,
            validation_reasons=validation_reasons,
            overlap_score=overlap_score,
            used_fallback=used_fallback,
            context_docs_count=context_docs_count,
            has_citations=has_citations,
            category=category
        )
        
        self._records.append(record)
        self._save_record(record)
        
        logger.debug(f"Recorded validation: passed={passed}, confidence={confidence_score:.2f}, reasons={validation_reasons}")
    
    def analyze_patterns(self, days: int = 7) -> List[ValidationPattern]:
        """
        Analyze validation patterns from recent records
        
        Args:
            days: Number of days to analyze (default: 7)
            
        Returns:
            List of detected patterns with suggested improvements
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
        ]
        
        if not recent_records:
            return []
        
        # Count failure reasons
        reason_counts: Dict[str, int] = {}
        reason_categories: Dict[str, set] = {}
        
        for record in recent_records:
            if not record.passed:
                for reason in record.validation_reasons:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                    if reason not in reason_categories:
                        reason_categories[reason] = set()
                    if record.category:
                        reason_categories[reason].add(record.category)
        
        # Generate patterns
        patterns = []
        for reason, count in reason_counts.items():
            if count >= 3:  # Only report patterns that occur 3+ times
                pattern = ValidationPattern(
                    pattern_type=reason,
                    frequency=count,
                    affected_categories=list(reason_categories.get(reason, set())),
                    suggested_improvement=self._suggest_improvement(reason, count)
                )
                patterns.append(pattern)
        
        return patterns
    
    def _suggest_improvement(self, reason: str, frequency: int) -> str:
        """Generate improvement suggestion based on failure reason"""
        suggestions = {
            "missing_citation": f"Missing citations detected {frequency} times. StillMe should prioritize learning content that requires citations, or improve citation detection logic.",
            "low_overlap": f"Low evidence overlap detected {frequency} times. StillMe should improve RAG retrieval relevance or adjust overlap threshold.",
            "missing_uncertainty": f"Missing uncertainty expressions detected {frequency} times. StillMe should improve confidence validator or adjust uncertainty detection.",
            "anthropomorphic_language": f"Anthropomorphic language detected {frequency} times. StillMe should strengthen identity validator or improve rewrite prompts.",
            "hallucination": f"Hallucinations detected {frequency} times. StillMe should improve validation chain or strengthen grounding mechanisms.",
        }
        
        return suggestions.get(reason, f"Pattern '{reason}' detected {frequency} times. Review validation logic and improve response quality.")
    
    def get_failure_rate_by_category(self, days: int = 7) -> Dict[str, float]:
        """
        Get failure rate by question category
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary mapping category to failure rate (0.0-1.0)
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time and r.category
        ]
        
        if not recent_records:
            return {}
        
        category_stats: Dict[str, Dict[str, int]] = {}
        for record in recent_records:
            if record.category not in category_stats:
                category_stats[record.category] = {"total": 0, "failed": 0}
            category_stats[record.category]["total"] += 1
            if not record.passed:
                category_stats[record.category]["failed"] += 1
        
        failure_rates = {}
        for category, stats in category_stats.items():
            failure_rates[category] = stats["failed"] / stats["total"] if stats["total"] > 0 else 0.0
        
        return failure_rates
    
    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with summary metrics
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
        ]
        
        if not recent_records:
            return {
                "total_validations": 0,
                "pass_rate": 0.0,
                "avg_confidence": 0.0,
                "patterns": []
            }
        
        total = len(recent_records)
        passed = sum(1 for r in recent_records if r.passed)
        avg_confidence = sum(r.confidence_score for r in recent_records) / total if total > 0 else 0.0
        
        patterns = self.analyze_patterns(days=days)
        
        return {
            "total_validations": total,
            "pass_rate": passed / total if total > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "patterns": [asdict(p) for p in patterns],
            "failure_rate_by_category": self.get_failure_rate_by_category(days=days)
        }


# Global tracker instance
_tracker = ValidationMetricsTracker()


def get_validation_tracker() -> ValidationMetricsTracker:
    """Get global validation metrics tracker instance"""
    return _tracker

