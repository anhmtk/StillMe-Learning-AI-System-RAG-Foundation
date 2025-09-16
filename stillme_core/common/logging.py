#!/usr/bin/env python3
"""
📝 STRUCTURED LOGGING - UNIFIED LOGGING SYSTEM
📝 LOGGING CÓ CẤU TRÚC - HỆ THỐNG LOGGING THỐNG NHẤT

PURPOSE / MỤC ĐÍCH:
- Unified structured logging system for StillMe modules
- Hệ thống logging có cấu trúc thống nhất cho các modules StillMe
- JSON and standard format support
- Hỗ trợ định dạng JSON và chuẩn
- Context-aware logging with correlation IDs
- Logging nhận biết context với correlation IDs

FUNCTIONALITY / CHỨC NĂNG:
- Structured JSON logging for production
- Logging JSON có cấu trúc cho production
- Standard text logging for development
- Logging text chuẩn cho development
- File rotation and size management
- Quản lý xoay vòng và kích thước file
- Context correlation across modules
- Tương quan context giữa các modules

RELATED FILES / FILES LIÊN QUAN:
- framework.py - Framework logging integration
- modules/* - Module logging usage
- config/framework_config.json - Logging configuration
- logs/ - Log files directory

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Thread-safe logging with proper handlers
- Automatic log file rotation
- Support for multiple log levels
- Integration with external log aggregation systems
"""

import json
import logging
import logging.handlers
import sys
import threading
import time
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    Formatter JSON cho logging có cấu trúc
    """

    def __init__(self, datefmt: Optional[str] = None):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Get correlation ID from context
        corr_id = correlation_id.get()

        # Build log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add correlation ID if available
        if corr_id:
            log_entry["correlation_id"] = corr_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


class StandardFormatter(logging.Formatter):
    """
    Standard text formatter for development
    Formatter text chuẩn cho development
    """

    def __init__(self, datefmt: Optional[str] = None):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt=datefmt or "%Y-%m-%d %H:%M:%S",
        )


class StructuredLogger:
    """
    Structured logger with context support
    Logger có cấu trúc với hỗ trợ context
    """

    _loggers: Dict[str, "StructuredLogger"] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        json_format: bool = True,
        console_output: bool = True,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        """
        Initialize structured logger

        Args:
            name: Logger name
            log_file: Path to log file (optional)
            level: Logging level
            json_format: Use JSON format (True) or standard format (False)
            console_output: Enable console output
            max_file_size: Maximum log file size in bytes
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_file = log_file
        self.level = level
        self.json_format = json_format
        self.console_output = console_output
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Get or create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Setup handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup console and file handlers"""
        formatter = JsonFormatter() if self.json_format else StandardFormatter()

        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str, **kwargs) -> "StructuredLogger":
        """
        Get or create logger instance (singleton pattern)
        Lấy hoặc tạo instance logger (pattern singleton)
        """
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = cls(name, **kwargs)
            return cls._loggers[name]

    def set_correlation_id(self, corr_id: str):
        """Set correlation ID for current context"""
        correlation_id.set(corr_id)

    def clear_correlation_id(self):
        """Clear correlation ID from current context"""
        correlation_id.set(None)

    def with_correlation_id(self, corr_id: str):
        """Context manager for correlation ID"""
        return CorrelationContext(corr_id)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.info(
            f"Performance: {operation} completed in {duration:.3f}s",
            operation=operation,
            duration=duration,
            **kwargs,
        )

    def log_api_call(
        self, method: str, url: str, status_code: int, duration: float, **kwargs
    ):
        """Log API call details"""
        self.info(
            f"API Call: {method} {url} - {status_code} ({duration:.3f}s)",
            method=method,
            url=url,
            status_code=status_code,
            duration=duration,
            **kwargs,
        )

    def log_security_event(self, event_type: str, details: str, **kwargs):
        """Log security-related events"""
        self.warning(
            f"Security Event: {event_type} - {details}",
            event_type=event_type,
            details=details,
            **kwargs,
        )


class CorrelationContext:
    """Context manager for correlation ID"""

    def __init__(self, corr_id: str):
        self.corr_id = corr_id
        self.token = None

    def __enter__(self):
        self.token = correlation_id.set(self.corr_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            correlation_id.reset(self.token)


class StillMeLogger:
    """
    StillMe-specific logger with common configurations
    Logger đặc thù StillMe với cấu hình chung
    """

    @staticmethod
    def get_framework_logger() -> StructuredLogger:
        """Get framework logger with default configuration"""
        return StructuredLogger.get_logger(
            "StillMe.Framework",
            log_file="logs/framework.log",
            level=logging.INFO,
            json_format=True,
        )

    @staticmethod
    def get_module_logger(module_name: str) -> StructuredLogger:
        """Get module-specific logger"""
        return StructuredLogger.get_logger(
            f"StillMe.Modules.{module_name}",
            log_file=f"logs/{module_name}.log",
            level=logging.INFO,
            json_format=True,
        )

    @staticmethod
    def get_api_logger() -> StructuredLogger:
        """Get API logger for HTTP requests"""
        return StructuredLogger.get_logger(
            "StillMe.API", log_file="logs/api.log", level=logging.INFO, json_format=True
        )

    @staticmethod
    def get_security_logger() -> StructuredLogger:
        """Get security logger for security events"""
        return StructuredLogger.get_logger(
            "StillMe.Security",
            log_file="logs/security.log",
            level=logging.WARNING,
            json_format=True,
        )

    @staticmethod
    def get_audit_logger() -> StructuredLogger:
        """Get audit logger for compliance"""
        return StructuredLogger.get_logger(
            "StillMe.Audit",
            log_file="logs/audit.log",
            level=logging.INFO,
            json_format=True,
            console_output=False,  # Audit logs should not go to console
        )


# Convenience functions
def get_logger(name: str, **kwargs) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger.get_logger(name, **kwargs)


def get_framework_logger() -> StructuredLogger:
    """Get framework logger"""
    return StillMeLogger.get_framework_logger()


def get_module_logger(module_name: str) -> StructuredLogger:
    """Get module logger"""
    return StillMeLogger.get_module_logger(module_name)


def get_api_logger() -> StructuredLogger:
    """Get API logger"""
    return StillMeLogger.get_api_logger()


def get_security_logger() -> StructuredLogger:
    """Get security logger"""
    return StillMeLogger.get_security_logger()


def get_audit_logger() -> StructuredLogger:
    """Get audit logger"""
    return StillMeLogger.get_audit_logger()


# Performance logging decorator
def log_performance(logger: StructuredLogger, operation_name: str = None):
    """Decorator to log function performance"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance: {op_name} failed after {duration:.3f}s",
                    error=str(e),
                    operation=op_name,
                    duration=duration,
                )
                raise

        return wrapper

    return decorator
