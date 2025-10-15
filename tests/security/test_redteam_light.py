"""
Test Red-Team Light Security Check
==================================

Tests for the light security check functionality in RedTeamEngine.
"""

import tempfile
from pathlib import Path

from stillme_core.core.advanced_security.red_team_engine import RedTeamEngine


class TestRedTeamLightSecurity:
    """Test cases for light security check"""

    def test_light_security_check_clean_files(self):
        """Test security check with clean files"""
        engine = RedTeamEngine()

        # Create temporary directory with clean Python file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create clean Python file
            clean_file = temp_path / "clean.py"
            clean_file.write_text("""
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
""")

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should have no findings
            assert result["score"] == 0.0
            assert len(result["findings"]) == 0
            assert "error" not in result

    def test_light_security_check_hardcoded_secrets(self):
        """Test security check with hardcoded secrets"""
        engine = RedTeamEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with hardcoded secrets
            secret_file = temp_path / "secrets.py"
            secret_file.write_text("""
# This file contains hardcoded secrets (for testing)
api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef"
password = "super_secret_password"
token = "ghp_1234567890abcdef1234567890abcdef12345678"

def connect_to_api():
    headers = {"Authorization": f"Bearer {token}"}
    return headers
""")

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should have findings
            assert result["score"] > 0.0
            assert len(result["findings"]) > 0

            # Check for specific findings
            finding_types = [f["type"] for f in result["findings"]]
            assert "secret" in finding_types

            # Check severity levels
            severities = [f["severity"] for f in result["findings"]]
            assert "HIGH" in severities

    def test_light_security_check_dangerous_apis(self):
        """Test security check with dangerous API usage"""
        engine = RedTeamEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with dangerous APIs
            dangerous_file = temp_path / "dangerous.py"
            dangerous_file.write_text("""
import os
import subprocess

def execute_command(user_input):
    # Dangerous: direct eval
    result = eval(user_input)

    # Dangerous: exec
    exec("print('Hello')")

    # Dangerous: system call
    os.system("ls -la")

    # Dangerous: subprocess call
    subprocess.call(["rm", "-rf", "/tmp"])

    return result
""")

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should have findings
            assert result["score"] > 0.0
            assert len(result["findings"]) > 0

            # Check for dangerous API findings
            finding_types = [f["type"] for f in result["findings"]]
            assert "dangerous_api" in finding_types

    def test_light_security_check_unicode_handling(self):
        """Test security check with Unicode files"""
        engine = RedTeamEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with Unicode content
            unicode_file = temp_path / "unicode.py"
            unicode_file.write_text(
                """
# File with Unicode content: 你好世界
def hello_unicode():
    message = "Xin chào thế giới! 🌍"
    password = "secret_password"  # This should be detected
    return message
""",
                encoding="utf-8",
            )

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should not crash and should detect secrets
            assert "error" not in result
            assert result["score"] > 0.0
            assert len(result["findings"]) > 0

    def test_light_security_check_mixed_content(self):
        """Test security check with mixed content"""
        engine = RedTeamEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple files with different content
            files = [
                ("clean.py", "def clean_function(): pass"),
                ("secrets.py", 'api_key = "sk-test123"'),
                ("dangerous.py", "eval('print(1)')"),
                (
                    "mixed.py",
                    """
def mixed_function():
    # Clean code
    x = 1 + 1

    # Secret
    secret = "password123"

    # Dangerous
    exec("print('dangerous')")

    return x
""",
                ),
            ]

            for filename, content in files:
                file_path = temp_path / filename
                file_path.write_text(content)

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should have findings from multiple files
            assert result["score"] > 0.0
            assert len(result["findings"]) > 0

            # Check that findings come from different files
            file_paths = [f["path"] for f in result["findings"]]
            assert len(set(file_paths)) > 1  # Multiple files should have findings

    def test_light_security_check_error_handling(self):
        """Test security check error handling"""
        engine = RedTeamEngine()

        # Test with non-existent directory
        result = engine.run_light_security_check("/non/existent/path")

        # Should handle gracefully
        assert "error" in result or result["score"] == 0.0
        assert len(result["findings"]) == 0

    def test_light_security_check_performance(self):
        """Test security check performance with many files"""
        engine = RedTeamEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create many files (but limit to 100 in implementation)
            for i in range(150):  # More than the 100 file limit
                file_path = temp_path / f"file_{i}.py"
                file_path.write_text(f"def function_{i}(): pass")

            # Run security check
            result = engine.run_light_security_check(str(temp_path))

            # Should complete without error
            assert "error" not in result
            assert result["score"] == 0.0  # Clean files
            assert len(result["findings"]) == 0
