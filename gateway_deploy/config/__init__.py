"""
StillMe Configuration Management - Centralized configuration system

This module provides centralized configuration management:
- Core system configuration
- AgentDev configuration
- Platform configuration
- Shared configuration

Author: StillMe AI Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Team"

from .shared.config import SharedConfig
from .core.config import CoreConfig
from .agent_dev.config import AgentDevConfig
from .platform.config import PlatformConfig

__all__ = [
    "SharedConfig",
    "CoreConfig", 
    "AgentDevConfig",
    "PlatformConfig"
]
