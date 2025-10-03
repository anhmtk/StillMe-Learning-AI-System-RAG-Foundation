"""
Test Monitoring and Metrics functionality
========================================

Test metrics collection and monitoring capabilities.
"""

import pytest
import time
from agent_dev.monitoring.metrics import (
    MetricsCollector,
    record_event,
    timer,
    dump_metrics,
)


def test_record_event_and_dump():
    """Test recording events and dumping metrics"""
    collector = MetricsCollector()
    
    # Record some events
    collector.record_event("tasks_completed", 5.0, "counter")
    collector.record_event("tasks_completed", 3.0, "counter")
    collector.record_event("memory_usage", 85.5, "gauge")
    collector.record_event("response_time", 150.0, "timer")
    
    # Check in-memory counters
    assert collector.get_counter_value("tasks_completed") == 8  # 5 + 3
    assert collector.get_gauge_value("memory_usage") == 85.5
    
    # Check timer stats
    timer_stats = collector.get_timer_stats("response_time")
    assert timer_stats["count"] == 1
    assert timer_stats["total"] == 150.0
    assert timer_stats["avg"] == 150.0
    
    # Dump metrics
    metrics = collector.dump_metrics()
    assert "in_memory_counters" in metrics
    assert "in_memory_gauges" in metrics
    assert "in_memory_timers" in metrics
    assert "timestamp" in metrics
    
    # Check counter in dump
    assert metrics["in_memory_counters"]["tasks_completed"] == 8
    assert metrics["in_memory_gauges"]["memory_usage"] == 85.5


def test_timer_context():
    """Test timer context manager"""
    collector = MetricsCollector()
    
    # Use timer context manager
    with collector.timer("test_operation"):
        time.sleep(0.01)  # Sleep for 10ms
    
    # Check timer was recorded
    timer_stats = collector.get_timer_stats("test_operation")
    assert timer_stats["count"] == 1
    assert timer_stats["total"] > 0  # Should be > 0ms
    assert timer_stats["avg"] > 0
    assert timer_stats["min"] > 0
    assert timer_stats["max"] > 0


def test_increment_counter():
    """Test counter increment functionality"""
    collector = MetricsCollector()
    
    # Increment counter
    collector.increment_counter("test_counter", 5)
    collector.increment_counter("test_counter", 3)
    
    # Check value
    assert collector.get_counter_value("test_counter") == 8


def test_set_gauge():
    """Test gauge setting functionality"""
    collector = MetricsCollector()
    
    # Set gauge
    collector.set_gauge("test_gauge", 42.5)
    collector.set_gauge("test_gauge", 100.0)
    
    # Check value (should be last set value)
    assert collector.get_gauge_value("test_gauge") == 100.0


def test_record_timer():
    """Test timer recording functionality"""
    collector = MetricsCollector()
    
    # Record timer values
    collector.record_timer("test_timer", 100.0)
    collector.record_timer("test_timer", 200.0)
    collector.record_timer("test_timer", 150.0)
    
    # Check stats
    timer_stats = collector.get_timer_stats("test_timer")
    assert timer_stats["count"] == 3
    assert timer_stats["total"] == 450.0
    assert timer_stats["avg"] == 150.0
    assert timer_stats["min"] == 100.0
    assert timer_stats["max"] == 200.0


def test_reset_metrics():
    """Test metrics reset functionality"""
    collector = MetricsCollector()
    
    # Add some metrics
    collector.increment_counter("test_counter", 5)
    collector.set_gauge("test_gauge", 42.5)
    collector.record_timer("test_timer", 100.0)
    
    # Verify metrics exist
    assert collector.get_counter_value("test_counter") == 5
    assert collector.get_gauge_value("test_gauge") == 42.5
    assert collector.get_timer_stats("test_timer")["count"] == 1
    
    # Reset metrics
    collector.reset_metrics()
    
    # Verify metrics are cleared
    assert collector.get_counter_value("test_counter") == 0
    assert collector.get_gauge_value("test_gauge") == 0.0
    assert collector.get_timer_stats("test_timer")["count"] == 0


def test_standalone_functions():
    """Test standalone functions"""
    # Test record_event function
    record_event("standalone_counter", 10.0, "counter")
    
    # Test timer function
    with timer("standalone_timer"):
        time.sleep(0.005)  # Sleep for 5ms
    
    # Test dump_metrics function
    metrics = dump_metrics()
    assert "in_memory_counters" in metrics
    assert "in_memory_timers" in metrics


def test_context_parameter():
    """Test context parameter in metrics"""
    collector = MetricsCollector()
    
    # Record event with context
    context = {"user_id": "test_user", "session_id": "test_session"}
    collector.record_event("test_event", 1.0, "counter", context)
    
    # Dump metrics to verify context is stored
    metrics = collector.dump_metrics()
    assert "database_metrics" in metrics


def test_multiple_metric_types():
    """Test multiple metric types"""
    collector = MetricsCollector()
    
    # Record different types
    collector.record_event("counter_metric", 1.0, "counter")
    collector.record_event("gauge_metric", 50.0, "gauge")
    collector.record_event("timer_metric", 100.0, "timer")
    
    # Check all types are recorded
    assert collector.get_counter_value("counter_metric") == 1
    assert collector.get_gauge_value("gauge_metric") == 50.0
    timer_stats = collector.get_timer_stats("timer_metric")
    assert timer_stats["count"] == 1
    assert timer_stats["total"] == 100.0


def test_empty_timer_stats():
    """Test timer stats for non-existent timer"""
    collector = MetricsCollector()
    
    # Get stats for non-existent timer
    timer_stats = collector.get_timer_stats("non_existent")
    assert timer_stats["count"] == 0
    assert timer_stats["total"] == 0
    assert timer_stats["avg"] == 0
    assert timer_stats["min"] == 0
    assert timer_stats["max"] == 0


def test_global_collector():
    """Test global collector functionality"""
    from agent_dev.monitoring.metrics import get_global_collector
    
    # Get global collector
    collector1 = get_global_collector()
    collector2 = get_global_collector()
    
    # Should be the same instance
    assert collector1 is collector2
    
    # Record event using global collector
    collector1.record_event("global_test", 1.0, "counter")
    
    # Check event is recorded
    assert collector1.get_counter_value("global_test") == 1
    assert collector2.get_counter_value("global_test") == 1
