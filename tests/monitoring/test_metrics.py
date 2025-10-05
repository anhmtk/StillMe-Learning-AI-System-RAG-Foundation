#!/usr/bin/env python3
"""
AgentDev Monitoring Tests
=========================

Test cases for the monitoring and metrics system.
"""

import time
from unittest.mock import Mock

from agent_dev.monitoring.metrics import (
    MetricsCollector,
    dump_metrics,
    get_metrics_collector,
    record_event,
    reset_metrics,
    timer,
)


class TestMetricsCollector:
    """Test MetricsCollector class"""

    def test_metrics_collector_init(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        assert collector._counters == {}
        assert collector._gauges == {}
        assert collector._timers == {}
        assert collector._events == []
        assert collector.metric_repo is None

    def test_metrics_collector_with_repo(self):
        """Test metrics collector with repository"""
        mock_repo = Mock()
        collector = MetricsCollector(metric_repo=mock_repo)
        assert collector.metric_repo == mock_repo

    def test_record_event(self):
        """Test recording events"""
        collector = MetricsCollector()

        # Record single event
        collector.record_event("tasks_pass", 1.0)
        assert collector.get_counter("tasks_pass") == 1.0

        # Record multiple events
        collector.record_event("tasks_pass", 2.0)
        collector.record_event("tasks_pass", 1.5)
        assert collector.get_counter("tasks_pass") == 4.5

        # Record with tags
        collector.record_event("security_block", 1.0, {"rule": "test_rule"})
        assert collector.get_counter("security_block") == 1.0

    def test_increment_counter(self):
        """Test incrementing counters"""
        collector = MetricsCollector()

        collector.increment_counter("tasks_pass")
        assert collector.get_counter("tasks_pass") == 1.0

        collector.increment_counter("tasks_pass", 3.0)
        assert collector.get_counter("tasks_pass") == 4.0

    def test_set_gauge(self):
        """Test setting gauge values"""
        collector = MetricsCollector()

        collector.set_gauge("memory_usage", 85.5)
        assert collector.get_gauge("memory_usage") == 85.5

        collector.set_gauge("memory_usage", 90.0)
        assert collector.get_gauge("memory_usage") == 90.0

    def test_record_timer(self):
        """Test recording timer metrics"""
        collector = MetricsCollector()

        collector.record_timer("task_execution", 100.0)
        collector.record_timer("task_execution", 150.0)
        collector.record_timer("task_execution", 200.0)

        stats = collector.get_timer_stats("task_execution")
        assert stats["count"] == 3
        assert stats["avg"] == 150.0
        assert stats["min"] == 100.0
        assert stats["max"] == 200.0

    def test_timer_context_manager(self):
        """Test timer context manager"""
        collector = MetricsCollector()

        with collector.timer("test_operation"):
            time.sleep(0.01)  # Sleep for 10ms

        stats = collector.get_timer_stats("test_operation")
        assert stats["count"] == 1
        assert stats["avg"] >= 10.0  # Should be at least 10ms

    def test_dump_metrics(self):
        """Test dumping metrics"""
        collector = MetricsCollector()

        # Add some metrics
        collector.record_event("tasks_pass", 3.0)
        collector.set_gauge("memory_usage", 75.0)
        collector.record_timer("task_execution", 100.0)

        metrics = collector.dump_metrics()

        assert "counters" in metrics
        assert "gauges" in metrics
        assert "timers" in metrics
        assert "events" in metrics
        assert "timestamp" in metrics

        assert metrics["counters"]["tasks_pass"] == 3.0
        assert metrics["gauges"]["memory_usage"] == 75.0
        assert "task_execution" in metrics["timers"]

    def test_reset_metrics(self):
        """Test resetting metrics"""
        collector = MetricsCollector()

        # Add some metrics
        collector.record_event("tasks_pass", 5.0)
        collector.set_gauge("memory_usage", 80.0)
        collector.record_timer("task_execution", 100.0)

        # Reset
        collector.reset_metrics()

        assert collector.get_counter("tasks_pass") == 0.0
        assert collector.get_gauge("memory_usage") is None
        assert collector.get_timer_stats("task_execution")["count"] == 0

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        collector = MetricsCollector()

        # Add some metrics
        collector.record_event("tasks_pass", 3.0)
        collector.record_event("tasks_fail", 1.0)
        collector.set_gauge("memory_usage", 75.0)
        collector.record_timer("task_execution", 100.0)

        summary = collector.get_metrics_summary()

        assert summary["total_events"] == 2
        assert summary["total_counters"] == 4.0
        assert summary["counter_count"] == 2
        assert summary["gauge_count"] == 1
        assert summary["timer_count"] == 1
        assert "task_execution" in summary["timer_summary"]


class TestGlobalFunctions:
    """Test global monitoring functions"""

    def test_record_event_and_dump(self):
        """Test record_event function and dump_metrics"""
        # Reset global state
        reset_metrics()

        # Record events
        record_event("tasks_pass", 1.0)
        record_event("tasks_pass", 2.0)
        record_event("tasks_pass", 1.5)

        # Dump metrics
        metrics = dump_metrics()

        assert metrics["counters"]["tasks_pass"] == 4.5
        assert len(metrics["events"]) == 3

    def test_timer_context(self):
        """Test timer context manager"""
        # Reset global state
        reset_metrics()

        with timer("test_operation"):
            time.sleep(0.01)  # Sleep for 10ms

        metrics = dump_metrics()
        assert "test_operation" in metrics["timers"]

        timer_stats = metrics["timers"]["test_operation"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] >= 10.0

    def test_increment_counter(self):
        """Test incrementing counter"""
        # Reset global state
        reset_metrics()

        collector = get_metrics_collector()
        collector.increment_counter("tasks_pass", 3.0)

        metrics = dump_metrics()
        assert metrics["counters"]["tasks_pass"] == 3.0

    def test_set_gauge(self):
        """Test setting gauge"""
        # Reset global state
        reset_metrics()

        collector = get_metrics_collector()
        collector.set_gauge("memory_usage", 85.0)

        metrics = dump_metrics()
        assert metrics["gauges"]["memory_usage"] == 85.0

    def test_record_timer(self):
        """Test recording timer"""
        # Reset global state
        reset_metrics()

        collector = get_metrics_collector()
        collector.record_timer("task_execution", 150.0)

        metrics = dump_metrics()
        assert "task_execution" in metrics["timers"]

        timer_stats = metrics["timers"]["task_execution"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] == 150.0

    def test_reset_metrics(self):
        """Test resetting metrics"""
        # Add some metrics
        record_event("tasks_pass", 5.0)

        # Reset
        reset_metrics()

        metrics = dump_metrics()
        assert metrics["counters"] == {}
        assert metrics["gauges"] == {}
        assert metrics["timers"] == {}
        assert metrics["events"] == []

    def test_standalone_functions(self):
        """Test standalone functions work independently"""
        # Reset global state
        reset_metrics()

        # Test record_event
        record_event("test_event", 2.0, {"tag": "value"})

        # Test timer
        with timer("test_timer"):
            time.sleep(0.005)  # 5ms

        # Test dump
        metrics = dump_metrics()

        assert metrics["counters"]["test_event"] == 2.0
        assert "test_timer" in metrics["timers"]
        assert len(metrics["events"]) == 1

        # Check event details
        event = metrics["events"][0]
        assert event["name"] == "test_event"
        assert event["value"] == 2.0
        assert event["tags"]["tag"] == "value"

    def test_context_parameter(self):
        """Test timer context with parameters"""
        # Reset global state
        reset_metrics()

        def test_function(duration: float):
            time.sleep(duration)

        with timer("parameterized_test"):
            test_function(0.01)  # 10ms

        metrics = dump_metrics()
        timer_stats = metrics["timers"]["parameterized_test"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] >= 10.0

    def test_multiple_metric_types(self):
        """Test multiple metric types together"""
        # Reset global state
        reset_metrics()

        # Record different types of metrics
        record_event("counter_metric", 3.0)
        record_event("counter_metric", 2.0)

        collector = get_metrics_collector()
        collector.set_gauge("gauge_metric", 75.5)
        collector.record_timer("timer_metric", 100.0)
        collector.record_timer("timer_metric", 200.0)

        # Test with timer context
        with timer("context_timer"):
            time.sleep(0.005)

        metrics = dump_metrics()

        # Check counters
        assert metrics["counters"]["counter_metric"] == 5.0

        # Check gauges
        assert metrics["gauges"]["gauge_metric"] == 75.5

        # Check timers
        assert "timer_metric" in metrics["timers"]
        assert "context_timer" in metrics["timers"]

        timer_stats = metrics["timers"]["timer_metric"]
        assert timer_stats["count"] == 2
        assert timer_stats["avg"] == 150.0

    def test_empty_timer_stats(self):
        """Test timer stats for non-existent timer"""
        collector = MetricsCollector()

        stats = collector.get_timer_stats("non_existent")
        assert stats["count"] == 0
        assert stats["avg"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0

    def test_global_collector(self):
        """Test global collector singleton"""
        # Reset global state
        reset_metrics()

        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Should be the same instance
        assert collector1 is collector2

        # Test that changes are shared
        collector1.record_event("shared_metric", 1.0)
        assert collector2.get_counter("shared_metric") == 1.0


class TestIntegration:
    """Integration tests for monitoring system"""

    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # Reset global state
        reset_metrics()

        # Simulate AgentDev workflow
        with timer("task_execution"):
            # Simulate task execution
            record_event("tasks_started", 1.0)

            # Simulate some work
            time.sleep(0.01)

            # Simulate success
            record_event("tasks_pass", 1.0)
            record_event("tasks_completed", 1.0)

        # Simulate rule violation
        record_event("security_block", 1.0, {"rule": "forbid_dangerous_shell"})

        # Simulate memory usage
        collector = get_metrics_collector()
        collector.set_gauge("memory_usage", 85.0)

        # Get final metrics
        metrics = dump_metrics()

        # Verify counters
        assert metrics["counters"]["tasks_started"] == 1.0
        assert metrics["counters"]["tasks_pass"] == 1.0
        assert metrics["counters"]["tasks_completed"] == 1.0
        assert metrics["counters"]["security_block"] == 1.0

        # Verify gauges
        assert metrics["gauges"]["memory_usage"] == 85.0

        # Verify timers
        assert "task_execution" in metrics["timers"]
        timer_stats = metrics["timers"]["task_execution"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] >= 10.0

        # Verify events
        assert len(metrics["events"]) == 4

        # Check event details
        security_event = next(
            e for e in metrics["events"] if e["name"] == "security_block"
        )
        assert security_event["tags"]["rule"] == "forbid_dangerous_shell"
