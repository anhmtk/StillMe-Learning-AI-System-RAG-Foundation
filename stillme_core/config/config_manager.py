"""
Configuration Management System for StillMe AI Framework

This module provides centralized configuration management with support for:
- YAML configuration files
- Environment variable overrides
- Schema validation
- Type conversion
- Default values

Author: StillMe AI Team
Version: 1.0.0
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ThresholdsConfig(BaseModel):
    """Threshold configuration schema"""

    abuse_guard: dict[str, float] = Field(
        default_factory=lambda: {"suggestion": 0.8, "abuse": 0.15}
    )
    latency: dict[str, float] = Field(
        default_factory=lambda: {"p95": 500.0, "p99": 1000.0}
    )
    quality: dict[str, float] = Field(
        default_factory=lambda: {"min_score": 70.0, "max_errors": 0.0}
    )


class PerformanceConfig(BaseModel):
    """Performance configuration schema"""

    max_latency_ms: int = Field(default=10)
    target_throughput_req_s: int = Field(default=1000)
    max_workers: int = Field(default=4)
    timeout_seconds: int = Field(default=30)


class SecurityConfig(BaseModel):
    """Security configuration schema"""

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_window: int = Field(default=30)
    max_requests_per_window: int = Field(default=100)
    pii_redaction: bool = Field(default=True)
    audit_logging: bool = Field(default=True)


class ProviderConfig(BaseModel):
    """Provider configuration schema"""

    order: list[str] = Field(
        default_factory=lambda: ["local_llm", "openai", "openrouter"]
    )
    timeout: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    circuit_breaker_threshold: int = Field(default=5)


class FeaturesConfig(BaseModel):
    """Features configuration schema"""

    emotion_detection: bool = Field(default=False)
    multi_modal: bool = Field(default=True)
    proactive_suggestions: bool = Field(default=True)
    learning_enabled: bool = Field(default=True)


class StillMeConfig(BaseModel):
    """Main StillMe configuration schema"""

    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    # Logging configuration
    logging: dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "rationale": False,
        }
    )

    # Policy configuration
    policy: dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "balanced",  # strict | balanced | creative
            "dry_run": False,
        }
    )

    # Privacy configuration
    privacy: dict[str, Any] = Field(
        default_factory=lambda: {
            "mode": "standard",  # standard | strict
            "opt_in_required": False,
            "data_retention_days": 30,
        }
    )


class ConfigManager:
    """
    Configuration manager for StillMe AI Framework

    Handles loading, validation, and access to configuration values
    with support for environment variable overrides.
    """

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file
        """
        self.config_path = (
            Path(config_path) if config_path else Path("config/default.yaml")
        )
        self._config: StillMeConfig | None = None
        self._env_prefix = "STILLME__"

    def load_config(self) -> StillMeConfig:
        """
        Load configuration from file and environment variables

        Returns:
            StillMeConfig: Loaded and validated configuration
        """
        # Load base configuration from file
        base_config = self._load_file_config()

        # Override with environment variables
        env_config = self._load_env_config()

        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)

        # Validate configuration
        self._config = StillMeConfig(**merged_config)

        logger.info("Configuration loaded successfully")
        return self._config

    def _load_file_config(self) -> dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            logger.warning(f"Configuration file not found: {self.config_path}")
            return {}

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from: {self.config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
            return {}

    def _load_env_config(self) -> dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                # Remove prefix and convert to nested dict
                config_key = key[len(self._env_prefix) :].lower()
                env_config[config_key] = self._parse_env_value(value)

        if env_config:
            logger.info(f"Loaded {len(env_config)} environment variable overrides")

        return env_config

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try to parse as boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try to parse as number
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Try to parse as list (comma-separated)
        if "," in value:
            return [item.strip() for item in value.split(",")]

        # Return as string
        return value

    def _merge_configs(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge base configuration with overrides"""
        merged = base.copy()

        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def get_config(self) -> StillMeConfig:
        """
        Get current configuration

        Returns:
            StillMeConfig: Current configuration
        """
        if self._config is None:
            return self.load_config()
        return self._config

    def get_threshold(
        self, category: str, threshold: str, default: float = 0.0
    ) -> float:
        """
        Get threshold value

        Args:
            category: Threshold category (e.g., 'abuse_guard', 'latency')
            threshold: Threshold name (e.g., 'suggestion', 'p95')
            default: Default value if not found

        Returns:
            float: Threshold value
        """
        config = self.get_config()

        if category == "abuse_guard":
            return config.thresholds.abuse_guard.get(threshold, default)
        elif category == "latency":
            return config.thresholds.latency.get(threshold, default)
        elif category == "quality":
            return config.thresholds.quality.get(threshold, default)

        return default

    def get_feature_flag(self, feature: str, default: bool = False) -> bool:
        """
        Get feature flag value

        Args:
            feature: Feature name
            default: Default value if not found

        Returns:
            bool: Feature flag value
        """
        config = self.get_config()
        return getattr(config.features, feature, default)

    def is_dry_run(self) -> bool:
        """Check if dry run mode is enabled"""
        config = self.get_config()
        return config.policy.get("dry_run", False)

    def get_policy_level(self) -> str:
        """Get current policy level"""
        config = self.get_config()
        return config.policy.get("level", "balanced")

    def get_privacy_mode(self) -> str:
        """Get current privacy mode"""
        config = self.get_config()
        return config.privacy.get("mode", "standard")


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """
    Get global configuration manager instance

    Returns:
        ConfigManager: Global configuration manager
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> StillMeConfig:
    """
    Get current configuration

    Returns:
        StillMeConfig: Current configuration
    """
    return get_config_manager().get_config()


def get_threshold(category: str, threshold: str, default: float = 0.0) -> float:
    """
    Get threshold value (convenience function)

    Args:
        category: Threshold category
        threshold: Threshold name
        default: Default value

    Returns:
        float: Threshold value
    """
    return get_config_manager().get_threshold(category, threshold, default)


def get_feature_flag(feature: str, default: bool = False) -> bool:
    """
    Get feature flag value (convenience function)

    Args:
        feature: Feature name
        default: Default value

    Returns:
        bool: Feature flag value
    """
    return get_config_manager().get_feature_flag(feature, default)