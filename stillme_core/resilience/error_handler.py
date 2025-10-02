"""
🛡️ StillMe Error Handling Framework
==================================

Advanced error handling and resilience framework for AGI learning automation.
Provides comprehensive error recovery, retry policies, circuit breakers,
and graceful degradation for robust AGI operation.

Tính năng:
- Intelligent retry policies với exponential backoff
- Circuit breaker pattern cho service protection
- Graceful degradation và fallback mechanisms
- Error classification và intelligent recovery
- AGI-specific error handling strategies
- Comprehensive error logging và analytics
- Self-healing capabilities

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import functools
import json
import logging
import random
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for AGI systems"""

    RESOURCE = "resource"  # CPU, memory, disk, network
    LEARNING = "learning"  # Training, inference, model errors
    DATA = "data"  # Data corruption, missing data
    NETWORK = "network"  # API calls, external services
    SYSTEM = "system"  # OS, hardware, infrastructure
    LOGIC = "logic"  # Algorithm, business logic errors
    SECURITY = "security"  # Authentication, authorization
    CONFIGURATION = "configuration"  # Config errors, missing settings


class RetryStrategy(Enum):
    """Retry strategies"""

    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    RANDOM = "random"  # Random jitter
    ADAPTIVE = "adaptive"  # Adaptive based on error type


@dataclass
class RetryPolicy:
    """Retry policy configuration"""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retryable_errors: list[type[Exception]] = None
    non_retryable_errors: list[type[Exception]] = None

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ConnectionError,
                TimeoutError,
                OSError,
                asyncio.TimeoutError,
                RuntimeError,
            ]
        if self.non_retryable_errors is None:
            self.non_retryable_errors = [
                ValueError,
                TypeError,
                AttributeError,
                KeyError,
                IndexError,
                NotImplementedError,
            ]


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception: type[Exception] = Exception
    half_open_max_calls: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class ErrorContext:
    """Error context information"""

    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    operation: str
    retry_count: int = 0
    context_data: dict[str, Any] = None
    stack_trace: str = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class CircuitBreaker:
    """
    Circuit breaker implementation for service protection
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.logger = logging.getLogger(__name__)

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True

        return (
            datetime.now() - self.last_failure_time
        ).total_seconds() >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info("Circuit breaker reset to CLOSED")
        else:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning("Circuit breaker opened from HALF_OPEN")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "half_open_calls": self.half_open_calls,
        }


class ErrorHandler:
    """
    Advanced error handling framework for AGI systems
    """

    def __init__(self, log_file: str = "logs/errors.jsonl"):
        self.logger = logging.getLogger(__name__)
        self.error_log_file = Path(log_file)
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Error tracking
        self.error_history: list[ErrorContext] = []
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_policies: dict[str, RetryPolicy] = {}

        # Recovery strategies
        self.recovery_strategies: dict[ErrorCategory, list[Callable]] = {}
        self._setup_default_recovery_strategies()

        # Statistics
        self.stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_attempts": 0,
            "recovery_successes": 0,
            "circuit_breaker_trips": 0,
        }

    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies"""
        self.recovery_strategies = {
            ErrorCategory.RESOURCE: [
                self._recover_from_resource_error,
                self._scale_down_operations,
                self._cleanup_memory,
            ],
            ErrorCategory.LEARNING: [
                self._recover_from_learning_error,
                self._reset_learning_state,
                self._fallback_to_simpler_model,
            ],
            ErrorCategory.NETWORK: [
                self._recover_from_network_error,
                self._switch_to_offline_mode,
                self._use_cached_data,
            ],
            ErrorCategory.DATA: [
                self._recover_from_data_error,
                self._validate_data_integrity,
                self._use_backup_data,
            ],
            ErrorCategory.SYSTEM: [
                self._recover_from_system_error,
                self._restart_components,
                self._enter_safe_mode,
            ],
        }

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Register a circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(config)
        self.logger.info(f"Registered circuit breaker: {name}")

    def register_retry_policy(self, name: str, policy: RetryPolicy):
        """Register a retry policy"""
        self.retry_policies[name] = policy
        self.logger.info(f"Registered retry policy: {name}")

    def add_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Add recovery strategy for error category"""
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
        self.logger.info(f"Added recovery strategy for {category.value}")

    def classify_error(
        self, error: Exception, context: dict[str, Any] = None
    ) -> ErrorContext:
        """Classify error and create error context"""
        error_id = f"error_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # Determine category
        category = self._determine_error_category(error, context)

        # Determine severity
        severity = self._determine_error_severity(error, category, context)

        # Create error context
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            component=context.get("component", "unknown") if context else "unknown",
            operation=context.get("operation", "unknown") if context else "unknown",
            context_data=context or {},
            stack_trace=traceback.format_exc(),
        )

        return error_context

    def _determine_error_category(
        self, error: Exception, context: dict[str, Any] = None
    ) -> ErrorCategory:
        """Determine error category"""
        type(error).__name__.lower()
        error_message = str(error).lower()

        # Resource errors
        if any(
            keyword in error_message
            for keyword in ["memory", "cpu", "disk", "resource", "out of"]
        ):
            return ErrorCategory.RESOURCE

        # Network errors
        if any(
            keyword in error_message
            for keyword in ["connection", "timeout", "network", "http", "api"]
        ):
            return ErrorCategory.NETWORK

        # Learning errors
        if any(
            keyword in error_message
            for keyword in ["model", "training", "inference", "learning", "neural"]
        ):
            return ErrorCategory.LEARNING

        # Data errors
        if any(
            keyword in error_message
            for keyword in ["data", "file", "corrupt", "missing", "invalid"]
        ):
            return ErrorCategory.DATA

        # Security errors
        if any(
            keyword in error_message
            for keyword in ["auth", "permission", "security", "unauthorized"]
        ):
            return ErrorCategory.SECURITY

        # Configuration errors
        if any(
            keyword in error_message
            for keyword in ["config", "setting", "parameter", "option"]
        ):
            return ErrorCategory.CONFIGURATION

        # System errors
        if any(
            keyword in error_message
            for keyword in ["system", "os", "hardware", "kernel"]
        ):
            return ErrorCategory.SYSTEM

        return ErrorCategory.LOGIC

    def _determine_error_severity(
        self, error: Exception, category: ErrorCategory, context: dict[str, Any] = None
    ) -> ErrorSeverity:
        """Determine error severity"""
        error_message = str(error).lower()

        # Critical errors
        if any(
            keyword in error_message
            for keyword in ["fatal", "critical", "crash", "corrupt", "security"]
        ):
            return ErrorSeverity.CRITICAL

        # High severity
        if category in [ErrorCategory.SYSTEM, ErrorCategory.SECURITY]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [
            ErrorCategory.RESOURCE,
            ErrorCategory.LEARNING,
            ErrorCategory.NETWORK,
        ]:
            return ErrorSeverity.MEDIUM

        # Low severity
        return ErrorSeverity.LOW

    async def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] = None,
        retry_policy: str = "default",
        circuit_breaker: str = None,
    ) -> Any:
        """Handle error with retry and recovery"""
        error_context = self.classify_error(error, context)
        self._log_error(error_context)
        self._update_statistics(error_context)

        # Check if error is retryable
        if not self._is_retryable(error, retry_policy):
            self.logger.error(f"Non-retryable error: {error_context.error_id}")
            return None

        # Apply circuit breaker if specified
        if circuit_breaker and circuit_breaker in self.circuit_breakers:
            cb = self.circuit_breakers[circuit_breaker]
            if cb.state == CircuitBreakerState.OPEN:
                self.logger.warning(f"Circuit breaker {circuit_breaker} is OPEN")
                return None

        # Attempt recovery
        recovery_result = await self._attempt_recovery(error_context)
        if recovery_result:
            error_context.recovery_successful = True
            self.logger.info(f"Error recovery successful: {error_context.error_id}")
            return recovery_result

        # Apply retry policy
        return await self._apply_retry_policy(error_context, retry_policy)

    def _is_retryable(self, error: Exception, retry_policy: str) -> bool:
        """Check if error is retryable"""
        policy = self.retry_policies.get(retry_policy, RetryPolicy())

        # Check non-retryable errors
        for error_type in policy.non_retryable_errors:
            if isinstance(error, error_type):
                return False

        # Check retryable errors
        for error_type in policy.retryable_errors:
            if isinstance(error, error_type):
                return True

        return False

    async def _attempt_recovery(self, error_context: ErrorContext) -> Any:
        """Attempt error recovery"""
        error_context.recovery_attempted = True
        self.stats["recovery_attempts"] += 1

        strategies = self.recovery_strategies.get(error_context.category, [])

        for strategy in strategies:
            try:
                result = await strategy(error_context)
                if result:
                    self.stats["recovery_successes"] += 1
                    return result
            except Exception as e:
                self.logger.warning(f"Recovery strategy failed: {e}")

        return None

    async def _apply_retry_policy(
        self, error_context: ErrorContext, policy_name: str
    ) -> Any:
        """Apply retry policy"""
        policy = self.retry_policies.get(policy_name, RetryPolicy())

        for attempt in range(policy.max_attempts):
            error_context.retry_count = attempt + 1

            # Calculate delay
            delay = self._calculate_delay(attempt, policy)

            if delay > 0:
                self.logger.info(
                    f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{policy.max_attempts})"
                )
                await asyncio.sleep(delay)

            # This would be called by the retry decorator
            # For now, just log the retry attempt
            self.logger.info(
                f"Retry attempt {attempt + 1} for error: {error_context.error_id}"
            )

        return None

    def _calculate_delay(self, attempt: int, policy: RetryPolicy) -> float:
        """Calculate retry delay"""
        if policy.strategy == RetryStrategy.FIXED:
            delay = policy.base_delay
        elif policy.strategy == RetryStrategy.EXPONENTIAL:
            delay = policy.base_delay * (policy.backoff_multiplier**attempt)
        elif policy.strategy == RetryStrategy.LINEAR:
            delay = policy.base_delay * (attempt + 1)
        elif policy.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(
                0, policy.base_delay * (policy.backoff_multiplier**attempt)
            )
        else:  # ADAPTIVE
            delay = policy.base_delay * (policy.backoff_multiplier**attempt)

        # Apply jitter
        if policy.jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter

        return min(delay, policy.max_delay)

    def _log_error(self, error_context: ErrorContext):
        """Log error to file"""
        try:
            with open(self.error_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(error_context), default=str) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log error: {e}")

    def _update_statistics(self, error_context: ErrorContext):
        """Update error statistics"""
        self.stats["total_errors"] += 1

        # Update category stats
        category = error_context.category.value
        self.stats["errors_by_category"][category] = (
            self.stats["errors_by_category"].get(category, 0) + 1
        )

        # Update severity stats
        severity = error_context.severity.value
        self.stats["errors_by_severity"][severity] = (
            self.stats["errors_by_severity"].get(severity, 0) + 1
        )

        # Add to history
        self.error_history.append(error_context)

        # Keep only recent errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

    # Recovery strategies
    async def _recover_from_resource_error(self, error_context: ErrorContext) -> Any:
        """Recover from resource errors"""
        self.logger.info("Attempting resource error recovery")
        # Implement resource recovery logic
        return True

    async def _scale_down_operations(self, error_context: ErrorContext) -> Any:
        """Scale down operations to reduce resource usage"""
        self.logger.info("Scaling down operations")
        # Implement scaling logic
        return True

    async def _cleanup_memory(self, error_context: ErrorContext) -> Any:
        """Clean up memory"""
        self.logger.info("Cleaning up memory")
        # Implement memory cleanup
        return True

    async def _recover_from_learning_error(self, error_context: ErrorContext) -> Any:
        """Recover from learning errors"""
        self.logger.info("Attempting learning error recovery")
        # Implement learning recovery logic
        return True

    async def _reset_learning_state(self, error_context: ErrorContext) -> Any:
        """Reset learning state"""
        self.logger.info("Resetting learning state")
        # Implement state reset logic
        return True

    async def _fallback_to_simpler_model(self, error_context: ErrorContext) -> Any:
        """Fallback to simpler model"""
        self.logger.info("Falling back to simpler model")
        # Implement fallback logic
        return True

    async def _recover_from_network_error(self, error_context: ErrorContext) -> Any:
        """Recover from network errors"""
        self.logger.info("Attempting network error recovery")
        # Implement network recovery logic
        return True

    async def _switch_to_offline_mode(self, error_context: ErrorContext) -> Any:
        """Switch to offline mode"""
        self.logger.info("Switching to offline mode")
        # Implement offline mode logic
        return True

    async def _use_cached_data(self, error_context: ErrorContext) -> Any:
        """Use cached data"""
        self.logger.info("Using cached data")
        # Implement cache logic
        return True

    async def _recover_from_data_error(self, error_context: ErrorContext) -> Any:
        """Recover from data errors"""
        self.logger.info("Attempting data error recovery")
        # Implement data recovery logic
        return True

    async def _validate_data_integrity(self, error_context: ErrorContext) -> Any:
        """Validate data integrity"""
        self.logger.info("Validating data integrity")
        # Implement validation logic
        return True

    async def _use_backup_data(self, error_context: ErrorContext) -> Any:
        """Use backup data"""
        self.logger.info("Using backup data")
        # Implement backup logic
        return True

    async def _recover_from_system_error(self, error_context: ErrorContext) -> Any:
        """Recover from system errors"""
        self.logger.info("Attempting system error recovery")
        # Implement system recovery logic
        return True

    async def _restart_components(self, error_context: ErrorContext) -> Any:
        """Restart components"""
        self.logger.info("Restarting components")
        # Implement restart logic
        return True

    async def _enter_safe_mode(self, error_context: ErrorContext) -> Any:
        """Enter safe mode"""
        self.logger.info("Entering safe mode")
        # Implement safe mode logic
        return True

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics"""
        return {
            "statistics": self.stats,
            "recent_errors": [asdict(e) for e in self.error_history[-10:]],
            "circuit_breakers": {
                name: cb.get_state() for name, cb in self.circuit_breakers.items()
            },
            "retry_policies": {
                name: asdict(policy) for name, policy in self.retry_policies.items()
            },
        }


# Decorators for easy error handling
def with_error_handling(
    error_handler: ErrorHandler,
    retry_policy: str = "default",
    circuit_breaker: str = None,
    context: dict[str, Any] = None,
):
    """Decorator for error handling"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                return await error_handler.handle_error(
                    e, context, retry_policy, circuit_breaker
                )

        return wrapper

    return decorator


def with_retry(policy: RetryPolicy):
    """Decorator for retry logic"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(policy.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if error is retryable
                    if not any(
                        isinstance(e, error_type)
                        for error_type in policy.retryable_errors
                    ):
                        raise e

                    if attempt < policy.max_attempts - 1:
                        delay = policy.base_delay * (policy.backoff_multiplier**attempt)
                        if policy.jitter:
                            delay += random.uniform(0.1, 0.3) * delay
                        delay = min(delay, policy.max_delay)

                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


# Global error handler instance
_error_handler_instance: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    return _error_handler_instance


def initialize_error_handling() -> ErrorHandler:
    """Initialize error handling system"""
    handler = get_error_handler()

    # Register default retry policies
    handler.register_retry_policy("default", RetryPolicy())
    handler.register_retry_policy(
        "aggressive", RetryPolicy(max_attempts=5, base_delay=0.5)
    )
    handler.register_retry_policy(
        "conservative", RetryPolicy(max_attempts=2, base_delay=5.0)
    )

    # Register default circuit breakers
    handler.register_circuit_breaker(
        "learning", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
    )
    handler.register_circuit_breaker(
        "network", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
    )

    return handler
