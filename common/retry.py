#!/usr/bin/env python3
"""
🔄 RETRY MECHANISMS - RESILIENT OPERATIONS
🔄 CƠ CHẾ RETRY - CÁC THAO TÁC KIÊN CƯỜNG

PURPOSE / MỤC ĐÍCH:
- Retry mechanisms with exponential backoff for StillMe modules
- Cơ chế retry với exponential backoff cho các modules StillMe
- Circuit breaker pattern implementation
- Triển khai pattern circuit breaker
- Jitter and randomization for distributed systems
- Jitter và randomization cho hệ thống phân tán

FUNCTIONALITY / CHỨC NĂNG:
- Exponential backoff with jitter
- Exponential backoff với jitter
- Circuit breaker for fault tolerance
- Circuit breaker cho fault tolerance
- Retry decorators for functions
- Decorator retry cho functions
- Async retry support
- Hỗ trợ retry async

RELATED FILES / FILES LIÊN QUAN:
- common/errors.py - Error handling integration
- common/logging.py - Retry logging
- modules/api_provider_manager.py - API retry usage
- stable_ai_server.py - Server retry mechanisms

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Thread-safe retry mechanisms
- Configurable retry strategies
- Integration with monitoring systems
- Support for custom retry conditions
"""

import asyncio
import time
import random
import functools
import threading
from typing import Callable, Any, Optional, Union, List, Type, Tuple, Dict
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from .errors import StillMeException, CircuitBreakerError
from .logging import get_logger


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    retry_condition: Optional[Callable[[Exception], bool]] = None


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    success_threshold: int = 2  # For half-open state


class RetryManager:
    """
    Retry manager with exponential backoff and jitter
    Quản lý retry với exponential backoff và jitter
    """
    
    def __init__(self, config: RetryConfig = None, logger=None):
        self.config = config or RetryConfig()
        self.logger = logger or get_logger("RetryManager")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0.0
        
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        
        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number
            
        Returns:
            True if should retry, False otherwise
        """
        # Check max attempts
        if attempt >= self.config.max_attempts:
            return False
        
        # Check if exception is in retry list
        if not isinstance(exception, self.config.exceptions):
            return False
        
        # Check custom retry condition
        if self.config.retry_condition and not self.config.retry_condition(exception):
            return False
        
        return True
    
    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry synchronous function
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    break
                
                delay = self.calculate_delay(attempt)
                if delay > 0:
                    self.logger.warning(f"Retry attempt {attempt + 1}/{self.config.max_attempts} "
                                      f"after {delay:.2f}s delay. Error: {e}")
                    time.sleep(delay)
                else:
                    self.logger.warning(f"Retry attempt {attempt + 1}/{self.config.max_attempts}. Error: {e}")
        
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")
    
    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry asynchronous function
        
        Args:
            func: Async function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    break
                
                delay = self.calculate_delay(attempt)
                if delay > 0:
                    self.logger.warning(f"Retry attempt {attempt + 1}/{self.config.max_attempts} "
                                      f"after {delay:.2f}s delay. Error: {e}")
                    await asyncio.sleep(delay)
                else:
                    self.logger.warning(f"Retry attempt {attempt + 1}/{self.config.max_attempts}. Error: {e}")
        
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    Triển khai circuit breaker cho fault tolerance
    """
    
    def __init__(self, config: CircuitBreakerConfig = None, logger=None):
        self.config = config or CircuitBreakerConfig()
        self.logger = logger or get_logger("CircuitBreaker")
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.logger.info("Circuit breaker closed - service recovered")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.logger.warning("Circuit breaker reopened - service still failing")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Original exception: If function fails
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.logger.info("Circuit breaker half-open - testing service")
                else:
                    raise CircuitBreakerError(
                        "Circuit breaker is open",
                        service_name=getattr(func, '__name__', 'unknown'),
                        failure_count=self.failure_count
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Original exception: If function fails
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.logger.info("Circuit breaker half-open - testing service")
                else:
                    raise CircuitBreakerError(
                        "Circuit breaker is open",
                        service_name=getattr(func, '__name__', 'unknown'),
                        failure_count=self.failure_count
                    )
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state information"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "is_open": self.state == CircuitState.OPEN,
            "is_half_open": self.state == CircuitState.HALF_OPEN,
            "is_closed": self.state == CircuitState.CLOSED
        }


# Decorator functions
def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0, 
                      max_delay: float = 60.0, exceptions: Tuple[Type[Exception], ...] = (Exception,),
                      jitter: bool = True, retry_condition: Optional[Callable[[Exception], bool]] = None):
    """
    Decorator for retry with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exceptions: Exceptions to catch and retry
        jitter: Add random jitter to delays
        retry_condition: Custom condition for retry
    """
    def decorator(func: Callable) -> Callable:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exceptions=exceptions,
            jitter=jitter,
            retry_condition=retry_condition
        )
        retry_manager = RetryManager(config)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry_manager.retry_sync(func, *args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_manager.retry_async(func, *args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 60.0,
                   expected_exception: Type[Exception] = Exception):
    """
    Decorator for circuit breaker pattern
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting reset
        expected_exception: Exception type to track
    """
    def decorator(func: Callable) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        breaker = CircuitBreaker(config)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        # Add circuit breaker state access
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Convenience functions
def retry_api_call(max_attempts: int = 3, base_delay: float = 1.0):
    """Retry decorator specifically for API calls"""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        exceptions=(ConnectionError, TimeoutError, Exception)
    )


def retry_database_operation(max_attempts: int = 3, base_delay: float = 0.5):
    """Retry decorator specifically for database operations"""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        exceptions=(ConnectionError, TimeoutError, Exception)
    )


def retry_file_operation(max_attempts: int = 3, base_delay: float = 0.1):
    """Retry decorator specifically for file operations"""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        exceptions=(IOError, OSError, PermissionError)
    )
