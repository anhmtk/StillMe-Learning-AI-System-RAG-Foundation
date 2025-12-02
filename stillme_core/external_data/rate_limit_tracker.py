"""
Rate limit tracking for external data APIs

Tracks API call rates to prevent exceeding API limits.
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitTracker:
    """
    Tracks rate limits for external data providers
    
    Tracks calls per provider and enforces rate limits based on
    provider-specific configurations.
    """
    
    def __init__(self):
        """Initialize rate limit tracker"""
        self._lock = Lock()
        
        # Track calls per provider: {provider_name: [timestamps]}
        self._call_history: Dict[str, list] = defaultdict(list)
        
        # Rate limit configs per provider (calls per window)
        self._rate_limits: Dict[str, Dict[str, int]] = {
            "Open-Meteo": {
                "max_calls": 10000,  # 10k/day
                "window_seconds": 86400,  # 24 hours
            },
            "GNews": {
                "max_calls": 100,  # 100/day
                "window_seconds": 86400,  # 24 hours
            },
        }
        
        # Track rate limit violations
        self._violations: Dict[str, int] = defaultdict(int)
    
    def can_make_request(self, provider_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if a request can be made without exceeding rate limit
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Tuple of (can_make_request, error_message)
        """
        with self._lock:
            # Get rate limit config for provider
            config = self._rate_limits.get(provider_name)
            if not config:
                # No rate limit configured - allow request
                return True, None
            
            max_calls = config["max_calls"]
            window_seconds = config["window_seconds"]
            
            # Clean old timestamps outside window
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            call_history = self._call_history[provider_name]
            call_history[:] = [ts for ts in call_history if ts > cutoff_time]
            
            # Check if we're at the limit
            if len(call_history) >= max_calls:
                # Calculate when next request can be made
                oldest_call = min(call_history) if call_history else current_time
                next_available = oldest_call + window_seconds
                wait_seconds = max(0, next_available - current_time)
                
                error_msg = (
                    f"Rate limit exceeded for {provider_name}. "
                    f"{len(call_history)}/{max_calls} calls used in last {window_seconds}s. "
                    f"Next request available in {wait_seconds:.0f}s."
                )
                
                self._violations[provider_name] += 1
                logger.warning(error_msg)
                
                return False, error_msg
            
            return True, None
    
    def record_call(self, provider_name: str):
        """
        Record an API call for rate limit tracking
        
        Args:
            provider_name: Name of the provider
        """
        with self._lock:
            current_time = time.time()
            self._call_history[provider_name].append(current_time)
            logger.debug(f"Recorded API call for {provider_name}")
    
    def get_stats(self, provider_name: Optional[str] = None) -> Dict:
        """
        Get rate limit statistics
        
        Args:
            provider_name: Optional provider name to get stats for specific provider
            
        Returns:
            Dictionary with rate limit statistics
        """
        with self._lock:
            current_time = time.time()
            
            if provider_name:
                # Stats for specific provider
                config = self._rate_limits.get(provider_name, {})
                call_history = self._call_history[provider_name]
                
                # Clean old timestamps
                window_seconds = config.get("window_seconds", 86400)
                cutoff_time = current_time - window_seconds
                call_history = [ts for ts in call_history if ts > cutoff_time]
                
                return {
                    "provider": provider_name,
                    "calls_in_window": len(call_history),
                    "max_calls": config.get("max_calls", 0),
                    "window_seconds": window_seconds,
                    "violations": self._violations.get(provider_name, 0),
                }
            else:
                # Stats for all providers
                stats = {}
                for prov_name in self._rate_limits.keys():
                    stats[prov_name] = self.get_stats(prov_name)
                return stats
    
    def configure_rate_limit(
        self,
        provider_name: str,
        max_calls: int,
        window_seconds: int
    ):
        """
        Configure rate limit for a provider
        
        Args:
            provider_name: Name of the provider
            max_calls: Maximum calls allowed in window
            window_seconds: Time window in seconds
        """
        with self._lock:
            self._rate_limits[provider_name] = {
                "max_calls": max_calls,
                "window_seconds": window_seconds,
            }
            logger.info(
                f"Configured rate limit for {provider_name}: "
                f"{max_calls} calls per {window_seconds}s"
            )


# Global rate limit tracker instance
_rate_limit_tracker: Optional[RateLimitTracker] = None


def get_rate_limit_tracker() -> RateLimitTracker:
    """Get global rate limit tracker instance"""
    global _rate_limit_tracker
    if _rate_limit_tracker is None:
        _rate_limit_tracker = RateLimitTracker()
    return _rate_limit_tracker

