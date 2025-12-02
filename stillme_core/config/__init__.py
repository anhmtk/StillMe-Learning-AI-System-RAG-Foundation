"""
StillMe Core Configuration System

Provides centralized configuration management for the framework.

This module allows:
- Configuration injection instead of hardcoded values
- Environment variable support
- Type-safe configuration classes
- Easy testing with different configs
"""

from .base import BaseConfig, get_config
from .validators import ValidatorConfig

__all__ = [
    "BaseConfig",
    "get_config",
    "ValidatorConfig",
]

