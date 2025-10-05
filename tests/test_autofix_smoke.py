#!/usr/bin/env python3
"""
Test Auto-Fix Smoke Tests
=========================

Smoke tests for the autofix system.
"""

import pytest
import tempfile
from pathlib import Path

from agent_dev.auto_fix import AutoFixSystem


class TestAutoFixSmoke:
    """Smoke tests for autofix system"""

    def test_autofix_initialization(self):
        """Test autofix system initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))
            assert autofix.engine is not None
            assert autofix.repo is not None
            assert autofix.rule_engine is not None
            assert autofix.monitoring is not None
            assert autofix.anomaly_detector is not None
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()

    def test_parse_errors(self):
        """Test error parsing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))

            # Test pytest error parsing
            stdout = """
test_file.py::test_function FAILED
test_file.py::test_another PASSED
"""
            stderr = """
FAILED test_file.py::test_function - NameError: name 'json' is not defined
"""

            errors = autofix.parse_errors(stdout, stderr)

            assert len(errors) > 0
            assert any(e["source"] == "pytest" for e in errors)
            assert any("json" in e["error_sig"] for e in errors)
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()

    def test_select_rules(self):
        """Test rule selection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))

            # Test with JSON import error
            errors = [
                {
                    "source": "pytest",
                    "test_name": "test_function",
                    "error_sig": "NameError: name 'json' is not defined",
                    "file_path": "test_file.py",
                    "line_number": 10,
                }
            ]

            rule_error_pairs = autofix.select_rules(errors)

            # Should find matching rules (or at least not crash)
            # Note: May be 0 if no rules match, which is acceptable for smoke test
            assert isinstance(rule_error_pairs, list)
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()

    def test_apply_fixes_smoke(self):
        """Test applying fixes (smoke test)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))

            # Create a test file with missing import
            test_file_path = Path(temp_dir) / "test_file.py"
            test_file_path.write_text("""
def test_function():
    json.dumps({"test": "data"})
""")

            # Test applying fixes
            rule_error_pairs = [
                (
                    {
                        "name": "missing_imports_general",
                        "fix_action": "fix_missing_imports_general",
                        "severity": "medium",
                        "enabled": True,
                    },
                    {
                        "source": "pytest",
                        "test_name": "test_function",
                        "error_sig": "NameError: name 'json' is not defined",
                        "file_path": str(test_file_path),
                        "line_number": 2,
                    },
                )
            ]

            results = autofix.apply_fixes(rule_error_pairs)

            assert len(results) == 1
            # Note: This might fail if the fixer doesn't work perfectly
            # but it's a smoke test to ensure the system runs
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()

    def test_run_autofix_cycle_smoke(self):
        """Test running autofix cycle (smoke test)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))

            # Run autofix cycle (should not crash)
            result = autofix.run_autofix_cycle()

            assert "success" in result
            assert "fixes_applied" in result
            assert "tests_passing" in result
            assert "message" in result
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()

    def test_run_multiple_cycles_smoke(self):
        """Test running multiple cycles (smoke test)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            autofix = AutoFixSystem(str(db_path))

            # Run multiple cycles (should not crash)
            result = autofix.run_multiple_cycles(max_tries=1)

            assert "success" in result
            assert "cycles_run" in result
            assert "total_fixes" in result
            assert "final_result" in result
            # Close database connection
            if hasattr(autofix, "engine") and autofix.engine:
                autofix.engine.dispose()


if __name__ == "__main__":
    pytest.main([__file__])
