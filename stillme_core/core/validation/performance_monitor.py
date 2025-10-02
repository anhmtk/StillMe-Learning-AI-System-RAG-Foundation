"""
📊 PERFORMANCE MONITOR

Performance monitoring for StillMe validation framework.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import psutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a performance metric"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: dict[str, str] = None


class PerformanceMonitor:
    """
    Performance monitoring system
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.performance_events = []
        self.start_time = datetime.now()
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_total": psutil.disk_usage("/").total
                if hasattr(psutil, "disk_usage")
                else 0,
                "platform": psutil.sys.platform,
                "python_version": psutil.sys.version,
            }
        except Exception as e:
            logger.warning(f"Could not get system info: {e}")
            return {}

    def record_metric(
        self, name: str, value: float, unit: str = "", tags: dict[str, str] = None
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name, value=value, unit=unit, timestamp=datetime.now(), tags=tags or {}
        )

        self.metrics_history[name].append(metric)
        logger.debug(f"Recorded metric: {name} = {value} {unit}")

    def record_execution_time(
        self, operation_name: str, execution_time: float, tags: dict[str, str] = None
    ):
        """Record execution time for an operation"""
        self.record_metric(
            f"execution_time_{operation_name}", execution_time, "seconds", tags
        )

        # Check for performance issues
        if execution_time > 5.0:  # 5 seconds threshold
            self._log_performance_event(
                "slow_operation",
                "WARNING",
                {
                    "operation": operation_name,
                    "execution_time": execution_time,
                    "tags": tags or {},
                },
            )

    def record_memory_usage(
        self, operation_name: str, memory_mb: float, tags: dict[str, str] = None
    ):
        """Record memory usage for an operation"""
        self.record_metric(f"memory_usage_{operation_name}", memory_mb, "MB", tags)

        # Check for memory issues
        if memory_mb > 1000:  # 1GB threshold
            self._log_performance_event(
                "high_memory_usage",
                "WARNING",
                {
                    "operation": operation_name,
                    "memory_mb": memory_mb,
                    "tags": tags or {},
                },
            )

    def record_cpu_usage(
        self, operation_name: str, cpu_percent: float, tags: dict[str, str] = None
    ):
        """Record CPU usage for an operation"""
        self.record_metric(f"cpu_usage_{operation_name}", cpu_percent, "percent", tags)

        # Check for CPU issues
        if cpu_percent > 80:  # 80% threshold
            self._log_performance_event(
                "high_cpu_usage",
                "WARNING",
                {
                    "operation": operation_name,
                    "cpu_percent": cpu_percent,
                    "tags": tags or {},
                },
            )

    def _log_performance_event(
        self, event_type: str, severity: str, details: dict[str, Any]
    ):
        """Log performance event"""
        event = {
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.performance_events.append(event)
        logger.warning(f"Performance event: {event_type} - {severity} - {details}")

    def get_metric_summary(self, metric_name: str, hours: int = 24) -> dict[str, Any]:
        """Get summary for a specific metric"""
        if metric_name not in self.metrics_history:
            return {"error": f"Metric {metric_name} not found"}

        # Filter by time window
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history[metric_name] if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {"error": f"No data for {metric_name} in the last {hours} hours"}

        values = [m.value for m in recent_metrics]

        return {
            "metric_name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "unit": recent_metrics[0].unit,
            "time_window_hours": hours,
            "first_timestamp": recent_metrics[0].timestamp.isoformat(),
            "last_timestamp": recent_metrics[-1].timestamp.isoformat(),
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Get system metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/") if hasattr(psutil, "disk_usage") else None
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            cpu_percent = 0
            memory = type(
                "obj", (object,), {"percent": 0, "available": 0, "total": 0}
            )()
            disk = None

        # Count performance events by severity
        event_counts = defaultdict(int)
        for event in self.performance_events:
            event_counts[event["severity"]] += 1

        return {
            "uptime_seconds": uptime,
            "uptime_human": str(timedelta(seconds=int(uptime))),
            "system_info": self.system_info,
            "current_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "memory_total_mb": memory.total / (1024 * 1024),
                "disk_usage_percent": (disk.percent if disk else 0),
                "disk_free_gb": (disk.free / (1024 * 1024 * 1024) if disk else 0),
            },
            "metrics_tracked": list(self.metrics_history.keys()),
            "total_metrics_recorded": sum(
                len(history) for history in self.metrics_history.values()
            ),
            "performance_events": {
                "total": len(self.performance_events),
                "by_severity": dict(event_counts),
                "recent_events": self.performance_events[-10:]
                if self.performance_events
                else [],
            },
            "summary_timestamp": datetime.now().isoformat(),
        }

    def get_top_metrics(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top metrics by count"""
        metric_counts = [
            {"name": name, "count": len(history)}
            for name, history in self.metrics_history.items()
        ]

        return sorted(metric_counts, key=lambda x: x["count"], reverse=True)[:limit]

    def clear_old_data(self, hours: int = 24):
        """Clear old data to free memory"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for _metric_name, history in self.metrics_history.items():
            # Remove old metrics
            while history and history[0].timestamp < cutoff_time:
                history.popleft()

        # Remove old performance events
        self.performance_events = [
            event
            for event in self.performance_events
            if datetime.fromisoformat(event["timestamp"]) >= cutoff_time
        ]

        logger.info(f"Cleared data older than {hours} hours")


def main():
    """Test the performance monitor"""
    monitor = PerformanceMonitor()

    # Record some test metrics
    print("📊 Performance Monitor Test:")

    # Simulate some operations
    operations = ["validation", "security_check", "data_processing", "file_io"]

    for operation in operations:
        # Simulate execution time
        execution_time = 0.5 + (hash(operation) % 100) / 100.0
        monitor.record_execution_time(operation, execution_time, {"test": "true"})

        # Simulate memory usage
        memory_mb = 10 + (hash(operation) % 50)
        monitor.record_memory_usage(operation, memory_mb, {"test": "true"})

        # Simulate CPU usage
        cpu_percent = 20 + (hash(operation) % 60)
        monitor.record_cpu_usage(operation, cpu_percent, {"test": "true"})

        print(f"✅ Recorded metrics for {operation}")

    # Get performance summary
    summary = monitor.get_performance_summary()
    print("\n📈 Performance Summary:")
    print(f"Uptime: {summary['uptime_human']}")
    print(f"Metrics tracked: {len(summary['metrics_tracked'])}")
    print(f"Total metrics recorded: {summary['total_metrics_recorded']}")
    print(f"Performance events: {summary['performance_events']['total']}")

    # Get top metrics
    top_metrics = monitor.get_top_metrics(5)
    print("\n🏆 Top Metrics:")
    for metric in top_metrics:
        print(f"  {metric['name']}: {metric['count']} records")

    # Get specific metric summary
    if summary["metrics_tracked"]:
        first_metric = summary["metrics_tracked"][0]
        metric_summary = monitor.get_metric_summary(first_metric)
        print(f"\n📊 Metric Summary for {first_metric}:")
        print(f"  Count: {metric_summary.get('count', 0)}")
        print(
            f"  Average: {metric_summary.get('avg', 0):.2f} {metric_summary.get('unit', '')}"
        )
        print(f"  Min: {metric_summary.get('min', 0):.2f}")
        print(f"  Max: {metric_summary.get('max', 0):.2f}")


if __name__ == "__main__":
    main()
