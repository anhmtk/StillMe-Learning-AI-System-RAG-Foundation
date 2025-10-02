"""
StillMe Resilience Module
========================

Advanced resilience and error handling framework for AGI learning automation.
Provides comprehensive error recovery, retry policies, circuit breakers,
and system resilience management.

Components:
- ErrorHandler: Advanced error handling and recovery
- ResilienceManager: System-wide resilience orchestration
- Circuit Breakers: Service protection mechanisms
- Retry Policies: Intelligent retry strategies
- Failure Prediction: Proactive failure detection
- Self-Healing: Automatic recovery capabilities

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Framework"

# Import error handling
from .error_handler import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    RetryPolicy,
    RetryStrategy,
    get_error_handler,
    initialize_error_handling,
    with_error_handling,
    with_retry,
)

# Import resilience management
from .resilience_manager import (
    FailurePrediction,
    HealthMetrics,
    ResilienceConfig,
    ResilienceLevel,
    ResilienceManager,
    SystemHealth,
    get_resilience_manager,
    initialize_resilience_system,
)

__all__ = [
    # Error Handling
    "ErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "RetryStrategy",
    "RetryPolicy",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreaker",
    "ErrorContext",
    "with_error_handling",
    "with_retry",
    "get_error_handler",
    "initialize_error_handling",
    # Resilience Management
    "ResilienceManager",
    "ResilienceLevel",
    "SystemHealth",
    "ResilienceConfig",
    "HealthMetrics",
    "FailurePrediction",
    "get_resilience_manager",
    "initialize_resilience_system",
]
