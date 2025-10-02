#!/usr/bin/env python3
"""
🔄 CIRCUIT BREAKER COMPATIBILITY LAYER
🔄 LỚP TƯƠNG THÍCH CIRCUIT BREAKER

PURPOSE / MỤC ĐÍCH:
- Compatibility wrapper for CircuitBreaker with different parameter names
- Lớp wrapper tương thích cho CircuitBreaker với tên tham số khác nhau
- Supports both old and new parameter naming conventions
- Hỗ trợ cả tên tham số cũ và mới

FUNCTIONALITY / CHỨC NĂNG:
- Maps failure_threshold/recovery_timeout to CircuitBreakerConfig
- Maps failure_threshold/recovery_timeout tới CircuitBreakerConfig
- Provides transparent interface to underlying CircuitBreaker
- Cung cấp interface trong suốt tới CircuitBreaker gốc
- Maintains all CircuitBreaker functionality
- Duy trì tất cả chức năng CircuitBreaker
"""

from typing import Any

from .common.logging import get_logger
from .common.retry import CircuitBreaker, CircuitBreakerConfig

logger = get_logger(__name__)


class SafeCircuitBreaker:
    """
    Safe CircuitBreaker wrapper that handles parameter mapping
    """

    def __init__(self, **kwargs):
        """
        Initialize SafeCircuitBreaker with parameter mapping

        Supported parameters:
        - failure_threshold: int (default: 5)
        - recovery_timeout: float (default: 60.0)
        - expected_exception: Type[Exception] (default: Exception)
        - success_threshold: int (default: 2)
        - logger: logger instance (optional)
        """
        # Extract known parameters
        failure_threshold = kwargs.pop('failure_threshold', 5)
        recovery_timeout = kwargs.pop('recovery_timeout', 60.0)
        expected_exception = kwargs.pop('expected_exception', Exception)
        success_threshold = kwargs.pop('success_threshold', 2)
        logger_instance = kwargs.pop('logger', None)

        # Check for unknown parameters
        if kwargs:
            unknown_params = ', '.join(kwargs.keys())
            logger.warning(f"Unknown parameters passed to SafeCircuitBreaker: {unknown_params}")

        # Create CircuitBreakerConfig
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold
        )

        # Initialize the actual CircuitBreaker
        self._circuit_breaker = CircuitBreaker(config=config, logger=logger_instance)

        logger.debug(f"SafeCircuitBreaker initialized with config: {config}")

    def __getattr__(self, name: str) -> Any:
        """
        Delegate all other attributes to the underlying CircuitBreaker
        """
        return getattr(self._circuit_breaker, name)

    def __call__(self, func):
        """
        Allow using SafeCircuitBreaker as a decorator
        """
        return self._circuit_breaker(func)

    @property
    def state(self):
        """Get current circuit breaker state"""
        return self._circuit_breaker.state

    @property
    def failure_count(self):
        """Get current failure count"""
        return self._circuit_breaker.failure_count

    @property
    def success_count(self):
        """Get current success count"""
        return self._circuit_breaker.success_count

    def call(self, func, *args, **kwargs):
        """
        Call function through circuit breaker
        """
        return self._circuit_breaker.call(func, *args, **kwargs)

    def allow(self):
        """
        Check if circuit breaker allows calls
        """
        return self._circuit_breaker.allow()

    def reset(self):
        """
        Reset circuit breaker state
        """
        return self._circuit_breaker.reset()


__all__ = ['SafeCircuitBreaker']
