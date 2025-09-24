#!/usr/bin/env python3
"""
AgentDev Structured Logger - SEAL-GRADE
Enterprise-grade structured logging with JSON output
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import threading
from contextlib import asynccontextmanager
import sys
import traceback

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log categories"""
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"
    AI_INTERACTION = "ai_interaction"
    TOOL_EXECUTION = "tool_execution"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    ERROR = "error"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    trace_id: str
    span_id: Optional[str] = None
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    duration_ms: Optional[float] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class StructuredLogger:
    """
    SEAL-GRADE Structured Logger
    
    Features:
    - JSON structured logging
    - Trace correlation
    - Performance metrics
    - Error tracking
    - Thread-safe
    - Async support
    - File rotation
    - Log aggregation
    """
    
    def __init__(self, 
                 log_file: str = "logs/agentdev.log",
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 5,
                 log_level: LogLevel = LogLevel.INFO):
        self.log_file = Path(log_file)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.log_level = log_level
        
        # Create log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Trace context
        self._trace_context = threading.local()
        
        # Initialize logger
        self._setup_logger()
        
        # Performance metrics
        self._metrics = {
            "total_logs": 0,
            "logs_by_level": {},
            "logs_by_category": {},
            "error_count": 0,
            "last_log_time": None
        }
        
        # Log the initialization
        self.info("StructuredLogger initialized", LogCategory.SYSTEM)
    
    def _setup_logger(self):
        """Setup the underlying logger"""
        self.logger = logging.getLogger("agentdev.structured")
        self.logger.setLevel(getattr(logging, self.log_level.value))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        
        # JSON formatter
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
        
        # Store handlers for cleanup
        self._handlers = [file_handler, console_handler]
    
    def set_trace_context(self, trace_id: str, span_id: Optional[str] = None):
        """Set trace context for current thread"""
        self._trace_context.trace_id = trace_id
        self._trace_context.span_id = span_id
    
    def get_trace_context(self) -> tuple[str, Optional[str]]:
        """Get current trace context"""
        trace_id = getattr(self._trace_context, 'trace_id', None)
        span_id = getattr(self._trace_context, 'span_id', None)
        return trace_id, span_id
    
    def _create_log_entry(self, 
                         level: LogLevel,
                         category: LogCategory,
                         message: str,
                         **kwargs) -> LogEntry:
        """Create a structured log entry"""
        trace_id, span_id = self.get_trace_context()
        
        # Generate trace_id if not set
        if not trace_id:
            trace_id = str(uuid.uuid4())
            self.set_trace_context(trace_id)
        
        return LogEntry(
            timestamp=time.time(),
            level=level,
            category=category,
            message=message,
            trace_id=trace_id,
            span_id=span_id,
            **kwargs
        )
    
    def _log_entry(self, log_entry: LogEntry):
        """Log a structured entry"""
        with self._lock:
            # Update metrics
            self._metrics["total_logs"] += 1
            self._metrics["last_log_time"] = log_entry.timestamp
            
            level_name = log_entry.level.value
            category_name = log_entry.category.value
            
            self._metrics["logs_by_level"][level_name] = \
                self._metrics["logs_by_level"].get(level_name, 0) + 1
            self._metrics["logs_by_category"][category_name] = \
                self._metrics["logs_by_category"].get(category_name, 0) + 1
            
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self._metrics["error_count"] += 1
            
            # Convert to dict and serialize enums properly
            log_dict = asdict(log_entry)
            log_dict["level"] = log_entry.level.value
            log_dict["category"] = log_entry.category.value
            
            # Log the entry
            self.logger.log(
                getattr(logging, level_name),
                json.dumps(log_dict, default=str)
            )
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log debug message"""
        if self.log_level.value <= LogLevel.DEBUG.value:
            entry = self._create_log_entry(LogLevel.DEBUG, category, message, **kwargs)
            self._log_entry(entry)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log info message"""
        if self.log_level.value <= LogLevel.INFO.value:
            entry = self._create_log_entry(LogLevel.INFO, category, message, **kwargs)
            self._log_entry(entry)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log warning message"""
        if self.log_level.value <= LogLevel.WARNING.value:
            entry = self._create_log_entry(LogLevel.WARNING, category, message, **kwargs)
            self._log_entry(entry)
    
    def error(self, message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
        """Log error message"""
        if self.log_level.value <= LogLevel.ERROR.value:
            # Add stack trace for errors
            if 'stack_trace' not in kwargs:
                kwargs['stack_trace'] = traceback.format_exc()
            
            entry = self._create_log_entry(LogLevel.ERROR, category, message, **kwargs)
            self._log_entry(entry)
    
    def critical(self, message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
        """Log critical message"""
        # Critical messages should always be logged regardless of log level
        # Add stack trace for critical errors
        if 'stack_trace' not in kwargs:
            kwargs['stack_trace'] = traceback.format_exc()
        
        entry = self._create_log_entry(LogLevel.CRITICAL, category, message, **kwargs)
        self._log_entry(entry)
    
    def log_tool_execution(self, 
                          tool_name: str,
                          job_id: str,
                          duration_ms: float,
                          status: str,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          error_message: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Log tool execution"""
        level = LogLevel.ERROR if status == "failed" else LogLevel.INFO
        category = LogCategory.TOOL_EXECUTION
        
        self._log_entry(self._create_log_entry(
            level=level,
            category=category,
            message=f"Tool execution: {tool_name}",
            tool_name=tool_name,
            job_id=job_id,
            duration_ms=duration_ms,
            status=status,
            user_id=user_id,
            session_id=session_id,
            error_message=error_message,
            metadata=metadata
        ))
    
    def log_ai_interaction(self,
                          job_id: str,
                          model: str,
                          tokens_in: int,
                          tokens_out: int,
                          duration_ms: float,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Log AI interaction"""
        self._log_entry(self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.AI_INTERACTION,
            message=f"AI interaction: {model}",
            job_id=job_id,
            duration_ms=duration_ms,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                **(metadata or {})
            }
        ))
    
    def log_security_event(self,
                          event_type: str,
                          severity: str,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Log security event"""
        level = LogLevel.CRITICAL if severity == "critical" else LogLevel.WARNING
        
        self._log_entry(self._create_log_entry(
            level=level,
            category=LogCategory.SECURITY,
            message=f"Security event: {event_type}",
            user_id=user_id,
            session_id=session_id,
            metadata={
                "event_type": event_type,
                "severity": severity,
                **(metadata or {})
            }
        ))
    
    def log_performance_metric(self,
                              metric_name: str,
                              value: float,
                              unit: str,
                              job_id: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None):
        """Log performance metric"""
        self._log_entry(self._create_log_entry(
            level=LogLevel.INFO,
            category=LogCategory.PERFORMANCE,
            message=f"Performance metric: {metric_name}",
            job_id=job_id,
            metadata={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                **(metadata or {})
            }
        ))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics"""
        with self._lock:
            return self._metrics.copy()
    
    def clear_metrics(self):
        """Clear logging metrics"""
        with self._lock:
            self._metrics = {
                "total_logs": 0,
                "logs_by_level": {},
                "logs_by_category": {},
                "error_count": 0,
                "last_log_time": None
            }
    
    def close(self):
        """Close logger and cleanup handlers"""
        for handler in getattr(self, '_handlers', []):
            handler.close()
            self.logger.removeHandler(handler)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        try:
            # Parse the JSON message
            log_data = json.loads(record.getMessage())
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        except (json.JSONDecodeError, TypeError):
            # Fallback to simple format
            return json.dumps({
                "timestamp": time.time(),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            }, ensure_ascii=False, separators=(',', ':'))

# Global logger instance
_global_logger: Optional[StructuredLogger] = None

def get_logger() -> StructuredLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger()
    return _global_logger

def set_global_logger(logger: StructuredLogger):
    """Set global logger instance"""
    global _global_logger
    _global_logger = logger

# Convenience functions
def debug(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """Log debug message"""
    get_logger().debug(message, category, **kwargs)

def info(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """Log info message"""
    get_logger().info(message, category, **kwargs)

def warning(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """Log warning message"""
    get_logger().warning(message, category, **kwargs)

def error(message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
    """Log error message"""
    get_logger().error(message, category, **kwargs)

def critical(message: str, category: LogCategory = LogCategory.ERROR, **kwargs):
    """Log critical message"""
    get_logger().critical(message, category, **kwargs)
