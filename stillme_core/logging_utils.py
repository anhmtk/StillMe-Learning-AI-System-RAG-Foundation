"""Logging Utilities for StillMe Framework"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def setup_logger(
    name: str = "stillme",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Setup logger with consistent configuration"""
    try:
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatter
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Prevent duplicate logs
        logger.propagate = False

        logger.info(
            f"✅ Logger '{name}' initialized (level: {logging.getLevelName(level)})"
        )
        return logger

    except Exception as e:
        print(f"❌ Failed to setup logger: {e}")
        return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger, level: int, message: str, context: dict[str, Any] = None
):
    """Log message with additional context"""
    try:
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            full_message = f"{message} | Context: {context_str}"
        else:
            full_message = message

        logger.log(level, full_message)

    except Exception as e:
        logger.error(f"❌ Failed to log with context: {e}")


def get_logger(name: str = "stillme") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def log_function_call(
    logger: logging.Logger,
    function_name: str,
    args: tuple = None,
    kwargs: dict = None,
    result: Any = None,
    duration: float = None,
):
    """Log function call details"""
    try:
        context = {"function": function_name, "timestamp": datetime.now().isoformat()}

        if args:
            context["args"] = str(args)
        if kwargs:
            context["kwargs"] = str(kwargs)
        if result is not None:
            context["result"] = str(result)
        if duration is not None:
            context["duration"] = f"{duration:.3f}s"

        log_with_context(
            logger, logging.INFO, f"Function call: {function_name}", context
        )

    except Exception as e:
        logger.error(f"❌ Failed to log function call: {e}")


def log_error(logger: logging.Logger, error: Exception, context: dict[str, Any] = None):
    """Log error with context"""
    try:
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        if context:
            error_context.update(context)

        log_with_context(
            logger, logging.ERROR, f"Error occurred: {error}", error_context
        )

    except Exception as e:
        logger.error(f"❌ Failed to log error: {e}")


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    metrics: dict[str, Any] = None,
):
    """Log performance metrics"""
    try:
        context = {
            "operation": operation,
            "duration": f"{duration:.3f}s",
            "timestamp": datetime.now().isoformat(),
        }

        if metrics:
            context.update(metrics)

        log_with_context(logger, logging.INFO, f"Performance: {operation}", context)

    except Exception as e:
        logger.error(f"❌ Failed to log performance: {e}")


def log_security_event(
    logger: logging.Logger,
    event: str,
    severity: str = "medium",
    details: dict[str, Any] = None,
):
    """Log security event"""
    try:
        context = {
            "event": event,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        }

        if details:
            context.update(details)

        # Use appropriate log level based on severity
        if severity.lower() == "critical":
            log_level = logging.CRITICAL
        elif severity.lower() == "high":
            log_level = logging.ERROR
        elif severity.lower() == "medium":
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        log_with_context(logger, log_level, f"Security event: {event}", context)

    except Exception as e:
        logger.error(f"❌ Failed to log security event: {e}")


def log_audit(
    logger: logging.Logger,
    action: str,
    user: str = None,
    resource: str = None,
    details: dict[str, Any] = None,
):
    """Log audit trail"""
    try:
        context = {"action": action, "timestamp": datetime.now().isoformat()}

        if user:
            context["user"] = user
        if resource:
            context["resource"] = resource
        if details:
            context.update(details)

        log_with_context(logger, logging.INFO, f"Audit: {action}", context)

    except Exception as e:
        logger.error(f"❌ Failed to log audit: {e}")


# Global logger instance
_global_logger = None


def get_global_logger() -> logging.Logger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger("stillme_global")
    return _global_logger
