# metrics/web_metrics.py
# Web metrics collection
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class WebRequest:
    """Web request data"""
    url: str
    method: str
    status_code: int
    response_time: float
    timestamp: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

@dataclass
class WebMetrics:
    """Web metrics data"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    requests_per_minute: float = 0.0
    error_rate: float = 0.0

class WebMetricsCollector:
    """Web metrics collector for monitoring web traffic and performance"""

    def __init__(self):
        self.logger = logger
        self.requests: List[WebRequest] = []
        self.metrics_cache: Optional[WebMetrics] = None
        self.cache_timestamp = 0
        self.cache_duration = 60  # Cache for 1 minute

    def record_request(self, url: str, method: str, status_code: int,
                      response_time: float, user_agent: str = None,
                      ip_address: str = None) -> None:
        """Record a web request"""
        request = WebRequest(
            url=url,
            method=method.upper(),
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now().isoformat(),
            user_agent=user_agent,
            ip_address=ip_address
        )

        self.requests.append(request)
        self.logger.debug(f"Recorded request: {method} {url} - {status_code} ({response_time:.3f}s)")

        # Invalidate cache
        self.metrics_cache = None

    def get_metrics(self, force_refresh: bool = False) -> WebMetrics:
        """Get current web metrics"""
        current_time = time.time()

        # Return cached metrics if still valid
        if (not force_refresh and
            self.metrics_cache and
            current_time - self.cache_timestamp < self.cache_duration):
            return self.metrics_cache

        # Calculate fresh metrics
        if not self.requests:
            return WebMetrics()

        total_requests = len(self.requests)
        successful_requests = len([r for r in self.requests if 200 <= r.status_code < 300])
        failed_requests = total_requests - successful_requests

        response_times = [r.response_time for r in self.requests]
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)

        # Calculate requests per minute (last 60 seconds)
        recent_requests = [r for r in self.requests
                          if (datetime.now() - datetime.fromisoformat(r.timestamp)).seconds < 60]
        requests_per_minute = len(recent_requests)

        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0.0

        self.metrics_cache = WebMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=round(avg_response_time, 3),
            min_response_time=round(min_response_time, 3),
            max_response_time=round(max_response_time, 3),
            requests_per_minute=requests_per_minute,
            error_rate=round(error_rate, 2)
        )

        self.cache_timestamp = current_time
        return self.metrics_cache

    def get_requests_by_status(self, status_code: int) -> List[WebRequest]:
        """Get requests filtered by status code"""
        return [r for r in self.requests if r.status_code == status_code]

    def get_requests_by_method(self, method: str) -> List[WebRequest]:
        """Get requests filtered by HTTP method"""
        return [r for r in self.requests if r.method == method.upper()]

    def get_requests_by_url_pattern(self, pattern: str) -> List[WebRequest]:
        """Get requests filtered by URL pattern"""
        return [r for r in self.requests if pattern.lower() in r.url.lower()]

    def get_slow_requests(self, threshold: float = 1.0) -> List[WebRequest]:
        """Get requests that took longer than threshold seconds"""
        return [r for r in self.requests if r.response_time > threshold]

    def get_error_requests(self) -> List[WebRequest]:
        """Get requests that resulted in errors (4xx, 5xx)"""
        return [r for r in self.requests if r.status_code >= 400]

    def get_popular_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular endpoints"""
        url_counts = {}
        for request in self.requests:
            url_counts[request.url] = url_counts.get(request.url, 0) + 1

        # Sort by count descending
        sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"url": url, "count": count} for url, count in sorted_urls[:limit]]

    def get_user_agent_stats(self) -> Dict[str, int]:
        """Get user agent statistics"""
        ua_counts = {}
        for request in self.requests:
            if request.user_agent:
                ua_counts[request.user_agent] = ua_counts.get(request.user_agent, 0) + 1

        return ua_counts

    def export_metrics(self, format: str = "dict") -> Dict[str, Any]:
        """Export metrics in various formats"""
        metrics = self.get_metrics()

        if format == "dict":
            return {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "avg_response_time": metrics.avg_response_time,
                "min_response_time": metrics.min_response_time,
                "max_response_time": metrics.max_response_time,
                "requests_per_minute": metrics.requests_per_minute,
                "error_rate": metrics.error_rate,
                "popular_endpoints": self.get_popular_endpoints(5),
                "slow_requests_count": len(self.get_slow_requests()),
                "error_requests_count": len(self.get_error_requests())
            }
        else:
            return {"error": f"Unsupported format: {format}"}

    def reset_metrics(self):
        """Reset all collected metrics"""
        self.requests.clear()
        self.metrics_cache = None
        self.cache_timestamp = 0
        self.logger.info("Web metrics reset")

    def cleanup_old_requests(self, max_age_hours: int = 24):
        """Remove requests older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        initial_count = len(self.requests)
        self.requests = [r for r in self.requests
                        if datetime.fromisoformat(r.timestamp).timestamp() > cutoff_time]

        removed_count = initial_count - len(self.requests)
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old requests")
            self.metrics_cache = None  # Invalidate cache

# Global instance for backward compatibility
_global_collector = WebMetricsCollector()

def web_metrics() -> WebMetrics:
    """Get current web metrics (global function)"""
    return _global_collector.get_metrics()

def record_request(url: str, method: str, status_code: int,
                  response_time: float, user_agent: str = None,
                  ip_address: str = None) -> None:
    """Record a web request (global function)"""
    _global_collector.record_request(url, method, status_code, response_time, user_agent, ip_address)

def get_web_metrics() -> WebMetrics:
    """Alias for web_metrics()"""
    return web_metrics()

def reset_web_metrics() -> None:
    """Reset global web metrics"""
    _global_collector.reset_metrics()

def export_web_metrics(format: str = "dict") -> Dict[str, Any]:
    """Export global web metrics"""
    return _global_collector.export_metrics(format)