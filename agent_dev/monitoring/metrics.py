#!/usr/bin/env python3
"""
AgentDev Metrics Collector
=========================

Self-monitoring system for collecting and analyzing metrics.
"""

import json
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from agent_dev.persistence.repo import MetricRepo


class MetricsCollector:
    """Metrics collector for AgentDev operations"""
    
    def __init__(self, metric_repo: MetricRepo | None = None):
        self.metric_repo = metric_repo
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timers: dict[str, list[float]] = {}
        self._events: list[dict[str, Any]] = []
        self._lock = Lock()
    
    def record_event(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """Record an event with optional value and tags"""
        with self._lock:
            # Increment counter
            if name not in self._counters:
                self._counters[name] = 0.0
            self._counters[name] += value
            
            # Record event
            event = {
                "name": name,
                "value": value,
                "timestamp": datetime.now(UTC).isoformat(),
                "tags": tags or {}
            }
            self._events.append(event)
            
            # Persist to database if available
            if self.metric_repo:
                try:
                    context = json.dumps(event) if event else None
                    self.metric_repo.record_metric(name, value, "counter", context)
                except Exception as e:
                    print(f"Warning: Failed to persist metric {name}: {e}")
    
    def increment_counter(self, name: str, value: float = 1.0) -> None:
        """Increment a counter metric"""
        self.record_event(name, value)
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value"""
        with self._lock:
            self._gauges[name] = value
            
            # Persist to database if available
            if self.metric_repo:
                try:
                    self.metric_repo.record_metric(name, value, "gauge")
                except Exception as e:
                    print(f"Warning: Failed to persist gauge {name}: {e}")
    
    def record_timer(self, name: str, duration_ms: float) -> None:
        """Record a timer metric"""
        with self._lock:
            if name not in self._timers:
                self._timers[name] = []
            self._timers[name].append(duration_ms)
            
            # Persist to database if available
            if self.metric_repo:
                try:
                    self.metric_repo.record_metric(name, duration_ms, "timer")
                except Exception as e:
                    print(f"Warning: Failed to persist timer {name}: {e}")
    
    @contextmanager
    def timer(self, name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_timer(name, duration_ms)
    
    def get_counter(self, name: str) -> float:
        """Get counter value"""
        with self._lock:
            return self._counters.get(name, 0.0)
    
    def get_gauge(self, name: str) -> float | None:
        """Get gauge value"""
        with self._lock:
            return self._gauges.get(name)
    
    def get_timer_stats(self, name: str) -> dict[str, float]:
        """Get timer statistics"""
        with self._lock:
            if name not in self._timers or not self._timers[name]:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
            
            values = self._timers[name]
            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
    
    def dump_metrics(self) -> dict[str, Any]:
        """Dump all metrics as JSON"""
        with self._lock:
            # Calculate timer stats without nested lock
            timer_stats = {}
            for name in self._timers:
                if name in self._timers and self._timers[name]:
                    values = self._timers[name]
                    timer_stats[name] = {
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
                else:
                    timer_stats[name] = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
            
            return {
                "counters": self._counters.copy(),
                "gauges": self._gauges.copy(),
                "timers": timer_stats,
                "events": self._events[-100:],  # Last 100 events
                "timestamp": datetime.now(UTC).isoformat()
            }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
            self._events.clear()
    
    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        with self._lock:
            total_events = len(self._events)
            total_counters = sum(self._counters.values())
            
            # Calculate timer summary without nested lock
            timer_summary = {}
            for name in self._timers:
                if name in self._timers and self._timers[name]:
                    values = self._timers[name]
                    timer_summary[name] = {
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
                else:
                    timer_summary[name] = {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
            
            return {
                "total_events": total_events,
                "total_counters": total_counters,
                "counter_count": len(self._counters),
                "gauge_count": len(self._gauges),
                "timer_count": len(self._timers),
                "timer_summary": timer_summary,
                "last_updated": datetime.now(UTC).isoformat()
            }


# Global metrics collector instance
_global_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def record_event(name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
    """Record an event using the global collector"""
    collector = get_metrics_collector()
    collector.record_event(name, value, tags)


@contextmanager
def timer(name: str):
    """Timer context manager using the global collector"""
    collector = get_metrics_collector()
    with collector.timer(name):
        yield


def dump_metrics() -> dict[str, Any]:
    """Dump metrics from the global collector"""
    collector = get_metrics_collector()
    return collector.dump_metrics()


def reset_metrics() -> None:
    """Reset metrics in the global collector"""
    collector = get_metrics_collector()
    collector.reset_metrics()