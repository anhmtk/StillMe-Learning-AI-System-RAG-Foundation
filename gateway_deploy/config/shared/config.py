"""
Shared Configuration - Configuration chung cho toàn bộ hệ thống

This module provides shared configuration that applies to all components:
- Database settings
- Logging configuration
- Security settings
- Common environment variables

Author: StillMe AI Team
Version: 2.0.0
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class SharedConfig:
    """Shared configuration for all StillMe components"""

    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///stillme.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    cors_origins: str = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    )

    # Common environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def from_env(cls) -> "SharedConfig":
        """Create SharedConfig from environment variables"""
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "database_url": self.database_url,
            "redis_url": self.redis_url,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "secret_key": self.secret_key,
            "cors_origins": self.cors_origins,
            "environment": self.environment,
            "debug": self.debug,
        }
