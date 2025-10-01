#!/usr/bin/env python3
"""
Advanced Debugging System - Debug Session Management & Troubleshooting
Hệ thống debug nâng cao cho AgentDev Unified

Tính năng:
1. Debug Session Management - Quản lý debug sessions
2. Error Pattern Recognition - Nhận dạng pattern lỗi
3. Root Cause Analysis - Phân tích root cause
4. Troubleshooting Guides - Hướng dẫn troubleshoot
5. Log Analysis - Phân tích logs
6. Error Injection Testing - Test error injection
"""

import os
import re
import json
import time
import traceback
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import threading
import queue

class DebugLevel(Enum):
    """Mức độ debug"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"

class ErrorType(Enum):
    """Loại lỗi"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ERROR = "performance_error"
    SECURITY_ERROR = "security_error"
    INTEGRATION_ERROR = "integration_error"
    DATA_ERROR = "data_error"
    CONFIGURATION_ERROR = "configuration_error"

class DebugSessionStatus(Enum):
    """Trạng thái debug session"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class ErrorPattern:
    """Pattern lỗi"""
    pattern_id: str
    error_type: ErrorType
    pattern_regex: str
    description: str
    frequency: int
    severity: DebugLevel
    common_causes: List[str]
    solutions: List[str]
    last_seen: datetime

@dataclass
class DebugSession:
    """Debug session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: DebugSessionStatus
    error_count: int
    warnings_count: int
    logs: List[Dict[str, Any]]
    error_patterns: List[ErrorPattern]
    root_cause: Optional[str]
    resolution: Optional[str]
    duration: Optional[float]

@dataclass
class LogEntry:
    """Log entry"""
    timestamp: datetime
    level: DebugLevel
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    session_id: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class RootCauseAnalysis:
    """Phân tích root cause"""
    analysis_id: str
    error_patterns: List[ErrorPattern]
    timeline: List[LogEntry]
    probable_causes: List[str]
    confidence_score: float
    recommendations: List[str]
    analysis_time: float

@dataclass
class DebuggingReport:
    """Báo cáo debugging"""
    total_sessions: int
    active_sessions: int
    error_patterns_found: int
    common_errors: List[Tuple[str, int]]
    performance_issues: List[str]
    security_issues: List[str]
    recommendations: List[str]
    analysis_time: float

class AdvancedDebuggingSystem:
    """Advanced Debugging System - Hệ thống debug nâng cao"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.debug_sessions_dir = self.project_root / "debug_sessions"
        self.troubleshooting_dir = self.project_root / "docs" / "troubleshooting"

        # Tạo thư mục cần thiết
        self._ensure_directories()

        # Initialize logging
        self._setup_logging()

        # Error patterns database
        self.error_patterns = self._load_error_patterns()

        # Active debug sessions
        self.active_sessions: Dict[str, DebugSession] = {}
        self.session_counter = 0

        # Log queue for real-time processing
        self.log_queue = queue.Queue()
        self.log_processor_thread = threading.Thread(target=self._process_logs, daemon=True)
        self.log_processor_thread.start()

    def _ensure_directories(self):
        """Đảm bảo thư mục cần thiết tồn tại"""
        for dir_path in [self.logs_dir, self.debug_sessions_dir, self.troubleshooting_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging system"""
        log_file = self.logs_dir / f"agentdev_debug_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger("AgentDevDebug")

    def _load_error_patterns(self) -> Dict[str, ErrorPattern]:
        """Load error patterns database"""
        patterns = {
            "syntax_error": ErrorPattern(
                pattern_id="syntax_error",
                error_type=ErrorType.SYNTAX_ERROR,
                pattern_regex=r"SyntaxError|IndentationError|TabError",
                description="Python syntax errors",
                frequency=0,
                severity=DebugLevel.ERROR,
                common_causes=[
                    "Missing colon after if/for/while statements",
                    "Incorrect indentation",
                    "Missing parentheses or brackets",
                    "Invalid variable names"
                ],
                solutions=[
                    "Check syntax with Python linter",
                    "Verify indentation consistency",
                    "Use IDE with syntax highlighting",
                    "Run code through syntax checker"
                ],
                last_seen=datetime.now()
            ),
            "import_error": ErrorPattern(
                pattern_id="import_error",
                error_type=ErrorType.RUNTIME_ERROR,
                pattern_regex=r"ImportError|ModuleNotFoundError",
                description="Module import errors",
                frequency=0,
                severity=DebugLevel.ERROR,
                common_causes=[
                    "Missing dependencies",
                    "Incorrect module path",
                    "Virtual environment not activated",
                    "Package not installed"
                ],
                solutions=[
                    "Install missing packages",
                    "Check PYTHONPATH",
                    "Activate virtual environment",
                    "Verify package installation"
                ],
                last_seen=datetime.now()
            ),
            "attribute_error": ErrorPattern(
                pattern_id="attribute_error",
                error_type=ErrorType.RUNTIME_ERROR,
                pattern_regex=r"AttributeError",
                description="Attribute access errors",
                frequency=0,
                severity=DebugLevel.ERROR,
                common_causes=[
                    "Object doesn't have the attribute",
                    "Typo in attribute name",
                    "Object is None",
                    "Wrong object type"
                ],
                solutions=[
                    "Check object type and attributes",
                    "Verify attribute name spelling",
                    "Add null checks",
                    "Use hasattr() before access"
                ],
                last_seen=datetime.now()
            ),
            "key_error": ErrorPattern(
                pattern_id="key_error",
                error_type=ErrorType.RUNTIME_ERROR,
                pattern_regex=r"KeyError",
                description="Dictionary key errors",
                frequency=0,
                severity=DebugLevel.ERROR,
                common_causes=[
                    "Key doesn't exist in dictionary",
                    "Typo in key name",
                    "Dictionary is empty",
                    "Key was deleted"
                ],
                solutions=[
                    "Check if key exists before access",
                    "Use dict.get() with default value",
                    "Verify key spelling",
                    "Add key existence checks"
                ],
                last_seen=datetime.now()
            ),
            "timeout_error": ErrorPattern(
                pattern_id="timeout_error",
                error_type=ErrorType.PERFORMANCE_ERROR,
                pattern_regex=r"TimeoutError|timeout",
                description="Operation timeout errors",
                frequency=0,
                severity=DebugLevel.WARNING,
                common_causes=[
                    "Network connectivity issues",
                    "Server overload",
                    "Insufficient resources",
                    "Long-running operations"
                ],
                solutions=[
                    "Increase timeout values",
                    "Optimize operation performance",
                    "Add retry mechanisms",
                    "Check resource availability"
                ],
                last_seen=datetime.now()
            ),
            "memory_error": ErrorPattern(
                pattern_id="memory_error",
                error_type=ErrorType.PERFORMANCE_ERROR,
                pattern_regex=r"MemoryError|out of memory",
                description="Memory allocation errors",
                frequency=0,
                severity=DebugLevel.CRITICAL,
                common_causes=[
                    "Insufficient system memory",
                    "Memory leaks",
                    "Large data processing",
                    "Inefficient memory usage"
                ],
                solutions=[
                    "Optimize memory usage",
                    "Use generators for large datasets",
                    "Implement memory monitoring",
                    "Add garbage collection"
                ],
                last_seen=datetime.now()
            )
        }

        return patterns

    def start_debug_session(self, session_name: str = None) -> str:
        """Bắt đầu debug session mới"""
        self.session_counter += 1
        session_id = f"debug_session_{self.session_counter}_{int(time.time())}"

        if not session_name:
            session_name = f"Debug Session {self.session_counter}"

        session = DebugSession(
            session_id=session_id,
            start_time=datetime.now(),
            end_time=None,
            status=DebugSessionStatus.ACTIVE,
            error_count=0,
            warnings_count=0,
            logs=[],
            error_patterns=[],
            root_cause=None,
            resolution=None,
            duration=None
        )

        self.active_sessions[session_id] = session

        self.logger.info(f"Started debug session: {session_id}")
        return session_id

    def end_debug_session(self, session_id: str, resolution: str = None) -> DebugSession:
        """Kết thúc debug session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Debug session {session_id} not found")

        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        session.status = DebugSessionStatus.COMPLETED
        session.duration = (session.end_time - session.start_time).total_seconds()
        session.resolution = resolution

        # Save session to file
        self._save_debug_session(session)

        # Remove from active sessions
        del self.active_sessions[session_id]

        self.logger.info(f"Ended debug session: {session_id}, duration: {session.duration:.2f}s")
        return session

    def log_debug_event(self, level: DebugLevel, message: str, module: str = "",
                       function: str = "", line_number: int = 0, session_id: str = None,
                       metadata: Dict[str, Any] = None) -> LogEntry:
        """Log debug event"""
        if metadata is None:
            metadata = {}

        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            thread_id=threading.current_thread().ident,
            session_id=session_id,
            metadata=metadata
        )

        # Add to queue for processing
        self.log_queue.put(log_entry)

        # Add to active session if exists
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id].logs.append(asdict(log_entry))

            if level in [DebugLevel.ERROR, DebugLevel.CRITICAL]:
                self.active_sessions[session_id].error_count += 1
            elif level == DebugLevel.WARNING:
                self.active_sessions[session_id].warnings_count += 1

        return log_entry

    def _process_logs(self):
        """Process logs in background thread"""
        while True:
            try:
                log_entry = self.log_queue.get(timeout=1)

                # Analyze for error patterns
                self._analyze_error_patterns(log_entry)

                # Write to log file
                self.logger.log(
                    getattr(logging, log_entry.level.value.upper()),
                    f"[{log_entry.module}:{log_entry.function}:{log_entry.line_number}] {log_entry.message}"
                )

                self.log_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing log: {e}")

    def _analyze_error_patterns(self, log_entry: LogEntry):
        """Phân tích error patterns trong log"""
        for pattern_id, pattern in self.error_patterns.items():
            if re.search(pattern.pattern_regex, log_entry.message, re.IGNORECASE):
                # Update pattern frequency
                pattern.frequency += 1
                pattern.last_seen = log_entry.timestamp

                # Add to session if active
                if log_entry.session_id and log_entry.session_id in self.active_sessions:
                    self.active_sessions[log_entry.session_id].error_patterns.append(pattern)

                self.logger.warning(f"Error pattern detected: {pattern_id} - {log_entry.message}")

    def analyze_root_cause(self, session_id: str) -> RootCauseAnalysis:
        """Phân tích root cause cho debug session"""
        start_time = time.time()

        if session_id not in self.active_sessions:
            # Try to load from saved sessions
            session = self._load_debug_session(session_id)
            if not session:
                raise ValueError(f"Debug session {session_id} not found")
        else:
            session = self.active_sessions[session_id]

        # Analyze error patterns
        error_patterns = session.error_patterns
        timeline = [LogEntry(**log) for log in session.logs]

        # Find probable causes
        probable_causes = []
        for pattern in error_patterns:
            if hasattr(pattern, 'common_causes'):
                probable_causes.extend(pattern.common_causes)
            elif isinstance(pattern, dict) and 'common_causes' in pattern:
                probable_causes.extend(pattern['common_causes'])

        # Remove duplicates
        probable_causes = list(set(probable_causes))

        # Calculate confidence score
        confidence_score = min(len(error_patterns) * 0.2, 1.0)

        # Generate recommendations
        recommendations = []
        for pattern in error_patterns:
            if hasattr(pattern, 'solutions'):
                recommendations.extend(pattern.solutions)
            elif isinstance(pattern, dict) and 'solutions' in pattern:
                recommendations.extend(pattern['solutions'])

        # Remove duplicates
        recommendations = list(set(recommendations))

        analysis_time = time.time() - start_time

        analysis = RootCauseAnalysis(
            analysis_id=f"rca_{session_id}_{int(time.time())}",
            error_patterns=error_patterns,
            timeline=timeline,
            probable_causes=probable_causes,
            confidence_score=confidence_score,
            recommendations=recommendations,
            analysis_time=analysis_time
        )

        return analysis

    def create_troubleshooting_guide(self, error_type: ErrorType) -> str:
        """Tạo troubleshooting guide cho loại lỗi"""
        patterns = [p for p in self.error_patterns.values() if p.error_type == error_type]

        if not patterns:
            return ""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Troubleshooting Guide: {error_type.value.replace('_', ' ').title()}

**Generated**: {timestamp}  
**Source**: AgentDev Unified Advanced Debugging System

## Overview

This guide helps troubleshoot {error_type.value.replace('_', ' ')} issues in AgentDev Unified.

## Common Error Patterns

"""

        for pattern in patterns:
            content += f"""### {pattern.description}

**Pattern**: `{pattern.pattern_regex}`  
**Severity**: {pattern.severity.value}  
**Frequency**: {pattern.frequency} occurrences

#### Common Causes:
"""
            for cause in pattern.common_causes:
                content += f"- {cause}\n"

            content += "\n#### Solutions:\n"
            for solution in pattern.solutions:
                content += f"- {solution}\n"

            content += "\n"

        content += f"""## Debugging Steps

1. **Identify the Error**: Check logs for error patterns
2. **Analyze Context**: Review the code around the error
3. **Check Dependencies**: Verify all required modules are available
4. **Test Isolation**: Isolate the problematic code
5. **Apply Solutions**: Try the recommended solutions
6. **Monitor Results**: Check if the issue is resolved

## Prevention

- Follow best practices for {error_type.value.replace('_', ' ')}
- Implement proper error handling
- Use logging for debugging
- Regular code reviews
- Automated testing

## Tools

- AgentDev Unified Debugging System
- Python debugger (pdb)
- Log analysis tools
- Performance profilers

## Notes

- This guide is automatically maintained
- Last updated: {timestamp}
- For additional help, refer to AgentDev Unified documentation
"""

        # Save troubleshooting guide
        filename = f"troubleshooting_{error_type.value}.md"
        file_path = self.troubleshooting_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(file_path)

    def _save_debug_session(self, session: DebugSession):
        """Lưu debug session vào file"""
        filename = f"session_{session.session_id}.json"
        file_path = self.debug_sessions_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(session), f, indent=2, default=str)

    def _load_debug_session(self, session_id: str) -> Optional[DebugSession]:
        """Load debug session từ file"""
        filename = f"session_{session_id}.json"
        file_path = self.debug_sessions_dir / filename

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert back to DebugSession
            session = DebugSession(**data)
            return session
        except Exception as e:
            self.logger.error(f"Error loading debug session {session_id}: {e}")
            return None

    def generate_debugging_report(self) -> DebuggingReport:
        """Tạo báo cáo debugging"""
        start_time = time.time()

        # Load all debug sessions
        session_files = list(self.debug_sessions_dir.glob("session_*.json"))
        total_sessions = len(session_files)
        active_sessions = len(self.active_sessions)

        # Analyze error patterns
        error_patterns_found = len(self.error_patterns)
        error_counts = Counter()

        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for pattern_data in data.get('error_patterns', []):
                    error_counts[pattern_data['pattern_id']] += 1
            except Exception as e:
                self.logger.error(f"Error analyzing session {session_file}: {e}")

        common_errors = error_counts.most_common(10)

        # Identify performance and security issues
        performance_issues = []
        security_issues = []

        for pattern_id, pattern in self.error_patterns.items():
            if pattern.error_type == ErrorType.PERFORMANCE_ERROR:
                performance_issues.append(f"{pattern.description}: {pattern.frequency} occurrences")
            elif pattern.error_type == ErrorType.SECURITY_ERROR:
                security_issues.append(f"{pattern.description}: {pattern.frequency} occurrences")

        # Generate recommendations
        recommendations = []
        if total_sessions > 0:
            recommendations.append("Review common error patterns and implement preventive measures")
        if performance_issues:
            recommendations.append("Address performance issues to improve system stability")
        if security_issues:
            recommendations.append("Investigate and resolve security-related errors immediately")

        analysis_time = time.time() - start_time

        return DebuggingReport(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            error_patterns_found=error_patterns_found,
            common_errors=common_errors,
            performance_issues=performance_issues,
            security_issues=security_issues,
            recommendations=recommendations,
            analysis_time=analysis_time
        )

    def save_debugging_report(self, report: DebuggingReport) -> str:
        """Lưu báo cáo debugging"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save JSON report
        json_path = self.project_root / "artifacts" / f"debugging_report_{timestamp}.json"
        json_path.parent.mkdir(exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        return str(json_path)

def main():
    """Main function for testing"""
    debug_system = AdvancedDebuggingSystem(".")

    # Start debug session
    session_id = debug_system.start_debug_session("Test Session")

    # Log some events
    debug_system.log_debug_event(
        DebugLevel.INFO, "Test info message", "test_module", "test_function", 10, session_id
    )

    debug_system.log_debug_event(
        DebugLevel.ERROR, "Test error: AttributeError", "test_module", "test_function", 15, session_id
    )

    # End session
    session = debug_system.end_debug_session(session_id, "Test completed")

    # Generate report
    report = debug_system.generate_debugging_report()
    json_path = debug_system.save_debugging_report(report)

    print(f"Debugging report generated: {json_path}")
    print(f"Total sessions: {report.total_sessions}")
    print(f"Error patterns found: {report.error_patterns_found}")

if __name__ == "__main__":
    main()
