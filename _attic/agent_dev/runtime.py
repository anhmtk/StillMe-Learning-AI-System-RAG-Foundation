"""
Core runtime for AgentDev Sprint 1
Minimal runtime APIs: plan, execute_task, validate
"""

import time
from typing import Any, Dict, List
from pathlib import Path

from agent_dev.schemas import (
    TaskSpec,
    Plan,
    ExecResult,
    ValidationReport,
    PolicyViolation,
)
from agent_dev.sandbox import mkdir_sandbox, safe_write_file, safe_read_file
from agent_dev.safety import SafetyManager, is_command_whitelisted
from agent_dev.telemetry import create_telemetry_logger


class AgentDev:
    """Core AgentDev runtime for task execution"""

    def __init__(self, sandbox_root: str = "./agentdev_tests/e2e_sandboxes"):
        self.sandbox_root = Path(sandbox_root)
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.telemetry = create_telemetry_logger(str(self.sandbox_root))

    def plan(self, task_spec: TaskSpec) -> Plan:
        """
        Plan execution for a task.

        Args:
            task_spec: Task specification

        Returns:
            Execution plan with steps and sandbox path

        Raises:
            PolicyViolation: If task type is not supported
        """
        with self.telemetry.phase_tracking("planning", {"task_type": task_spec.type}):
            # Create unique sandbox for this task
            trace_id = self.telemetry.trace_id
            sandbox_path = self.sandbox_root / trace_id
            sandbox_path = mkdir_sandbox(sandbox_path)

            # Plan steps based on task type
            if task_spec.type == "file_edit":
                steps = self._plan_file_edit(task_spec, sandbox_path)
            elif task_spec.type == "code_analysis":
                steps = self._plan_code_analysis(task_spec, sandbox_path)
            elif task_spec.type == "refactoring":
                steps = self._plan_refactoring(task_spec, sandbox_path)
            else:
                raise PolicyViolation(f"Unsupported task type: {task_spec.type}")

            # Define validation checks
            checks = [
                "file_exists",
                "content_valid",
                "no_syntax_errors",
                "policy_compliance",
            ]

            # Estimate duration (simplified)
            estimated_duration_ms = len(steps) * 1000  # 1 second per step

            plan = Plan(
                steps=steps,
                sandbox_path=str(sandbox_path),
                checks=checks,
                estimated_duration_ms=estimated_duration_ms,
            )

            self.telemetry.log_policy_decision(
                "task_planning",
                "approved",
                f"Created plan for {task_spec.type} with {len(steps)} steps",
                {"task_type": task_spec.type, "steps_count": len(steps)},
            )

            return plan

    def execute_task(self, task_spec: TaskSpec, plan: Plan) -> ExecResult:
        """
        Execute a task according to the plan.

        Args:
            task_spec: Task specification
            plan: Execution plan

        Returns:
            Execution result with output and files created/modified
        """
        with self.telemetry.phase_tracking("execution", {"task_type": task_spec.type}):
            # Initialize safety manager
            safety_manager = SafetyManager(task_spec.budgets, task_spec.policy.level)

            # Track execution
            start_time = time.time()
            files_created = []
            files_modified = []
            errors = []
            output = {}

            try:
                # Execute each step
                for i, step in enumerate(plan.steps):
                    self.telemetry.log_event(
                        "step_start",
                        "execution",
                        {
                            "step_number": i + 1,
                            "step_type": step.get("type", "unknown"),
                        },
                    )

                    # Check safety limits
                    safety_manager.check_timeout()
                    safety_manager.check_fs_quota()

                    # Execute step
                    step_result = self._execute_step(
                        step, plan.sandbox_path, safety_manager
                    )

                    # Track results
                    if step_result.get("files_created"):
                        files_created.extend(step_result["files_created"])
                    if step_result.get("files_modified"):
                        files_modified.extend(step_result["files_modified"])
                    if step_result.get("errors"):
                        errors.extend(step_result["errors"])

                    output[f"step_{i+1}"] = step_result

                    self.telemetry.log_event(
                        "step_end",
                        "execution",
                        {
                            "step_number": i + 1,
                            "success": step_result.get("success", True),
                        },
                    )

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                exec_result = ExecResult(
                    success=len(errors) == 0,
                    output=output,
                    files_created=files_created,
                    files_modified=files_modified,
                    errors=errors,
                    duration_ms=duration_ms,
                    resources_used={
                        "fs_usage_bytes": safety_manager.fs_usage_bytes,
                        "execution_time_ms": duration_ms,
                    },
                )

                self.telemetry.log_task_result(
                    task_spec.model_dump(), exec_result.model_dump(), duration_ms
                )

                return exec_result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                self.telemetry.log_error(
                    type(e).__name__, str(e), "execution", {"task_type": task_spec.type}
                )

                return ExecResult(
                    success=False,
                    output={"error": str(e)},
                    files_created=files_created,
                    files_modified=files_modified,
                    errors=[str(e)],
                    duration_ms=duration_ms,
                    resources_used={"fs_usage_bytes": safety_manager.fs_usage_bytes},
                )

    def validate(
        self, task_spec: TaskSpec, plan: Plan, exec_result: ExecResult
    ) -> ValidationReport:
        """
        Validate the execution result.

        Args:
            task_spec: Original task specification
            plan: Execution plan
            exec_result: Execution result

        Returns:
            Validation report with checks and recommendations
        """
        with self.telemetry.phase_tracking("validation", {"task_type": task_spec.type}):
            checks_passed = []
            checks_failed = []
            recommendations = []

            # Check if execution was successful
            if exec_result.success:
                checks_passed.append("execution_success")
            else:
                checks_failed.append("execution_failed")
                recommendations.append("Review execution errors and retry")

            # Check file operations
            if exec_result.files_created:
                checks_passed.append("files_created")
            if exec_result.files_modified:
                checks_passed.append("files_modified")

            # Check for policy violations
            if not exec_result.errors:
                checks_passed.append("no_policy_violations")
            else:
                checks_failed.append("policy_violations_detected")
                recommendations.append("Review and fix policy violations")

            # Check resource usage
            if exec_result.resources_used:
                fs_usage = exec_result.resources_used.get("fs_usage_bytes", 0)
                if fs_usage <= task_spec.budgets.fs_quota_kb * 1024:
                    checks_passed.append("fs_quota_respected")
                else:
                    checks_failed.append("fs_quota_exceeded")
                    recommendations.append(
                        "Optimize file operations to reduce disk usage"
                    )

            # Calculate confidence score
            total_checks = len(checks_passed) + len(checks_failed)
            confidence_score = (
                len(checks_passed) / total_checks if total_checks > 0 else 0.0
            )

            validation_report = ValidationReport(
                valid=len(checks_failed) == 0,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                recommendations=recommendations,
                confidence_score=confidence_score,
            )

            self.telemetry.log_policy_decision(
                "validation",
                "passed" if validation_report.valid else "failed",
                f"Validation completed with {len(checks_passed)} passed, {len(checks_failed)} failed",
                {"confidence_score": confidence_score},
            )

            return validation_report

    def _plan_file_edit(
        self, task_spec: TaskSpec, sandbox_path: Path
    ) -> List[Dict[str, Any]]:
        """Plan steps for file_edit task"""
        steps = []

        # Step 1: Create target file
        if "file_path" in task_spec.inputs:
            steps.append(
                {
                    "type": "create_file",
                    "file_path": task_spec.inputs["file_path"],
                    "content": task_spec.inputs.get("content", ""),
                }
            )

        # Step 2: Validate file
        steps.append(
            {
                "type": "validate_file",
                "file_path": task_spec.inputs.get("file_path", "output.txt"),
            }
        )

        return steps

    def _plan_code_analysis(
        self, task_spec: TaskSpec, sandbox_path: Path
    ) -> List[Dict[str, Any]]:
        """Plan steps for code_analysis task"""
        steps = []

        # Step 1: Analyze code structure
        steps.append(
            {"type": "analyze_structure", "target": task_spec.inputs.get("target", ".")}
        )

        # Step 2: Generate report
        steps.append({"type": "generate_report", "output_file": "analysis_report.txt"})

        return steps

    def _plan_refactoring(
        self, task_spec: TaskSpec, sandbox_path: Path
    ) -> List[Dict[str, Any]]:
        """Plan steps for refactoring task"""
        steps = []

        # Step 1: Backup original
        steps.append(
            {"type": "backup_original", "target": task_spec.inputs.get("target", ".")}
        )

        # Step 2: Apply refactoring
        steps.append(
            {
                "type": "apply_refactoring",
                "changes": task_spec.inputs.get("changes", {}),
            }
        )

        return steps

    def _execute_step(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute a single step"""
        step_type = step.get("type", "unknown")

        # Check if command is whitelisted
        if not is_command_whitelisted(step_type):
            raise PolicyViolation(f"Command not whitelisted: {step_type}")

        try:
            if step_type == "create_file":
                return self._execute_create_file(step, sandbox_path, safety_manager)
            elif step_type == "validate_file":
                return self._execute_validate_file(step, sandbox_path, safety_manager)
            elif step_type == "analyze_structure":
                return self._execute_analyze_structure(
                    step, sandbox_path, safety_manager
                )
            elif step_type == "generate_report":
                return self._execute_generate_report(step, sandbox_path, safety_manager)
            elif step_type == "backup_original":
                return self._execute_backup_original(step, sandbox_path, safety_manager)
            elif step_type == "apply_refactoring":
                return self._execute_apply_refactoring(
                    step, sandbox_path, safety_manager
                )
            else:
                raise PolicyViolation(f"Unknown step type: {step_type}")

        except Exception as e:
            return {"success": False, "error": str(e), "errors": [str(e)]}

    def _execute_create_file(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute create_file step"""
        file_path = step.get("file_path", "output.txt")
        content = step.get("content", "")

        # Check file size
        content_bytes = len(content.encode("utf-8"))
        safety_manager.check_fs_quota(content_bytes)

        # Create file
        safe_write_file(file_path, content, sandbox_path)

        return {
            "success": True,
            "files_created": [file_path],
            "output": f"Created file {file_path} with {len(content)} characters",
        }

    def _execute_validate_file(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute validate_file step"""
        file_path = step.get("file_path", "output.txt")

        try:
            content = safe_read_file(file_path, sandbox_path)
            return {
                "success": True,
                "output": f"File {file_path} validated successfully",
                "file_size": len(content),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "errors": [str(e)]}

    def _execute_analyze_structure(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute analyze_structure step"""
        target = step.get("target", ".")

        # Simulate analysis
        return {
            "success": True,
            "output": f"Analyzed structure of {target}",
            "analysis_data": {"files_count": 1, "complexity": "low"},
        }

    def _execute_generate_report(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute generate_report step"""
        output_file = step.get("output_file", "analysis_report.txt")
        report_content = "Analysis Report\n==============\n\nGenerated by AgentDev\n"

        # Check file size
        content_bytes = len(report_content.encode("utf-8"))
        safety_manager.check_fs_quota(content_bytes)

        safe_write_file(output_file, report_content, sandbox_path)

        return {
            "success": True,
            "files_created": [output_file],
            "output": f"Generated report {output_file}",
        }

    def _execute_backup_original(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute backup_original step"""
        target = step.get("target", ".")

        # Simulate backup
        return {
            "success": True,
            "output": f"Backed up {target}",
            "backup_location": f"{target}.backup",
        }

    def _execute_apply_refactoring(
        self, step: Dict[str, Any], sandbox_path: str, safety_manager: SafetyManager
    ) -> Dict[str, Any]:
        """Execute apply_refactoring step"""
        changes = step.get("changes", {})

        # Simulate refactoring
        return {
            "success": True,
            "output": f"Applied {len(changes)} refactoring changes",
            "changes_applied": list(changes.keys()),
        }
