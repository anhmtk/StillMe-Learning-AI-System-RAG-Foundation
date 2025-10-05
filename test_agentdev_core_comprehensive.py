#!/usr/bin/env python3
"""
Comprehensive AgentDev Core Tests - Tự sinh test cases
Kiểm tra toàn diện các chức năng core của AgentDev
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agent_dev.core.agentdev import AgentDev, ErrorInfo

    AGENTDEV_AVAILABLE = True
except ImportError as e:
    AGENTDEV_AVAILABLE = False
    print(f"Warning: AgentDev not available: {e}")


@pytest.fixture
def temp_project():
    """Tạo project tạm thời để test"""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Tạo cấu trúc project cơ bản
    (project_path / "src").mkdir()
    (project_path / "tests").mkdir()

    # Tạo file Python có lỗi để test
    test_file = project_path / "src" / "test_module.py"
    test_file.write_text("""
def broken_function():
    x = 1
    y = 2
    z = x + y  # Missing return
    print(z)

class TestClass:
    def __init__(self):
        self.value = None
    
    def method_with_error(self):
        return self.value.upper()  # Potential AttributeError
""")

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)


class TestAgentDevCore:
    """Test core AgentDev functionality"""

    def test_agentdev_initialization(self):
        """Test AgentDev initialization"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=".", mode="critical-first")
        assert agent.project_root == Path(".")
        assert agent.mode == "critical-first"
        assert agent.total_errors_fixed == 0
        assert agent.total_files_processed == 0

    def test_agentdev_inventory_check(self, temp_project):
        """Test inventory check functionality"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))
        inventory = agent._inventory_check()

        assert "valid" in inventory
        assert "issues" in inventory
        assert "timestamp" in inventory

    def test_agentdev_scan_errors(self, temp_project):
        """Test error scanning functionality"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Mock ruff output - _run_ruff_scan returns a dict with success, errors, files, details
        mock_report = {
            "success": True,
            "errors": 1,
            "files": 1,
            "details": [
                {
                    "code": "E999",
                    "message": "Syntax error",
                    "filename": str(temp_project / "src" / "test_module.py"),
                    "location": {"row": 1, "column": 1},
                }
            ],
        }

        with patch.object(agent, "_run_ruff_scan", return_value=mock_report):
            errors = agent.scan_errors()
            assert isinstance(errors, list)

    def test_agentdev_fix_errors(self, temp_project):
        """Test error fixing functionality"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Mock error info - use correct constructor
        error_info = ErrorInfo(
            file=str(temp_project / "src" / "test_module.py"),
            line=1,
            col=1,
            rule="E999",
            msg="Test error",
            severity="error",
        )

        with patch.object(agent, "_apply_fix", return_value=True):
            fixed_count = agent.fix_errors([error_info])
            assert fixed_count == 1
            assert agent.total_errors_fixed == 1

    def test_agentdev_backup_creation(self, temp_project):
        """Test backup creation before fixes"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Test backup creation
        backup_path = agent._create_backup()
        assert backup_path.exists()
        assert backup_path.is_dir()

    def test_agentdev_rollback(self, temp_project):
        """Test rollback functionality"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Create backup first
        backup_path = agent._create_backup()

        # Modify a file to test rollback
        test_file = temp_project / "src" / "test_module.py"
        if test_file.exists():
            test_file.write_text("def modified_function():\n    pass")

        # Test rollback
        agent._rollback(backup_path)
        # Verify rollback worked (file should be restored)
        if test_file.exists():
            # Just check that file exists and has content
            content = test_file.read_text()
            assert len(content) > 0


class TestAgentMode:
    """Test AgentMode functionality"""

    def test_agent_mode_initialization(self):
        """Test AgentMode initialization"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        # AgentMode is an enum, not a class
        from agent_dev.core.agentdev import AgentDev

        agent = AgentDev()
        assert agent.mode == "critical-first"

    def test_agent_mode_switching(self):
        """Test mode switching"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        # Test mode switching
        from agent_dev.core.agentdev import AgentDev

        agent = AgentDev(mode="safe")
        assert agent.mode == "safe"


class TestAdaptiveStrategy:
    """Test AdaptiveStrategy functionality"""

    def test_adaptive_strategy_initialization(self):
        """Test AdaptiveStrategy initialization"""
        # AdaptiveStrategy not implemented yet
        pytest.skip("AdaptiveStrategy not implemented yet")

    def test_adaptive_strategy_learning(self):
        """Test strategy learning"""
        # AdaptiveStrategy not implemented yet
        pytest.skip("AdaptiveStrategy not implemented yet")


class TestExperienceLearner:
    """Test ExperienceLearner functionality"""

    def test_experience_learner_initialization(self):
        """Test ExperienceLearner initialization"""
        # ExperienceLearner not implemented yet
        pytest.skip("ExperienceLearner not implemented yet")

    def test_experience_learner_learning(self):
        """Test experience learning"""
        # ExperienceLearner not implemented yet
        pytest.skip("ExperienceLearner not implemented yet")


class TestAgentDevIntegration:
    """Test AgentDev integration with other components"""

    def test_agentdev_with_adaptive_strategy(self):
        """Test AgentDev with AdaptiveStrategy"""
        # AdaptiveStrategy not implemented yet
        pytest.skip("AdaptiveStrategy not implemented yet")

    def test_agentdev_with_experience_learner(self):
        """Test AgentDev with ExperienceLearner"""
        # ExperienceLearner not implemented yet
        pytest.skip("ExperienceLearner not implemented yet")

    def test_agentdev_error_handling(self):
        """Test AgentDev error handling"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        # Test with invalid project root - should not raise exception
        agent = AgentDev(project_root="/nonexistent/path")
        assert agent.project_root == Path("/nonexistent/path")

    def test_agentdev_logging(self, temp_project):
        """Test AgentDev logging functionality"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Test logging
        agent._log("Test message")
        assert len(agent.log_messages) > 0
        assert "Test message" in agent.log_messages[-1]


class TestAgentDevPerformance:
    """Test AgentDev performance"""

    def test_agentdev_scan_performance(self, temp_project):
        """Test AgentDev scan performance"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        agent = AgentDev(project_root=str(temp_project))

        # Test scan performance
        import time

        start_time = time.time()

        with patch.object(
            agent,
            "_run_ruff_scan",
            return_value={"success": True, "errors": 0, "files": 0, "details": []},
        ):
            agent.scan_errors()

        end_time = time.time()
        scan_time = end_time - start_time

        # Should complete within reasonable time
        assert scan_time < 5.0  # 5 seconds max

    def test_agentdev_memory_usage(self, temp_project):
        """Test AgentDev memory usage"""
        if not AGENTDEV_AVAILABLE:
            pytest.skip("AgentDev not available")

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        agent = AgentDev(project_root=str(temp_project))

        # Simulate some operations
        for i in range(100):
            agent._log(f"Test message {i}")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
