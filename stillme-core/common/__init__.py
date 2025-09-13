#!/usr/bin/env python3
"""
🔧 COMMON UTILITIES - SHARED FUNCTIONALITY
🔧 TIỆN ÍCH CHUNG - CHỨC NĂNG DÙNG CHUNG

PURPOSE / MỤC ĐÍCH:
- Shared utilities and common functionality across StillMe modules
- Tiện ích dùng chung và chức năng chung cho các modules StillMe
- Reduces code duplication and improves maintainability
- Giảm trùng lặp code và cải thiện khả năng bảo trì

MODULES / CÁC MODULE:
- config: Configuration management
- logging: Structured logging utilities
- errors: Exception handling patterns
- retry: Retry mechanisms with backoff
- http: HTTP client utilities
- io: File I/O helpers
- templates: Response templates
- metrics: Performance metrics
- cache: Caching utilities

USAGE / CÁCH SỬ DỤNG:
from common.config import ConfigManager
from common.logging import StructuredLogger
from common.errors import StillMeException
"""

__version__ = "1.0.0"
__author__ = "StillMe Framework Team"

# Import main utilities for easy access
from .config import (
    ConfigManager,
    StillMeConfig,
    load_framework_config,
    load_module_config,
)
from .errors import (
    APIError,
    CircuitBreakerError,
    ConfigurationError,
    ErrorHandler,
    ModuleError,
    SecurityError,
    StillMeException,
)
from .http import (
    AsyncHttpClient,
    HTTPClientConfig,
    HTTPMethod,
    HTTPRequest,
    HttpRequestBuilder,
    HTTPResponse,
    ResponseValidator,
    download_file,
    get_json,
    post_json,
)
from .io import (
    FileFormat,
    FileInfo,
    FileManager,
    FileOperation,
    async_read_json,
    async_write_json,
    read_json,
    read_yaml,
    write_json,
    write_yaml,
)
from .logging import (
    JsonFormatter,
    StandardFormatter,
    StructuredLogger,
    get_logger,
    get_module_logger,
)
from .retry import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    RetryManager,
    retry_with_backoff,
)
from .templates import (
    SecurityLevel,
    SecurityValidator,
    TemplateConfig,
    TemplateContext,
    TemplateManager,
    TemplateType,
    create_response_template,
    render_secure_response,
)
from .validation import (
    DataType,
    DataValidator,
    InputSanitizer,
    ValidationEngine,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    sanitize_user_input,
    validate_user_input,
)

__all__ = [
    # Config
    "ConfigManager",
    "StillMeConfig",
    "load_framework_config",
    "load_module_config",
    # Logging
    "StructuredLogger",
    "JsonFormatter",
    "StandardFormatter",
    "get_logger",
    "get_module_logger",
    # Errors
    "StillMeException",
    "ModuleError",
    "ConfigurationError",
    "APIError",
    "SecurityError",
    "CircuitBreakerError",
    "ErrorHandler",
    # Retry
    "retry_with_backoff",
    "RetryManager",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerError",
    # I/O
    "FileManager",
    "FileFormat",
    "FileInfo",
    "FileOperation",
    "read_json",
    "write_json",
    "read_yaml",
    "write_yaml",
    "async_read_json",
    "async_write_json",
    # HTTP
    "AsyncHttpClient",
    "HTTPClientConfig",
    "HTTPRequest",
    "HTTPResponse",
    "HTTPMethod",
    "HttpRequestBuilder",
    "ResponseValidator",
    "get_json",
    "post_json",
    "download_file",
    # Templates
    "TemplateManager",
    "TemplateType",
    "SecurityLevel",
    "TemplateConfig",
    "TemplateContext",
    "SecurityValidator",
    "create_response_template",
    "render_secure_response",
    # Validation
    "ValidationEngine",
    "ValidationRule",
    "ValidationResult",
    "ValidationSeverity",
    "DataType",
    "DataValidator",
    "InputSanitizer",
    "validate_user_input",
    "sanitize_user_input",
]
