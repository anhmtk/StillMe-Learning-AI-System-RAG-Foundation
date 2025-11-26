"""
Metrics Collector for Prometheus Export
Tracks system-wide metrics for monitoring and observability
"""

from typing import Dict, List
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
        
        # Nested Learning metrics
        self._tier_distribution: Dict[str, int] = defaultdict(int)  # L0, L1, L2, L3 counts
        self._tier_update_counts: Dict[str, int] = defaultdict(int)  # Updates per tier
        self._tier_skipped_counts: Dict[str, int] = defaultdict(int)  # Skipped updates per tier
        self._embedding_operations_total = 0
        self._embedding_operations_by_tier: Dict[str, int] = defaultdict(int)
        self._surprise_score_distribution: List[float] = []  # Store recent surprise scores
        self._cycle_count = 0
        
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
    
    # Nested Learning metrics methods
    def update_tier_distribution(self, tier: str, count: int):
        """Update tier distribution count"""
        with self._lock:
            self._tier_distribution[tier] = count
    
    def increment_tier_update(self, tier: str):
        """Increment tier update counter"""
        with self._lock:
            self._tier_update_counts[tier] += 1
    
    def increment_tier_skipped(self, tier: str):
        """Increment tier skipped counter"""
        with self._lock:
            self._tier_skipped_counts[tier] += 1
    
    def increment_embedding_operation(self, tier: str = None):
        """Increment embedding operation counter"""
        with self._lock:
            self._embedding_operations_total += 1
            if tier:
                self._embedding_operations_by_tier[tier] += 1
    
    def add_surprise_score(self, score: float):
        """Add surprise score to distribution (keep last 1000)"""
        with self._lock:
            self._surprise_score_distribution.append(score)
            # Keep only last 1000 scores to prevent memory bloat
            if len(self._surprise_score_distribution) > 1000:
                self._surprise_score_distribution = self._surprise_score_distribution[-1000:]
    
    def set_cycle_count(self, count: int):
        """Set current learning cycle count"""
        with self._lock:
            self._cycle_count = count
    
    def get_metrics(self) -> Dict:
        """Get current metrics snapshot"""
        with self._lock:
            # Calculate surprise score statistics
            surprise_stats = {}
            if self._surprise_score_distribution:
                sorted_scores = sorted(self._surprise_score_distribution)
                surprise_stats = {
                    "count": len(self._surprise_score_distribution),
                    "min": min(sorted_scores),
                    "max": max(sorted_scores),
                    "avg": sum(sorted_scores) / len(sorted_scores),
                    "median": sorted_scores[len(sorted_scores) // 2] if sorted_scores else 0.0
                }
            
            return {
                "request_counters": dict(self._request_counters),
                "error_counters": dict(self._error_counters),
                "component_health": dict(self._component_health),
                "knowledge_items_total": self._knowledge_items_total,
                "validation_passed_total": self._validation_passed_total,
                "validation_failed_total": self._validation_failed_total,
                # Nested Learning metrics
                "nested_learning": {
                    "tier_distribution": dict(self._tier_distribution),
                    "tier_update_counts": dict(self._tier_update_counts),
                    "tier_skipped_counts": dict(self._tier_skipped_counts),
                    "embedding_operations_total": self._embedding_operations_total,
                    "embedding_operations_by_tier": dict(self._embedding_operations_by_tier),
                    "surprise_score_stats": surprise_stats,
                    "cycle_count": self._cycle_count
                },
                # External Data metrics (if available)
                "external_data": self._get_external_data_metrics()
            }
    
    def _get_external_data_metrics(self) -> Dict:
        """Get external data metrics"""
        try:
            from backend.external_data.rate_limit_tracker import get_rate_limit_tracker
            tracker = get_rate_limit_tracker()
            return tracker.get_stats()
        except Exception:
            return {}


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    return _metrics_collector

