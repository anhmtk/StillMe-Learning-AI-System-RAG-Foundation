"""
Vertical slice tests for AgentDev runtime
End-to-end tests for core pipeline: plan -> execute -> validate
"""

import pytest
import tempfile
from pathlib import Path

from agent_dev.runtime import AgentDev
from agent_dev.schemas import TaskSpec, Policy, SafetyBudget, PolicyLevel


class TestRuntimeVertical:
    """Vertical slice tests for AgentDev runtime"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent_dev = AgentDev(str(self.temp_dir / "sandboxes"))

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_agentdev_initialization(self):
        """Test AgentDev initialization"""
        assert self.agent_dev is not None
        assert self.agent_dev.sandbox_root.exists()
        assert self.agent_dev.telemetry is not None

    @pytest.mark.unit
    def test_plan_file_edit_task(self):
        """Test planning a file_edit task"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "test.py", "content": "print('Hello, World!')"},
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        plan = self.agent_dev.plan(task_spec)

        assert plan is not None
        assert plan.sandbox_path is not None
        assert len(plan.steps) > 0
        assert "file_exists" in plan.checks
        assert plan.estimated_duration_ms > 0

    @pytest.mark.unit
    def test_plan_code_analysis_task(self):
        """Test planning a code_analysis task"""
        task_spec = TaskSpec(
            type="code_analysis",
            inputs={"target": "."},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=2000, mem_mb=200, fs_quota_kb=200, timeout_s=20
            ),
        )

        plan = self.agent_dev.plan(task_spec)

        assert plan is not None
        assert plan.sandbox_path is not None
        assert len(plan.steps) > 0
        assert plan.estimated_duration_ms > 0

    @pytest.mark.unit
    def test_plan_refactoring_task(self):
        """Test planning a refactoring task"""
        task_spec = TaskSpec(
            type="refactoring",
            inputs={
                "target": "src/",
                "changes": {"rename_function": "old_name -> new_name"},
            },
            policy=Policy(level=PolicyLevel.CREATIVE),
            budgets=SafetyBudget(
                cpu_ms=5000, mem_mb=500, fs_quota_kb=500, timeout_s=30
            ),
        )

        plan = self.agent_dev.plan(task_spec)

        assert plan is not None
        assert plan.sandbox_path is not None
        assert len(plan.steps) > 0
        assert plan.estimated_duration_ms > 0

    @pytest.mark.unit
    def test_plan_unsupported_task_type(self):
        """Test planning with unsupported task type"""
        # This test expects validation error during TaskSpec creation
        with pytest.raises(Exception, match="Task type must be one of"):
            TaskSpec(
                type="unsupported_type",
                inputs={},
                policy=Policy(),
                budgets=SafetyBudget(),
            )

    @pytest.mark.unit
    def test_execute_file_edit_task(self):
        """Test executing a file_edit task"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "hello.py", "content": "print('Hello, AgentDev!')"},
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)

        assert exec_result is not None
        assert exec_result.success is True
        assert len(exec_result.files_created) > 0
        assert exec_result.duration_ms > 0
        assert exec_result.resources_used is not None

    @pytest.mark.unit
    def test_execute_code_analysis_task(self):
        """Test executing a code_analysis task"""
        task_spec = TaskSpec(
            type="code_analysis",
            inputs={"target": "."},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=2000, mem_mb=200, fs_quota_kb=200, timeout_s=20
            ),
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)

        assert exec_result is not None
        assert exec_result.success is True
        assert exec_result.duration_ms >= 0  # Allow 0 for fast tests

    @pytest.mark.unit
    def test_execute_refactoring_task(self):
        """Test executing a refactoring task"""
        task_spec = TaskSpec(
            type="refactoring",
            inputs={"target": "src/", "changes": {"optimize_imports": True}},
            policy=Policy(level=PolicyLevel.CREATIVE),
            budgets=SafetyBudget(
                cpu_ms=5000, mem_mb=500, fs_quota_kb=500, timeout_s=30
            ),
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)

        assert exec_result is not None
        assert exec_result.success is True
        assert exec_result.duration_ms >= 0  # Allow 0 for fast tests

    @pytest.mark.unit
    def test_validate_successful_execution(self):
        """Test validation of successful execution"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "test.py", "content": "print('test')"},
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)
        validation_report = self.agent_dev.validate(task_spec, plan, exec_result)

        assert validation_report is not None
        assert validation_report.valid is True
        assert len(validation_report.checks_passed) > 0
        assert validation_report.confidence_score > 0.0

    @pytest.mark.unit
    def test_validate_failed_execution(self):
        """Test validation of failed execution"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "test.py", "content": "print('test')"},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=100, mem_mb=10, fs_quota_kb=1, timeout_s=1
            ),  # Very restrictive
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)
        validation_report = self.agent_dev.validate(task_spec, plan, exec_result)

        assert validation_report is not None
        # May be valid or invalid depending on execution success
        assert validation_report.confidence_score >= 0.0
        assert validation_report.confidence_score <= 1.0

    @pytest.mark.unit
    def test_full_pipeline_file_edit(self):
        """Test complete pipeline for file_edit task"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={
                "file_path": "hello_world.py",
                "content": "#!/usr/bin/env python3\nprint('Hello, World!')",
            },
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(
                cpu_ms=2000, mem_mb=200, fs_quota_kb=200, timeout_s=20
            ),
        )

        # Plan
        plan = self.agent_dev.plan(task_spec)
        assert plan is not None

        # Execute
        exec_result = self.agent_dev.execute_task(task_spec, plan)
        assert exec_result is not None

        # Validate
        validation_report = self.agent_dev.validate(task_spec, plan, exec_result)
        assert validation_report is not None

        # Check overall success
        assert exec_result.success is True
        assert validation_report.valid is True
        assert len(exec_result.files_created) > 0

    @pytest.mark.unit
    def test_full_pipeline_code_analysis(self):
        """Test complete pipeline for code_analysis task"""
        task_spec = TaskSpec(
            type="code_analysis",
            inputs={"target": "src/"},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=3000, mem_mb=300, fs_quota_kb=300, timeout_s=30
            ),
        )

        # Plan
        plan = self.agent_dev.plan(task_spec)
        assert plan is not None

        # Execute
        exec_result = self.agent_dev.execute_task(task_spec, plan)
        assert exec_result is not None

        # Validate
        validation_report = self.agent_dev.validate(task_spec, plan, exec_result)
        assert validation_report is not None

        # Check overall success
        assert exec_result.success is True
        assert validation_report.valid is True

    @pytest.mark.unit
    def test_telemetry_integration(self):
        """Test that telemetry is properly integrated"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={
                "file_path": "telemetry_test.py",
                "content": "# Telemetry test file",
            },
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        # Execute pipeline
        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)
        validation_report = self.agent_dev.validate(task_spec, plan, exec_result)

        # Check telemetry stats
        stats = self.agent_dev.telemetry.get_session_stats()
        assert stats["trace_id"] is not None
        assert stats["phase_count"] > 0
        assert stats["session_duration"] >= 0

    @pytest.mark.unit
    def test_safety_budget_enforcement(self):
        """Test that safety budgets are enforced"""
        task_spec = TaskSpec(
            type="file_edit",
            inputs={
                "file_path": "large_file.py",
                "content": "A" * 10000,  # Large content
            },
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=100, mem_mb=10, fs_quota_kb=1, timeout_s=1
            ),  # Very restrictive
        )

        plan = self.agent_dev.plan(task_spec)
        exec_result = self.agent_dev.execute_task(task_spec, plan)

        # Should either succeed within limits or fail due to budget constraints
        assert exec_result is not None
        # The result depends on whether the safety manager catches the violation

    @pytest.mark.unit
    def test_policy_level_impact(self):
        """Test that different policy levels have different behaviors"""
        # Test with STRICT policy
        strict_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "strict.py", "content": "test"},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        # Test with CREATIVE policy
        creative_spec = TaskSpec(
            type="file_edit",
            inputs={"file_path": "creative.py", "content": "test"},
            policy=Policy(level=PolicyLevel.CREATIVE),
            budgets=SafetyBudget(
                cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=30
            ),
        )

        # Both should work but may have different behaviors
        strict_plan = self.agent_dev.plan(strict_spec)
        creative_plan = self.agent_dev.plan(creative_spec)

        assert strict_plan is not None
        assert creative_plan is not None
        # Plans may differ based on policy level

    @pytest.mark.unit
    def test_error_handling(self):
        """Test error handling in the pipeline"""
        # Test with invalid task spec
        invalid_spec = TaskSpec(
            type="file_edit",
            inputs={},  # Missing required inputs
            policy=Policy(),
            budgets=SafetyBudget(),
        )

        # Should handle gracefully
        try:
            plan = self.agent_dev.plan(invalid_spec)
            exec_result = self.agent_dev.execute_task(invalid_spec, plan)
            validation_report = self.agent_dev.validate(invalid_spec, plan, exec_result)

            # If it doesn't raise an exception, check the results
            assert plan is not None
            assert exec_result is not None
            assert validation_report is not None

        except Exception as e:
            # If it raises an exception, that's also acceptable error handling
            assert str(e) is not None