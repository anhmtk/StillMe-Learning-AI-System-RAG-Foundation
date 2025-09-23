#!/usr/bin/env python3
"""
Web Metrics - Performance and Usage Tracking
Tracks web access metrics, performance, and usage patterns
"""
import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class RequestMetric:
    """Individual request metric"""
    timestamp: datetime
    tool_name: str
    success: bool
    latency_ms: float
    cache_hit: bool
    domain: str
    error_type: Optional[str] = None
    response_size_bytes: int = 0

@dataclass
class WebMetricsSummary:
    """Web metrics summary"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    total_latency_ms: float
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float
    total_response_size_bytes: int
    average_response_size_bytes: float
    top_domains: List[Tuple[str, int]]
    top_tools: List[Tuple[str, int]]
    error_types: Dict[str, int]
    requests_by_hour: Dict[int, int]
    period_start: datetime
    period_end: datetime

class WebMetricsCollector:
    """Collects and analyzes web access metrics"""
    
    def __init__(self, log_file: str = "logs/web_metrics.log", 
                 summary_interval_minutes: int = 5):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Metrics storage
        self._metrics: deque = deque(maxlen=10000)  # Keep last 10k requests
        self._lock = threading.RLock()
        
        # Summary tracking
        self._summary_interval = summary_interval_minutes
        self._last_summary_time = datetime.now()
        
        # Real-time counters
        self._counters = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_latency_ms': 0.0,
            'total_response_size_bytes': 0
        }
        
        # Domain and tool tracking
        self._domain_counts = defaultdict(int)
        self._tool_counts = defaultdict(int)
        self._error_types = defaultdict(int)
        
        # Hourly tracking
        self._hourly_requests = defaultdict(int)
        
        # Start summary thread
        self._summary_thread = threading.Thread(target=self._periodic_summary, daemon=True)
        self._summary_thread.start()
        
        logger.info(f"📊 Web Metrics Collector initialized: log_file={log_file}")
    
    def record_request(self, tool_name: str, success: bool, latency_ms: float,
                      cache_hit: bool, domain: str, error_type: Optional[str] = None,
                      response_size_bytes: int = 0) -> None:
        """Record a web request metric"""
        with self._lock:
            metric = RequestMetric(
                timestamp=datetime.now(),
                tool_name=tool_name,
                success=success,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                domain=domain,
                error_type=error_type,
                response_size_bytes=response_size_bytes
            )
            
            # Add to metrics
            self._metrics.append(metric)
            
            # Update counters
            self._counters['total_requests'] += 1
            self._counters['total_latency_ms'] += latency_ms
            self._counters['total_response_size_bytes'] += response_size_bytes
            
            if success:
                self._counters['successful_requests'] += 1
            else:
                self._counters['failed_requests'] += 1
            
            if cache_hit:
                self._counters['cache_hits'] += 1
            else:
                self._counters['cache_misses'] += 1
            
            # Update domain and tool counts
            self._domain_counts[domain] += 1
            self._tool_counts[tool_name] += 1
            
            if error_type:
                self._error_types[error_type] += 1
            
            # Update hourly tracking
            current_hour = datetime.now().hour
            self._hourly_requests[current_hour] += 1
            
            logger.debug(f"📊 Recorded metric: {tool_name} - {latency_ms:.1f}ms - {'SUCCESS' if success else 'FAIL'}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self._lock:
            total_requests = self._counters['total_requests']
            
            if total_requests == 0:
                return {
                    'total_requests': 0,
                    'success_rate': 0.0,
                    'average_latency_ms': 0.0,
                    'cache_hit_ratio': 0.0,
                    'top_domains': [],
                    'top_tools': []
                }
            
            success_rate = self._counters['successful_requests'] / total_requests
            average_latency = self._counters['total_latency_ms'] / total_requests
            
            cache_total = self._counters['cache_hits'] + self._counters['cache_misses']
            cache_hit_ratio = self._counters['cache_hits'] / cache_total if cache_total > 0 else 0.0
            
            # Get top domains and tools
            top_domains = sorted(self._domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_tools = sorted(self._tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_requests': total_requests,
                'successful_requests': self._counters['successful_requests'],
                'failed_requests': self._counters['failed_requests'],
                'success_rate': success_rate,
                'average_latency_ms': average_latency,
                'cache_hit_ratio': cache_hit_ratio,
                'total_response_size_bytes': self._counters['total_response_size_bytes'],
                'top_domains': top_domains,
                'top_tools': top_tools,
                'error_types': dict(self._error_types),
                'hourly_requests': dict(self._hourly_requests)
            }
    
    def get_summary(self, period_hours: int = 1) -> WebMetricsSummary:
        """Get detailed summary for a time period"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=period_hours)
            
            # Filter metrics for the period
            period_metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
            
            if not period_metrics:
                return WebMetricsSummary(
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    success_rate=0.0,
                    total_latency_ms=0.0,
                    average_latency_ms=0.0,
                    p50_latency_ms=0.0,
                    p95_latency_ms=0.0,
                    cache_hits=0,
                    cache_misses=0,
                    cache_hit_ratio=0.0,
                    total_response_size_bytes=0,
                    average_response_size_bytes=0.0,
                    top_domains=[],
                    top_tools=[],
                    error_types={},
                    requests_by_hour={},
                    period_start=cutoff_time,
                    period_end=datetime.now()
                )
            
            # Calculate statistics
            total_requests = len(period_metrics)
            successful_requests = sum(1 for m in period_metrics if m.success)
            failed_requests = total_requests - successful_requests
            success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
            
            latencies = [m.latency_ms for m in period_metrics]
            total_latency_ms = sum(latencies)
            average_latency_ms = total_latency_ms / total_requests if total_requests > 0 else 0.0
            p50_latency_ms = statistics.median(latencies) if latencies else 0.0
            p95_latency_ms = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0.0
            
            cache_hits = sum(1 for m in period_metrics if m.cache_hit)
            cache_misses = total_requests - cache_hits
            cache_hit_ratio = cache_hits / total_requests if total_requests > 0 else 0.0
            
            total_response_size_bytes = sum(m.response_size_bytes for m in period_metrics)
            average_response_size_bytes = total_response_size_bytes / total_requests if total_requests > 0 else 0.0
            
            # Top domains and tools
            domain_counts = defaultdict(int)
            tool_counts = defaultdict(int)
            error_types = defaultdict(int)
            hourly_counts = defaultdict(int)
            
            for metric in period_metrics:
                domain_counts[metric.domain] += 1
                tool_counts[metric.tool_name] += 1
                if metric.error_type:
                    error_types[metric.error_type] += 1
                hourly_counts[metric.timestamp.hour] += 1
            
            top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return WebMetricsSummary(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=success_rate,
                total_latency_ms=total_latency_ms,
                average_latency_ms=average_latency_ms,
                p50_latency_ms=p50_latency_ms,
                p95_latency_ms=p95_latency_ms,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_hit_ratio=cache_hit_ratio,
                total_response_size_bytes=total_response_size_bytes,
                average_response_size_bytes=average_response_size_bytes,
                top_domains=top_domains,
                top_tools=top_tools,
                error_types=dict(error_types),
                requests_by_hour=dict(hourly_counts),
                period_start=cutoff_time,
                period_end=datetime.now()
            )
    
    def _periodic_summary(self) -> None:
        """Periodically write summary to log file"""
        while True:
            try:
                time.sleep(self._summary_interval * 60)  # Convert minutes to seconds
                
                summary = self.get_summary(period_hours=1)  # Last hour
                self._write_summary_log(summary)
                
            except Exception as e:
                logger.error(f"❌ Metrics summary error: {e}")
    
    def _write_summary_log(self, summary: WebMetricsSummary) -> None:
        """Write summary to log file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "metrics_summary",
                "summary": asdict(summary)
            }
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + '\n')
            
            logger.info(f"📊 Metrics summary written: {summary.total_requests} requests, "
                       f"{summary.success_rate:.1%} success rate, "
                       f"{summary.cache_hit_ratio:.1%} cache hit ratio")
            
        except Exception as e:
            logger.error(f"❌ Failed to write metrics summary: {e}")
    
    def export_metrics(self, period_hours: int = 24) -> Dict[str, Any]:
        """Export metrics data for analysis"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=period_hours)
            period_metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
            
            return {
                "export_timestamp": datetime.now().isoformat(),
                "period_hours": period_hours,
                "total_metrics": len(period_metrics),
                "summary": asdict(self.get_summary(period_hours)),
                "raw_metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "tool_name": m.tool_name,
                        "success": m.success,
                        "latency_ms": m.latency_ms,
                        "cache_hit": m.cache_hit,
                        "domain": m.domain,
                        "error_type": m.error_type,
                        "response_size_bytes": m.response_size_bytes
                    }
                    for m in period_metrics
                ]
            }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._metrics.clear()
            self._counters = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'total_latency_ms': 0.0,
                'total_response_size_bytes': 0
            }
            self._domain_counts.clear()
            self._tool_counts.clear()
            self._error_types.clear()
            self._hourly_requests.clear()
            
            logger.info("📊 Metrics reset")
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on metrics"""
        alerts = []
        current_stats = self.get_current_stats()
        
        # Check success rate
        if current_stats['success_rate'] < 0.8:  # Less than 80% success rate
            alerts.append({
                "type": "low_success_rate",
                "severity": "warning",
                "message": f"Low success rate: {current_stats['success_rate']:.1%}",
                "threshold": 0.8,
                "current": current_stats['success_rate']
            })
        
        # Check average latency
        if current_stats['average_latency_ms'] > 10000:  # More than 10 seconds
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"High average latency: {current_stats['average_latency_ms']:.1f}ms",
                "threshold": 10000,
                "current": current_stats['average_latency_ms']
            })
        
        # Check cache hit ratio
        if current_stats['cache_hit_ratio'] < 0.3:  # Less than 30% cache hit ratio
            alerts.append({
                "type": "low_cache_hit_ratio",
                "severity": "info",
                "message": f"Low cache hit ratio: {current_stats['cache_hit_ratio']:.1%}",
                "threshold": 0.3,
                "current": current_stats['cache_hit_ratio']
            })
        
        return alerts

# Global metrics collector
web_metrics = WebMetricsCollector()

# Export functions
def record_request(tool_name: str, success: bool, latency_ms: float,
                  cache_hit: bool, domain: str, error_type: Optional[str] = None,
                  response_size_bytes: int = 0) -> None:
    """Record a web request metric"""
    web_metrics.record_request(tool_name, success, latency_ms, cache_hit, 
                              domain, error_type, response_size_bytes)

def get_current_stats() -> Dict[str, Any]:
    """Get current statistics"""
    return web_metrics.get_current_stats()

def get_summary(period_hours: int = 1) -> WebMetricsSummary:
    """Get detailed summary"""
    return web_metrics.get_summary(period_hours)

def export_metrics(period_hours: int = 24) -> Dict[str, Any]:
    """Export metrics data"""
    return web_metrics.export_metrics(period_hours)

def reset_metrics() -> None:
    """Reset all metrics"""
    web_metrics.reset_metrics()

def get_performance_alerts() -> List[Dict[str, Any]]:
    """Get performance alerts"""
    return web_metrics.get_performance_alerts()

if __name__ == "__main__":
    # Test metrics collection
    print("📊 Testing Web Metrics...")
    
    # Record some test metrics
    record_request("web.search_news", True, 1500.0, False, "newsapi.org", None, 2048)
    record_request("web.search_news", True, 200.0, True, "newsapi.org", None, 2048)
    record_request("web.github_trending", True, 3000.0, False, "api.github.com", None, 4096)
    record_request("web.hackernews_top", False, 5000.0, False, "hn.algolia.com", "timeout", 0)
    
    # Get current stats
    stats = get_current_stats()
    print(f"Current stats: {stats['total_requests']} requests, {stats['success_rate']:.1%} success rate")
    
    # Get summary
    summary = get_summary(period_hours=1)
    print(f"Summary: {summary.total_requests} requests, {summary.average_latency_ms:.1f}ms avg latency")
    
    # Get alerts
    alerts = get_performance_alerts()
    print(f"Alerts: {len(alerts)}")
    
    # Export metrics
    exported = export_metrics(period_hours=1)
    print(f"Exported: {exported['total_metrics']} metrics")
    
    print("✅ Web Metrics test completed")
