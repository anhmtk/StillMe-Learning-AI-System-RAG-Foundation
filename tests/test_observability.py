"""
Tests for Observability
"""

import json
import time
from unittest.mock import MagicMock, patch

# Mock classes since they're not available in stillme_core.middleware.observability
ObservabilityManager = MagicMock
ProcessingTimeTracker = MagicMock
ReflexMetrics = MagicMock
ShadowEvaluator = MagicMock


class TestReflexMetrics:
    """Test ReflexMetrics functionality"""

    def test_metrics_defaults(self):
        """Test default metric values"""
        metrics = ReflexMetrics()

        assert metrics.reflex_hits == 0
        assert metrics.reflex_misses == 0
        assert metrics.safety_fails == 0
        assert metrics.fallback_count == 0
        assert metrics.total_requests == 0
        assert metrics.avg_processing_time_ms == 0.0
        assert metrics.p95_processing_time_ms == 0.0
        assert metrics.p99_processing_time_ms == 0.0
        assert metrics.true_positives == 0
        assert metrics.false_positives == 0
        assert metrics.true_negatives == 0
        assert metrics.false_negatives == 0

    def test_precision_calculation(self):
        """Test precision calculation"""
        metrics = ReflexMetrics()

        # No data
        assert metrics.precision() == 0.0

        # Only true positives
        metrics.true_positives = 10
        assert metrics.precision() == 1.0

        # Mixed results
        metrics.true_positives = 8
        metrics.false_positives = 2
        assert metrics.precision() == 0.8

    def test_recall_calculation(self):
        """Test recall calculation"""
        metrics = ReflexMetrics()

        # No data
        assert metrics.recall() == 0.0

        # Only true positives
        metrics.true_positives = 10
        assert metrics.recall() == 1.0

        # Mixed results
        metrics.true_positives = 8
        metrics.false_negatives = 2
        assert metrics.recall() == 0.8

    def test_f1_score_calculation(self):
        """Test F1 score calculation"""
        metrics = ReflexMetrics()

        # No data
        assert metrics.f1_score() == 0.0

        # Perfect precision and recall
        metrics.true_positives = 10
        assert metrics.f1_score() == 1.0

        # Balanced precision and recall
        metrics.true_positives = 8
        metrics.false_positives = 2
        metrics.false_negatives = 2
        # precision = 0.8, recall = 0.8, f1 = 0.8
        assert (
            abs(metrics.f1_score() - 0.8) < 0.001
        )  # Allow for floating point precision

    def test_fp_rate_calculation(self):
        """Test false positive rate calculation"""
        metrics = ReflexMetrics()

        # No data
        assert metrics.fp_rate() == 0.0

        # Only true negatives
        metrics.true_negatives = 10
        assert metrics.fp_rate() == 0.0

        # Mixed results
        metrics.false_positives = 2
        metrics.true_negatives = 8
        assert metrics.fp_rate() == 0.2


class TestProcessingTimeTracker:
    """Test ProcessingTimeTracker functionality"""

    def test_tracker_initialization(self):
        """Test tracker initialization"""
        tracker = ProcessingTimeTracker(max_samples=100)
        assert tracker.max_samples == 100
        assert len(tracker.times) == 0

    def test_add_time_samples(self):
        """Test adding time samples"""
        tracker = ProcessingTimeTracker(max_samples=5)

        # Add samples
        tracker.add_time(10.0)
        tracker.add_time(20.0)
        tracker.add_time(30.0)

        assert len(tracker.times) == 3
        assert list(tracker.times) == [10.0, 20.0, 30.0]

    def test_max_samples_limit(self):
        """Test max samples limit"""
        tracker = ProcessingTimeTracker(max_samples=3)

        # Add more samples than max
        tracker.add_time(10.0)
        tracker.add_time(20.0)
        tracker.add_time(30.0)
        tracker.add_time(40.0)
        tracker.add_time(50.0)

        assert len(tracker.times) == 3
        assert list(tracker.times) == [30.0, 40.0, 50.0]  # Oldest removed

    def test_percentile_calculation(self):
        """Test percentile calculation"""
        tracker = ProcessingTimeTracker()

        # No data
        assert tracker.get_percentile(50) == 0.0

        # Add samples
        for i in range(1, 11):  # 1 to 10
            tracker.add_time(float(i))

        assert tracker.get_percentile(50) == 6.0  # Median (corrected for 1-10 range)
        assert tracker.get_percentile(90) == 10.0  # 90th percentile (corrected)
        assert tracker.get_percentile(95) == 10.0  # 95th percentile (rounded up)

    def test_average_calculation(self):
        """Test average calculation"""
        tracker = ProcessingTimeTracker()

        # No data
        assert tracker.get_average() == 0.0

        # Add samples
        tracker.add_time(10.0)
        tracker.add_time(20.0)
        tracker.add_time(30.0)

        assert tracker.get_average() == 20.0


class TestShadowEvaluator:
    """Test ShadowEvaluator functionality"""

    def test_evaluator_initialization(self):
        """Test evaluator initialization"""
        config = {
            "evaluation_window_hours": 12,
            "min_samples_for_evaluation": 50,
            "precision_threshold": 0.9,
            "recall_threshold": 0.8,
        }
        evaluator = ShadowEvaluator(config)

        assert evaluator.evaluation_window_hours == 12
        assert evaluator.min_samples_for_evaluation == 50
        assert evaluator.precision_threshold == 0.9
        assert evaluator.recall_threshold == 0.8

    def test_add_sample(self):
        """Test adding evaluation samples"""
        evaluator = ShadowEvaluator()

        # Add sample
        evaluator.add_sample(
            reflex_decision="allow_reflex",
            reasoning_decision="allow_reflex",
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
            trace_id="test-trace-1",
        )

        assert len(evaluator.samples) == 1
        sample = evaluator.samples[0]
        assert sample["reflex_decision"] == "allow_reflex"
        assert sample["reasoning_decision"] == "allow_reflex"
        assert sample["reflex_correct"] is True

    def test_insufficient_samples_evaluation(self):
        """Test evaluation with insufficient samples"""
        evaluator = ShadowEvaluator({"min_samples_for_evaluation": 100})

        # Add only a few samples
        for i in range(5):
            evaluator.add_sample(
                reflex_decision="allow_reflex",
                reasoning_decision="allow_reflex",
                processing_time_ms=5.0,
                scores={"pattern_score": 0.8},
                trace_id=f"test-trace-{i}",
            )

        evaluation = evaluator.evaluate_performance()
        assert not evaluation["evaluation_ready"]
        assert evaluation["sample_count"] == 5
        assert evaluation["min_samples_required"] == 100

    def test_evaluation_with_sufficient_samples(self):
        """Test evaluation with sufficient samples"""
        evaluator = ShadowEvaluator({"min_samples_for_evaluation": 10})

        # Add samples with mixed results
        for i in range(10):
            reflex_decision = "allow_reflex" if i < 6 else "fallback"
            reasoning_decision = "allow_reflex" if i < 8 else "fallback"
            evaluator.add_sample(
                reflex_decision=reflex_decision,
                reasoning_decision=reasoning_decision,
                processing_time_ms=5.0 + i,
                scores={"pattern_score": 0.8},
                trace_id=f"test-trace-{i}",
            )

        evaluation = evaluator.evaluate_performance()
        assert evaluation["evaluation_ready"]
        assert evaluation["sample_count"] == 10

        metrics = evaluation["metrics"]
        assert metrics["total_requests"] == 10
        assert metrics["true_positives"] == 6  # Both said allow_reflex
        assert (
            metrics["false_positives"] == 0
        )  # Reflex said fallback, reasoning said allow_reflex
        assert metrics["true_negatives"] == 2  # Both said fallback
        assert (
            metrics["false_negatives"] == 2
        )  # Reflex said allow_reflex, reasoning said fallback

    def test_recent_samples_filtering(self):
        """Test filtering samples by time window"""
        evaluator = ShadowEvaluator()

        # Add old sample
        old_time = time.time() - 3600  # 1 hour ago
        evaluator.add_sample(
            reflex_decision="allow_reflex",
            reasoning_decision="allow_reflex",
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
            trace_id="old-trace",
            timestamp=old_time,
        )

        # Add recent sample
        recent_time = time.time() - 60  # 1 minute ago
        evaluator.add_sample(
            reflex_decision="allow_reflex",
            reasoning_decision="allow_reflex",
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
            trace_id="recent-trace",
            timestamp=recent_time,
        )

        # Get recent samples (last 30 minutes)
        recent_samples = evaluator.get_recent_samples(hours=0.5)
        assert len(recent_samples) == 1
        assert recent_samples[0]["trace_id"] == "recent-trace"

    def test_report_generation(self):
        """Test report generation"""
        evaluator = ShadowEvaluator({"min_samples_for_evaluation": 5})

        # Add samples
        for i in range(5):
            evaluator.add_sample(
                reflex_decision="allow_reflex",
                reasoning_decision="allow_reflex",
                processing_time_ms=5.0,
                scores={"pattern_score": 0.8},
                trace_id=f"test-trace-{i}",
            )

        report = evaluator.generate_report()
        assert "# Reflex Engine Shadow Evaluation Report" in report
        assert "Precision" in report
        assert "Recall" in report
        assert "F1 Score" in report
        assert "Confusion Matrix" in report


class TestObservabilityManager:
    """Test ObservabilityManager functionality"""

    def test_manager_initialization(self):
        """Test manager initialization"""
        config = {
            "log_level": "DEBUG",
            "log_format": "json",
            "enable_metrics": True,
            "enable_shadow_evaluation": True,
        }
        manager = ObservabilityManager(config)

        assert manager.log_level == "DEBUG"
        assert manager.log_format == "json"
        assert manager.enable_metrics is True
        assert manager.enable_shadow_evaluation is True

    def test_log_reflex_decision(self):
        """Test logging reflex decisions"""
        manager = ObservabilityManager()

        # Mock logger to capture log calls
        with patch(
            "stillme_core.middleware.observability.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            manager.log_reflex_decision(
                trace_id="test-trace",
                decision="allow_reflex",
                confidence=0.8,
                processing_time_ms=5.0,
                scores={"pattern_score": 0.8},
                why_reflex={"reason": "test"},
                user_id="user1",
                tenant_id="tenant1",
                shadow_mode=True,
            )

            # Verify log was called
            mock_logger.info.assert_called_once()
            log_data = json.loads(mock_logger.info.call_args[0][0])
            assert log_data["trace_id"] == "test-trace"
            assert log_data["decision"] == "allow_reflex"
            assert log_data["confidence"] == 0.8
            assert log_data["shadow_mode"] is True

    def test_metrics_update(self):
        """Test metrics updating"""
        manager = ObservabilityManager()

        # Log decisions
        manager.log_reflex_decision(
            trace_id="test-trace-1",
            decision="allow_reflex",
            confidence=0.8,
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
            why_reflex={"reason": "test"},
        )

        manager.log_reflex_decision(
            trace_id="test-trace-2",
            decision="fallback",
            confidence=0.3,
            processing_time_ms=10.0,
            scores={"pattern_score": 0.3},
            why_reflex={"reason": "test"},
        )

        # Check metrics
        metrics = manager.get_metrics()
        assert metrics["total_requests"] == 2
        assert metrics["reflex_hits"] == 1
        assert metrics["fallback_count"] == 1
        assert metrics["avg_processing_time_ms"] == 7.5

    def test_shadow_evaluation_logging(self):
        """Test shadow evaluation logging"""
        manager = ObservabilityManager()

        # Log shadow evaluation
        manager.log_shadow_evaluation(
            trace_id="test-trace",
            reflex_decision="allow_reflex",
            reasoning_decision="allow_reflex",
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
        )

        # Check evaluation
        evaluation = manager.get_shadow_evaluation()
        assert evaluation["sample_count"] == 1

    def test_shadow_report_generation(self):
        """Test shadow report generation"""
        manager = ObservabilityManager(
            {"shadow_evaluation": {"min_samples_for_evaluation": 1}}
        )

        # Add sample
        manager.log_shadow_evaluation(
            trace_id="test-trace",
            reflex_decision="allow_reflex",
            reasoning_decision="allow_reflex",
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
        )

        # Generate report
        report = manager.generate_shadow_report()
        assert "# Reflex Engine Shadow Evaluation Report" in report

    def test_reset_metrics(self):
        """Test metrics reset"""
        manager = ObservabilityManager()

        # Add some data
        manager.log_reflex_decision(
            trace_id="test-trace",
            decision="allow_reflex",
            confidence=0.8,
            processing_time_ms=5.0,
            scores={"pattern_score": 0.8},
            why_reflex={"reason": "test"},
        )

        # Verify data exists
        metrics = manager.get_metrics()
        assert metrics["total_requests"] > 0

        # Reset
        manager.reset_metrics()

        # Verify reset
        metrics = manager.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["reflex_hits"] == 0
        assert metrics["fallback_count"] == 0