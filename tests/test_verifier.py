"""
Test for Verifier class
"""

from stillme_core.verifier import Verifier


class TestVerifier:
    def test_verify_success_basic(self):
        """Test basic successful verification"""
        verifier = Verifier()

        step = {"action": "run_tests"}
        exec_result = {"ok": True, "stdout": "2 passed", "stderr": "", "exit_code": 0}

        result = verifier.verify(step, exec_result)

        assert result["passed"] is True
        assert "success patterns matched" in result["reason"]

    def test_verify_failure_basic(self):
        """Test basic failed verification"""
        verifier = Verifier()

        step = {"action": "run_tests"}
        exec_result = {
            "ok": False,
            "stdout": "",
            "stderr": "Error occurred",
            "exit_code": 1,
        }

        result = verifier.verify(step, exec_result)

        assert result["passed"] is False
        assert "execution failed" in result["reason"]

    def test_verify_custom_criteria(self):
        """Test verification with custom success criteria"""
        verifier = Verifier()

        step = {
            "action": "run_tests",
            "success_criteria": {
                "exit_code": 0,
                "stdout_patterns": [r"(\d+)\s+passed"],
                "stderr_patterns": [r"^$"],  # Empty stderr
            },
        }

        exec_result = {"ok": True, "stdout": "3 passed", "stderr": "", "exit_code": 0}

        result = verifier.verify(step, exec_result)

        assert result["passed"] is True
        assert "custom criteria satisfied" in result["reason"]

    def test_verify_custom_criteria_failure(self):
        """Test verification with custom criteria that fail"""
        verifier = Verifier()

        step = {
            "action": "run_tests",
            "success_criteria": {
                "exit_code": 0,
                "stdout_patterns": [r"(\d+)\s+passed"],
                "stderr_patterns": [r"^$"],  # Empty stderr
            },
        }

        exec_result = {
            "ok": True,
            "stdout": "1 failed",
            "stderr": "Some error",
            "exit_code": 0,
        }

        result = verifier.verify(step, exec_result)

        assert result["passed"] is False
        assert "stdout patterns not matched" in result["reason"]

    def test_verify_exit_code_mismatch(self):
        """Test verification with exit code mismatch"""
        verifier = Verifier()

        step = {"action": "run_tests", "success_criteria": {"exit_code": 0}}

        exec_result = {
            "ok": True,
            "stdout": "Tests passed",
            "stderr": "",
            "exit_code": 1,
        }

        result = verifier.verify(step, exec_result)

        assert result["passed"] is False
        assert "exit code mismatch" in result["reason"]

    def test_verify_invalid_exec_result(self):
        """Test verification with invalid exec_result"""
        verifier = Verifier()

        step = {"action": "run_tests"}
        exec_result = "invalid result"

        result = verifier.verify(step, exec_result)

        assert result["passed"] is False
        assert "not a dictionary" in result["reason"]

    def test_verify_test_results(self):
        """Test specialized test results verification"""
        verifier = Verifier()

        exec_result = {
            "ok": True,
            "stdout": "collected 5 items\n3 passed, 2 failed",
            "stderr": "",
            "exit_code": 0,
        }

        result = verifier.verify_test_results(exec_result)

        assert result["passed"] is False  # 2 failed
        assert "test results verification" in result["reason"]
        assert "stats" in result["details"]
        assert result["details"]["stats"]["collected"] == 5
        assert result["details"]["stats"]["passed"] == 3
        assert result["details"]["stats"]["failed"] == 2

    def test_verify_test_results_success(self):
        """Test successful test results verification"""
        verifier = Verifier()

        exec_result = {
            "ok": True,
            "stdout": "collected 3 items\n3 passed",
            "stderr": "",
            "exit_code": 0,
        }

        result = verifier.verify_test_results(exec_result)

        assert result["passed"] is True
        assert result["details"]["stats"]["collected"] == 3
        assert result["details"]["stats"]["passed"] == 3
        assert result["details"]["stats"]["failed"] == 0

    def test_extract_test_stats(self):
        """Test test statistics extraction"""
        verifier = Verifier()

        text = "collected 10 items\n8 passed, 1 failed, 1 skipped, 2 warnings"
        stats = verifier._extract_test_stats(text)

        assert stats["collected"] == 10
        assert stats["passed"] == 8
        assert stats["failed"] == 1
        assert stats["skipped"] == 1
        assert stats["warnings"] == 2

    def test_check_patterns(self):
        """Test pattern checking functionality"""
        verifier = Verifier()

        text = "3 tests passed successfully"
        patterns = [r"(\d+)\s+passed", r"success"]

        result = verifier._check_patterns(text, patterns)
        assert result is True

        # Test with no matches
        patterns = [r"(\d+)\s+failed"]
        result = verifier._check_patterns(text, patterns)
        assert result is False

        # Test with empty patterns
        result = verifier._check_patterns(text, [])
        assert result is True
