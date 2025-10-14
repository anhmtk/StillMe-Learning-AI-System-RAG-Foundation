"""
Base classes for LLM provider abstraction in StillMe AI Framework.

This module provides a common interface for different LLM providers,
enabling easy switching between providers and graceful fallback handling.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Status of an LLM provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FallbackStrategy(Enum):
    """Strategy for provider fallback."""

    ROUND_ROBIN = "round_robin"
    FIRST_AVAILABLE = "first_available"
    FAIL_FAST = "fail_fast"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    api_key: str
    base_url: str
    model: str
    timeout: int = 30
    max_retries: int = 3
    priority: int = 0  # Lower number = higher priority
    enabled: bool = True
    fallback_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


@dataclass
class LLMRequest:
    """Request to an LLM provider."""

    prompt: str
    max_tokens: int | None = None
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None
    user: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    usage: dict[str, int]
    finish_reason: str
    response_time: float
    metadata: dict[str, Any] | None = None


@dataclass
class ProviderHealth:
    """Health status of a provider."""

    status: ProviderStatus
    last_check: datetime
    response_time: float
    error_rate: float
    total_requests: int
    failed_requests: int
    circuit_breaker_open: bool = False
    circuit_breaker_until: datetime | None = None


class CircuitBreaker:
    """Circuit breaker for provider health monitoring."""

    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "closed"  # closed, open, half-open

    def record_success(self):
        """Record a successful request."""
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None

    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.threshold:
            self.state = "open"

    def can_attempt(self) -> bool:
        """Check if we can attempt a request."""
        if self.state == "closed":
            return True

        if self.state == "open":
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time
                > timedelta(seconds=self.timeout)
            ):
                self.state = "half-open"
                return True
            return False

        if self.state == "half-open":
            return True

        return False

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == "open"


class LLMProviderBase(ABC):
    """Base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.health = ProviderHealth(
            status=ProviderStatus.UNKNOWN,
            last_check=datetime.now(),
            response_time=0.0,
            error_rate=0.0,
            total_requests=0,
            failed_requests=0,
        )
        self.circuit_breaker = CircuitBreaker(
            config.circuit_breaker_threshold, config.circuit_breaker_timeout
        )
        self._client: Any | None = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider client."""
        pass

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass

    async def cleanup(self):
        """Cleanup provider resources."""
        if self._client:
            try:
                if hasattr(self._client, "close"):
                    await self._client.close()
                elif hasattr(self._client, "aclose"):
                    await self._client.aclose()
            except Exception as e:
                logger.warning(f"Error closing {self.config.name} client: {e}")

    def update_health(self, success: bool, response_time: float):
        """Update provider health metrics."""
        self.health.total_requests += 1
        self.health.last_check = datetime.now()
        self.health.response_time = response_time

        if success:
            self.health.failed_requests = max(0, self.health.failed_requests - 1)
            self.circuit_breaker.record_success()
        else:
            self.health.failed_requests += 1
            self.circuit_breaker.record_failure()

        # Update error rate
        if self.health.total_requests > 0:
            self.health.error_rate = (
                self.health.failed_requests / self.health.total_requests
            )

        # Update status based on error rate and circuit breaker
        if self.circuit_breaker.is_open():
            self.health.status = ProviderStatus.UNHEALTHY
            self.health.circuit_breaker_open = True
            self.health.circuit_breaker_until = datetime.now() + timedelta(
                seconds=self.config.circuit_breaker_timeout
            )
        elif self.health.error_rate > 0.5:
            self.health.status = ProviderStatus.DEGRADED
        elif self.health.error_rate < 0.1:
            self.health.status = ProviderStatus.HEALTHY
        else:
            self.health.status = ProviderStatus.DEGRADED


class LLMProviderManager:
    """Manager for multiple LLM providers with fallback support."""

    def __init__(
        self,
        providers: list[LLMProviderBase],
        fallback_strategy: FallbackStrategy = FallbackStrategy.ROUND_ROBIN,
    ):
        self.providers = {p.config.name: p for p in providers}
        self.fallback_strategy = fallback_strategy
        self._current_provider_index = 0
        self._provider_order = sorted(providers, key=lambda p: p.config.priority)

    async def initialize_all(self) -> bool:
        """Initialize all providers."""
        success_count = 0
        for provider in self.providers.values():
            try:
                if await provider.initialize():
                    success_count += 1
                    logger.info(f"Initialized provider: {provider.config.name}")
                else:
                    logger.warning(
                        f"Failed to initialize provider: {provider.config.name}"
                    )
            except Exception as e:
                logger.error(f"Error initializing provider {provider.config.name}: {e}")

        return success_count > 0

    async def generate(
        self, request: LLMRequest, preferred_provider: str | None = None
    ) -> LLMResponse:
        """Generate a response using the best available provider."""
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.config.enabled and not provider.circuit_breaker.is_open():
                try:
                    return await self._try_provider(provider, request)
                except Exception as e:
                    logger.warning(
                        f"Preferred provider {preferred_provider} failed: {e}"
                    )

        # Try providers in order based on fallback strategy
        if self.fallback_strategy == FallbackStrategy.FIRST_AVAILABLE:
            for provider in self._provider_order:
                if provider.config.enabled and not provider.circuit_breaker.is_open():
                    try:
                        return await self._try_provider(provider, request)
                    except Exception as e:
                        logger.warning(f"Provider {provider.config.name} failed: {e}")
                        continue

        elif self.fallback_strategy == FallbackStrategy.ROUND_ROBIN:
            for _ in range(len(self._provider_order)):
                provider = self._provider_order[self._current_provider_index]
                self._current_provider_index = (self._current_provider_index + 1) % len(
                    self._provider_order
                )

                if provider.config.enabled and not provider.circuit_breaker.is_open():
                    try:
                        return await self._try_provider(provider, request)
                    except Exception as e:
                        logger.warning(f"Provider {provider.config.name} failed: {e}")
                        continue

        # If all providers failed, raise an exception
        raise Exception("All LLM providers are unavailable")

    async def _try_provider(
        self, provider: LLMProviderBase, request: LLMRequest
    ) -> LLMResponse:
        """Try to generate a response using a specific provider."""
        start_time = datetime.now()

        try:
            response = await provider.generate(request)
            response_time = (datetime.now() - start_time).total_seconds()
            provider.update_health(True, response_time)
            return response
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            provider.update_health(False, response_time)
            raise e

    async def health_check_all(self) -> dict[str, ProviderHealth]:
        """Check health of all providers."""
        health_status = {}

        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                provider.update_health(is_healthy, 0.0)
                health_status[name] = provider.health
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                provider.update_health(False, 0.0)
                health_status[name] = provider.health

        return health_status

    async def cleanup_all(self):
        """Cleanup all providers."""
        for provider in self.providers.values():
            await provider.cleanup()

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "enabled": provider.config.enabled,
                "priority": provider.config.priority,
                "health": provider.health,
                "circuit_breaker": {
                    "state": provider.circuit_breaker.state,
                    "failure_count": provider.circuit_breaker.failure_count,
                    "can_attempt": provider.circuit_breaker.can_attempt(),
                },
            }
        return status