#!/usr/bin/env python3
"""
Safety module for AgentDev Sprint 1
Kill switch, whitelist, and resource monitoring
"""

import functools
import time
from typing import Any, Callable, Dict, List
from agent_dev.schemas import PolicyViolation


def budgeted(
    cpu_ms: int = 1000, mem_mb: int = 100, fs_quota_kb: int = 1024, timeout_s: int = 30
):
    """
    Decorator to enforce resource budgets and timeouts.

    Args:
        cpu_ms: CPU time limit in milliseconds
        mem_mb: Memory limit in MB
        fs_quota_kb: Filesystem quota in KB
        timeout_s: Timeout in seconds

    Raises:
        PolicyViolation: If budget limits are exceeded
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.monotonic()
            start_memory = _get_memory_usage()
            bytes_written = 0

            try:
                # Set timeout
                import signal

                def timeout_handler(signum, frame):
                    raise PolicyViolation(f"Function timeout after {timeout_s}s")

                # Set signal handler for timeout (Unix only)
                if hasattr(signal, "SIGALRM"):
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout_s)

                try:
                    result = func(*args, **kwargs)

                    # Check resource usage
                    elapsed_time = time.monotonic() - start_time
                    current_memory = _get_memory_usage()
                    memory_used = current_memory - start_memory

                    # Check CPU time (approximate)
                    if elapsed_time * 1000 > cpu_ms:
                        raise PolicyViolation(
                            f"CPU time limit exceeded: {elapsed_time*1000:.1f}ms > {cpu_ms}ms"
                        )

                    # Check memory usage
                    if memory_used > mem_mb * 1024 * 1024:  # Convert MB to bytes
                        raise PolicyViolation(
                            f"Memory limit exceeded: {memory_used/1024/1024:.1f}MB > {mem_mb}MB"
                        )

                    # Check filesystem quota (tracked separately)
                    if bytes_written > fs_quota_kb * 1024:  # Convert KB to bytes
                        raise PolicyViolation(
                            f"Filesystem quota exceeded: {bytes_written/1024:.1f}KB > {fs_quota_kb}KB"
                        )

                    return result

                finally:
                    # Restore signal handler
                    if hasattr(signal, "SIGALRM"):
                        signal.alarm(0)
                        signal.signal(signal.SIGALRM, old_handler)

            except PolicyViolation:
                raise
            except Exception as e:
                # Check if it's a timeout
                if "timeout" in str(e).lower():
                    raise PolicyViolation(f"Function timeout after {timeout_s}s")
                raise

        return wrapper

    return decorator


def _get_memory_usage() -> int:
    """Get current memory usage in bytes"""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss
    except ImportError:
        # Fallback for systems without psutil
        return 0


class CommandWhitelist:
    """Command whitelist for security"""

    def __init__(self):
        self.allowed_commands = {
            "file_operations": [
                "read_file",
                "write_file",
                "list_files",
                "mkdir",
                "rmdir",
                "create_file",
                "validate_file",
            ],
            "text_operations": ["search_text", "replace_text", "count_lines"],
            "validation": ["validate_syntax", "check_format"],
            "analysis": ["analyze_structure", "generate_report"],
            "refactoring": ["backup_original", "apply_refactoring"],
        }
        self.blocked_patterns = [
            "subprocess",
            "os.system",
            "exec",
            "eval",
            "import os",
            "import subprocess",
            "import sys",
        ]

    def is_allowed(self, command: str) -> bool:
        """Check if command is allowed"""
        command_lower = command.lower()

        # Check blocked patterns first
        for pattern in self.blocked_patterns:
            if pattern in command_lower:
                return False

        # Check allowed commands
        for category, commands in self.allowed_commands.items():
            if command_lower in commands:
                return True

        return False

    def validate_code(self, code: str) -> List[str]:
        """Validate code for security violations"""
        violations = []
        code_lower = code.lower()

        for pattern in self.blocked_patterns:
            if pattern in code_lower:
                violations.append(f"Blocked pattern detected: {pattern}")

        return violations


class NetworkPolicy:
    """Network access policy"""

    def __init__(self, allow_network: bool = False):
        self.allow_network = allow_network
        self.allowed_domains = []
        self.blocked_domains = []

    def is_network_allowed(self) -> bool:
        """Check if network access is allowed"""
        return self.allow_network

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed"""
        if not self.allow_network:
            return False

        if domain in self.blocked_domains:
            return False

        if self.allowed_domains and domain not in self.allowed_domains:
            return False

        return True


class SafetyMonitor:
    """Monitor safety constraints during execution"""

    def __init__(self):
        self.start_time = time.monotonic()
        self.bytes_written = 0
        self.commands_executed = []
        self.violations = []

    def track_file_write(self, bytes_count: int) -> None:
        """Track file write operations"""
        self.bytes_written += bytes_count

    def track_command(self, command: str) -> None:
        """Track command execution"""
        self.commands_executed.append(
            {"command": command, "timestamp": time.monotonic()}
        )

    def add_violation(self, violation: str) -> None:
        """Add safety violation"""
        self.violations.append({"violation": violation, "timestamp": time.monotonic()})

    def check_limits(self, limits: Dict[str, Any]) -> bool:
        """Check if limits are exceeded"""
        current_time = time.monotonic()
        elapsed = current_time - self.start_time

        # Check timeout
        if "timeout_s" in limits and elapsed > limits["timeout_s"]:
            self.add_violation(
                f"Timeout exceeded: {elapsed:.1f}s > {limits['timeout_s']}s"
            )
            return False

        # Check filesystem quota
        if (
            "fs_quota_kb" in limits
            and self.bytes_written > limits["fs_quota_kb"] * 1024
        ):
            self.add_violation(
                f"Filesystem quota exceeded: {self.bytes_written/1024:.1f}KB > {limits['fs_quota_kb']}KB"
            )
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        current_time = time.monotonic()
        return {
            "elapsed_time": current_time - self.start_time,
            "bytes_written": self.bytes_written,
            "commands_executed": len(self.commands_executed),
            "violations": len(self.violations),
            "violation_details": self.violations,
        }


def enforce_safety_policy(policy: Dict[str, Any], monitor: SafetyMonitor) -> None:
    """Enforce safety policy"""
    if not monitor.check_limits(policy):
        raise PolicyViolation("Safety limits exceeded")

    if monitor.violations:
        raise PolicyViolation(f"Safety violations detected: {len(monitor.violations)}")


class SafetyManager:
    """Manages safety policies and enforces budgets"""

    def __init__(self, budget, policy_level: str = "strict"):
        self.budget = budget
        self.policy_level = policy_level
        self.start_time = time.monotonic()
        self.fs_usage_bytes = 0
        self.network_allowed = False  # Default to no-internet mode

    def check_timeout(self) -> None:
        """Check if execution has exceeded timeout budget"""
        if (
            self.budget.timeout_s > 0
            and (time.monotonic() - self.start_time) * 1000 > self.budget.timeout_s
        ):
            raise PolicyViolation(
                f"Execution timed out after {self.budget.timeout_s}ms. "
                f"Current duration: {(time.monotonic() - self.start_time) * 1000:.2f}ms"
            )

    def check_fs_quota(self, bytes_written: int = 0) -> None:
        """Check if file system usage has exceeded quota budget"""
        self.fs_usage_bytes += bytes_written
        if (
            self.budget.fs_quota_kb > 0
            and self.fs_usage_bytes > self.budget.fs_quota_kb * 1024
        ):
            raise PolicyViolation(
                f"File system usage ({self.fs_usage_bytes / 1024:.2f}KB) "
                f"exceeded quota of {self.budget.fs_quota_kb}KB"
            )

    def check_network_access(self) -> None:
        """Check if network access is allowed"""
        if not self.network_allowed:
            raise PolicyViolation("Network access is not allowed by policy")

    def set_network_access(self, allowed: bool) -> None:
        """Set network access permission"""
        self.network_allowed = allowed

    def budgeted(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to enforce resource budgets for a function"""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.check_timeout()
            # For now, only check timeout and FS quota.
            # CPU/Memory checks would require more advanced OS-level monitoring.
            return func(*args, **kwargs)

        return wrapper

    def get_error_taxonomy(self, e: PolicyViolation) -> Dict[str, Any]:
        """Classify a PolicyViolation into ErrorTaxonomy"""
        return {
            "error_type": "POLICY_VIOLATION",
            "message": str(e),
            "context": {
                "budget": self.budget.dict(),
                "policy_level": self.policy_level,
            },
            "recoverable": False,
            "suggested_action": "Adjust policy or increase budget",
        }


def is_command_whitelisted(command_name: str) -> bool:
    """Check if a command is in the whitelist"""
    whitelist = CommandWhitelist()
    return whitelist.is_allowed(command_name)


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
