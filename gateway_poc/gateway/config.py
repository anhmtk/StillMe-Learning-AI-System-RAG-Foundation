# Enhanced Configuration for StillMe Gateway POC
"""
Enhanced configuration management with improved security and performance settings
"""

import os
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class EnhancedSettings(BaseSettings):
    """Enhanced application settings with improved defaults"""

    # Application
    APP_NAME: str = "Enhanced StillMe Gateway"
    VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production", env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Enhanced security settings
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./gateway.db", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_PRE_PING: bool = True

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_POOL_SIZE: int = 20
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS: dict[str, int] = {
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5,  # TCP_KEEPCNT
    }

    # CORS
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS",
    )
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS"
    )

    # StillMe Integration
    STILLME_CORE_URL: str = Field(
        default="http://localhost:8000", env="STILLME_CORE_URL"
    )
    STILLME_API_KEY: Optional[str] = Field(default=None, env="STILLME_API_KEY")
    STILLME_TIMEOUT: int = 30
    STILLME_RETRY_ATTEMPTS: int = 3
    STILLME_RETRY_DELAY: int = 1

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 300
    WS_MESSAGE_TIMEOUT: int = 10
    WS_MAX_CONNECTIONS: int = 1000
    WS_MAX_MESSAGE_SIZE: int = 1024 * 1024  # 1MB

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_STORAGE: str = "redis"  # redis or memory

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: list[str] = [
        "ConnectionError",
        "TimeoutError",
        "HTTPException",
    ]

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    METRICS_PATH: str = "/metrics"
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/gateway.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    LOG_JSON_FORMAT: bool = True

    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "text/plain",
        "application/pdf",
        "application/json",
        "text/csv",
    ]

    # Performance
    ENABLE_COMPRESSION: bool = True
    COMPRESSION_MIN_SIZE: int = 1000
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000

    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CSP_POLICY: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss: ws:; frame-ancestors 'none';"

    # Notifications
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY: Optional[str] = Field(
        default=None, env="FIREBASE_PRIVATE_KEY"
    )
    FIREBASE_CLIENT_EMAIL: Optional[str] = Field(
        default=None, env="FIREBASE_CLIENT_EMAIL"
    )

    # Email notifications
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")

    # Alerting
    ENABLE_ALERTS: bool = True
    ALERT_EMAIL_RECIPIENTS: list[str] = Field(default=[], env="ALERT_EMAIL_RECIPIENTS")
    ALERT_WEBHOOK_URL: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")
    ALERT_THRESHOLDS: dict[str, int] = {
        "error_rate": 5,  # 5% error rate
        "response_time": 1000,  # 1 second
        "memory_usage": 80,  # 80% memory usage
        "cpu_usage": 80,  # 80% CPU usage
    }

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        return v

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("sqlite://", "postgresql://", "mysql://")):
            raise ValueError("Invalid DATABASE_URL format")
        return v

    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("Invalid REDIS_URL format")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True


# Global settings instance
settings = EnhancedSettings()

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
    settings.ENABLE_METRICS = True
elif os.getenv("ENVIRONMENT") == "staging":
    settings.DEBUG = False
    settings.LOG_LEVEL = "INFO"
    settings.ENABLE_METRICS = True
elif os.getenv("ENVIRONMENT") == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
    settings.ENABLE_METRICS = True
