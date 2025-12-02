"""
Base Configuration System

Provides base configuration class and utilities for framework components.
"""

import os
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseConfig(ABC):
    """
    Base configuration class for framework components.
    
    Subclasses should define configuration fields and their defaults.
    Values can be overridden via environment variables or direct assignment.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize configuration
        
        Args:
            **kwargs: Configuration values to override defaults
        """
        # Set defaults from class attributes
        for key, value in self._get_defaults().items():
            if not hasattr(self, key):
                setattr(self, key, value)
        
        # Override with environment variables
        for key in self._get_defaults().keys():
            env_key = self._get_env_key(key)
            if env_key in os.environ:
                env_value = os.environ[env_key]
                # Try to convert to appropriate type
                default_value = getattr(self, key, None)
                if default_value is not None:
                    env_value = self._convert_type(env_value, type(default_value))
                setattr(self, key, env_value)
        
        # Override with kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) or key in self._get_defaults():
                setattr(self, key, value)
    
    @abstractmethod
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values"""
        pass
    
    def _get_env_key(self, key: str) -> str:
        """
        Convert config key to environment variable name
        
        Default: STILLME_<UPPERCASE_KEY>
        """
        return f"STILLME_{key.upper()}"
    
    def _convert_type(self, value: str, target_type: type) -> Any:
        """Convert string value to target type"""
        if target_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return value
        else:
            return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            key: getattr(self, key)
            for key in self._get_defaults().keys()
            if hasattr(self, key)
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}({self.to_dict()})"


# Global config instance (can be set by application)
_config: Optional[BaseConfig] = None


def get_config() -> Optional[BaseConfig]:
    """Get global configuration instance"""
    return _config


def set_config(config: BaseConfig) -> None:
    """Set global configuration instance"""
    global _config
    _config = config
    logger.info(f"Global config set to {config.__class__.__name__}")

