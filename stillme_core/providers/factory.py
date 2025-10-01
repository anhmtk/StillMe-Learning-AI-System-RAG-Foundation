"""
Provider factory for creating LLM provider instances.
"""

import logging
from typing import Dict, List, Optional, Type

from .llm_base import FallbackStrategy, LLMProviderBase, ProviderConfig
from .local_llm import LocalLLMProvider
from .openai import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: Dict[str, Type[LLMProviderBase]] = {
        "openai": OpenAIProvider,
        "local_llm": LocalLLMProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProviderBase]):
        """Register a new provider type."""
        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def create_provider(cls, config: ProviderConfig) -> LLMProviderBase:
        """Create a provider instance from configuration."""
        if config.name not in cls._providers:
            raise ValueError(f"Unknown provider type: {config.name}")

        provider_class = cls._providers[config.name]
        return provider_class(config)

    @classmethod
    def create_providers_from_config(cls, configs: List[Dict]) -> List[LLMProviderBase]:
        """Create multiple provider instances from configuration list."""
        providers = []

        for config_dict in configs:
            try:
                config = ProviderConfig(**config_dict)
                provider = cls.create_provider(config)
                providers.append(provider)
                logger.info(f"Created provider: {config.name}")
            except Exception as e:
                logger.error(f"Failed to create provider from config {config_dict}: {e}")

        return providers

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return list(cls._providers.keys())
