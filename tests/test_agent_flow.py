"""
Integration test for AgentDev flow (Controller)
"""

from unittest.mock import Mock, patch

from stillme_core.controller import AgentController, run_agent
from stillme_core.plan_types import PlanItem


class TestAgentFlow:
    def test_run_agent_success_flow(self, tmp_path):
        """Test successful agent flow with mock components"""
        # Create a simple test file
        test_file = tmp_path / "test_simple.py"
        test_file.write_text("def test_something():\n    assert True\n")

        # Mock plan items
        mock_plan_items = [
            PlanItem(
                id="test-1",
                title="Run simple test",
                description="Run simple test",
                steps=[],
            )
        ]

        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.return_value = mock_plan_items
            mock_planner_class.return_value = mock_planner

            with patch("stillme_core.executor.PatchExecutor") as mock_executor_class:
                mock_executor = Mock()
                mock_executor.apply_patch_and_test.return_value = {
                    "ok": True,
                    "stdout": "1 passed",
                    "stderr": "",
                    "tests_run": [str(test_file)],
                }
                mock_executor_class.return_value = mock_executor

                with patch("stillme_core.verifier.Verifier") as mock_verifier_class:
                    mock_verifier = Mock()
                    mock_verifier.verify.return_value = {
                        "passed": True,
                        "reason": "test passed",
                    }
                    mock_verifier_class.return_value = mock_verifier

                    # Run the agent
                    controller = AgentController()
                    import asyncio

                    result = asyncio.run(controller.execute_task("Run unit tests"))

                    # Verify result structure
                    assert "summary" in result
                    assert "steps" in result
                    assert "pass_rate" in result
                    assert "total_steps" in result
                    assert "passed_steps" in result
                    assert "total_duration_s" in result
                    assert "goal" in result

                    # Verify content
                    assert result["goal"] == "Run unit tests"
                    assert result["total_steps"] == 1
                    assert result["passed_steps"] == 1
                    assert result["pass_rate"] == 1.0
                    assert len(result["steps"]) == 1

                    # Verify step details
                    step = result["steps"][0]
                    assert step["id"] == 1
                    assert step["desc"] == "Run simple test"
                    assert step["action"] == "run_tests"
                    assert step["exec_ok"] is True
                    assert "1 passed" in step["stdout_tail"]
                    assert step["duration_s"] >= 0

    def test_run_agent_failure_flow(self, tmp_path):
        """Test agent flow with failures"""
        # Mock plan items
        mock_plan_items = [
            PlanItem(
                id="test-1",
                title="Run failing test",
                description="Run failing test",
                steps=[],
            )
        ]

        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.return_value = mock_plan_items
            mock_planner_class.return_value = mock_planner

            with patch("stillme_core.executor.PatchExecutor") as mock_executor_class:
                mock_executor = Mock()
                mock_executor.apply_patch_and_test.return_value = {
                    "ok": False,
                    "stdout": "",
                    "stderr": "Test failed",
                    "error": "AssertionError",
                }
                mock_executor_class.return_value = mock_executor

                with patch("stillme_core.verifier.Verifier") as mock_verifier_class:
                    mock_verifier = Mock()
                    mock_verifier.verify.return_value = {
                        "passed": False,
                        "reason": "test failed",
                    }
                    mock_verifier_class.return_value = mock_verifier

                    # Run the agent
                    controller = AgentController()

                    result = asyncio.run(controller.execute_task("Run failing tests"))

                    # Verify result
                    assert result["total_steps"] == 1
                    assert result["passed_steps"] == 0
                    assert result["pass_rate"] == 0.0

                    # Verify step details
                    step = result["steps"][0]
                    assert step["exec_ok"] is False
                    # stdout_tail should contain stderr when exec fails
                    assert (
                        "Test failed" in step["stdout_tail"]
                        or "AssertionError" in step["stdout_tail"]
                    )

    def test_run_agent_no_plan_items(self, tmp_path):
        """Test agent flow when no plan items are generated"""
        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.return_value = []  # No plan items
            mock_planner_class.return_value = mock_planner

            # Run the agent
            controller = AgentController()

            result = asyncio.run(controller.execute_task("No plan goal"))

            # Verify result
            assert result["total_steps"] == 0
            assert result["passed_steps"] == 0
            assert result["pass_rate"] == 0.0
            assert "No plan items generated" in result["summary"]

    def test_run_agent_multiple_steps(self, tmp_path):
        """Test agent flow with multiple steps"""
        # Mock plan items
        mock_plan_items = [
            PlanItem(
                id="test-1",
                title="Step 1",
                description="Step 1",
                steps=[],
            ),
            PlanItem(
                id="test-2",
                title="Step 2",
                description="Step 2",
                steps=[],
            ),
        ]

        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.return_value = mock_plan_items
            mock_planner_class.return_value = mock_planner

            with patch("stillme_core.executor.PatchExecutor") as mock_executor_class:
                mock_executor = Mock()
                # First step passes, second fails
                mock_executor.apply_patch_and_test.side_effect = [
                    {
                        "ok": True,
                        "stdout": "1 passed",
                        "stderr": "",
                        "tests_run": ["test1.py"],
                    },
                    {
                        "ok": False,
                        "stdout": "",
                        "stderr": "Test failed",
                        "error": "AssertionError",
                    },
                ]
                mock_executor_class.return_value = mock_executor

                with patch("stillme_core.verifier.Verifier") as mock_verifier_class:
                    mock_verifier = Mock()
                    # First verification passes, second fails
                    mock_verifier.verify.side_effect = [
                        {"passed": True, "reason": "test passed"},
                        {"passed": False, "reason": "test failed"},
                    ]
                    mock_verifier_class.return_value = mock_verifier

                    # Run the agent
                    controller = AgentController()

                    result = asyncio.run(controller.execute_task("Run multiple tests"))

                    # Verify result
                    assert result["total_steps"] == 2
                    assert result["passed_steps"] == 1
                    assert result["pass_rate"] == 0.5

                    # Verify step details
                    assert len(result["steps"]) == 2
                    assert result["steps"][0]["exec_ok"] is True
                    assert result["steps"][1]["exec_ok"] is False

    def test_run_agent_convenience_function(self, tmp_path):
        """Test the convenience function"""
        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.return_value = []
            mock_planner_class.return_value = mock_planner

            # Test convenience function

            result = asyncio.run(run_agent("Test goal"))

            # Verify result structure
            assert "summary" in result
            assert "steps" in result
            assert "pass_rate" in result
            assert result["goal"] == "Test goal"

    def test_run_agent_exception_handling(self, tmp_path):
        """Test agent flow with exceptions"""
        with patch("stillme_core.core.planner.Planner") as mock_planner_class:
            mock_planner = Mock()
            mock_planner.build_plan.side_effect = Exception("Planner error")
            mock_planner_class.return_value = mock_planner

            # Run the agent
            controller = AgentController()

            result = asyncio.run(controller.execute_task("Error goal"))

            # Verify result
            assert result["total_steps"] == 0
            assert result["passed_steps"] == 0
            assert "AgentDev failed" in result["summary"]
            assert "Planner error" in result["summary"]