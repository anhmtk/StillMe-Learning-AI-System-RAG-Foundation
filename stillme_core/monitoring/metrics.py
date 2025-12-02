"""
Unified Metrics System for StillMe Framework

Consolidates metrics from all components:
- Validation metrics
- RAG metrics
- Learning metrics
- Post-processing metrics

This provides a single interface for metrics collection and analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Categories of metrics"""
    VALIDATION = "validation"
    RAG = "rag"
    LEARNING = "learning"
    POST_PROCESSING = "post_processing"
    SYSTEM = "system"


@dataclass
class MetricRecord:
    """Single metric record"""
    timestamp: str  # ISO format
    category: str  # MetricCategory value
    metric_name: str
    value: Union[float, int, str, bool, Dict, List]
    metadata: Optional[Dict[str, Any]] = None


class UnifiedMetricsCollector:
    """
    Unified metrics collector for all StillMe framework components.
    
    Consolidates metrics from:
    - Validation system (pass/fail rates, overlap scores, etc.)
    - RAG system (retrieval quality, similarity scores, etc.)
    - Learning system (entries fetched/added, cycle metrics, etc.)
    - Post-processing system (quality scores, rewrite rates, etc.)
    
    Provides both in-memory and persistent storage.
    """
    
    def __init__(
        self,
        persist_to_file: bool = True,
        metrics_file: Optional[str] = None,
        max_in_memory_records: int = 10000
    ):
        """
        Initialize unified metrics collector
        
        Args:
            persist_to_file: Whether to persist metrics to file
            metrics_file: Path to metrics file (default: data/framework_metrics.jsonl)
            max_in_memory_records: Maximum records to keep in memory
        """
        self.persist_to_file = persist_to_file
        self.metrics_file = metrics_file or "data/framework_metrics.jsonl"
        self.max_in_memory_records = max_in_memory_records
        
        # In-memory storage
        self._records: List[MetricRecord] = []
        
        # Aggregated counters by category
        self._counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.metrics_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_metrics()
        
        logger.info(f"UnifiedMetricsCollector initialized (persist={persist_to_file}, file={self.metrics_file})")
    
    def _load_metrics(self):
        """Load recent metrics from file (last N records)"""
        try:
            if Path(self.metrics_file).exists():
                # Load last N records to avoid memory issues
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Load last max_in_memory_records
                    for line in lines[-self.max_in_memory_records:]:
                        if line.strip():
                            data = json.loads(line)
                            record = MetricRecord(**data)
                            self._records.append(record)
                            self._update_aggregates(record)
                logger.info(f"Loaded {len(self._records)} metric records from {self.metrics_file}")
        except Exception as e:
            logger.warning(f"Failed to load metrics from {self.metrics_file}: {e}")
    
    def _update_aggregates(self, record: MetricRecord):
        """Update aggregated metrics from a record"""
        category = record.category
        metric_name = record.metric_name
        
        # Update counters (for integer values)
        if isinstance(record.value, int):
            self._counters[category][metric_name] += record.value
        
        # Update gauges (for float values)
        elif isinstance(record.value, float):
            self._gauges[category][metric_name] = record.value  # Latest value
        
        # Update histograms (for list of values)
        elif isinstance(record.value, list) and all(isinstance(v, (int, float)) for v in record.value):
            if metric_name not in self._histograms[category]:
                self._histograms[category][metric_name] = []
            self._histograms[category][metric_name].extend(record.value)
            # Keep only last 1000 values per histogram
            if len(self._histograms[category][metric_name]) > 1000:
                self._histograms[category][metric_name] = self._histograms[category][metric_name][-1000:]
    
    def _save_record(self, record: MetricRecord):
        """Save a single record to file"""
        if self.persist_to_file:
            try:
                with open(self.metrics_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to save metric record to {self.metrics_file}: {e}")
    
    def record(
        self,
        category: Union[MetricCategory, str],
        metric_name: str,
        value: Union[float, int, str, bool, Dict, List],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a metric
        
        Args:
            category: Metric category (MetricCategory enum or string)
            metric_name: Name of the metric
            value: Metric value (can be number, string, bool, dict, or list)
            metadata: Optional metadata dictionary
        """
        if isinstance(category, MetricCategory):
            category = category.value
        
        record = MetricRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=category,
            metric_name=metric_name,
            value=value,
            metadata=metadata or {}
        )
        
        self._records.append(record)
        self._update_aggregates(record)
        self._save_record(record)
        
        # Keep only recent records in memory
        if len(self._records) > self.max_in_memory_records:
            self._records = self._records[-self.max_in_memory_records:]
        
        logger.debug(f"Recorded metric: {category}.{metric_name} = {value}")
    
    # Convenience methods for different metric types
    
    def increment_counter(
        self,
        category: Union[MetricCategory, str],
        metric_name: str,
        value: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Increment a counter metric"""
        self.record(category, metric_name, value, metadata)
    
    def set_gauge(
        self,
        category: Union[MetricCategory, str],
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set a gauge metric (latest value)"""
        self.record(category, metric_name, value, metadata)
    
    def record_histogram(
        self,
        category: Union[MetricCategory, str],
        metric_name: str,
        values: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record histogram values"""
        self.record(category, metric_name, values, metadata)
    
    # Validation metrics helpers
    
    def record_validation(
        self,
        passed: bool,
        reasons: List[str],
        overlap_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        used_fallback: bool = False,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        context_docs_count: int = 0,
        has_citations: bool = False,
        category: Optional[str] = None
    ) -> None:
        """Record validation metrics (convenience method)"""
        self.increment_counter(
            MetricCategory.VALIDATION,
            "total_validations"
        )
        
        if passed:
            self.increment_counter(MetricCategory.VALIDATION, "passed_count")
        else:
            self.increment_counter(MetricCategory.VALIDATION, "failed_count")
        
        # Record reasons
        for reason in reasons:
            self.increment_counter(
                MetricCategory.VALIDATION,
                f"reason:{reason}",
                metadata={"reason": reason}
            )
        
        # Record scores
        if overlap_score is not None:
            self.record_histogram(
                MetricCategory.VALIDATION,
                "overlap_scores",
                [overlap_score]
            )
        
        if confidence_score is not None:
            self.record_histogram(
                MetricCategory.VALIDATION,
                "confidence_scores",
                [confidence_score]
            )
        
        # Record fallback usage
        if used_fallback:
            self.increment_counter(MetricCategory.VALIDATION, "fallback_usage")
        
        # Record full validation event
        self.record(
            MetricCategory.VALIDATION,
            "validation_event",
            {
                "passed": passed,
                "reasons": reasons,
                "overlap_score": overlap_score,
                "confidence_score": confidence_score,
                "used_fallback": used_fallback,
                "context_docs_count": context_docs_count,
                "has_citations": has_citations,
                "category": category
            },
            metadata={
                "question": question[:200] if question else None,
                "answer": answer[:500] if answer else None
            }
        )
    
    # RAG metrics helpers
    
    def record_rag_retrieval(
        self,
        query: str,
        num_results: int,
        avg_similarity: float,
        context_quality: str,
        retrieval_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record RAG retrieval metrics"""
        self.increment_counter(MetricCategory.RAG, "retrieval_count")
        self.set_gauge(MetricCategory.RAG, "avg_similarity", avg_similarity)
        self.set_gauge(MetricCategory.RAG, "retrieval_time_ms", retrieval_time_ms)
        
        self.record(
            MetricCategory.RAG,
            "retrieval_event",
            {
                "num_results": num_results,
                "avg_similarity": avg_similarity,
                "context_quality": context_quality,
                "retrieval_time_ms": retrieval_time_ms
            },
            metadata={
                "query": query[:200] if query else None,
                **(metadata or {})
            }
        )
    
    # Learning metrics helpers
    
    def record_learning_cycle(
        self,
        cycle_number: int,
        entries_fetched: int,
        entries_added: int,
        entries_filtered: int,
        sources: Dict[str, int],
        duration_seconds: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record learning cycle metrics"""
        self.increment_counter(MetricCategory.LEARNING, "cycle_count")
        self.increment_counter(MetricCategory.LEARNING, "entries_fetched", entries_fetched)
        self.increment_counter(MetricCategory.LEARNING, "entries_added", entries_added)
        self.increment_counter(MetricCategory.LEARNING, "entries_filtered", entries_filtered)
        
        self.record(
            MetricCategory.LEARNING,
            "learning_cycle",
            {
                "cycle_number": cycle_number,
                "entries_fetched": entries_fetched,
                "entries_added": entries_added,
                "entries_filtered": entries_filtered,
                "sources": sources,
                "duration_seconds": duration_seconds,
                "error": error
            },
            metadata=metadata
        )
    
    # Post-processing metrics helpers
    
    def record_post_processing(
        self,
        quality_score: float,
        rewrite_attempted: bool,
        rewrite_successful: bool,
        processing_time_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record post-processing metrics"""
        self.increment_counter(MetricCategory.POST_PROCESSING, "processing_count")
        self.record_histogram(
            MetricCategory.POST_PROCESSING,
            "quality_scores",
            [quality_score]
        )
        
        if rewrite_attempted:
            self.increment_counter(MetricCategory.POST_PROCESSING, "rewrite_attempted")
        if rewrite_successful:
            self.increment_counter(MetricCategory.POST_PROCESSING, "rewrite_successful")
        
        self.set_gauge(MetricCategory.POST_PROCESSING, "processing_time_ms", processing_time_ms)
        
        self.record(
            MetricCategory.POST_PROCESSING,
            "processing_event",
            {
                "quality_score": quality_score,
                "rewrite_attempted": rewrite_attempted,
                "rewrite_successful": rewrite_successful,
                "processing_time_ms": processing_time_ms
            },
            metadata=metadata
        )
    
    # Query methods
    
    def get_metrics(
        self,
        category: Optional[Union[MetricCategory, str]] = None,
        metric_name: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics
        
        Args:
            category: Filter by category (optional)
            metric_name: Filter by metric name (optional)
            days: Filter by last N days (optional)
        
        Returns:
            Dictionary with aggregated metrics
        """
        if isinstance(category, MetricCategory):
            category = category.value
        
        # Filter records
        filtered_records = self._records
        if days:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            filtered_records = [
                r for r in filtered_records
                if datetime.fromisoformat(r.timestamp) >= cutoff_time
            ]
        
        if category:
            filtered_records = [r for r in filtered_records if r.category == category]
        
        if metric_name:
            filtered_records = [r for r in filtered_records if r.metric_name == metric_name]
        
        # Aggregate
        result = {
            "total_records": len(filtered_records),
            "counters": {},
            "gauges": {},
            "histograms": {},
            "recent_records": [asdict(r) for r in filtered_records[-10:]]
        }
        
        # Calculate aggregates from filtered records
        category_counters = defaultdict(lambda: defaultdict(int))
        category_gauges = defaultdict(lambda: defaultdict(list))
        category_histograms = defaultdict(lambda: defaultdict(list))
        
        for record in filtered_records:
            cat = record.category
            name = record.metric_name
            
            if isinstance(record.value, int):
                category_counters[cat][name] += record.value
            elif isinstance(record.value, float):
                category_gauges[cat][name].append(record.value)
            elif isinstance(record.value, list) and all(isinstance(v, (int, float)) for v in record.value):
                category_histograms[cat][name].extend(record.value)
        
        # Convert to final format
        for cat, counters in category_counters.items():
            result["counters"][cat] = dict(counters)
        
        for cat, gauges in category_gauges.items():
            result["gauges"][cat] = {
                name: {
                    "latest": values[-1] if values else None,
                    "avg": sum(values) / len(values) if values else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None
                }
                for name, values in gauges.items()
            }
        
        for cat, histograms in category_histograms.items():
            result["histograms"][cat] = {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "p50": sorted(values)[len(values) // 2] if values else None,
                    "p95": sorted(values)[int(len(values) * 0.95)] if values else None,
                    "p99": sorted(values)[int(len(values) * 0.99)] if values else None
                }
                for name, values in histograms.items()
            }
        
        return result
    
    def reset(self) -> None:
        """Reset all metrics (for testing)"""
        self._records.clear()
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# Global instance
_metrics_collector: Optional[UnifiedMetricsCollector] = None


def get_metrics_collector() -> UnifiedMetricsCollector:
    """Get global unified metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = UnifiedMetricsCollector()
    return _metrics_collector

