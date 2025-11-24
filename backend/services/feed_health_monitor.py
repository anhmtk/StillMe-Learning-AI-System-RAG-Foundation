"""
Feed Health Monitoring Service
Monitors RSS feed health and automatically replaces failing feeds
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class FeedHealthRecord:
    """Health record for a single feed"""
    feed_url: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    circuit_breaker_state: str = "closed"  # closed, open, half_open
    total_requests: int = 0
    failure_rate: float = 0.0
    last_error: Optional[str] = None
    
    def update_success(self):
        """Update record on successful fetch"""
        self.success_count += 1
        self.total_requests += 1
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        self.failure_rate = (self.failure_count / self.total_requests * 100) if self.total_requests > 0 else 0.0
    
    def update_failure(self, error: Optional[str] = None):
        """Update record on failed fetch"""
        self.failure_count += 1
        self.total_requests += 1
        self.last_failure = datetime.now()
        self.consecutive_failures += 1
        self.failure_rate = (self.failure_count / self.total_requests * 100) if self.total_requests > 0 else 0.0
        if error:
            self.last_error = error
    
    def update_circuit_breaker_state(self, state: str):
        """Update circuit breaker state"""
        self.circuit_breaker_state = state
    
    def is_unhealthy(self, threshold_failure_rate: float = 50.0, threshold_consecutive: int = 10) -> bool:
        """Check if feed is unhealthy"""
        # Unhealthy if:
        # 1. Failure rate > threshold (default 50%)
        # 2. Consecutive failures > threshold (default 10)
        # 3. Circuit breaker is open
        # 4. No success in last 24 hours (if we have requests)
        if self.circuit_breaker_state == "open":
            return True
        if self.failure_rate > threshold_failure_rate and self.total_requests >= 5:
            return True
        if self.consecutive_failures >= threshold_consecutive:
            return True
        if self.last_success and (datetime.now() - self.last_success).total_seconds() > 86400:
            # No success in 24 hours
            if self.total_requests >= 3:  # Only if we've tried at least 3 times
                return True
        return False
    
    def get_health_score(self) -> float:
        """Get health score (0.0-1.0, higher is better)"""
        if self.total_requests == 0:
            return 1.0  # No data yet, assume healthy
        
        # Base score from success rate
        success_rate = (self.success_count / self.total_requests) if self.total_requests > 0 else 0.0
        
        # Penalty for circuit breaker being open
        if self.circuit_breaker_state == "open":
            success_rate *= 0.1  # Heavy penalty
        elif self.circuit_breaker_state == "half_open":
            success_rate *= 0.5  # Moderate penalty
        
        # Penalty for consecutive failures
        if self.consecutive_failures > 0:
            penalty = min(self.consecutive_failures / 10.0, 0.5)  # Max 50% penalty
            success_rate *= (1.0 - penalty)
        
        return max(0.0, min(1.0, success_rate))


class FeedHealthMonitor:
    """Monitor RSS feed health and manage replacements"""
    
    def __init__(self, unhealthy_threshold_failure_rate: float = 50.0, unhealthy_threshold_consecutive: int = 10):
        """Initialize feed health monitor
        
        Args:
            unhealthy_threshold_failure_rate: Failure rate threshold for unhealthy (default: 50%)
            unhealthy_threshold_consecutive: Consecutive failures threshold (default: 10)
        """
        self.health_records: Dict[str, FeedHealthRecord] = {}
        self.unhealthy_threshold_failure_rate = unhealthy_threshold_failure_rate
        self.unhealthy_threshold_consecutive = unhealthy_threshold_consecutive
        self.replacement_history: List[Dict[str, Any]] = []
        logger.info("Feed Health Monitor initialized")
    
    def record_success(self, feed_url: str):
        """Record successful feed fetch"""
        if feed_url not in self.health_records:
            self.health_records[feed_url] = FeedHealthRecord(feed_url=feed_url)
        self.health_records[feed_url].update_success()
    
    def record_failure(self, feed_url: str, error: Optional[str] = None):
        """Record failed feed fetch"""
        if feed_url not in self.health_records:
            self.health_records[feed_url] = FeedHealthRecord(feed_url=feed_url)
        self.health_records[feed_url].update_failure(error)
    
    def update_circuit_breaker_state(self, feed_url: str, state: str):
        """Update circuit breaker state for a feed"""
        if feed_url not in self.health_records:
            self.health_records[feed_url] = FeedHealthRecord(feed_url=feed_url)
        self.health_records[feed_url].update_circuit_breaker_state(state)
    
    def get_unhealthy_feeds(self) -> List[str]:
        """Get list of unhealthy feed URLs"""
        unhealthy = []
        for feed_url, record in self.health_records.items():
            if record.is_unhealthy(
                threshold_failure_rate=self.unhealthy_threshold_failure_rate,
                threshold_consecutive=self.unhealthy_threshold_consecutive
            ):
                unhealthy.append(feed_url)
        return unhealthy
    
    def get_feed_health(self, feed_url: str) -> Optional[Dict[str, Any]]:
        """Get health information for a specific feed"""
        if feed_url not in self.health_records:
            return None
        
        record = self.health_records[feed_url]
        return {
            "feed_url": feed_url,
            "health_score": record.get_health_score(),
            "is_unhealthy": record.is_unhealthy(
                threshold_failure_rate=self.unhealthy_threshold_failure_rate,
                threshold_consecutive=self.unhealthy_threshold_consecutive
            ),
            "success_count": record.success_count,
            "failure_count": record.failure_count,
            "total_requests": record.total_requests,
            "failure_rate": record.failure_rate,
            "consecutive_failures": record.consecutive_failures,
            "circuit_breaker_state": record.circuit_breaker_state,
            "last_success": record.last_success.isoformat() if record.last_success else None,
            "last_failure": record.last_failure.isoformat() if record.last_failure else None,
            "last_error": record.last_error
        }
    
    def get_all_health_stats(self) -> Dict[str, Any]:
        """Get health statistics for all feeds"""
        total_feeds = len(self.health_records)
        unhealthy_feeds = self.get_unhealthy_feeds()
        healthy_feeds = [url for url in self.health_records.keys() if url not in unhealthy_feeds]
        
        # Calculate average health score
        health_scores = [record.get_health_score() for record in self.health_records.values()]
        avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 1.0
        
        # Group by circuit breaker state
        by_state = defaultdict(int)
        for record in self.health_records.values():
            by_state[record.circuit_breaker_state] += 1
        
        return {
            "total_feeds": total_feeds,
            "healthy_feeds": len(healthy_feeds),
            "unhealthy_feeds": len(unhealthy_feeds),
            "average_health_score": round(avg_health_score, 3),
            "unhealthy_feed_urls": unhealthy_feeds,
            "circuit_breaker_states": dict(by_state),
            "replacement_count": len(self.replacement_history)
        }
    
    def suggest_replacements(self, unhealthy_feeds: List[str], alternative_feeds: Dict[str, List[str]]) -> Dict[str, str]:
        """Suggest replacement feeds for unhealthy feeds
        
        Args:
            unhealthy_feeds: List of unhealthy feed URLs
            alternative_feeds: Dictionary mapping feed URLs to alternative URLs
            
        Returns:
            Dictionary mapping unhealthy feed URL to suggested replacement
        """
        suggestions = {}
        for feed_url in unhealthy_feeds:
            if feed_url in alternative_feeds:
                alternatives = alternative_feeds[feed_url]
                # Choose first alternative that's not also unhealthy
                for alt_url in alternatives:
                    if alt_url not in unhealthy_feeds:
                        suggestions[feed_url] = alt_url
                        break
        return suggestions
    
    def record_replacement(self, old_feed: str, new_feed: str, reason: str):
        """Record a feed replacement"""
        self.replacement_history.append({
            "old_feed": old_feed,
            "new_feed": new_feed,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Feed replacement recorded: {old_feed} → {new_feed} (reason: {reason})")
    
    def get_replacement_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get feed replacement history"""
        return self.replacement_history[-limit:]


# Global feed health monitor instance
_feed_health_monitor: Optional[FeedHealthMonitor] = None


def get_feed_health_monitor() -> FeedHealthMonitor:
    """Get global feed health monitor instance"""
    global _feed_health_monitor
    if _feed_health_monitor is None:
        _feed_health_monitor = FeedHealthMonitor()
    return _feed_health_monitor

