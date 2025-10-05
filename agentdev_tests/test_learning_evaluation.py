#!/usr/bin/env python3
"""
Learning Evaluation tests for AgentDev
Tests A/B learning evaluation and continuous improvement
"""

import os
import shutil
import tempfile
import time

import pytest

# Import AgentDev modules
from agent_dev.core.agentdev import AgentDev
from agent_dev.core.experience_learner import ExperienceLearner


class TestAgentDevLearning:
    """Learning Evaluation tests for AgentDev"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agentdev = AgentDev()
        self.experience_learner = ExperienceLearner()

        # Create test project structure
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.learning
    def test_ab_learning_evaluation(self):
        """Test A/B learning evaluation"""
        # Test A/B learning setup
        task = "Implement A/B testing for learning evaluation"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "ab" in str(result).lower() or "testing" in str(result).lower()

    @pytest.mark.learning
    def test_learning_curve_analysis(self):
        """Test learning curve analysis"""
        # Simulate learning over multiple iterations
        tasks = [
            "Task 1: Basic optimization",
            "Task 2: Advanced optimization",
            "Task 3: Complex optimization",
            "Task 4: Expert optimization",
            "Task 5: Master optimization",
        ]

        success_rates = []
        execution_times = []

        for i, task in enumerate(tasks):
            start_time = time.time()
            result = self.agentdev.execute_task(
                task, project_path=self.test_project, mode="senior"
            )
            end_time = time.time()

            execution_time = end_time - start_time
            success = result.get("success", False)

            success_rates.append(1.0 if success else 0.0)
            execution_times.append(execution_time)

            # Record learning
            if success:
                self.experience_learner.record_success(task, result)
            else:
                self.experience_learner.record_failure(task, result)

        # Analyze learning curve
        learning_stats = self.experience_learner.get_learning_stats()

        assert learning_stats["success_count"] > 0
        assert learning_stats["total_attempts"] == len(tasks)

        # Success rate should improve over time (learning curve)
        early_success_rate = sum(success_rates[:2]) / 2
        late_success_rate = sum(success_rates[-2:]) / 2

        # Learning should show improvement
        assert late_success_rate >= early_success_rate

    @pytest.mark.learning
    def test_learning_adaptation(self):
        """Test learning adaptation"""
        # Test learning adaptation
        task = "Adapt learning strategy based on experience"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "adapt" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_experience_storage(self):
        """Test experience storage and retrieval"""
        # Test experience storage
        experiences = [
            {"task": "Task 1", "success": True, "time": 1.5},
            {"task": "Task 2", "success": False, "time": 2.0},
            {"task": "Task 3", "success": True, "time": 1.2},
            {"task": "Task 4", "success": True, "time": 1.0},
            {"task": "Task 5", "success": False, "time": 2.5},
        ]

        for experience in experiences:
            if experience["success"]:
                self.experience_learner.record_success(experience["task"], experience)
            else:
                self.experience_learner.record_failure(experience["task"], experience)

        # Retrieve stored experiences
        stored_experiences = self.experience_learner.get_experiences()

        assert len(stored_experiences) == len(experiences)
        assert all(
            exp["task"] in [e["task"] for e in stored_experiences]
            for exp in experiences
        )

    @pytest.mark.learning
    def test_pattern_recognition(self):
        """Test pattern recognition in learning"""
        # Test pattern recognition
        task = "Recognize patterns in successful operations"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "pattern" in str(result).lower() or "recognize" in str(result).lower()

    @pytest.mark.learning
    def test_learning_optimization(self):
        """Test learning optimization"""
        # Test learning optimization
        task = "Optimize learning algorithms for better performance"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "optimize" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_validation(self):
        """Test learning validation"""
        # Test learning validation
        task = "Validate learning effectiveness"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "validate" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_metrics(self):
        """Test learning metrics collection"""
        # Test learning metrics
        task = "Collect learning performance metrics"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "metrics" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_improvement(self):
        """Test learning improvement over time"""
        # Simulate learning improvement
        base_tasks = ["Basic task 1", "Basic task 2", "Basic task 3"]

        # Record initial performance
        initial_success_rate = 0
        for task in base_tasks:
            result = self.agentdev.execute_task(
                task, project_path=self.test_project, mode="senior"
            )
            if result.get("success", False):
                initial_success_rate += 1
                self.experience_learner.record_success(task, result)
            else:
                self.experience_learner.record_failure(task, result)

        initial_success_rate /= len(base_tasks)

        # Apply learning improvements
        improved_tasks = ["Improved task 1", "Improved task 2", "Improved task 3"]

        improved_success_rate = 0
        for task in improved_tasks:
            result = self.agentdev.execute_task(
                task, project_path=self.test_project, mode="senior"
            )
            if result.get("success", False):
                improved_success_rate += 1
                self.experience_learner.record_success(task, result)
            else:
                self.experience_learner.record_failure(task, result)

        improved_success_rate /= len(improved_tasks)

        # Learning should show improvement
        assert improved_success_rate >= initial_success_rate

    @pytest.mark.learning
    def test_learning_consistency(self):
        """Test learning consistency"""
        # Test learning consistency
        task = "Maintain consistent learning performance"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "consistent" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_efficiency(self):
        """Test learning efficiency"""
        # Test learning efficiency
        task = "Improve learning efficiency"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "efficient" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_robustness(self):
        """Test learning robustness"""
        # Test learning robustness
        task = "Ensure robust learning under various conditions"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "robust" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_scalability(self):
        """Test learning scalability"""
        # Test learning scalability
        task = "Scale learning to handle large datasets"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "scale" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_accuracy(self):
        """Test learning accuracy"""
        # Test learning accuracy
        task = "Improve learning accuracy"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "accuracy" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_generalization(self):
        """Test learning generalization"""
        # Test learning generalization
        task = "Generalize learning to new domains"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "generalize" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_transfer(self):
        """Test learning transfer"""
        # Test learning transfer
        task = "Transfer learning between tasks"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "transfer" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_retention(self):
        """Test learning retention"""
        # Test learning retention
        task = "Retain learned knowledge over time"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "retain" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_adaptation_speed(self):
        """Test learning adaptation speed"""
        # Test learning adaptation speed
        task = "Adapt quickly to new situations"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "adapt" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_quality(self):
        """Test learning quality"""
        # Test learning quality
        task = "Maintain high learning quality"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "quality" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_effectiveness(self):
        """Test learning effectiveness"""
        # Test learning effectiveness
        task = "Measure learning effectiveness"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert (
            "effectiveness" in str(result).lower() or "learning" in str(result).lower()
        )

    @pytest.mark.learning
    def test_learning_benchmarking(self):
        """Test learning benchmarking"""
        # Test learning benchmarking
        task = "Benchmark learning performance"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "benchmark" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_comparison(self):
        """Test learning comparison"""
        # Test learning comparison
        task = "Compare different learning approaches"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert "compare" in str(result).lower() or "learning" in str(result).lower()

    @pytest.mark.learning
    def test_learning_evaluation_comprehensive(self):
        """Test comprehensive learning evaluation"""
        # Test comprehensive learning evaluation
        task = "Perform comprehensive learning evaluation"

        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)
        assert (
            "comprehensive" in str(result).lower() or "learning" in str(result).lower()
        )


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
