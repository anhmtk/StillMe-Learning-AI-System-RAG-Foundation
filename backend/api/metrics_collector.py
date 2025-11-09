"""
Metrics Collector for Prometheus Export
Tracks system-wide metrics for monitoring and observability
"""

from typing import Dict
from collections import defaultdict
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Thread-safe metrics collector for Prometheus export.
    Tracks request counts, error rates, and component health.
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self._lock = Lock()
        
        # Request counters
        self._request_counters: Dict[str, int] = defaultdict(int)
        self._error_counters: Dict[str, int] = defaultdict(int)
        
        # Component health (0 = down, 1 = up)
        self._component_health: Dict[str, int] = {
            "rag_initialized": 0,
            "chromadb_available": 0,
            "embedding_service_ready": 0,
            "knowledge_retention_ready": 0
        }
        
        # Learning metrics
        self._knowledge_items_total = 0
        self._validation_passed_total = 0
        self._validation_failed_total = 0
        
    def increment_request(self, method: str, endpoint: str, status_code: int = 200):
        """
        Increment request counter
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path
            status_code: HTTP status code
        """
        with self._lock:
            key = f"{method}:{endpoint}"
            self._request_counters[key] += 1
            
            if status_code >= 400:
                error_key = f"{method}:{endpoint}:{status_code}"
                self._error_counters[error_key] += 1
    
    def set_component_health(self, component: str, healthy: bool):
        """
        Update component health status
        
        Args:
            component: Component name (rag_initialized, chromadb_available, etc.)
            healthy: True if healthy, False otherwise
        """
        with self._lock:
            if component in self._component_health:
                self._component_health[component] = 1 if healthy else 0
    
    def set_knowledge_items_total(self, count: int):
        """Set total knowledge items count"""
        with self._lock:
            self._knowledge_items_total = count
    
    def increment_validation(self, passed: bool):
        """Increment validation counter"""
        with self._lock:
            if passed:
                self._validation_passed_total += 1
            else:
                self._validation_failed_total += 1
    
    def get_metrics(self) -> Dict:
        """Get current metrics snapshot"""
        with self._lock:
            return {
                "request_counters": dict(self._request_counters),
                "error_counters": dict(self._error_counters),
                "component_health": dict(self._component_health),
                "knowledge_items_total": self._knowledge_items_total,
                "validation_passed_total": self._validation_passed_total,
                "validation_failed_total": self._validation_failed_total
            }


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    return _metrics_collector

