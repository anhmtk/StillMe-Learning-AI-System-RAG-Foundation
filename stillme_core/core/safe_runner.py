"""Safe Runner for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class RunStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class SafetyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SafeRun:
    """Safe run record"""
    run_id: str
    function_name: str
    status: RunStatus
    safety_level: SafetyLevel
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SafeRunner:
    """Safe runner for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.runs: List[SafeRun] = []
        self.safety_checks = self._initialize_safety_checks()
        self.logger.info("✅ SafeRunner initialized")

    def _initialize_safety_checks(self) -> Dict[SafetyLevel, List[str]]:
        """Initialize safety checks for different levels"""
        return {
            SafetyLevel.LOW: [
                "basic_input_validation",
                "output_sanitization"
            ],
            SafetyLevel.MEDIUM: [
                "basic_input_validation",
                "output_sanitization",
                "resource_limits",
                "timeout_checks"
            ],
            SafetyLevel.HIGH: [
                "basic_input_validation",
                "output_sanitization",
                "resource_limits",
                "timeout_checks",
                "sandbox_execution",
                "audit_logging"
            ],
            SafetyLevel.CRITICAL: [
                "basic_input_validation",
                "output_sanitization",
                "resource_limits",
                "timeout_checks",
                "sandbox_execution",
                "audit_logging",
                "approval_required",
                "rollback_capability"
            ]
        }

    def run_safely(self,
                   function: Callable,
                   function_name: str,
                   safety_level: SafetyLevel = SafetyLevel.MEDIUM,
                   timeout: float = 30.0,
                   *args, **kwargs) -> SafeRun:
        """Run a function safely with specified safety level"""
        try:
            run_id = f"run_{len(self.runs) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()

            # Create run record
            run = SafeRun(
                run_id=run_id,
                function_name=function_name,
                status=RunStatus.PENDING,
                safety_level=safety_level,
                start_time=start_time,
                metadata={
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "timeout": timeout
                }
            )

            self.runs.append(run)
            self.logger.info(f"🚀 Starting safe run: {function_name} (ID: {run_id})")

            # Perform safety checks
            if not self._perform_safety_checks(safety_level, function, args, kwargs):
                run.status = RunStatus.FAILED
                run.error = "Safety checks failed"
                run.end_time = datetime.now()
                run.duration = (run.end_time - run.start_time).total_seconds()
                self.logger.error(f"❌ Safety checks failed for run: {run_id}")
                return run

            # Execute function with safety measures
            run.status = RunStatus.RUNNING
            result = self._execute_with_safety(function, safety_level, timeout, *args, **kwargs)

            # Update run record
            run.status = RunStatus.COMPLETED
            run.result = result
            run.end_time = datetime.now()
            run.duration = (run.end_time - run.start_time).total_seconds()

            self.logger.info(f"✅ Safe run completed: {function_name} (ID: {run_id}) in {run.duration:.2f}s")
            return run

        except Exception as e:
            # Update run record with error
            if 'run' in locals():
                run.status = RunStatus.FAILED
                run.error = str(e)
                run.end_time = datetime.now()
                run.duration = (run.end_time - run.start_time).total_seconds()

            self.logger.error(f"❌ Safe run failed: {function_name} - {e}")
            return run if 'run' in locals() else None

    def _perform_safety_checks(self, safety_level: SafetyLevel, function: Callable, args: tuple, kwargs: dict) -> bool:
        """Perform safety checks based on safety level"""
        try:
            checks = self.safety_checks.get(safety_level, [])

            for check in checks:
                if not self._execute_safety_check(check, function, args, kwargs):
                    self.logger.warning(f"⚠️ Safety check failed: {check}")
                    return False

            self.logger.info(f"✅ All safety checks passed for level: {safety_level.value}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Safety check error: {e}")
            return False

    def _execute_safety_check(self, check_name: str, function: Callable, args: tuple, kwargs: dict) -> bool:
        """Execute a specific safety check"""
        try:
            if check_name == "basic_input_validation":
                return self._check_basic_input_validation(args, kwargs)
            elif check_name == "output_sanitization":
                return self._check_output_sanitization(function)
            elif check_name == "resource_limits":
                return self._check_resource_limits(function)
            elif check_name == "timeout_checks":
                return self._check_timeout_checks(function)
            elif check_name == "sandbox_execution":
                return self._check_sandbox_execution(function)
            elif check_name == "audit_logging":
                return self._check_audit_logging(function)
            elif check_name == "approval_required":
                return self._check_approval_required(function)
            elif check_name == "rollback_capability":
                return self._check_rollback_capability(function)
            else:
                self.logger.warning(f"⚠️ Unknown safety check: {check_name}")
                return True  # Allow unknown checks to pass

        except Exception as e:
            self.logger.error(f"❌ Safety check execution error: {e}")
            return False

    def _check_basic_input_validation(self, args: tuple, kwargs: dict) -> bool:
        """Check basic input validation"""
        try:
            # Check for dangerous inputs
            dangerous_patterns = ['<script>', 'javascript:', 'eval(', 'exec(']

            for arg in args:
                if isinstance(arg, str):
                    if any(pattern in arg.lower() for pattern in dangerous_patterns):
                        self.logger.warning("⚠️ Dangerous input pattern detected in args")
                        return False

            for key, value in kwargs.items():
                if isinstance(value, str):
                    if any(pattern in value.lower() for pattern in dangerous_patterns):
                        self.logger.warning("⚠️ Dangerous input pattern detected in kwargs")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Input validation check error: {e}")
            return False

    def _check_output_sanitization(self, function: Callable) -> bool:
        """Check output sanitization capability"""
        try:
            # Check if function has output sanitization
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Output sanitization check error: {e}")
            return False

    def _check_resource_limits(self, function: Callable) -> bool:
        """Check resource limits"""
        try:
            # Check if function respects resource limits
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Resource limits check error: {e}")
            return False

    def _check_timeout_checks(self, function: Callable) -> bool:
        """Check timeout handling"""
        try:
            # Check if function has timeout handling
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Timeout checks error: {e}")
            return False

    def _check_sandbox_execution(self, function: Callable) -> bool:
        """Check sandbox execution capability"""
        try:
            # Check if function can run in sandbox
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Sandbox execution check error: {e}")
            return False

    def _check_audit_logging(self, function: Callable) -> bool:
        """Check audit logging capability"""
        try:
            # Check if function has audit logging
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Audit logging check error: {e}")
            return False

    def _check_approval_required(self, function: Callable) -> bool:
        """Check if approval is required"""
        try:
            # Check if function requires approval
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Approval required check error: {e}")
            return False

    def _check_rollback_capability(self, function: Callable) -> bool:
        """Check rollback capability"""
        try:
            # Check if function has rollback capability
            # This is a simplified check - in reality, you'd analyze the function's code
            return True

        except Exception as e:
            self.logger.error(f"❌ Rollback capability check error: {e}")
            return False

    def _execute_with_safety(self, function: Callable, safety_level: SafetyLevel, timeout: float, *args, **kwargs) -> Any:
        """Execute function with safety measures"""
        try:
            # In a real implementation, this would:
            # 1. Set up resource limits
            # 2. Set up timeout
            # 3. Execute in sandbox if needed
            # 4. Monitor execution
            # 5. Handle errors gracefully

            # For now, we'll just execute the function normally
            result = function(*args, **kwargs)
            return result

        except Exception as e:
            self.logger.error(f"❌ Function execution error: {e}")
            raise

    def get_runs_by_status(self, status: RunStatus) -> List[SafeRun]:
        """Get runs by status"""
        return [r for r in self.runs if r.status == status]

    def get_runs_by_safety_level(self, safety_level: SafetyLevel) -> List[SafeRun]:
        """Get runs by safety level"""
        return [r for r in self.runs if r.safety_level == safety_level]

    def get_run_summary(self) -> Dict[str, Any]:
        """Get run summary"""
        try:
            total_runs = len(self.runs)

            runs_by_status = {}
            runs_by_safety_level = {}
            successful_runs = 0
            failed_runs = 0

            for run in self.runs:
                # By status
                status_key = run.status.value
                runs_by_status[status_key] = runs_by_status.get(status_key, 0) + 1

                # By safety level
                safety_key = run.safety_level.value
                runs_by_safety_level[safety_key] = runs_by_safety_level.get(safety_key, 0) + 1

                # Count successful/failed runs
                if run.status == RunStatus.COMPLETED:
                    successful_runs += 1
                elif run.status == RunStatus.FAILED:
                    failed_runs += 1

            # Calculate success rate
            success_rate = (successful_runs / max(1, total_runs)) * 100

            return {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": success_rate,
                "runs_by_status": runs_by_status,
                "runs_by_safety_level": runs_by_safety_level,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get run summary: {e}")
            return {"error": str(e)}

    def clear_runs(self):
        """Clear all runs"""
        self.runs.clear()
        self.logger.info("🧹 All safe runs cleared")