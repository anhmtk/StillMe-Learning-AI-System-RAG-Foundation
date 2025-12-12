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
class FeedQualityMetrics:
    """Quality metrics for a feed"""
    feed_url: str
    avg_importance_score: float = 0.0
    high_quality_items: int = 0  # importance > 0.7
    low_quality_items: int = 0   # importance < 0.3
    total_items_processed: int = 0
    duplicate_rate: float = 0.0
    freshness_score: float = 0.0  # Average freshness of items
    
    def update_quality(self, importance_score: float, is_duplicate: bool = False, freshness: float = 0.0):
        """Update quality metrics"""
        self.total_items_processed += 1
        # Update average importance (moving average)
        if self.total_items_processed == 1:
            self.avg_importance_score = importance_score
        else:
            # Exponential moving average (weight new items more)
            self.avg_importance_score = (self.avg_importance_score * 0.9) + (importance_score * 0.1)
        
        # Track quality buckets
        if importance_score > 0.7:
            self.high_quality_items += 1
        elif importance_score < 0.3:
            self.low_quality_items += 1
        
        # Update duplicate rate
        if is_duplicate:
            self.duplicate_rate = (self.duplicate_rate * 0.9) + (1.0 * 0.1)
        else:
            self.duplicate_rate = (self.duplicate_rate * 0.9) + (0.0 * 0.1)
        
        # Update freshness (moving average)
        if freshness > 0:
            if self.freshness_score == 0.0:
                self.freshness_score = freshness
            else:
                self.freshness_score = (self.freshness_score * 0.9) + (freshness * 0.1)


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
    avg_response_time: float = 0.0  # Average response time in seconds
    quality_metrics: FeedQualityMetrics = None
    
    def __post_init__(self):
        """Initialize quality metrics"""
        if self.quality_metrics is None:
            self.quality_metrics = FeedQualityMetrics(feed_url=self.feed_url)
    
    def update_success(self, response_time: Optional[float] = None):
        """Update record on successful fetch"""
        self.success_count += 1
        self.total_requests += 1
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        self.failure_rate = (self.failure_count / self.total_requests * 100) if self.total_requests > 0 else 0.0
        
        # Update response time (moving average)
        if response_time is not None:
            if self.avg_response_time == 0.0:
                self.avg_response_time = response_time
            else:
                self.avg_response_time = (self.avg_response_time * 0.9) + (response_time * 0.1)
    
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
    
    def record_success(self, feed_url: str, response_time: Optional[float] = None):
        """Record successful feed fetch"""
        if feed_url not in self.health_records:
            self.health_records[feed_url] = FeedHealthRecord(feed_url=feed_url)
        self.health_records[feed_url].update_success(response_time=response_time)
    
    def track_feed_quality(self, feed_url: str, importance_score: float, is_duplicate: bool = False, freshness: float = 0.0):
        """Track quality metrics for a feed entry"""
        if feed_url not in self.health_records:
            self.health_records[feed_url] = FeedHealthRecord(feed_url=feed_url)
        self.health_records[feed_url].quality_metrics.update_quality(
            importance_score=importance_score,
            is_duplicate=is_duplicate,
            freshness=freshness
        )
    
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
    
    def get_feeds_to_disable(self, days_threshold: int = 3) -> List[str]:
        """
        P4: Get feeds that should be auto-disabled (failed for N consecutive days)
        
        Args:
            days_threshold: Number of consecutive days of failure before disabling (default: 3)
            
        Returns:
            List of feed URLs that should be disabled
        """
        feeds_to_disable = []
        now = datetime.now()
        
        for feed_url, record in self.health_records.items():
            # Check if feed has been failing for N consecutive days
            if record.last_failure and not record.last_success:
                # Never succeeded, check if failing for N days
                days_failing = (now - record.last_failure).days
                if days_failing >= days_threshold and record.total_requests >= days_threshold:
                    feeds_to_disable.append(feed_url)
                    logger.warning(
                        f"P4: Feed {feed_url[:50]}... has been failing for {days_failing} days "
                        f"(threshold: {days_threshold}) - should be disabled"
                    )
            elif record.last_failure and record.last_success:
                # Has succeeded before, check if last success was before last failure
                if record.last_failure > record.last_success:
                    days_failing = (now - record.last_failure).days
                    if days_failing >= days_threshold:
                        feeds_to_disable.append(feed_url)
                        logger.warning(
                            f"P4: Feed {feed_url[:50]}... has been failing for {days_failing} days "
                            f"since last success - should be disabled"
                        )
        
        return feeds_to_disable
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for all feeds
        
        Returns:
            Dictionary with health metrics for all feeds
        """
        report = {
            "total_feeds": len(self.health_records),
            "healthy_feeds": 0,
            "unhealthy_feeds": 0,
            "feeds": []
        }
        
        for feed_url, record in self.health_records.items():
            is_unhealthy = record.is_unhealthy(
                threshold_failure_rate=self.unhealthy_threshold_failure_rate,
                threshold_consecutive=self.unhealthy_threshold_consecutive
            )
            
            if is_unhealthy:
                report["unhealthy_feeds"] += 1
            else:
                report["healthy_feeds"] += 1
            
            feed_info = {
                "feed_url": feed_url,
                "health_score": record.get_health_score(),
                "is_unhealthy": is_unhealthy,
                "success_count": record.success_count,
                "failure_count": record.failure_count,
                "total_requests": record.total_requests,
                "failure_rate": round(record.failure_rate, 2),
                "consecutive_failures": record.consecutive_failures,
                "circuit_breaker_state": record.circuit_breaker_state,
                "last_success": record.last_success.isoformat() if record.last_success else None,
                "last_failure": record.last_failure.isoformat() if record.last_failure else None,
                "last_error": record.last_error,
                "avg_response_time": round(record.avg_response_time, 3),
                "quality_metrics": {
                    "avg_importance_score": round(record.quality_metrics.avg_importance_score, 3),
                    "high_quality_items": record.quality_metrics.high_quality_items,
                    "low_quality_items": record.quality_metrics.low_quality_items,
                    "total_items_processed": record.quality_metrics.total_items_processed,
                    "duplicate_rate": round(record.quality_metrics.duplicate_rate, 3),
                    "freshness_score": round(record.quality_metrics.freshness_score, 3)
                } if record.quality_metrics else None
            }
            report["feeds"].append(feed_info)
        
        return report
    
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
            "last_error": record.last_error,
            "avg_response_time": round(record.avg_response_time, 3),
            "quality_metrics": {
                "avg_importance_score": round(record.quality_metrics.avg_importance_score, 3),
                "high_quality_items": record.quality_metrics.high_quality_items,
                "low_quality_items": record.quality_metrics.low_quality_items,
                "total_items_processed": record.quality_metrics.total_items_processed,
                "duplicate_rate": round(record.quality_metrics.duplicate_rate, 3),
                "freshness_score": round(record.quality_metrics.freshness_score, 3)
            } if record.quality_metrics else None
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
    
    def _detect_feed_domain(self, feed_url: str) -> Optional[str]:
        """
        Detect domain/category of a feed based on URL and historical quality metrics
        
        Args:
            feed_url: Feed URL
            
        Returns:
            Domain name (ethics, transparency, science, philosophy, etc.) or None
        """
        url_lower = feed_url.lower()
        
        # Domain detection based on URL patterns and known feeds
        domain_patterns = {
            "ethics": ["bioethics", "ethics", "ethical"],
            "transparency": ["eff.org", "transparency", "open"],
            "ai_governance": ["governance", "policy", "regulation"],
            "philosophy": ["philosophy", "3ammagazine", "iep.utm.edu"],
            "religion": ["religion", "tricycle", "ncronline", "americamagazine", "commonweal"],
            "science": ["nature.com", "science.org", "phys.org"],
            "history": ["history", "historynet", "bbc.com/history"],
            "psychology": ["psychologicalscience", "apa.org", "psychology"]
        }
        
        for domain, patterns in domain_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                return domain
        
        return None
    
    def suggest_replacements(self, unhealthy_feeds: List[str], alternative_feeds: Optional[Dict[str, List[str]]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Suggest replacement feeds for unhealthy feeds based on domain similarity and quality metrics
        
        Args:
            unhealthy_feeds: List of unhealthy feed URLs
            alternative_feeds: Optional dictionary mapping feed URLs to alternative URLs
            
        Returns:
            Dictionary mapping unhealthy feed URL to replacement suggestion with:
            - suggested_feed: URL of suggested replacement
            - reason: Why this feed was suggested
            - domain_match: Whether domain matches
            - quality_score: Quality score of suggested feed
        """
        suggestions = {}
        
        for feed_url in unhealthy_feeds:
            unhealthy_record = self.health_records.get(feed_url)
            if not unhealthy_record:
                continue
            
            # Detect domain of unhealthy feed
            unhealthy_domain = self._detect_feed_domain(feed_url)
            
            # Find best replacement from healthy feeds
            best_replacement = None
            best_score = 0.0
            best_reason = ""
            
            for candidate_url, candidate_record in self.health_records.items():
                # Skip if candidate is also unhealthy
                if candidate_record.is_unhealthy(
                    threshold_failure_rate=self.unhealthy_threshold_failure_rate,
                    threshold_consecutive=self.unhealthy_threshold_consecutive
                ):
                    continue
                
                # Skip if same feed
                if candidate_url == feed_url:
                    continue
                
                # Calculate replacement score
                score = 0.0
                reasons = []
                
                # Domain match bonus (+0.5)
                candidate_domain = self._detect_feed_domain(candidate_url)
                if unhealthy_domain and candidate_domain == unhealthy_domain:
                    score += 0.5
                    reasons.append("domain_match")
                
                # Quality metrics bonus (+0.3 for high quality)
                if candidate_record.quality_metrics:
                    quality_score = candidate_record.quality_metrics.avg_importance_score
                    if quality_score > 0.6:
                        score += 0.3
                        reasons.append("high_quality")
                    elif quality_score > 0.4:
                        score += 0.2
                        reasons.append("medium_quality")
                
                # Health score bonus (+0.2 for healthy)
                health_score = candidate_record.get_health_score()
                if health_score > 0.8:
                    score += 0.2
                    reasons.append("very_healthy")
                elif health_score > 0.6:
                    score += 0.1
                    reasons.append("healthy")
                
                # Low duplicate rate bonus (+0.1)
                if candidate_record.quality_metrics and candidate_record.quality_metrics.duplicate_rate < 0.1:
                    score += 0.1
                    reasons.append("low_duplicate_rate")
                
                if score > best_score:
                    best_score = score
                    best_replacement = candidate_url
                    best_reason = ", ".join(reasons) if reasons else "general_replacement"
            
            # Check alternative_feeds if provided
            if alternative_feeds and feed_url in alternative_feeds:
                for alt_url in alternative_feeds[feed_url]:
                    # Check if alternative is healthy
                    alt_record = self.health_records.get(alt_url)
                    if alt_record and not alt_record.is_unhealthy(
                        threshold_failure_rate=self.unhealthy_threshold_failure_rate,
                        threshold_consecutive=self.unhealthy_threshold_consecutive
                    ):
                        # Prefer alternative if it exists and is healthy
                        best_replacement = alt_url
                        best_reason = "configured_alternative"
                        break
            
            if best_replacement:
                replacement_record = self.health_records.get(best_replacement)
                suggestions[feed_url] = {
                    "suggested_feed": best_replacement,
                    "reason": best_reason,
                    "domain_match": unhealthy_domain and self._detect_feed_domain(best_replacement) == unhealthy_domain,
                    "quality_score": replacement_record.quality_metrics.avg_importance_score if replacement_record and replacement_record.quality_metrics else 0.0,
                    "health_score": replacement_record.get_health_score() if replacement_record else 0.0
                }
        
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
    
    def get_feed_performance_analytics(self, feed_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feed performance analytics (Phase 3.3)
        
        Args:
            feed_url: Specific feed URL (if None, returns aggregate for all feeds)
            
        Returns:
            Dictionary with performance metrics:
            - items_fetched: Total items fetched from feed
            - items_passed_filter: Items that passed importance threshold
            - items_added_to_rag: Items successfully added to RAG
            - avg_importance_score: Average importance score
            - cost_per_feed: Estimated cost (if available)
        """
        if feed_url:
            # Single feed analytics
            record = self.health_records.get(feed_url)
            if not record:
                return {
                    "feed_url": feed_url,
                    "error": "Feed not found in health records"
                }
            
            quality_metrics = record.quality_metrics
            return {
                "feed_url": feed_url,
                "items_processed": quality_metrics.total_items_processed if quality_metrics else 0,
                "items_passed_filter": quality_metrics.high_quality_items if quality_metrics else 0,
                "items_added_to_rag": quality_metrics.total_items_processed - quality_metrics.low_quality_items if quality_metrics else 0,
                "avg_importance_score": round(quality_metrics.avg_importance_score, 3) if quality_metrics else 0.0,
                "high_quality_items": quality_metrics.high_quality_items if quality_metrics else 0,
                "low_quality_items": quality_metrics.low_quality_items if quality_metrics else 0,
                "duplicate_rate": round(quality_metrics.duplicate_rate, 3) if quality_metrics else 0.0,
                "freshness_score": round(quality_metrics.freshness_score, 3) if quality_metrics else 0.0,
                "success_count": record.success_count,
                "failure_count": record.failure_count,
                "avg_response_time": round(record.avg_response_time, 3),
                "health_score": round(record.get_health_score(), 3)
            }
        else:
            # Aggregate analytics for all feeds
            total_items_processed = 0
            total_high_quality = 0
            total_low_quality = 0
            total_importance_scores = []
            total_success = 0
            total_failures = 0
            total_response_times = []
            
            for record in self.health_records.values():
                if record.quality_metrics:
                    total_items_processed += record.quality_metrics.total_items_processed
                    total_high_quality += record.quality_metrics.high_quality_items
                    total_low_quality += record.quality_metrics.low_quality_items
                    if record.quality_metrics.avg_importance_score > 0:
                        total_importance_scores.append(record.quality_metrics.avg_importance_score)
                
                total_success += record.success_count
                total_failures += record.failure_count
                if record.avg_response_time > 0:
                    total_response_times.append(record.avg_response_time)
            
            avg_importance = sum(total_importance_scores) / len(total_importance_scores) if total_importance_scores else 0.0
            avg_response_time = sum(total_response_times) / len(total_response_times) if total_response_times else 0.0
            
            return {
                "total_feeds": len(self.health_records),
                "total_items_processed": total_items_processed,
                "total_items_passed_filter": total_high_quality,
                "total_items_added_to_rag": total_items_processed - total_low_quality,
                "avg_importance_score": round(avg_importance, 3),
                "total_high_quality_items": total_high_quality,
                "total_low_quality_items": total_low_quality,
                "total_success_count": total_success,
                "total_failure_count": total_failures,
                "avg_response_time": round(avg_response_time, 3),
                "success_rate": round((total_success / (total_success + total_failures) * 100) if (total_success + total_failures) > 0 else 0.0, 2)
            }


# Global feed health monitor instance
_feed_health_monitor: Optional[FeedHealthMonitor] = None


def get_feed_health_monitor() -> FeedHealthMonitor:
    """Get global feed health monitor instance"""
    global _feed_health_monitor
    if _feed_health_monitor is None:
        _feed_health_monitor = FeedHealthMonitor()
    return _feed_health_monitor

