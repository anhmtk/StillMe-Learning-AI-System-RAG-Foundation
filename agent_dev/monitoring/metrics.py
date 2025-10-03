"""
Metrics Collection for AgentDev
==============================

Self-monitoring and metrics collection system.
"""

import time
import json
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime, timezone
from collections import defaultdict

from ..persistence.repo import MetricRepo
from ..persistence.models import create_memory_database, create_database_engine


class MetricsCollector:
    """Metrics collector for AgentDev operations"""
    
    def __init__(self, database_url: str = "sqlite:///:memory:"):
        """Initialize metrics collector with database"""
        engine, SessionLocal = create_memory_database() if database_url == "sqlite:///:memory:" else create_database_engine(database_url)
        self.SessionLocal = SessionLocal
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = {}
    
    def record_event(self, name: str, value: float = 1.0, 
                    metric_type: str = "counter", 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric event"""
        try:
            session = self.SessionLocal()
            try:
                metric_repo = MetricRepo(session)
                
                # Store in database
                context_str = json.dumps(context) if context else None
                metric_repo.record_metric(
                    metric_name=name,
                    metric_value=value,
                    metric_type=metric_type,
                    context=context_str
                )
                
                # Update in-memory counters
                if metric_type == "counter":
                    self.counters[name] += int(value)
                elif metric_type == "gauge":
                    self.gauges[name] = value
                elif metric_type == "timer":
                    self.timers[name].append(value)
                    
            finally:
                session.close()
        except Exception:
            pass  # Fail silently for monitoring
    
    @contextmanager
    def timer(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_event(name, duration_ms, "timer", context)
    
    def increment_counter(self, name: str, value: int = 1, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """Increment a counter metric"""
        self.record_event(name, float(value), "counter", context)
    
    def set_gauge(self, name: str, value: float, 
                  context: Optional[Dict[str, Any]] = None) -> None:
        """Set a gauge metric"""
        self.record_event(name, value, "gauge", context)
    
    def record_timer(self, name: str, duration_ms: float, 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """Record a timer metric"""
        self.record_event(name, duration_ms, "timer", context)
    
    def dump_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Dump metrics summary"""
        try:
            session = self.SessionLocal()
            try:
                metric_repo = MetricRepo(session)
                summary = metric_repo.get_metrics_summary(hours=hours)
                
                # Add in-memory metrics
                result = {
                    "database_metrics": summary,
                    "in_memory_counters": dict(self.counters),
                    "in_memory_gauges": dict(self.gauges),
                    "in_memory_timers": {
                        name: {
                            "count": len(values),
                            "total": sum(values),
                            "avg": sum(values) / len(values) if values else 0,
                            "min": min(values) if values else 0,
                            "max": max(values) if values else 0
                        }
                        for name, values in self.timers.items()
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                return result
            finally:
                session.close()
        except Exception:
            return {
                "database_metrics": {},
                "in_memory_counters": dict(self.counters),
                "in_memory_gauges": dict(self.gauges),
                "in_memory_timers": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_counter_value(self, name: str) -> int:
        """Get current counter value"""
        return self.counters[name]
    
    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value"""
        return self.gauges.get(name, 0.0)
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics"""
        values = self.timers[name]
        if not values:
            return {"count": 0, "total": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(values),
            "total": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }
    
    def reset_metrics(self) -> None:
        """Reset all in-memory metrics"""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_global_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def record_event(name: str, value: float = 1.0, 
                metric_type: str = "counter", 
                context: Optional[Dict[str, Any]] = None) -> None:
    """Record a metric event using global collector"""
    collector = get_global_collector()
    collector.record_event(name, value, metric_type, context)


@contextmanager
def timer(name: str, context: Optional[Dict[str, Any]] = None):
    """Context manager for timing operations using global collector"""
    collector = get_global_collector()
    with collector.timer(name, context):
        yield


def dump_metrics(hours: int = 24) -> Dict[str, Any]:
    """Dump metrics summary using global collector"""
    collector = get_global_collector()
    return collector.dump_metrics(hours)
