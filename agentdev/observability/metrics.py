#!/usr/bin/env python3
"""
AgentDev Metrics Collector - SEAL-GRADE
Enterprise-grade metrics collection and monitoring
"""

import asyncio
import time
import threading
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from collections import defaultdict, deque
import statistics
import json
from pathlib import Path

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MetricUnit(Enum):
    """Metric units"""
    NONE = ""
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    BYTES = "bytes"
    KILOBYTES = "kilobytes"
    MEGABYTES = "megabytes"
    REQUESTS = "requests"
    ERRORS = "errors"
    PERCENT = "percent"
    TOKENS = "tokens"

@dataclass
class MetricValue:
    """Metric value with metadata"""
    value: Union[int, float]
    timestamp: float
    labels: Optional[Dict[str, str]] = None
    unit: Optional[MetricUnit] = None

@dataclass
class MetricSnapshot:
    """Metric snapshot for reporting"""
    name: str
    type: MetricType
    value: Union[int, float, Dict[str, Any]]
    timestamp: float
    labels: Optional[Dict[str, str]] = None
    unit: Optional[MetricUnit] = None
    description: Optional[str] = None

class Counter:
    """Counter metric - monotonically increasing"""
    
    def __init__(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None):
        self.name = name
        self.description = description
        self.unit = unit
        self._value = 0
        self._lock = threading.Lock()
        self._history = deque(maxlen=1000)  # Keep last 1000 values
    
    def increment(self, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        with self._lock:
            self._value += value
            self._history.append(MetricValue(
                value=self._value,
                timestamp=time.time(),
                labels=labels,
                unit=self.unit
            ))
    
    def get_value(self) -> int:
        """Get current value"""
        with self._lock:
            return self._value
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get metric snapshot"""
        with self._lock:
            return MetricSnapshot(
                name=self.name,
                type=MetricType.COUNTER,
                value=self._value,
                timestamp=time.time(),
                unit=self.unit,
                description=self.description
            )

class Gauge:
    """Gauge metric - can increase or decrease"""
    
    def __init__(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None):
        self.name = name
        self.description = description
        self.unit = unit
        self._value = 0.0
        self._lock = threading.Lock()
        self._history = deque(maxlen=1000)
    
    def set(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        with self._lock:
            self._value = float(value)
            self._history.append(MetricValue(
                value=self._value,
                timestamp=time.time(),
                labels=labels,
                unit=self.unit
            ))
    
    def increment(self, value: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        with self._lock:
            self._value += float(value)
            self._history.append(MetricValue(
                value=self._value,
                timestamp=time.time(),
                labels=labels,
                unit=self.unit
            ))
    
    def decrement(self, value: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        with self._lock:
            self._value -= float(value)
            self._history.append(MetricValue(
                value=self._value,
                timestamp=time.time(),
                labels=labels,
                unit=self.unit
            ))
    
    def get_value(self) -> float:
        """Get current value"""
        with self._lock:
            return self._value
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get metric snapshot"""
        with self._lock:
            return MetricSnapshot(
                name=self.name,
                type=MetricType.GAUGE,
                value=self._value,
                timestamp=time.time(),
                unit=self.unit,
                description=self.description
            )

class Histogram:
    """Histogram metric - distribution of values"""
    
    def __init__(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None,
                 buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.unit = unit
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, float('inf')]
        self._values = []
        self._lock = threading.Lock()
        self._count = 0
        self._sum = 0.0
    
    def observe(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        with self._lock:
            self._values.append(float(value))
            self._count += 1
            self._sum += float(value)
            
            # Keep only last 1000 values
            if len(self._values) > 1000:
                self._values = self._values[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get histogram statistics"""
        with self._lock:
            if not self._values:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "median": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "buckets": {str(bucket): 0 for bucket in self.buckets}
                }
            
            sorted_values = sorted(self._values)
            count = len(sorted_values)
            
            # Calculate percentiles
            p50_idx = int(count * 0.5)
            p95_idx = int(count * 0.95)
            p99_idx = int(count * 0.99)
            
            p50 = sorted_values[p50_idx] if p50_idx < count else sorted_values[-1]
            p95 = sorted_values[p95_idx] if p95_idx < count else sorted_values[-1]
            p99 = sorted_values[p99_idx] if p99_idx < count else sorted_values[-1]
            
            # Calculate bucket counts
            bucket_counts = {}
            for bucket in self.buckets:
                count_in_bucket = sum(1 for v in self._values if v <= bucket)
                bucket_counts[str(bucket)] = count_in_bucket
            
            return {
                "count": self._count,
                "sum": self._sum,
                "min": min(self._values),
                "max": max(self._values),
                "mean": self._sum / self._count if self._count > 0 else 0.0,
                "median": statistics.median(self._values),
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "buckets": bucket_counts
            }
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get metric snapshot"""
        stats = self.get_stats()
        return MetricSnapshot(
            name=self.name,
            type=MetricType.HISTOGRAM,
            value=stats,
            timestamp=time.time(),
            unit=self.unit,
            description=self.description
        )

class Summary:
    """Summary metric - quantiles over time"""
    
    def __init__(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None,
                 quantiles: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.unit = unit
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self._values = []
        self._lock = threading.Lock()
        self._count = 0
        self._sum = 0.0
    
    def observe(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        with self._lock:
            self._values.append(float(value))
            self._count += 1
            self._sum += float(value)
            
            # Keep only last 1000 values
            if len(self._values) > 1000:
                self._values = self._values[-1000:]
    
    def get_quantiles(self) -> Dict[str, float]:
        """Get quantile values"""
        with self._lock:
            if not self._values:
                return {f"q{int(q*100)}": 0.0 for q in self.quantiles}
            
            sorted_values = sorted(self._values)
            count = len(sorted_values)
            
            quantile_values = {}
            for q in self.quantiles:
                idx = int(count * q)
                if idx >= count:
                    idx = count - 1
                quantile_values[f"q{int(q*100)}"] = sorted_values[idx]
            
            return quantile_values
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get metric snapshot"""
        quantiles = self.get_quantiles()
        with self._lock:
            return MetricSnapshot(
                name=self.name,
                type=MetricType.SUMMARY,
                value={
                    "count": self._count,
                    "sum": self._sum,
                    "quantiles": quantiles
                },
                timestamp=time.time(),
                unit=self.unit,
                description=self.description
            )

class MetricsCollector:
    """
    SEAL-GRADE Metrics Collector
    
    Features:
    - Multiple metric types (Counter, Gauge, Histogram, Summary)
    - Thread-safe operations
    - Historical data tracking
    - Export to JSON/Prometheus
    - Performance monitoring
    - Custom metrics
    """
    
    def __init__(self, export_interval: float = 60.0, export_file: Optional[str] = None):
        self.export_interval = export_interval
        self.export_file = export_file
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}
        self._lock = threading.Lock()
        self._export_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize default metrics
        self._setup_default_metrics()
    
    def _setup_default_metrics(self):
        """Setup default system metrics"""
        # Job metrics
        self.create_counter("jobs_total", "Total number of jobs", MetricUnit.REQUESTS)
        self.create_counter("jobs_completed", "Number of completed jobs", MetricUnit.REQUESTS)
        self.create_counter("jobs_failed", "Number of failed jobs", MetricUnit.REQUESTS)
        self.create_gauge("jobs_active", "Number of active jobs", MetricUnit.REQUESTS)
        
        # Tool execution metrics
        self.create_counter("tool_executions_total", "Total tool executions", MetricUnit.REQUESTS)
        self.create_counter("tool_executions_failed", "Failed tool executions", MetricUnit.REQUESTS)
        self.create_histogram("tool_execution_duration", "Tool execution duration", MetricUnit.MILLISECONDS)
        
        # AI interaction metrics
        self.create_counter("ai_requests_total", "Total AI requests", MetricUnit.REQUESTS)
        self.create_counter("ai_requests_failed", "Failed AI requests", MetricUnit.REQUESTS)
        self.create_histogram("ai_request_duration", "AI request duration", MetricUnit.MILLISECONDS)
        self.create_counter("tokens_consumed", "Total tokens consumed", MetricUnit.TOKENS)
        
        # Security metrics
        self.create_counter("security_events_total", "Total security events", MetricUnit.REQUESTS)
        self.create_counter("security_blocks", "Security blocks", MetricUnit.REQUESTS)
        
        # Performance metrics
        self.create_gauge("memory_usage", "Memory usage", MetricUnit.BYTES)
        self.create_gauge("cpu_usage", "CPU usage", MetricUnit.PERCENT)
        self.create_histogram("response_time", "Response time", MetricUnit.MILLISECONDS)
    
    def create_counter(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None) -> Counter:
        """Create a counter metric"""
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            counter = Counter(name, description, unit)
            self._metrics[name] = counter
            return counter
    
    def create_gauge(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None) -> Gauge:
        """Create a gauge metric"""
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            gauge = Gauge(name, description, unit)
            self._metrics[name] = gauge
            return gauge
    
    def create_histogram(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None,
                        buckets: Optional[List[float]] = None) -> Histogram:
        """Create a histogram metric"""
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            histogram = Histogram(name, description, unit, buckets)
            self._metrics[name] = histogram
            return histogram
    
    def create_summary(self, name: str, description: Optional[str] = None, unit: Optional[MetricUnit] = None,
                      quantiles: Optional[List[float]] = None) -> Summary:
        """Create a summary metric"""
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            summary = Summary(name, description, unit, quantiles)
            self._metrics[name] = summary
            return summary
    
    def get_metric(self, name: str) -> Optional[Union[Counter, Gauge, Histogram, Summary]]:
        """Get a metric by name"""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all metrics"""
        with self._lock:
            return self._metrics.copy()
    
    def get_snapshots(self) -> List[MetricSnapshot]:
        """Get snapshots of all metrics"""
        with self._lock:
            return [metric.get_snapshot() for metric in self._metrics.values()]
    
    def export_json(self, file_path: Optional[str] = None) -> str:
        """Export metrics to JSON"""
        snapshots = self.get_snapshots()
        export_data = {
            "timestamp": time.time(),
            "metrics": [asdict(snapshot) for snapshot in snapshots]
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        lines.append("# HELP agentdev_metrics AgentDev metrics")
        lines.append("# TYPE agentdev_metrics counter")
        
        for snapshot in self.get_snapshots():
            name = snapshot.name
            value = snapshot.value
            timestamp = int(snapshot.timestamp * 1000)
            
            if snapshot.type == MetricType.COUNTER:
                lines.append(f"agentdev_{name} {value} {timestamp}")
            elif snapshot.type == MetricType.GAUGE:
                lines.append(f"agentdev_{name} {value} {timestamp}")
            elif snapshot.type == MetricType.HISTOGRAM:
                if isinstance(value, dict):
                    lines.append(f"agentdev_{name}_count {value.get('count', 0)} {timestamp}")
                    lines.append(f"agentdev_{name}_sum {value.get('sum', 0)} {timestamp}")
                    lines.append(f"agentdev_{name}_mean {value.get('mean', 0)} {timestamp}")
                    lines.append(f"agentdev_{name}_p95 {value.get('p95', 0)} {timestamp}")
                    lines.append(f"agentdev_{name}_p99 {value.get('p99', 0)} {timestamp}")
            elif snapshot.type == MetricType.SUMMARY:
                if isinstance(value, dict):
                    lines.append(f"agentdev_{name}_count {value.get('count', 0)} {timestamp}")
                    lines.append(f"agentdev_{name}_sum {value.get('sum', 0)} {timestamp}")
                    quantiles = value.get('quantiles', {})
                    for q_name, q_value in quantiles.items():
                        lines.append(f"agentdev_{name}_{q_name} {q_value} {timestamp}")
        
        return "\n".join(lines)
    
    async def start_export_task(self):
        """Start automatic export task"""
        if self._running:
            return
        
        self._running = True
        self._export_task = asyncio.create_task(self._export_loop())
    
    async def stop_export_task(self):
        """Stop automatic export task"""
        self._running = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
    
    async def _export_loop(self):
        """Export loop"""
        while self._running:
            try:
                if self.export_file:
                    self.export_json(self.export_file)
                await asyncio.sleep(self.export_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in export loop: {e}")
                await asyncio.sleep(self.export_interval)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on metrics"""
        snapshots = self.get_snapshots()
        health_data = {}
        
        for snapshot in snapshots:
            if snapshot.name == "jobs_failed":
                failed_jobs = snapshot.value
            elif snapshot.name == "jobs_completed":
                completed_jobs = snapshot.value
            elif snapshot.name == "tool_executions_failed":
                failed_tools = snapshot.value
            elif snapshot.name == "tool_executions_total":
                total_tools = snapshot.value
        
        # Calculate health scores
        job_success_rate = completed_jobs / (completed_jobs + failed_jobs) if (completed_jobs + failed_jobs) > 0 else 1.0
        tool_success_rate = (total_tools - failed_tools) / total_tools if total_tools > 0 else 1.0
        
        health_data = {
            "overall_health": "healthy" if job_success_rate > 0.8 and tool_success_rate > 0.9 else "unhealthy",
            "job_success_rate": job_success_rate,
            "tool_success_rate": tool_success_rate,
            "failed_jobs": failed_jobs,
            "completed_jobs": completed_jobs,
            "failed_tools": failed_tools,
            "total_tools": total_tools
        }
        
        return health_data

# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None

def get_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector

def set_global_collector(collector: MetricsCollector):
    """Set global metrics collector instance"""
    global _global_collector
    _global_collector = collector

# Convenience functions
def create_counter(name: str, **kwargs) -> Counter:
    """Create a counter metric"""
    return get_collector().create_counter(name, **kwargs)

def create_gauge(name: str, **kwargs) -> Gauge:
    """Create a gauge metric"""
    return get_collector().create_gauge(name, **kwargs)

def create_histogram(name: str, **kwargs) -> Histogram:
    """Create a histogram metric"""
    return get_collector().create_histogram(name, **kwargs)

def create_summary(name: str, **kwargs) -> Summary:
    """Create a summary metric"""
    return get_collector().create_summary(name, **kwargs)

def get_metric(name: str):
    """Get a metric by name"""
    return get_collector().get_metric(name)
