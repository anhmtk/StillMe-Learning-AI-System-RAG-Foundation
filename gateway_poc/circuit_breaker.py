#!/usr/bin/env python3
"""
Circuit Breaker Implementation for StillMe Gateway
Author: StillMe AI Assistant
Date: 2025-09-22

Features:
- Failure threshold detection
- Recovery timeout
- Half-open state
- Async support
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    name: str = "circuit_breaker"


class CircuitBreaker:
    """Circuit Breaker pattern implementation for fault tolerance"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "circuit_breaker",
    ):
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name,
        )

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(
                    f"Circuit breaker {self.config.name} entering HALF_OPEN state"
                )
            else:
                raise Exception(f"Circuit breaker {self.config.name} is OPEN")

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count
            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            # Unexpected exception - still count as failure
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # If we get enough successes in half-open, close the circuit
            if self.success_count >= 2:  # Require 2 successes to close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.config.name} CLOSED after recovery")
        else:
            # In CLOSED state, reset failure count on success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state - go back to open
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(
                f"Circuit breaker {self.config.name} OPENED again after failure in HALF_OPEN"
            )

        elif self.failure_count >= self.config.failure_threshold:
            # Too many failures - open the circuit
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker {self.config.name} OPENED after {self.failure_count} failures"
            )

    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "name": self.config.name,
            },
        }

    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.config.name} manually reset")
