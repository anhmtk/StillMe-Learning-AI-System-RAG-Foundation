"""
Observability - Metrics, Logging, and Shadow Evaluation
"""

import json
import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ReflexMetrics:
    """Metrics for reflex engine performance"""

    reflex_hits: int = 0
    reflex_misses: int = 0
    safety_fails: int = 0
    fallback_count: int = 0
    total_requests: int = 0
    avg_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    p99_processing_time_ms: float = 0.0

    # Shadow evaluation metrics
    true_positives: int = 0  # Reflex correct
    false_positives: int = 0  # Reflex wrong, should have been reasoning
    true_negatives: int = 0  # Reasoning correct
    false_negatives: int = 0  # Reasoning wrong, should have been reflex

    def precision(self) -> float:
        """Calculate precision: TP / (TP + FP)"""
        total_positive = self.true_positives + self.false_positives
        return self.true_positives / total_positive if total_positive > 0 else 0.0

    def recall(self) -> float:
        """Calculate recall: TP / (TP + FN)"""
        total_actual_positive = self.true_positives + self.false_negatives
        return (
            self.true_positives / total_actual_positive
            if total_actual_positive > 0
            else 0.0
        )

    def f1_score(self) -> float:
        """Calculate F1 score: 2 * (precision * recall) / (precision + recall)"""
        p = self.precision()
        r = self.recall()
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

    def fp_rate(self) -> float:
        """Calculate false positive rate: FP / (FP + TN)"""
        total_negative = self.false_positives + self.true_negatives
        return self.false_positives / total_negative if total_negative > 0 else 0.0


class ProcessingTimeTracker:
    """Track processing times for percentile calculations"""

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.times: deque = deque(maxlen=max_samples)
        self.lock = threading.Lock()

    def add_time(self, time_ms: float):
        """Add a processing time sample"""
        with self.lock:
            self.times.append(time_ms)

    def get_percentile(self, percentile: float) -> float:
        """Get percentile of processing times"""
        with self.lock:
            if not self.times:
                return 0.0

            sorted_times = sorted(self.times)
            index = int((percentile / 100.0) * len(sorted_times))
            index = min(index, len(sorted_times) - 1)
            return sorted_times[index]

    def get_average(self) -> float:
        """Get average processing time"""
        with self.lock:
            return sum(self.times) / len(self.times) if self.times else 0.0


class ShadowEvaluator:
    """Evaluate reflex engine performance in shadow mode"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.evaluation_window_hours = self.config.get("evaluation_window_hours", 24)
        self.min_samples_for_evaluation = self.config.get(
            "min_samples_for_evaluation", 100
        )

        # Store evaluation samples
        self.samples: deque = deque(maxlen=10000)  # Keep last 10k samples
        self.lock = threading.Lock()

        # Evaluation criteria
        self.precision_threshold = self.config.get("precision_threshold", 0.95)
        self.recall_threshold = self.config.get("recall_threshold", 0.80)
        self.fp_rate_threshold = self.config.get("fp_rate_threshold", 0.05)
        self.max_processing_time_ms = self.config.get("max_processing_time_ms", 10.0)

    def add_sample(
        self,
        reflex_decision: str,
        reasoning_decision: str,
        processing_time_ms: float,
        scores: dict[str, float],
        trace_id: str,
        timestamp: float | None = None,
    ):
        """Add a shadow evaluation sample"""
        if timestamp is None:
            timestamp = time.time()

        sample = {
            "timestamp": timestamp,
            "trace_id": trace_id,
            "reflex_decision": reflex_decision,
            "reasoning_decision": reasoning_decision,
            "processing_time_ms": processing_time_ms,
            "scores": scores.copy(),
            "reflex_correct": reflex_decision == reasoning_decision,
        }

        with self.lock:
            self.samples.append(sample)

    def get_recent_samples(self, hours: int | None = None) -> list[dict[str, Any]]:
        """Get samples from recent time window"""
        if hours is None:
            hours = self.evaluation_window_hours

        cutoff_time = time.time() - (hours * 3600)

        with self.lock:
            return [s for s in self.samples if s["timestamp"] >= cutoff_time]

    def evaluate_performance(self, hours: int | None = None) -> dict[str, Any]:
        """Evaluate reflex engine performance"""
        recent_samples = self.get_recent_samples(hours)

        if len(recent_samples) < self.min_samples_for_evaluation:
            return {
                "evaluation_ready": False,
                "sample_count": len(recent_samples),
                "min_samples_required": self.min_samples_for_evaluation,
                "message": "Insufficient samples for evaluation",
            }

        # Calculate metrics
        metrics = ReflexMetrics()

        for sample in recent_samples:
            metrics.total_requests += 1

            if sample["reflex_decision"] == "allow_reflex":
                if sample["reflex_correct"]:
                    metrics.true_positives += 1
                    metrics.reflex_hits += 1
                else:
                    metrics.false_positives += 1
                    metrics.reflex_misses += 1
            else:  # reflex_decision == "fallback"
                if sample["reflex_correct"]:
                    metrics.true_negatives += 1
                else:
                    metrics.false_negatives += 1
                    metrics.fallback_count += 1

        # Calculate processing time percentiles
        processing_times = [s["processing_time_ms"] for s in recent_samples]
        if processing_times:
            sorted_times = sorted(processing_times)
            metrics.avg_processing_time_ms = sum(processing_times) / len(
                processing_times
            )
            metrics.p95_processing_time_ms = sorted_times[int(0.95 * len(sorted_times))]
            metrics.p99_processing_time_ms = sorted_times[int(0.99 * len(sorted_times))]

        # Check if ready for production
        ready_for_production = (
            metrics.precision() >= self.precision_threshold
            and metrics.recall() >= self.recall_threshold
            and metrics.fp_rate() <= self.fp_rate_threshold
            and metrics.p95_processing_time_ms <= self.max_processing_time_ms
        )

        return {
            "evaluation_ready": True,
            "sample_count": len(recent_samples),
            "metrics": asdict(metrics),
            "performance": {
                "precision": metrics.precision(),
                "recall": metrics.recall(),
                "f1_score": metrics.f1_score(),
                "fp_rate": metrics.fp_rate(),
                "avg_processing_time_ms": metrics.avg_processing_time_ms,
                "p95_processing_time_ms": metrics.p95_processing_time_ms,
                "p99_processing_time_ms": metrics.p99_processing_time_ms,
            },
            "thresholds": {
                "precision_threshold": self.precision_threshold,
                "recall_threshold": self.recall_threshold,
                "fp_rate_threshold": self.fp_rate_threshold,
                "max_processing_time_ms": self.max_processing_time_ms,
            },
            "ready_for_production": ready_for_production,
            "evaluation_window_hours": hours or self.evaluation_window_hours,
        }

    def generate_report(self, hours: int | None = None) -> str:
        """Generate markdown report of shadow evaluation"""
        evaluation = self.evaluate_performance(hours)

        if not evaluation["evaluation_ready"]:
            return f"""# Reflex Engine Shadow Evaluation Report

**Status**: Insufficient Data
**Samples**: {evaluation['sample_count']} / {evaluation['min_samples_required']} required
**Message**: {evaluation['message']}

*Evaluation requires at least {evaluation['min_samples_required']} samples to be meaningful.*
"""

        metrics = evaluation["metrics"]
        performance = evaluation["performance"]
        thresholds = evaluation["thresholds"]

        # Determine status
        status = (
            "✅ READY FOR PRODUCTION"
            if evaluation["ready_for_production"]
            else "⚠️ NOT READY"
        )

        return f"""# Reflex Engine Shadow Evaluation Report

**Status**: {status}
**Evaluation Window**: {evaluation['evaluation_window_hours']} hours
**Sample Count**: {evaluation['sample_count']}

## Performance Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Precision | {performance['precision']:.3f} | {thresholds['precision_threshold']:.3f} | {'✅' if performance['precision'] >= thresholds['precision_threshold'] else '❌'} |
| Recall | {performance['recall']:.3f} | {thresholds['recall_threshold']:.3f} | {'✅' if performance['recall'] >= thresholds['recall_threshold'] else '❌'} |
| F1 Score | {performance['f1_score']:.3f} | - | - |
| FP Rate | {performance['fp_rate']:.3f} | {thresholds['fp_rate_threshold']:.3f} | {'✅' if performance['fp_rate'] <= thresholds['fp_rate_threshold'] else '❌'} |

## Processing Time

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Average | {performance['avg_processing_time_ms']:.2f} ms | - | - |
| P95 | {performance['p95_processing_time_ms']:.2f} ms | {thresholds['max_processing_time_ms']:.2f} ms | {'✅' if performance['p95_processing_time_ms'] <= thresholds['max_processing_time_ms'] else '❌'} |
| P99 | {performance['p99_processing_time_ms']:.2f} ms | - | - |

## Confusion Matrix

| | Reflex | Reasoning |
|---|--------|-----------|
| **Correct** | {metrics['true_positives']} (TP) | {metrics['true_negatives']} (TN) |
| **Incorrect** | {metrics['false_positives']} (FP) | {metrics['false_negatives']} (FN) |

## Summary

- **Total Requests**: {metrics['total_requests']}
- **Reflex Hits**: {metrics['reflex_hits']}
- **Reflex Misses**: {metrics['reflex_misses']}
- **Safety Fails**: {metrics['safety_fails']}
- **Fallback Count**: {metrics['fallback_count']}

## Recommendations

{'✅ **Ready for Production**: All thresholds met. Safe to enable real execution.' if evaluation['ready_for_production'] else '⚠️ **Not Ready**: Address failing metrics before enabling production.'}

Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
"""


class ObservabilityManager:
    """Central observability manager for reflex engine"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.metrics = ReflexMetrics()
        self.processing_tracker = ProcessingTimeTracker()
        self.shadow_evaluator = ShadowEvaluator(
            self.config.get("shadow_evaluation", {})
        )
        self.lock = threading.Lock()

        # Logging configuration
        self.log_level = self.config.get("log_level", "INFO")
        self.log_format = self.config.get("log_format", "json")
        self.enable_metrics = self.config.get("enable_metrics", True)
        self.enable_shadow_evaluation = self.config.get(
            "enable_shadow_evaluation", True
        )

        # Setup structured logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup structured logging for observability"""
        if self.log_format == "json":
            # JSON formatter for structured logs
            formatter = logging.Formatter(
                "%(message)s"  # Just the message, assuming it's already JSON
            )
        else:
            # Standard formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # Setup handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Setup logger
        obs_logger = logging.getLogger("stillme.observability")
        obs_logger.setLevel(getattr(logging, self.log_level.upper()))
        obs_logger.addHandler(handler)
        obs_logger.propagate = False  # Don't propagate to root logger

    def log_reflex_decision(
        self,
        trace_id: str,
        decision: str,
        confidence: float,
        processing_time_ms: float,
        scores: dict[str, float],
        why_reflex: dict[str, Any],
        user_id: str | None = None,
        tenant_id: str | None = None,
        shadow_mode: bool = True,
    ):
        """Log a reflex decision with full context"""

        log_entry = {
            "timestamp": int(time.time() * 1000),
            "trace_id": trace_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "event": "reflex_decision",
            "decision": decision,
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
            "shadow_mode": shadow_mode,
            "scores": scores,
            "why_reflex": why_reflex,
        }

        # Log to structured logger
        obs_logger = logging.getLogger("stillme.observability")
        obs_logger.info(json.dumps(log_entry, ensure_ascii=False))

        # Update metrics
        if self.enable_metrics:
            self._update_metrics(decision, processing_time_ms)

    def log_shadow_evaluation(
        self,
        trace_id: str,
        reflex_decision: str,
        reasoning_decision: str,
        processing_time_ms: float,
        scores: dict[str, float],
    ):
        """Log shadow evaluation sample"""
        if self.enable_shadow_evaluation:
            self.shadow_evaluator.add_sample(
                reflex_decision,
                reasoning_decision,
                processing_time_ms,
                scores,
                trace_id,
            )

    def _update_metrics(self, decision: str, processing_time_ms: float):
        """Update internal metrics"""
        with self.lock:
            self.metrics.total_requests += 1

            if decision == "allow_reflex":
                self.metrics.reflex_hits += 1
            else:
                self.metrics.fallback_count += 1

            self.processing_tracker.add_time(processing_time_ms)
            self.metrics.avg_processing_time_ms = self.processing_tracker.get_average()
            self.metrics.p95_processing_time_ms = (
                self.processing_tracker.get_percentile(95)
            )
            self.metrics.p99_processing_time_ms = (
                self.processing_tracker.get_percentile(99)
            )

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        with self.lock:
            return asdict(self.metrics)

    def get_shadow_evaluation(self, hours: int | None = None) -> dict[str, Any]:
        """Get shadow evaluation results"""
        return self.shadow_evaluator.evaluate_performance(hours)

    def generate_shadow_report(self, hours: int | None = None) -> str:
        """Generate shadow evaluation report"""
        return self.shadow_evaluator.generate_report(hours)

    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        with self.lock:
            self.metrics = ReflexMetrics()
            self.processing_tracker = ProcessingTimeTracker()
            self.shadow_evaluator = ShadowEvaluator(
                self.config.get("shadow_evaluation", {})
            )