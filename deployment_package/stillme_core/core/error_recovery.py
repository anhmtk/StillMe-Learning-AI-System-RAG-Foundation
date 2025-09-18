# stillme_core/error_recovery.py
"""
Enhanced error recovery and circuit breaker system
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


class RetryStrategy(Enum):
    """Retry strategies"""

    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    RANDOM = "random"  # Random jitter


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    backoff_multiplier: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    success_threshold: int = 2


@dataclass
class OperationResult:
    """Result of an operation"""

    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 1
    duration: float = 0.0
    circuit_state: Optional[CircuitState] = None


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt_time:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if isinstance(e, self.config.expected_exception):
                self._on_failure()
            raise e

    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt_time:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if isinstance(e, self.config.expected_exception):
                self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker {self.name} is now CLOSED")

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.config.recovery_timeout
            logger.warning(f"Circuit breaker {self.name} is now OPEN")


class RetryManager:
    """
    Retry manager with multiple strategies
    """

    def __init__(self, config: RetryConfig):
        self.config = config

    def execute(self, func: Callable[..., T], *args, **kwargs) -> OperationResult:
        """Execute function with retry logic"""
        last_exception = None
        start_time = time.time()

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                return OperationResult(
                    success=True, result=result, attempts=attempt, duration=duration
                )
            except Exception as e:
                last_exception = e

                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed")

        duration = time.time() - start_time
        return OperationResult(
            success=False,
            error=last_exception,
            attempts=self.config.max_attempts,
            duration=duration,
        )

    async def execute_async(
        self, func: Callable[..., T], *args, **kwargs
    ) -> OperationResult:
        """Execute async function with retry logic"""
        last_exception = None
        start_time = time.time()

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                return OperationResult(
                    success=True, result=result, attempts=attempt, duration=duration
                )
            except Exception as e:
                last_exception = e

                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed")

        duration = time.time() - start_time
        return OperationResult(
            success=False,
            error=last_exception,
            attempts=self.config.max_attempts,
            duration=duration,
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (
                self.config.backoff_multiplier ** (attempt - 1)
            )
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(0, self.config.base_delay * attempt)
        else:
            delay = self.config.base_delay

        # Apply jitter
        if self.config.jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter

        # Cap at max delay
        return min(delay, self.config.max_delay)


class ErrorRecoveryManager:
    """
    Comprehensive error recovery and fault tolerance manager
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.operation_history: List[OperationResult] = []

        # Default configurations
        self._setup_default_configs()

    def _setup_default_configs(self):
        """Setup default configurations"""
        # Default retry configs
        self.retry_configs["default"] = RetryConfig()
        self.retry_configs["fast"] = RetryConfig(max_attempts=2, base_delay=0.5)
        self.retry_configs["slow"] = RetryConfig(max_attempts=5, base_delay=2.0)
        self.retry_configs["network"] = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL,
            max_delay=30.0,
        )

        # Default circuit breaker configs
        self.circuit_breakers["default"] = CircuitBreaker(
            "default", CircuitBreakerConfig()
        )
        self.circuit_breakers["api"] = CircuitBreaker(
            "api", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
        )
        self.circuit_breakers["database"] = CircuitBreaker(
            "database", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        )

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, CircuitBreakerConfig())
        return self.circuit_breakers[name]

    def get_retry_config(self, name: str) -> RetryConfig:
        """Get retry configuration"""
        return self.retry_configs.get(name, self.retry_configs["default"])

    def execute_with_recovery(
        self,
        func: Callable[..., T],
        circuit_breaker_name: str = "default",
        retry_config_name: str = "default",
        *args,
        **kwargs,
    ) -> OperationResult:
        """Execute function with full error recovery"""
        circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
        retry_config = self.get_retry_config(retry_config_name)

        # Create wrapper function with circuit breaker
        def wrapped_func():
            return circuit_breaker.call(func, *args, **kwargs)

        # Execute with retry
        retry_manager = RetryManager(retry_config)
        result = retry_manager.execute(wrapped_func)

        # Add circuit breaker state to result
        result.circuit_state = circuit_breaker.state

        # Record operation
        self.operation_history.append(result)

        return result

    async def execute_with_recovery_async(
        self,
        func: Callable[..., T],
        circuit_breaker_name: str = "default",
        retry_config_name: str = "default",
        *args,
        **kwargs,
    ) -> OperationResult:
        """Execute async function with full error recovery"""
        circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
        retry_config = self.get_retry_config(retry_config_name)

        # Create wrapper function with circuit breaker
        async def wrapped_func():
            return await circuit_breaker.call_async(func, *args, **kwargs)

        # Execute with retry
        retry_manager = RetryManager(retry_config)
        result = await retry_manager.execute_async(wrapped_func)

        # Add circuit breaker state to result
        result.circuit_state = circuit_breaker.state

        # Record operation
        self.operation_history.append(result)

        return result

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics"""
        if not self.operation_history:
            return {"total_operations": 0}

        total_ops = len(self.operation_history)
        successful_ops = sum(1 for op in self.operation_history if op.success)
        failed_ops = total_ops - successful_ops

        avg_duration = sum(op.duration for op in self.operation_history) / total_ops
        avg_attempts = sum(op.attempts for op in self.operation_history) / total_ops

        # Circuit breaker states
        circuit_states = {}
        for cb_name, cb in self.circuit_breakers.items():
            circuit_states[cb_name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "success_count": cb.success_count,
            }

        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "average_duration": avg_duration,
            "average_attempts": avg_attempts,
            "circuit_breakers": circuit_states,
        }

    def reset_circuit_breaker(self, name: str):
        """Reset circuit breaker to closed state"""
        if name in self.circuit_breakers:
            cb = self.circuit_breakers[name]
            cb.state = CircuitState.CLOSED
            cb.failure_count = 0
            cb.success_count = 0
            logger.info(f"Circuit breaker {name} has been reset")


# Decorator functions for easy usage
def with_retry(config_name: str = "default"):
    """Decorator for retry functionality"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery_manager = ErrorRecoveryManager()
            retry_config = recovery_manager.get_retry_config(config_name)
            retry_manager = RetryManager(retry_config)
            result = retry_manager.execute(func, *args, **kwargs)

            if result.success:
                return result.result
            else:
                if result.error:
                    raise result.error
                else:
                    raise RuntimeError("Operation failed without error details")

        return wrapper

    return decorator


def with_circuit_breaker(circuit_name: str = "default"):
    """Decorator for circuit breaker functionality"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery_manager = ErrorRecoveryManager()
            circuit_breaker = recovery_manager.get_circuit_breaker(circuit_name)
            return circuit_breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


def with_recovery(circuit_name: str = "default", retry_config_name: str = "default"):
    """Decorator for full error recovery"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery_manager = ErrorRecoveryManager()
            result = recovery_manager.execute_with_recovery(
                func, circuit_name, retry_config_name, *args, **kwargs
            )

            if result.success:
                return result.result
            else:
                if result.error:
                    raise result.error
                else:
                    raise RuntimeError("Operation failed without error details")

        return wrapper

    return decorator


# Global recovery manager instance
recovery_manager = ErrorRecoveryManager()
