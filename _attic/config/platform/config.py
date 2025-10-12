"""
Platform Configuration - Configuration cho platform applications

This module provides platform-specific configuration:
- Desktop app settings
- Mobile app settings
- Gateway settings

Author: StillMe AI Team
Version: 2.0.0
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class PlatformConfig:
    """Platform configuration"""

    # Gateway settings
    gateway_host: str = os.getenv("GATEWAY_HOST", "localhost")
    gateway_port: int = int(os.getenv("GATEWAY_PORT", "8000"))
    gateway_workers: int = int(os.getenv("GATEWAY_WORKERS", "4"))

    # Desktop app settings
    desktop_app_port: int = int(os.getenv("DESKTOP_APP_PORT", "3000"))
    desktop_app_host: str = os.getenv("DESKTOP_APP_HOST", "localhost")

    # Mobile app settings
    mobile_app_debug: bool = os.getenv("MOBILE_APP_DEBUG", "false").lower() == "true"
    mobile_app_api_url: str = os.getenv("MOBILE_APP_API_URL", "http://localhost:8000")

    # WebSocket settings
    websocket_enabled: bool = os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true"
    websocket_port: int = int(os.getenv("WEBSOCKET_PORT", "8001"))

    @classmethod
    def from_env(cls) -> "PlatformConfig":
        """Create PlatformConfig from environment variables"""
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "gateway_host": self.gateway_host,
            "gateway_port": self.gateway_port,
            "gateway_workers": self.gateway_workers,
            "desktop_app_port": self.desktop_app_port,
            "desktop_app_host": self.desktop_app_host,
            "mobile_app_debug": self.mobile_app_debug,
            "mobile_app_api_url": self.mobile_app_api_url,
            "websocket_enabled": self.websocket_enabled,
            "websocket_port": self.websocket_port,
        }
