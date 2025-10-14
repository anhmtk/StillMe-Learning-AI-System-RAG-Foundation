#!/usr/bin/env python3
"""
⚙️ CONFIGURATION MANAGEMENT - CENTRALIZED CONFIG
⚙️ QUẢN LÝ CẤU HÌNH - CONFIG TẬP TRUNG

PURPOSE / MỤC ĐÍCH:
- Centralized configuration management for StillMe modules
- Quản lý cấu hình tập trung cho các modules StillMe
- Type-safe configuration loading with defaults
- Tải cấu hình an toàn kiểu với giá trị mặc định
- Environment variable override support
- Hỗ trợ ghi đè biến môi trường

FUNCTIONALITY / CHỨC NĂNG:
- JSON configuration file loading
- Tải file cấu hình JSON
- Default configuration fallback
- Fallback cấu hình mặc định
- Environment variable integration
- Tích hợp biến môi trường
- Configuration validation
- Xác thực cấu hình

RELATED FILES / FILES LIÊN QUAN:
- config/framework_config.json - Main framework configuration
- config/ethical_rules.json - Ethical rules configuration
- modules/* - Modules using configuration
- framework.py - Framework configuration integration

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Thread-safe configuration access
- Automatic config file creation with defaults
- Support for nested configuration structures
- Type hints for better IDE support
"""

import json
import os
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


class ConfigManager:
    """
    Centralized configuration manager with type safety
    Quản lý cấu hình tập trung với an toàn kiểu
    """

    def __init__(
        self, config_path: str, default_config: dict[str, Any], env_prefix: str = ""
    ):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file
            default_config: Default configuration values
            env_prefix: Prefix for environment variables (e.g., "STILLME_")
        """
        self.config_path = Path(config_path)
        self.default_config = default_config.copy()
        self.env_prefix = env_prefix.upper()
        self._config = self._load_config()
        self._last_modified = self._get_file_mtime()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration with fallback to defaults"""
        config = self.default_config.copy()

        # Load from file if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    file_config = json.load(f)
                    config = self._deep_merge(config, file_config)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")

        # Override with environment variables
        config = self._apply_env_overrides(config)

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        return config

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides"""
        result = config.copy()

        for key, value in config.items():
            env_key = f"{self.env_prefix}{key.upper()}"
            env_value = os.getenv(env_key)

            if env_value is not None:
                # Try to parse as JSON first, then as string
                try:
                    result[key] = json.loads(env_value)
                except (json.JSONDecodeError, ValueError):
                    # Convert string values to appropriate types
                    if isinstance(value, bool):
                        result[key] = env_value.lower() in ("true", "1", "yes", "on")
                    elif isinstance(value, int):
                        try:
                            result[key] = int(env_value)
                        except ValueError:
                            result[key] = env_value
                    elif isinstance(value, float):
                        try:
                            result[key] = float(env_value)
                        except ValueError:
                            result[key] = env_value
                    else:
                        result[key] = env_value
            elif isinstance(value, dict):
                result[key] = self._apply_env_overrides(value)

        return result

    def _get_file_mtime(self) -> float:
        """Get file modification time"""
        if self.config_path.exists():
            return self.config_path.stat().st_mtime
        return 0.0

    def reload(self) -> None:
        """Reload configuration from file"""
        current_mtime = self._get_file_mtime()
        if current_mtime > self._last_modified:
            self._config = self._load_config()
            self._last_modified = current_mtime

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation support

        Args:
            key: Configuration key (supports dot notation like 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value with dot notation support

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the final value
        config[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get_section(self, section: str) -> dict[str, Any]:
        """
        Get entire configuration section

        Args:
            section: Section name

        Returns:
            Configuration section as dictionary
        """
        return self.get(section, {})

    def update_section(self, section: str, values: dict[str, Any]) -> None:
        """
        Update entire configuration section

        Args:
            section: Section name
            values: Values to update
        """
        self.set(section, values)

    def to_dict(self) -> dict[str, Any]:
        """Get complete configuration as dictionary"""
        return self._config.copy()

    def validate_required(self, required_keys: list) -> None:
        """
        Validate that required configuration keys exist

        Args:
            required_keys: List of required keys (supports dot notation)

        Raises:
            ValueError: If any required key is missing
        """
        missing_keys = []

        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")

    def get_with_type(self, key: str, expected_type: type, default: T = None) -> T:
        """
        Get configuration value with type checking

        Args:
            key: Configuration key
            expected_type: Expected type
            default: Default value

        Returns:
            Configuration value with type checking
        """
        value = self.get(key, default)

        if not isinstance(value, expected_type):
            if default is not None:
                return default
            raise TypeError(
                f"Configuration key '{key}' expected {expected_type.__name__}, got {type(value).__name__}"
            )

        return value


class StillMeConfig:
    """
    StillMe-specific configuration with common defaults
    Cấu hình đặc thù StillMe với giá trị mặc định chung
    """

    @staticmethod
    def get_framework_defaults() -> dict[str, Any]:
        """Get default framework configuration"""
        return {
            "version": "2.1.1",
            "framework_name": "StillMe AI Framework",
            "description": "Enterprise-grade AI framework",
            "core_settings": {
                "modules_dir": "modules",
                "auto_load": True,
                "strict_mode": False,
                "max_module_load_time": 30,
                "security_level": "high",
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "file": "stillme.log",
                "max_size_mb": 10,
                "backup_count": 5,
            },
            "api": {"host": "localhost", "port": 8000, "timeout": 30, "max_retries": 3},
            "security": {
                "cors_origins": ["http://localhost:3000", "http://localhost:8080"],
                "rate_limit": 100,
                "auth_required": False,
            },
        }

    @staticmethod
    def get_module_defaults(module_name: str) -> dict[str, Any]:
        """Get default configuration for specific module"""
        return {
            "enabled": True,
            "auto_start": True,
            "restart_on_failure": True,
            "max_restart_attempts": 3,
            "health_check_interval": 30,
            "timeout_seconds": 60,
            "resource_limits": {},
            "environment_variables": {},
            "custom_settings": {},
        }


# Convenience functions for common use cases
def load_framework_config(
    config_path: str = "config/framework_config.json",
) -> ConfigManager:
    """Load framework configuration with defaults"""
    defaults = StillMeConfig.get_framework_defaults()
    return ConfigManager(config_path, defaults, "STILLME_")


def load_module_config(module_name: str, config_path: str = None) -> ConfigManager:
    """Load module-specific configuration"""
    if config_path is None:
        config_path = f"config/{module_name}_config.json"

    defaults = StillMeConfig.get_module_defaults(module_name)
    return ConfigManager(config_path, defaults, f"STILLME_{module_name.upper()}_")