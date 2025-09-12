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
from .config import ConfigManager, StillMeConfig, load_framework_config, load_module_config
from .logging import StructuredLogger, JsonFormatter, StandardFormatter, get_logger, get_module_logger
from .errors import StillMeException, ModuleError, ConfigurationError, APIError, SecurityError, CircuitBreakerError, ErrorHandler
from .retry import retry_with_backoff, RetryManager, CircuitBreaker, CircuitState, CircuitBreakerError
from .io import FileManager, FileFormat, FileInfo, FileOperation, read_json, write_json, read_yaml, write_yaml, async_read_json, async_write_json
from .http import AsyncHttpClient, HTTPClientConfig, HTTPRequest, HTTPResponse, HTTPMethod, HttpRequestBuilder, ResponseValidator, get_json, post_json, download_file
from .templates import TemplateManager, TemplateType, SecurityLevel, TemplateConfig, TemplateContext, SecurityValidator, create_response_template, render_secure_response
from .validation import ValidationEngine, ValidationRule, ValidationResult, ValidationSeverity, DataType, DataValidator, InputSanitizer, validate_user_input, sanitize_user_input

__all__ = [
    # Config
    "ConfigManager", "StillMeConfig", "load_framework_config", "load_module_config",
    # Logging
    "StructuredLogger", "JsonFormatter", "StandardFormatter", "get_logger", "get_module_logger",
    # Errors
    "StillMeException", "ModuleError", "ConfigurationError", "APIError", "SecurityError", "CircuitBreakerError", "ErrorHandler",
    # Retry
    "retry_with_backoff", "RetryManager", "CircuitBreaker", "CircuitState", "CircuitBreakerError",
    # I/O
    "FileManager", "FileFormat", "FileInfo", "FileOperation", "read_json", "write_json", "read_yaml", "write_yaml", "async_read_json", "async_write_json",
    # HTTP
    "AsyncHttpClient", "HTTPClientConfig", "HTTPRequest", "HTTPResponse", "HTTPMethod", "HttpRequestBuilder", "ResponseValidator", "get_json", "post_json", "download_file",
    # Templates
    "TemplateManager", "TemplateType", "SecurityLevel", "TemplateConfig", "TemplateContext", "SecurityValidator", "create_response_template", "render_secure_response",
    # Validation
    "ValidationEngine", "ValidationRule", "ValidationResult", "ValidationSeverity", "DataType", "DataValidator", "InputSanitizer", "validate_user_input", "sanitize_user_input"
]
