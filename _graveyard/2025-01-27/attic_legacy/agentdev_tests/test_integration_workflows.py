#!/usr/bin/env python3
"""
Integration tests for AgentDev cross-module workflows
Tests Plan→Evaluate→Execute→Validate pipeline
"""

import os
import shutil
import tempfile
import time

import pytest

# Import AgentDev modules
from agent_dev.core.agentdev import AgentDev
from agent_dev.fixtures.mock_llm import MockLLMProvider


class TestAgentDevWorkflows:
    """Integration tests for AgentDev workflows"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agentdev = AgentDev()
        self.mock_llm = MockLLMProvider(seed=42)

        # Create test project structure
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project, exist_ok=True)

        # Create test files
        self._create_test_files()

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_files(self):
        """Create test files for integration testing"""
        # Main application file
        main_file = os.path.join(self.test_project, "main.py")
        with open(main_file, "w") as f:
            f.write("""
import requests
import json
from typing import Dict, List

def process_data(data: Dict[str, Any]) -> List[str]:
    \"\"\"Process data and return results\"\"\"
    results = []
    for key, value in data.items():
        if isinstance(value, str):
            results.append(value.upper())
        elif isinstance(value, int):
            results.append(str(value * 2))
    return results

def calculate_sum(a: int, b: int) -> int:
    \"\"\"Calculate sum of two numbers\"\"\"
    return a + b

if __name__ == "__main__":
    data = {"name": "test", "value": 42}
    result = process_data(data)
    print(result)
""")

        # Test file
        test_file = os.path.join(self.test_project, "test_main.py")
        with open(test_file, "w") as f:
            f.write("""
import unittest
from main import process_data, calculate_sum

class TestMain(unittest.TestCase):
    def test_process_data(self):
        data = {"name": "test", "value": 42}
        result = process_data(data)
        self.assertEqual(result, ["TEST", "84"])
    
    def test_calculate_sum(self):
        result = calculate_sum(5, 3)
        self.assertEqual(result, 8)

if __name__ == "__main__":
    unittest.main()
""")

        # Requirements file
        requirements_file = os.path.join(self.test_project, "requirements.txt")
        with open(requirements_file, "w") as f:
            f.write("""
requests>=2.25.1
numpy>=1.19.5
pandas>=1.2.4
""")

    @pytest.mark.integration
    def test_plan_evaluate_execute_validate_workflow(self):
        """Test complete Plan→Evaluate→Execute→Validate workflow"""
        # Test task
        task = "Add error handling to the process_data function"

        # Step 1: Plan
        plan_result = self.agentdev.planner.create_plan(task, self.test_project)
        assert plan_result is not None
        assert "steps" in plan_result
        assert len(plan_result["steps"]) > 0

        # Step 2: Evaluate (Impact Analysis)
        impact_data = {
            "files_affected": ["main.py"],
            "lines_changed": 10,
            "functions_modified": 1,
            "dependencies": ["requests"],
        }

        impact_result = self.agentdev.impact_analyzer.analyze_impact(impact_data)
        assert impact_result.risk_level in ["low", "medium", "high", "critical"]

        # Step 3: Execute (Code Generation)
        execution_result = self.agentdev.executor.execute_plan(
            plan_result, self.test_project
        )
        assert execution_result is not None
        assert "success" in execution_result
        assert "files_modified" in execution_result

        # Step 4: Validate
        validation_result = self.agentdev.executor.validate_changes(self.test_project)
        assert validation_result is not None
        assert "validation_passed" in validation_result

    @pytest.mark.integration
    def test_cross_module_communication(self):
        """Test communication between different modules"""
        # Test data flow between modules
        task_data = {
            "task": "Optimize performance of data processing",
            "files": ["main.py"],
            "priority": "high",
            "security_impact": True,
        }

        # Impact Analysis
        impact_result = self.agentdev.impact_analyzer.analyze_impact(task_data)

        # Business Thinking
        business_data = {
            "development_cost": 50000,
            "maintenance_cost": 10000,
            "expected_revenue": 100000,
            "time_to_market": 3,
            "market_size": 1000000,
            "competitive_advantage": 0.8,
        }
        business_result = self.agentdev.business_thinking.calculate_roi(business_data)

        # Security Thinking
        security_data = {
            "files": ["main.py"],
            "authentication": True,
            "encryption": True,
            "input_validation": True,
        }
        security_result = self.agentdev.security_thinking.analyze_security(
            security_data
        )

        # All modules should work together
        assert impact_result.impact_score >= 0
        assert business_result.roi_score >= 0
        assert security_result["security_score"] >= 0

    @pytest.mark.integration
    def test_policy_levels_integration(self):
        """Test different policy levels (strict/balanced/creative)"""
        task = "Refactor the calculate_sum function"

        # Test strict policy
        strict_result = self.agentdev.execute_task(task, mode="strict")
        assert strict_result is not None
        assert "policy" in strict_result
        assert strict_result["policy"] == "strict"

        # Test balanced policy
        balanced_result = self.agentdev.execute_task(task, mode="balanced")
        assert balanced_result is not None
        assert balanced_result["policy"] == "balanced"

        # Test creative policy
        creative_result = self.agentdev.execute_task(task, mode="creative")
        assert creative_result is not None
        assert creative_result["policy"] == "creative"

        # Results should be different based on policy
        assert strict_result != balanced_result
        assert balanced_result != creative_result

    @pytest.mark.integration
    def test_learning_hooks_integration(self):
        """Test learning hooks between modules"""
        # Simulate multiple successful operations
        for i in range(5):
            task = f"Task {i}: Optimize function performance"
            result = self.agentdev.execute_task(task, mode="senior")

            # Record success for learning
            if result.get("success", False):
                self.agentdev.experience_learner.record_success(task, result)

        # Check if learning has improved success rate
        learning_stats = self.agentdev.experience_learner.get_learning_stats()
        assert learning_stats["success_count"] > 0
        assert learning_stats["total_attempts"] > 0

        # Success rate should improve over time
        success_rate = (
            learning_stats["success_count"] / learning_stats["total_attempts"]
        )
        assert success_rate > 0.5  # At least 50% success rate

    @pytest.mark.integration
    def test_error_handling_workflow(self):
        """Test error handling across modules"""
        # Test with invalid task
        invalid_task = None

        with pytest.raises((ValueError, TypeError)):
            self.agentdev.execute_task(invalid_task)

        # Test with invalid project path
        invalid_path = "/non/existent/path"

        with pytest.raises((FileNotFoundError, OSError)):
            self.agentdev.execute_task("Valid task", project_path=invalid_path)

    @pytest.mark.integration
    def test_monitoring_integration(self):
        """Test monitoring and metrics collection"""
        # Execute task and collect metrics
        task = "Add logging to the application"
        result = self.agentdev.execute_task(task, mode="senior")

        # Check if metrics were collected
        metrics = self.agentdev.monitor.get_metrics()
        assert metrics is not None
        assert "task_count" in metrics
        assert "success_rate" in metrics
        assert "average_execution_time" in metrics

    @pytest.mark.integration
    def test_security_integration(self):
        """Test security integration across modules"""
        # Test security-sensitive task
        security_task = "Add authentication to the API"

        # Security analysis should be triggered
        result = self.agentdev.execute_task(security_task, mode="senior")

        # Should include security analysis
        assert "security_analysis" in result
        assert "security_recommendations" in result

        # Security score should be calculated
        security_score = result.get("security_score", 0)
        assert 0 <= security_score <= 1

    @pytest.mark.integration
    def test_performance_integration(self):
        """Test performance monitoring across modules"""

        # Execute multiple tasks and measure performance
        start_time = time.time()

        tasks = [
            "Optimize data processing",
            "Add error handling",
            "Improve code readability",
        ]

        for task in tasks:
            result = self.agentdev.execute_task(task, mode="senior")
            assert result is not None

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 10.0  # Less than 10 seconds

        # Performance metrics should be collected
        performance_metrics = self.agentdev.monitor.get_performance_metrics()
        assert "average_execution_time" in performance_metrics
        assert "total_executions" in performance_metrics

    @pytest.mark.integration
    def test_cleanup_integration(self):
        """Test cleanup integration"""
        # Create temporary files for cleanup
        temp_files = ["temp_file.tmp", "backup_file.bak", "cache_file.cache"]

        for temp_file in temp_files:
            file_path = os.path.join(self.test_project, temp_file)
            with open(file_path, "w") as f:
                f.write("temporary content")

        # Run cleanup analysis
        cleanup_result = self.agentdev.cleanup_manager.analyze_cleanup_opportunities(
            self.test_project
        )

        assert isinstance(cleanup_result, list)
        assert len(cleanup_result) > 0

        # Should detect temporary files
        temp_file_detections = [
            item for item in cleanup_result if "temp" in item.description.lower()
        ]
        assert len(temp_file_detections) > 0

    @pytest.mark.integration
    def test_conflict_resolution_integration(self):
        """Test conflict resolution integration"""
        # Create files with conflicts
        conflict_file1 = os.path.join(self.test_project, "conflict1.py")
        conflict_file2 = os.path.join(self.test_project, "conflict2.py")

        with open(conflict_file1, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b
""")

        with open(conflict_file2, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b + 1  # Different implementation
""")

        # Detect conflicts
        conflicts = self.agentdev.conflict_resolver.detect_conflicts(self.test_project)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

        # Should detect code conflicts
        code_conflicts = [c for c in conflicts if c.conflict_type == "code_conflict"]
        assert len(code_conflicts) > 0

    @pytest.mark.integration
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # Complete workflow: Plan → Analyze → Execute → Validate → Learn
        task = "Create a secure data processing module with error handling"

        # Step 1: Plan
        plan = self.agentdev.planner.create_plan(task, self.test_project)
        assert plan is not None

        # Step 2: Analyze (Impact + Business + Security)
        impact_analysis = self.agentdev.impact_analyzer.analyze_impact(
            {
                "files_affected": ["new_module.py"],
                "lines_changed": 100,
                "functions_modified": 5,
                "dependencies": ["requests", "cryptography"],
            }
        )

        business_analysis = self.agentdev.business_thinking.calculate_roi(
            {
                "development_cost": 75000,
                "maintenance_cost": 15000,
                "expected_revenue": 150000,
                "time_to_market": 4,
                "market_size": 2000000,
                "competitive_advantage": 0.9,
            }
        )

        security_analysis = self.agentdev.security_thinking.analyze_security(
            {
                "files": ["new_module.py"],
                "authentication": True,
                "encryption": True,
                "input_validation": True,
            }
        )

        # Step 3: Execute
        execution_result = self.agentdev.executor.execute_plan(plan, self.test_project)
        assert execution_result is not None

        # Step 4: Validate
        validation_result = self.agentdev.executor.validate_changes(self.test_project)
        assert validation_result is not None

        # Step 5: Learn
        if execution_result.get("success", False):
            self.agentdev.experience_learner.record_success(task, execution_result)

        # All steps should complete successfully
        assert impact_analysis.impact_score >= 0
        assert business_analysis.roi_score >= 0
        assert security_analysis["security_score"] >= 0
        assert execution_result.get("success", False)
        assert validation_result.get("validation_passed", False)


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
