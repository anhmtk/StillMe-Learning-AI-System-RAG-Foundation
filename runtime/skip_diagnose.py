#!/usr/bin/env python3
"""
StillMe Skip Diagnose Function (Python)
Cài đặt hành vi Skip = Diagnose thay vì Cancel

Purpose: Chẩn đoán trạng thái task khi user bấm Skip
Usage: Gọi diagnose_on_skip() khi user bấm Skip button
"""

import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from .interaction_policy import (
    get_heartbeat_config,
    get_interaction_policy,
    get_log_tailing_config,
    get_pid_config,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SkipDiagnosisResult:
    """Result of skip diagnosis"""
    state: str  # 'COMPLETED' | 'RUNNING' | 'STALLED' | 'UNKNOWN'
    details: str
    confidence: float  # 0-1
    recommendations: List[str]
    log_snippet: Optional[str] = None
    heartbeat_status: Optional[bool] = None
    pid_status: Optional[bool] = None

@dataclass
class SkipDiagnoseOptions:
    """Options for skip diagnosis"""
    log_path: Optional[str] = None
    pid: Optional[int] = None
    heartbeat_path: Optional[str] = None
    diagnose_ms: Optional[int] = None
    process_name: Optional[str] = None
    working_directory: Optional[str] = None

def diagnose_on_skip(opts: SkipDiagnoseOptions = None) -> SkipDiagnosisResult:
    """
    Diagnose task status when Skip is pressed
    
    Args:
        opts: Diagnosis options
    
    Returns:
        SkipDiagnosisResult: Diagnosis result
    """
    if opts is None:
        opts = SkipDiagnoseOptions()

    policy = get_interaction_policy()
    log_config = get_log_tailing_config()
    heartbeat_config = get_heartbeat_config()
    pid_config = get_pid_config()

    # Set defaults
    if opts.diagnose_ms is None:
        opts.diagnose_ms = policy['skip']['timeouts']['diagnose_ms']
    if opts.working_directory is None:
        opts.working_directory = os.getcwd()

    logger.info("🔍 Diagnosing task status (Skip pressed)...")
    logger.info(f"⏱️ Diagnose timeout: {opts.diagnose_ms}ms")

    try:
        # Parallel diagnosis tasks
        log_analysis = _analyze_logs(opts.log_path, log_config, opts.working_directory)
        heartbeat_status = _check_heartbeat(opts.heartbeat_path, heartbeat_config, opts.working_directory)
        pid_status = _check_pid(opts.pid, pid_config, opts.working_directory)

        # Combine results
        result = _combine_diagnosis_results(
            log_analysis,
            heartbeat_status,
            pid_status,
            opts.diagnose_ms
        )

        logger.info(f"📊 Diagnosis result: {result.state}")
        logger.info(f"📝 Details: {result.details}")
        logger.info(f"🎯 Confidence: {result.confidence * 100:.1f}%")

        return result

    except Exception as error:
        logger.error(f"❌ Diagnosis failed: {error}")
        return SkipDiagnosisResult(
            state='UNKNOWN',
            details=f"Diagnosis failed: {error}",
            confidence=0,
            recommendations=['Check logs manually', 'Restart task if needed']
        )

def _analyze_logs(
    log_path: Optional[str],
    log_config: Dict[str, Any],
    working_directory: str
) -> Dict[str, Any]:
    """Analyze log files for task status"""
    log_files = [log_path] if log_path else _find_log_files(working_directory)

    if not log_files:
        return {'state': 'UNKNOWN', 'snippet': 'No log files found', 'confidence': 0}

    # Find the most recent log file
    latest_log = ''
    latest_size = 0

    for log_file in log_files:
        try:
            stats = os.stat(log_file)
            if stats.st_size > latest_size:
                latest_size = stats.st_size
                latest_log = log_file
        except OSError:
            # Skip inaccessible files
            continue

    if not latest_log:
        return {'state': 'UNKNOWN', 'snippet': 'No accessible log files', 'confidence': 0}

    try:
        # Read last N lines
        lines = _tail_file(latest_log, log_config['default_lines'])
        snippet = '\n'.join(lines)

        # Analyze patterns
        state = _analyze_log_patterns(lines, log_config['patterns'])
        confidence = _calculate_log_confidence(lines, log_config['patterns'])

        return {'state': state, 'snippet': snippet, 'confidence': confidence}

    except Exception as error:
        return {'state': 'UNKNOWN', 'snippet': f'Log analysis failed: {error}', 'confidence': 0}

def _check_heartbeat(
    heartbeat_path: Optional[str],
    heartbeat_config: Dict[str, Any],
    working_directory: str
) -> bool:
    """Check heartbeat status"""
    heartbeat_files = [heartbeat_path] if heartbeat_path else heartbeat_config['files']

    for heartbeat_file in heartbeat_files:
        full_path = os.path.join(working_directory, heartbeat_file)

        try:
            if os.path.exists(full_path):
                stats = os.stat(full_path)
                age = time.time() - stats.st_mtime

                # Check if heartbeat is recent
                if age < (heartbeat_config['timeout_ms'] / 1000):
                    return True
        except OSError:
            # Continue to next file
            continue

    return False

def _check_pid(
    pid: Optional[int],
    pid_config: Dict[str, Any],
    working_directory: str
) -> bool:
    """Check PID status"""
    if pid is not None:
        return _is_process_running(pid)

    # Check PID files
    for pid_file in pid_config['files']:
        full_path = os.path.join(working_directory, pid_file)

        try:
            if os.path.exists(full_path):
                with open(full_path) as f:
                    pid_content = f.read().strip()
                    pid_num = int(pid_content)

                    if _is_process_running(pid_num):
                        return True
        except (OSError, ValueError):
            # Continue to next file
            continue

    return False

def _find_log_files(working_directory: str) -> List[str]:
    """Find log files in working directory"""
    log_files = []
    common_log_paths = [
        'logs/app.log',
        'logs/error.log',
        'logs/debug.log',
        'runtime/current.log',
        'app.log',
        'error.log',
        'debug.log'
    ]

    for log_path in common_log_paths:
        full_path = os.path.join(working_directory, log_path)
        if os.path.exists(full_path):
            log_files.append(full_path)

    return log_files

def _tail_file(file_path: str, lines: int) -> List[str]:
    """Tail file to get last N lines"""
    try:
        # Use tail command if available
        result = subprocess.run(
            ['tail', '-n', str(lines), file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: read file and get last N lines
    try:
        with open(file_path, encoding='utf-8') as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception:
        return []

def _analyze_log_patterns(lines: List[str], patterns: Dict[str, List[str]]) -> str:
    """Analyze log patterns to determine state"""
    text = '\n'.join(lines).lower()

    # Check for completion patterns
    for pattern in patterns['completed']:
        if pattern.lower() in text:
            return 'COMPLETED'

    # Check for error patterns
    for pattern in patterns['error']:
        if pattern.lower() in text:
            return 'STALLED'

    # Check for running patterns
    for pattern in patterns['running']:
        if pattern.lower() in text:
            return 'RUNNING'

    return 'UNKNOWN'

def _calculate_log_confidence(lines: List[str], patterns: Dict[str, List[str]]) -> float:
    """Calculate confidence based on log analysis"""
    confidence = 0.0
    text = '\n'.join(lines).lower()

    # Higher confidence for multiple matching patterns
    completed_matches = sum(1 for p in patterns['completed'] if p.lower() in text)
    error_matches = sum(1 for p in patterns['error'] if p.lower() in text)
    running_matches = sum(1 for p in patterns['running'] if p.lower() in text)

    # Calculate confidence based on pattern matches
    total_matches = completed_matches + error_matches + running_matches
    if total_matches > 0:
        confidence = min(0.9, total_matches * 0.3)

    # Boost confidence for recent activity
    if lines:
        confidence += 0.1

    return min(1.0, confidence)

def _is_process_running(pid: int) -> bool:
    """Check if process is running"""
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False

def _combine_diagnosis_results(
    log_analysis: Dict[str, Any],
    heartbeat_status: bool,
    pid_status: bool,
    diagnose_ms: int
) -> SkipDiagnosisResult:
    """Combine diagnosis results"""
    state = log_analysis.get('state', 'UNKNOWN')
    confidence = log_analysis.get('confidence', 0.0)
    details = f"Log analysis: {state}"
    recommendations = []

    # Adjust based on heartbeat and PID
    if heartbeat_status and pid_status:
        if state == 'UNKNOWN':
            state = 'RUNNING'
            confidence = max(confidence, 0.7)
        details += ", Heartbeat: ✅, PID: ✅"
    elif pid_status:
        if state == 'UNKNOWN':
            state = 'STALLED'
            confidence = max(confidence, 0.5)
        details += ", Heartbeat: ❌, PID: ✅"
    else:
        if state == 'UNKNOWN':
            state = 'COMPLETED'
            confidence = max(confidence, 0.6)
        details += ", Heartbeat: ❌, PID: ❌"

    # Generate recommendations
    if state == 'COMPLETED':
        recommendations = ['Task completed successfully']
    elif state == 'RUNNING':
        recommendations = ['Wait for completion', 'Move to background', 'Monitor progress']
    elif state == 'STALLED':
        recommendations = ['Resume task', 'Retry task', 'Kill and restart']
    else:  # UNKNOWN
        recommendations = ['Check logs manually', 'Restart task', 'Contact support']

    return SkipDiagnosisResult(
        state=state,
        details=details,
        confidence=confidence,
        recommendations=recommendations,
        log_snippet=log_analysis.get('snippet'),
        heartbeat_status=heartbeat_status,
        pid_status=pid_status
    )

def get_diagnosis_prompt(result: SkipDiagnosisResult, language: str = 'en') -> str:
    """Get user-friendly prompt for diagnosis result"""
    from .interaction_policy import get_skip_prompt
    return get_skip_prompt(result.state, language)

def format_diagnosis_result(result: SkipDiagnosisResult, language: str = 'en') -> str:
    """Format diagnosis result for display"""
    prompt = get_diagnosis_prompt(result, language)
    confidence = f"{result.confidence * 100:.1f}"

    output = f"{prompt}\n\n"
    output += "📊 **Diagnosis Details:**\n"
    output += f"• State: {result.state}\n"
    output += f"• Confidence: {confidence}%\n"
    output += f"• Details: {result.details}\n\n"

    if result.recommendations:
        output += "💡 **Recommendations:**\n"
        for i, rec in enumerate(result.recommendations, 1):
            output += f"{i}. {rec}\n"

    if result.log_snippet:
        output += "\n📝 **Recent Log Snippet:**\n"
        output += f"```\n{result.log_snippet}\n```"

    return output

# Export for easy import
__all__ = [
    'diagnose_on_skip',
    'get_diagnosis_prompt',
    'format_diagnosis_result',
    'SkipDiagnosisResult',
    'SkipDiagnoseOptions'
]
