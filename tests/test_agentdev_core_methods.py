# tests/test_agentdev_core_methods.py
"""Unit tests for AgentDev core methods"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_log_method():
    """Test _log method"""
    from agent_dev.core.agentdev import AgentDev

    agent = AgentDev()

    # Test basic logging
    agent._log("Test message", "INFO")
    assert len(agent.log_messages) == 1
    assert "[INFO] Test message" in agent.log_messages[0]

    # Test with context
    agent._log("Test with context", "WARNING", action="test", result="success")
    assert len(agent.log_messages) == 2
    assert "[WARNING] Test with context" in agent.log_messages[1]


def test_run_ruff_scan():
    """Test _run_ruff_scan method"""

    agent = AgentDev()

    # Mock subprocess.run to return successful ruff output
    mock_output = "[]"  # Empty ruff output
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = agent._run_ruff_scan()

        assert result["success"] is True
        assert result["errors"] == 0
        assert result["files"] == 0
        assert result["details"] == []


def test_create_backup():
    """Test _create_backup method"""
    import tempfile


    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('hello')")

        agent = AgentDev(project_root=temp_dir)

        # Create backup
        backup_path = agent._create_backup()

        assert backup_path.exists()
        assert backup_path.is_dir()

        # Check backup contains the test file
        backup_file = backup_path / "test.py"
        assert backup_file.exists()
        assert backup_file.read_text() == "print('hello')"


def test_rollback():
    """Test _rollback method"""


    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('original')")

        agent = AgentDev(project_root=temp_dir)

        # Create backup
        backup_path = agent._create_backup()

        # Modify file
        test_file.write_text("print('modified')")
        assert test_file.read_text() == "print('modified')"

        # Rollback
        agent._rollback(backup_path)

        # Check file is restored
        assert test_file.read_text() == "print('original')"


def test_scan_errors():
    """Test scan_errors method"""

    agent = AgentDev()

    # Mock _run_ruff_scan to return test data
    mock_report = {
        "success": True,
        "errors": 1,
        "files": 1,
        "details": [
            {
                "filename": "test.py",
                "location": {"row": 1, "column": 1},
                "code": "E999",
                "message": "Test error",
            }
        ],
    }

    with patch.object(agent, "_run_ruff_scan", return_value=mock_report):
        errors = agent.scan_errors()

        assert len(errors) == 1
        assert errors[0].file == "test.py"
        assert errors[0].line == 1
        assert errors[0].rule == "E999"
        assert errors[0].msg == "Test error"


def test_fix_errors():
    """Test fix_errors method"""
    from agent_dev.core.agentdev import AgentDev, ErrorInfo

    agent = AgentDev()

    # Create test error
    error = ErrorInfo(file="test.py", line=1, col=1, rule="E999", msg="Test error")

    # Mock _apply_fix to return success
    with patch.object(agent, "_apply_fix", return_value=True):
        result = agent.fix_errors([error])

        assert result["fixed"] == 1
        assert result["failed"] == 0
        assert result["files_touched"] == 1