"""
Configuration Manager - Quản lý configuration hierarchy

This module provides centralized configuration management with clear precedence:
1. Environment variables (highest priority)
2. Component-specific config
3. Shared config (lowest priority)

Author: StillMe AI Team
Version: 2.0.0
"""

import os
from typing import Dict, Any, Optional
from .shared.config import SharedConfig
from .core.config import CoreConfig
from .agent_dev.config import AgentDevConfig
from .platform.config import PlatformConfig

class ConfigManager:
    """Centralized configuration manager with hierarchy support"""
    
    def __init__(self):
        self.shared_config = SharedConfig.from_env()
        self.core_config = CoreConfig.from_env()
        self.agent_dev_config = AgentDevConfig.from_env()
        self.platform_config = PlatformConfig.from_env()
        
        # Configuration precedence order
        self.config_sources = [
            "config/shared/",
            "config/core/",
            "config/agent-dev/",
            "config/platform/"
        ]
    
    def get_config(self, component: str) -> Dict[str, Any]:
        """Get configuration for specific component"""
        configs = {
            "shared": self.shared_config.to_dict(),
            "core": self.core_config.to_dict(),
            "agent-dev": self.agent_dev_config.to_dict(),
            "platform": self.platform_config.to_dict()
        }
        
        if component not in configs:
            raise ValueError(f"Unknown component: {component}")
        
        return configs[component]
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configurations"""
        return {
            "shared": self.shared_config.to_dict(),
            "core": self.core_config.to_dict(),
            "agent-dev": self.agent_dev_config.to_dict(),
            "platform": self.platform_config.to_dict()
        }
    
    def validate_config(self, component: str) -> bool:
        """Validate configuration for component"""
        try:
            config = self.get_config(component)
            
            # Basic validation rules
            if component == "shared":
                return bool(config.get("secret_key")) and config.get("secret_key") != "your-secret-key-here"
            elif component == "core":
                return bool(config.get("default_model")) and config.get("repo_root")
            elif component == "agent-dev":
                return config.get("min_quality_score", 0) >= 0
            elif component == "platform":
                return config.get("gateway_port", 0) > 0
            
            return True
        except Exception:
            return False
    
    def get_env_override(self, key: str) -> Optional[str]:
        """Get environment variable override"""
        return os.getenv(key)
    
    def reload_configs(self):
        """Reload all configurations from environment"""
        self.shared_config = SharedConfig.from_env()
        self.core_config = CoreConfig.from_env()
        self.agent_dev_config = AgentDevConfig.from_env()
        self.platform_config = PlatformConfig.from_env()

# Global configuration manager instance
config_manager = ConfigManager()

def get_config(component: str) -> Dict[str, Any]:
    """Get configuration for component"""
    return config_manager.get_config(component)

def get_all_configs() -> Dict[str, Dict[str, Any]]:
    """Get all configurations"""
    return config_manager.get_all_configs()

def validate_config(component: str) -> bool:
    """Validate configuration for component"""
    return config_manager.validate_config(component)
