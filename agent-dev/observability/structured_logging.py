#!/usr/bin/env python3
"""
StillMe AgentDev - Structured Logging
Enterprise-grade structured logging with correlation and context
"""

import asyncio
import json
import time
import uuid
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
import logging
import sys
from datetime import datetime

class LogLevel(Enum):
    """Log levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class LogCategory(Enum):
    """Log categories for AgentDev"""
    TASK = "TASK"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    SYSTEM = "SYSTEM"
    USER = "USER"
    API = "API"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    AUDIT = "AUDIT"

@dataclass
class LogEntry:
    """Structured log entry"""
    log_id: str
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    source: str
    correlation_id: Optional[str]
    span_id: Optional[str]
    trace_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    attributes: Dict[str, Any]
    stack_trace: Optional[str]
    tags: List[str]

class StructuredLogger:
    """Enterprise structured logging system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.log_entries: List[LogEntry] = []
        self.log_handlers: List[Any] = []
        self.correlation_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.lock = threading.RLock()
        self.max_entries = self.config.get('max_entries', 100000)
        self.enabled = True
        
        # Setup standard logging
        self._setup_standard_logging()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load logging configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/structured_logging.yaml")
            
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {
                'max_entries': 100000,
                'outputs': {
                    'console': {
                        'enabled': True,
                        'level': 'INFO',
                        'format': 'json'
                    },
                    'file': {
                        'enabled': True,
                        'path': '.agentdev/logs/agentdev.log',
                        'level': 'DEBUG',
                        'format': 'json',
                        'rotation': {
                            'enabled': True,
                            'max_size': '100MB',
                            'backup_count': 5
                        }
                    },
                    'elasticsearch': {
                        'enabled': False,
                        'host': 'localhost',
                        'port': 9200,
                        'index': 'agentdev-logs'
                    }
                },
                'correlation': {
                    'enabled': True,
                    'auto_generate': True
                },
                'performance': {
                    'enabled': True,
                    'slow_query_threshold': 1.0,
                    'memory_usage_threshold': 0.8
                }
            }
    
    def _setup_standard_logging(self):
        """Setup standard Python logging integration"""
        # Create custom formatter
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                # Convert standard log record to structured format
                log_entry = LogEntry(
                    log_id=str(uuid.uuid4()),
                    timestamp=time.time(),
                    level=LogLevel(record.levelname),
                    category=LogCategory.SYSTEM,
                    message=record.getMessage(),
                    source=f"{record.name}:{record.funcName}:{record.lineno}",
                    correlation_id=getattr(record, 'correlation_id', None),
                    span_id=getattr(record, 'span_id', None),
                    trace_id=getattr(record, 'trace_id', None),
                    user_id=getattr(record, 'user_id', None),
                    session_id=getattr(record, 'session_id', None),
                    attributes=getattr(record, 'attributes', {}),
                    stack_trace=self.formatException(record.exc_info) if record.exc_info else None,
                    tags=getattr(record, 'tags', [])
                )
                
                return json.dumps(asdict(log_entry), default=str)
        
        # Setup console handler
        if self.config['outputs']['console']['enabled']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            console_handler.setLevel(getattr(logging, self.config['outputs']['console']['level']))
            self.log_handlers.append(console_handler)
        
        # Setup file handler
        if self.config['outputs']['file']['enabled']:
            log_file = Path(self.config['outputs']['file']['path'])
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            file_handler.setLevel(getattr(logging, self.config['outputs']['file']['level']))
            self.log_handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        for handler in self.log_handlers:
            root_logger.addHandler(handler)
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context"""
        self.correlation_id = correlation_id
    
    def set_session_id(self, session_id: str):
        """Set session ID for current context"""
        self.session_id = session_id
    
    def set_user_id(self, user_id: str):
        """Set user ID for current context"""
        self.user_id = user_id
    
    def _create_log_entry(self, level: LogLevel, category: LogCategory,
                         message: str, source: str,
                         attributes: Optional[Dict[str, Any]] = None,
                         tags: Optional[List[str]] = None,
                         exception: Optional[Exception] = None) -> LogEntry:
        """Create structured log entry"""
        # Import trace context if available
        span_id = None
        trace_id = None
        try:
            from .distributed_tracing import get_current_span_id, get_current_trace_id
            span_id = get_current_span_id()
            trace_id = get_current_trace_id()
        except ImportError:
            pass
        
        # Format stack trace if exception provided
        stack_trace = None
        if exception:
            import traceback
            stack_trace = traceback.format_exc()
        
        return LogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=time.time(),
            level=level,
            category=category,
            message=message,
            source=source,
            correlation_id=self.correlation_id,
            span_id=span_id,
            trace_id=trace_id,
            user_id=self.user_id,
            session_id=self.session_id,
            attributes=attributes or {},
            stack_trace=stack_trace,
            tags=tags or []
        )
    
    def _log(self, level: LogLevel, category: LogCategory, message: str,
             source: str, attributes: Optional[Dict[str, Any]] = None,
             tags: Optional[List[str]] = None, exception: Optional[Exception] = None):
        """Internal logging method"""
        if not self.enabled:
            return
        
        log_entry = self._create_log_entry(
            level, category, message, source, attributes, tags, exception
        )
        
        with self.lock:
            self.log_entries.append(log_entry)
            
            # Limit log entries
            if len(self.log_entries) > self.max_entries:
                self.log_entries = self.log_entries[-self.max_entries:]
        
        # Output to standard logging
        logger = logging.getLogger(source)
        
        # Add custom attributes to log record
        record = logger.makeRecord(
            logger.name, level.value, source, 0, message, (), exception
        )
        record.correlation_id = log_entry.correlation_id
        record.span_id = log_entry.span_id
        record.trace_id = log_entry.trace_id
        record.user_id = log_entry.user_id
        record.session_id = log_entry.session_id
        record.attributes = log_entry.attributes
        record.tags = log_entry.tags
        
        logger.handle(record)
    
    def trace(self, message: str, source: str = "agentdev",
             attributes: Optional[Dict[str, Any]] = None,
             tags: Optional[List[str]] = None):
        """Log trace message"""
        self._log(LogLevel.TRACE, LogCategory.SYSTEM, message, source, attributes, tags)
    
    def debug(self, message: str, source: str = "agentdev",
             attributes: Optional[Dict[str, Any]] = None,
             tags: Optional[List[str]] = None):
        """Log debug message"""
        self._log(LogLevel.DEBUG, LogCategory.SYSTEM, message, source, attributes, tags)
    
    def info(self, message: str, source: str = "agentdev",
            attributes: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None):
        """Log info message"""
        self._log(LogLevel.INFO, LogCategory.SYSTEM, message, source, attributes, tags)
    
    def warn(self, message: str, source: str = "agentdev",
            attributes: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None):
        """Log warning message"""
        self._log(LogLevel.WARN, LogCategory.SYSTEM, message, source, attributes, tags)
    
    def error(self, message: str, source: str = "agentdev",
             attributes: Optional[Dict[str, Any]] = None,
             tags: Optional[List[str]] = None,
             exception: Optional[Exception] = None):
        """Log error message"""
        self._log(LogLevel.ERROR, LogCategory.SYSTEM, message, source, attributes, tags, exception)
    
    def fatal(self, message: str, source: str = "agentdev",
             attributes: Optional[Dict[str, Any]] = None,
             tags: Optional[List[str]] = None,
             exception: Optional[Exception] = None):
        """Log fatal message"""
        self._log(LogLevel.FATAL, LogCategory.SYSTEM, message, source, attributes, tags, exception)
    
    # Category-specific logging methods
    def log_task(self, level: LogLevel, message: str, task_id: str,
                attributes: Optional[Dict[str, Any]] = None,
                tags: Optional[List[str]] = None):
        """Log task-related message"""
        attrs = attributes or {}
        attrs['task_id'] = task_id
        self._log(level, LogCategory.TASK, message, "agentdev.task", attrs, tags)
    
    def log_security(self, level: LogLevel, message: str,
                    attributes: Optional[Dict[str, Any]] = None,
                    tags: Optional[List[str]] = None):
        """Log security-related message"""
        self._log(level, LogCategory.SECURITY, message, "agentdev.security", attributes, tags)
    
    def log_performance(self, level: LogLevel, message: str,
                       attributes: Optional[Dict[str, Any]] = None,
                       tags: Optional[List[str]] = None):
        """Log performance-related message"""
        self._log(level, LogCategory.PERFORMANCE, message, "agentdev.performance", attributes, tags)
    
    def log_audit(self, level: LogLevel, message: str, user_id: str,
                 attributes: Optional[Dict[str, Any]] = None,
                 tags: Optional[List[str]] = None):
        """Log audit message"""
        attrs = attributes or {}
        attrs['user_id'] = user_id
        self._log(level, LogCategory.AUDIT, message, "agentdev.audit", attrs, tags)
    
    def log_api(self, level: LogLevel, message: str, endpoint: str,
               attributes: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None):
        """Log API-related message"""
        attrs = attributes or {}
        attrs['endpoint'] = endpoint
        self._log(level, LogCategory.API, message, "agentdev.api", attrs, tags)
    
    def get_logs(self, level: Optional[LogLevel] = None,
                category: Optional[LogCategory] = None,
                source: Optional[str] = None,
                correlation_id: Optional[str] = None,
                limit: int = 100) -> List[LogEntry]:
        """Get filtered log entries"""
        with self.lock:
            filtered_logs = self.log_entries.copy()
        
        # Apply filters
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category]
        
        if source:
            filtered_logs = [log for log in filtered_logs if source in log.source]
        
        if correlation_id:
            filtered_logs = [log for log in filtered_logs if log.correlation_id == correlation_id]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_logs[:limit]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        with self.lock:
            total_logs = len(self.log_entries)
            
            # Count by level
            logs_by_level = {}
            for log in self.log_entries:
                level = log.level.value
                logs_by_level[level] = logs_by_level.get(level, 0) + 1
            
            # Count by category
            logs_by_category = {}
            for log in self.log_entries:
                category = log.category.value
                logs_by_category[category] = logs_by_category.get(category, 0) + 1
            
            # Count by source
            logs_by_source = {}
            for log in self.log_entries:
                source = log.source.split(':')[0]  # Get module name
                logs_by_source[source] = logs_by_source.get(source, 0) + 1
            
            # Get recent error rate
            recent_logs = [log for log in self.log_entries 
                          if time.time() - log.timestamp < 3600]  # Last hour
            error_count = len([log for log in recent_logs if log.level in [LogLevel.ERROR, LogLevel.FATAL]])
            error_rate = error_count / len(recent_logs) if recent_logs else 0
            
            return {
                'total_logs': total_logs,
                'logs_by_level': logs_by_level,
                'logs_by_category': logs_by_category,
                'logs_by_source': logs_by_source,
                'error_rate_last_hour': error_rate,
                'correlation_id': self.correlation_id,
                'session_id': self.session_id,
                'user_id': self.user_id
            }
    
    async def export_logs(self, file_path: str, 
                         level: Optional[LogLevel] = None,
                         category: Optional[LogCategory] = None,
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None):
        """Export logs to file"""
        try:
            logs = self.get_logs(level=level, category=category)
            
            # Filter by time range
            if start_time:
                logs = [log for log in logs if log.timestamp >= start_time]
            if end_time:
                logs = [log for log in logs if log.timestamp <= end_time]
            
            # Convert to serializable format
            export_data = {
                'export_timestamp': time.time(),
                'filters': {
                    'level': level.value if level else None,
                    'category': category.value if category else None,
                    'start_time': start_time,
                    'end_time': end_time
                },
                'logs': [asdict(log) for log in logs]
            }
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2, default=str))
            
            print(f"📄 Logs exported to: {file_path}")
            
        except Exception as e:
            print(f"⚠️ Failed to export logs: {e}")
    
    def clear_logs(self):
        """Clear all log entries"""
        with self.lock:
            self.log_entries.clear()
        print("🧹 Logs cleared")

# Global logger instance
logger = StructuredLogger()

# Convenience functions
def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    logger.set_correlation_id(correlation_id)

def set_session_id(session_id: str):
    """Set session ID for current context"""
    logger.set_session_id(session_id)

def set_user_id(user_id: str):
    """Set user ID for current context"""
    logger.set_user_id(user_id)

def log_task_start(task_id: str, task_type: str, attributes: Optional[Dict[str, Any]] = None):
    """Log task start"""
    attrs = attributes or {}
    attrs.update({
        'task_type': task_type,
        'start_time': time.time()
    })
    logger.log_task(LogLevel.INFO, f"Task started: {task_type}", task_id, attrs)

def log_task_complete(task_id: str, duration: float, attributes: Optional[Dict[str, Any]] = None):
    """Log task completion"""
    attrs = attributes or {}
    attrs.update({
        'duration': duration,
        'end_time': time.time()
    })
    logger.log_task(LogLevel.INFO, f"Task completed in {duration:.2f}s", task_id, attrs)

def log_security_event(event_type: str, severity: str, details: Dict[str, Any]):
    """Log security event"""
    level = LogLevel.ERROR if severity == 'HIGH' else LogLevel.WARN
    logger.log_security(level, f"Security event: {event_type}", details)

def log_performance_metric(metric_name: str, value: float, unit: str, attributes: Optional[Dict[str, Any]] = None):
    """Log performance metric"""
    attrs = attributes or {}
    attrs.update({
        'metric_name': metric_name,
        'value': value,
        'unit': unit
    })
    logger.log_performance(LogLevel.INFO, f"Performance metric: {metric_name} = {value} {unit}", attrs)

if __name__ == "__main__":
    async def main():
        # Example usage
        log = StructuredLogger()
        
        # Set context
        log.set_correlation_id("corr_123")
        log.set_session_id("session_456")
        log.set_user_id("user_789")
        
        # Log various types of messages
        log.info("AgentDev started", "agentdev.main")
        
        log.log_task(LogLevel.INFO, "Task started", "task_123", {
            'task_type': 'deploy_edge',
            'target': 'production'
        })
        
        log.log_security(LogLevel.WARN, "Suspicious activity detected", {
            'event_type': 'multiple_failed_logins',
            'ip_address': '192.168.1.100'
        })
        
        log.log_performance(LogLevel.INFO, "High memory usage", {
            'memory_percent': 85.5,
            'threshold': 80.0
        })
        
        log.log_audit(LogLevel.INFO, "User action", "user_789", {
            'action': 'deploy_edge',
            'resource': 'production'
        })
        
        # Get statistics
        stats = log.get_log_statistics()
        print(f"Log statistics: {stats}")
        
        # Export logs
        await log.export_logs("logs_export.json")
    
    asyncio.run(main())
