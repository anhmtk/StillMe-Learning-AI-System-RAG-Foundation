"""
Circuit Breaker Pattern Implementation
Prevents cascading failures by stopping requests to failing services
"""

import time
import logging
from typing import Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes (half-open state)
    timeout_seconds: int = 60  # Time to wait before trying half-open
    timeout_window: int = 300  # Time window for counting failures (5 minutes)


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker
        
        Args:
            name: Name of the circuit breaker (e.g., "rss_feed_nature")
            config: Optional configuration (uses defaults if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.failure_times: list = []  # Track failure times for window-based counting
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.opened_at and (datetime.now() - self.opened_at).total_seconds() >= self.config.timeout_seconds:
                logger.info(f"🔄 Circuit breaker {self.name}: Moving to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN - request rejected")
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"✅ Circuit breaker {self.name}: Moving to CLOSED state (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.opened_at = None
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success (service is healthy)
            self.failure_count = 0
            self.failure_times = []
    
    def _on_failure(self):
        """Handle failed call"""
        self.last_failure_time = datetime.now()
        current_time = datetime.now()
        
        # Clean old failures outside time window
        self.failure_times = [
            ft for ft in self.failure_times
            if (current_time - ft).total_seconds() < self.config.timeout_window
        ]
        
        # Add current failure
        self.failure_times.append(current_time)
        self.failure_count = len(self.failure_times)
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state immediately opens circuit
            logger.warning(f"❌ Circuit breaker {self.name}: Moving to OPEN state (failed in half-open)")
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(f"❌ Circuit breaker {self.name}: Moving to OPEN state (failure threshold reached: {self.failure_count})")
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()
    
    def get_state(self) -> dict:
        """Get current circuit breaker state
        
        Returns:
            Dictionary with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "failures_in_window": len(self.failure_times),
            "time_until_retry": max(0, self.config.timeout_seconds - (datetime.now() - self.opened_at).total_seconds()) if self.opened_at else None
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        logger.info(f"🔄 Circuit breaker {self.name}: Manually reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        self.failure_times = []


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        """Initialize circuit breaker manager"""
        self.breakers: dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker
        
        Args:
            name: Circuit breaker name
            config: Optional configuration
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, config)
        return self.breakers[name]
    
    def get_all_states(self) -> dict:
        """Get states of all circuit breakers
        
        Returns:
            Dictionary mapping breaker names to their states
        """
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
        logger.info("🔄 All circuit breakers reset")

