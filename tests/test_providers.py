import os
from unittest.mock import patch

"""
Tests for LLM provider abstraction and management.
"""


import pytest

from stillme_core.providers.factory import ProviderFactory
from stillme_core.providers.llm_base import (
    CircuitBreaker,
    LLMProviderBase,
    LLMRequest,
    LLMResponse,
    ProviderConfig,
)
from stillme_core.providers.local_llm import LocalLLMProvider
from stillme_core.providers.manager import StillMeProviderManager
from stillme_core.providers.openai import OpenAIProvider


class TestProviderConfig:
    """Test ProviderConfig dataclass."""

    def test_provider_config_creation(self):
        """Test creating a ProviderConfig."""
        config = ProviderConfig(
            name="test",
            api_key=os.getenv("API_KEY", ""),
            base_url="https://api.test.com",
            model="test-model",
        )

        assert config.name == "test"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.test.com"
        assert config.model == "test-model"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.priority == 0
        assert config.enabled is True
        assert config.fallback_enabled is True


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        cb = CircuitBreaker(threshold=3, timeout=60)

        assert cb.state == "closed"
        assert cb.failure_count == 0
        assert cb.can_attempt() is True
        assert cb.is_open() is False

    def test_circuit_breaker_record_success(self):
        """Test recording success."""
        cb = CircuitBreaker(threshold=3, timeout=60)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb.state == "closed"
        assert cb.failure_count == 0
        assert cb.can_attempt() is True

    def test_circuit_breaker_open_on_threshold(self):
        """Test circuit breaker opens on threshold."""
        cb = CircuitBreaker(threshold=3, timeout=60)

        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "open"
        assert cb.can_attempt() is False
        assert cb.is_open() is True

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker goes half-open after timeout."""
        cb = CircuitBreaker(threshold=3, timeout=0.1)  # Very short timeout for testing

        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "open"

        # Wait for timeout
        import time

        time.sleep(0.2)

        assert cb.can_attempt() is True
        assert cb.state == "half-open"


class TestLLMRequest:
    """Test LLMRequest dataclass."""

    def test_llm_request_creation(self):
        """Test creating an LLMRequest."""
        request = LLMRequest(prompt="Test prompt", max_tokens=100, temperature=0.7)

        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.top_p == 1.0
        assert request.frequency_penalty == 0.0
        assert request.presence_penalty == 0.0
        assert request.stop is None
        assert request.user is None
        assert request.metadata is None


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_llm_response_creation(self):
        """Test creating an LLMResponse."""
        response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test-provider",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            response_time=1.5,
        )

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.provider == "test-provider"
        assert response.usage == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        assert response.finish_reason == "stop"
        assert response.response_time == 1.5
        assert response.metadata is None


class TestProviderFactory:
    """Test ProviderFactory functionality."""

    def test_register_provider(self):
        """Test registering a new provider."""

        class TestProvider(LLMProviderBase):
            async def initialize(self) -> bool:
                return True

            async def generate(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="test",
                    model="test",
                    provider="test",
                    usage={},
                    finish_reason="stop",
                    response_time=0.0,
                )

            async def health_check(self) -> bool:
                return True

        ProviderFactory.register_provider("test", TestProvider)
        assert "test" in ProviderFactory.get_available_providers()

    def test_create_provider(self):
        """Test creating a provider instance."""
        config = ProviderConfig(
            name="openai",
            api_key=os.getenv("API_KEY", ""),
            base_url="https://api.openai.com",
            model="gpt-3.5-turbo",
        )

        provider = ProviderFactory.create_provider(config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.config.name == "openai"

    def test_create_provider_unknown_type(self):
        """Test creating a provider with unknown type."""
        config = ProviderConfig(
            name="unknown",
            api_key=os.getenv("API_KEY", ""),
            base_url="https://api.test.com",
            model="test-model",
        )

        with pytest.raises(ValueError, match="Unknown provider type"):
            ProviderFactory.create_provider(config)

    def test_create_providers_from_config(self):
        """Test creating multiple providers from config list."""
        configs = [
            {
                "name": "openai",
                "api_key": "test-key",
                "base_url": "https://api.openai.com",
                "model": "gpt-3.5-turbo",
            },
            {
                "name": "local_llm",
                "api_key": "",
                "base_url": "http://localhost:11434",
                "model": "llama2",
            },
        ]

        providers = ProviderFactory.create_providers_from_config(configs)
        assert len(providers) == 2
        assert isinstance(providers[0], OpenAIProvider)
        assert isinstance(providers[1], LocalLLMProvider)


class TestStillMeProviderManager:
    """Test StillMeProviderManager functionality."""

    @pytest.fixture
    async def provider_manager(self):
        """Fixture for provider manager."""
        config = {
            "providers": [
                {
                    "name": "openai",
                    "api_key": "test-key",
                    "base_url": "https://api.openai.com",
                    "model": "gpt-3.5-turbo",
                    "priority": 1,
                },
                {
                    "name": "local_llm",
                    "api_key": "",
                    "base_url": "http://localhost:11434",
                    "model": "llama2",
                    "priority": 2,
                },
            ],
            "fallback_strategy": "round_robin",
        }

        manager = StillMeProviderManager(config)
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_provider_manager_initialization(self, provider_manager):
        """Test provider manager initialization."""
        with patch.object(
            provider_manager._manager, "initialize_all", return_value=True
        ):
            result = await provider_manager.initialize()
            assert result is True
            assert provider_manager._initialized is True

    @pytest.mark.asyncio
    async def test_provider_manager_initialization_failure(self, provider_manager):
        """Test provider manager initialization failure."""
        with patch.object(
            provider_manager._manager, "initialize_all", return_value=False
        ):
            result = await provider_manager.initialize()
            assert result is False
            assert provider_manager._initialized is False

    @pytest.mark.asyncio
    async def test_provider_manager_generate(self, provider_manager):
        """Test generating a response."""
        await provider_manager.initialize()

        request = LLMRequest(prompt="Test prompt")
        expected_response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test-provider",
            usage={},
            finish_reason="stop",
            response_time=0.0,
        )

        with patch.object(
            provider_manager._manager, "generate", return_value=expected_response
        ):
            response = await provider_manager.generate(request)
            assert response == expected_response

    @pytest.mark.asyncio
    async def test_provider_manager_health_check(self, provider_manager):
        """Test health check."""
        await provider_manager.initialize()

        expected_health = {"openai": "healthy", "local_llm": "healthy"}

        with patch.object(
            provider_manager._manager, "health_check_all", return_value=expected_health
        ):
            health = await provider_manager.health_check()
            assert health == expected_health

    @pytest.mark.asyncio
    async def test_provider_manager_status(self, provider_manager):
        """Test getting provider status."""
        await provider_manager.initialize()

        expected_status = {
            "openai": {"enabled": True, "priority": 1},
            "local_llm": {"enabled": True, "priority": 2},
        }

        with patch.object(
            provider_manager._manager,
            "get_provider_status",
            return_value=expected_status,
        ):
            status = provider_manager.get_status()
            assert status == expected_status

    @pytest.mark.asyncio
    async def test_provider_manager_not_initialized(self, provider_manager):
        """Test operations when not initialized."""
        with pytest.raises(RuntimeError, match="Provider manager not initialized"):
            await provider_manager.generate(LLMRequest(prompt="test"))

        health = await provider_manager.health_check()
        assert "error" in health

        status = provider_manager.get_status()
        assert "error" in status
