"""
Structured Logger Module
========================

Provides structured logging with JSON format, log levels, and context tracking.
"""

import json
import sys
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Context variables for request tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


class LogLevel(Enum):
    """Log levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry"""

    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line_number: int
    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    extra_data: dict[str, Any] | None = None
    duration_ms: float | None = None
    trace_id: str | None = None


class StructuredLogger:
    """Structured logger with JSON output and context tracking"""

    def __init__(
        self,
        name: str = "stillme",
        log_file: str | None = None,
        level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
    ):
        self.name = name
        self.level = level
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Setup log file
        if log_file:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.log_file = Path("logs") / f"{name}.jsonl"
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Thread lock for file operations
        self._lock = threading.Lock()

        # Performance tracking
        self._start_times: dict[str, float] = {}

    def _get_context(self) -> dict[str, str | None]:
        """Get current context variables"""
        return {
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "session_id": session_id_var.get(),
        }

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level"""
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_priority[level] >= level_priority[self.level]

    def _create_log_entry(
        self,
        level: LogLevel,
        message: str,
        extra_data: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> LogEntry:
        """Create a structured log entry"""
        # Get caller information
        frame = sys._getframe(2)  # Skip this method and the calling method
        module = frame.f_globals.get("__name__", "unknown")
        function = frame.f_code.co_name
        line_number = frame.f_lineno

        # Get context
        context = self._get_context()

        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            request_id=context.get("request_id"),
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            extra_data=extra_data,
            duration_ms=duration_ms,
            trace_id=str(uuid.uuid4()),
        )

    def _write_log(self, log_entry: LogEntry):
        """Write log entry to console and/or file"""
        log_dict = asdict(log_entry)

        # Console output
        if self.enable_console:
            level_colors = {
                LogLevel.DEBUG: "\033[36m",  # Cyan
                LogLevel.INFO: "\033[32m",  # Green
                LogLevel.WARNING: "\033[33m",  # Yellow
                LogLevel.ERROR: "\033[31m",  # Red
                LogLevel.CRITICAL: "\033[35m",  # Magenta
            }
            reset_color = "\033[0m"

            color = level_colors.get(LogLevel(log_entry.level), "")
            timestamp = log_entry.timestamp
            level = log_entry.level
            message = log_entry.message
            module = log_entry.module
            function = log_entry.function
            line = log_entry.line_number

            console_msg = f"{color}[{timestamp}] {level:8} {module}:{function}:{line} - {message}{reset_color}"

            if log_entry.extra_data:
                console_msg += (
                    f" | Extra: {json.dumps(log_entry.extra_data, ensure_ascii=False)}"
                )

            if log_entry.duration_ms:
                console_msg += f" | Duration: {log_entry.duration_ms:.2f}ms"

            print(console_msg)

        # File output (JSON Lines format)
        if self.enable_file:
            with self._lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_dict, ensure_ascii=False) + "\n")

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if self._should_log(LogLevel.DEBUG):
            extra_data = kwargs if kwargs else None
            log_entry = self._create_log_entry(LogLevel.DEBUG, message, extra_data)
            self._write_log(log_entry)

    def info(self, message: str, **kwargs):
        """Log info message"""
        if self._should_log(LogLevel.INFO):
            extra_data = kwargs if kwargs else None
            log_entry = self._create_log_entry(LogLevel.INFO, message, extra_data)
            self._write_log(log_entry)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if self._should_log(LogLevel.WARNING):
            extra_data = kwargs if kwargs else None
            log_entry = self._create_log_entry(LogLevel.WARNING, message, extra_data)
            self._write_log(log_entry)

    def error(self, message: str, **kwargs):
        """Log error message"""
        if self._should_log(LogLevel.ERROR):
            extra_data = kwargs if kwargs else None
            log_entry = self._create_log_entry(LogLevel.ERROR, message, extra_data)
            self._write_log(log_entry)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        if self._should_log(LogLevel.CRITICAL):
            extra_data = kwargs if kwargs else None
            log_entry = self._create_log_entry(LogLevel.CRITICAL, message, extra_data)
            self._write_log(log_entry)

    def start_timer(self, operation: str):
        """Start timing an operation"""
        self._start_times[operation] = time.time()
        self.debug(f"Started timing operation: {operation}")

    def end_timer(self, operation: str, message: str | None = None):
        """End timing an operation and log duration"""
        if operation in self._start_times:
            duration_ms = (time.time() - self._start_times[operation]) * 1000
            del self._start_times[operation]

            log_message = message or f"Completed operation: {operation}"
            extra_data = {"operation": operation, "duration_ms": duration_ms}

            if duration_ms > 1000:  # Log as warning if > 1 second
                self.warning(log_message, **extra_data)
            else:
                self.info(log_message, **extra_data)
        else:
            self.warning(f"Timer not found for operation: {operation}")

    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics"""
        extra_data = {"operation": operation, "duration_ms": duration_ms, **kwargs}

        if duration_ms > 5000:  # > 5 seconds
            self.error(f"Slow operation: {operation}", **extra_data)
        elif duration_ms > 1000:  # > 1 second
            self.warning(f"Slow operation: {operation}", **extra_data)
        else:
            self.info(f"Operation completed: {operation}", **extra_data)

    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with full context"""
        import traceback

        extra_data = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc(),
            "context": context,
        }

        self.error(f"Exception occurred: {context}", **extra_data)

    def set_context(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        """Set context variables for current thread"""
        if request_id:
            request_id_var.set(request_id)
        if user_id:
            user_id_var.set(user_id)
        if session_id:
            session_id_var.set(session_id)

    def clear_context(self):
        """Clear context variables"""
        request_id_var.set(None)
        user_id_var.set(None)
        session_id_var.set(None)

    def get_log_stats(self) -> dict[str, Any]:
        """Get logging statistics"""
        if not self.log_file.exists():
            return {"total_logs": 0, "file_size": 0}

        try:
            with open(self.log_file, encoding="utf-8") as f:
                lines = f.readlines()

            total_logs = len(lines)
            file_size = self.log_file.stat().st_size

            # Count by level
            level_counts = {}
            for line in lines:
                try:
                    log_data = json.loads(line.strip())
                    level = log_data.get("level", "UNKNOWN")
                    level_counts[level] = level_counts.get(level, 0) + 1
                except json.JSONDecodeError:
                    continue

            return {
                "total_logs": total_logs,
                "file_size": file_size,
                "file_size_mb": file_size / 1024 / 1024,
                "level_counts": level_counts,
                "log_file": str(self.log_file),
            }
        except Exception as e:
            return {"error": str(e)}


# Global logger instance
_global_logger: StructuredLogger | None = None


def get_logger(name: str = "stillme") -> StructuredLogger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger


def setup_logging(
    name: str = "stillme",
    log_file: str | None = None,
    level: LogLevel = LogLevel.INFO,
    enable_console: bool = True,
    enable_file: bool = True,
) -> StructuredLogger:
    """Setup global logging configuration"""
    global _global_logger
    _global_logger = StructuredLogger(
        name=name,
        log_file=log_file,
        level=level,
        enable_console=enable_console,
        enable_file=enable_file,
    )
    return _global_logger


# Context manager for request tracking
class LogContext:
    """Context manager for request tracking"""

    def __init__(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.logger = get_logger()

    def __enter__(self):
        self.logger.set_context(
            request_id=self.request_id, user_id=self.user_id, session_id=self.session_id
        )
        self.logger.info(f"Request started: {self.request_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.log_exception(exc_val, f"Request {self.request_id}")
        else:
            self.logger.info(f"Request completed: {self.request_id}")
        self.logger.clear_context()
