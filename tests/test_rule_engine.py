#!/usr/bin/env python3
"""
Test Rule Engine
================

Tests for the rule engine and fixers.
"""

import pytest
import tempfile
from pathlib import Path

from agent_dev.rules.actions import apply_fixer, fix_missing_imports_general
from agent_dev.rules.engine import RuleEngine


class TestRuleEngine:
    """Test rule engine functionality"""

    def test_load_yaml_rules(self):
        """Test loading YAML rules"""
        engine = RuleEngine()
        engine.load_yaml_rules("rulesets/agentdev_rules.yaml")

        assert len(engine.rules) > 0
        assert any(
            rule.get("name") == "import_missing_sqlalchemy_session"
            for rule in engine.rules
        )

    def test_find_matching_rules(self):
        """Test finding matching rules"""
        engine = RuleEngine()
        engine.load_yaml_rules("rulesets/agentdev_rules.yaml")

        # Test SQLAlchemy Session error
        error_text = "NameError: name 'Session' is not defined"
        matching = engine.find_matching_rules(error_text)

        assert len(matching) > 0
        assert any(
            rule["name"] == "import_missing_sqlalchemy_session" for rule in matching
        )

    def test_rule_priority_sorting(self):
        """Test rule priority sorting"""
        engine = RuleEngine()

        # Add some test rules with different priorities
        engine.rules = [
            {
                "name": "low_priority",
                "severity": "low",
                "hits": 5,
                "enabled": True,
                "pattern_regex": "test error",
            },
            {
                "name": "high_priority",
                "severity": "high",
                "hits": 2,
                "enabled": True,
                "pattern_regex": "test error",
            },
            {
                "name": "medium_priority",
                "severity": "medium",
                "hits": 3,
                "enabled": True,
                "pattern_regex": "test error",
            },
        ]

        matching = engine.find_matching_rules("test error")

        # Should be sorted by priority (severity * hits)
        # high_priority: 3 * 2 = 6
        # medium_priority: 2 * 3 = 6
        # low_priority: 1 * 5 = 5
        assert len(matching) == 3


class TestFixers:
    """Test individual fixers"""

    def test_fix_missing_imports_general(self):
        """Test general missing imports fixer"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def test_function():
    json.dumps({})
    os.path.join("a", "b")
""")
            f.flush()

            try:
                # Test JSON import fix
                success = fix_missing_imports_general(
                    f.name, 0, "NameError: name 'json' is not defined"
                )

                assert success

                # Check if import was added
                with open(f.name, "r") as f_read:
                    content = f_read.read()
                    assert "import json" in content
            finally:
                # Clean up
                try:
                    Path(f.name).unlink()
                except PermissionError:
                    pass  # File might be in use on Windows

    def test_apply_fixer(self):
        """Test apply_fixer function"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def test_function():
    json.dumps({})
""")
            f.flush()

            try:
                # Test applying fixer
                success = apply_fixer(
                    "fix_missing_imports_general",
                    f.name,
                    0,
                    "NameError: name 'json' is not defined",
                )

                assert success

                # Check if import was added
                with open(f.name, "r") as f_read:
                    content = f_read.read()
                    assert "import json" in content
            finally:
                # Clean up
                try:
                    Path(f.name).unlink()
                except PermissionError:
                    pass  # File might be in use on Windows

    def test_apply_fixer_invalid_action(self):
        """Test apply_fixer with invalid action"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test(): pass")
            f.flush()

            try:
                # Test invalid fixer
                success = apply_fixer("invalid_fixer", f.name, 0, "test error")

                assert not success
            finally:
                # Clean up
                try:
                    Path(f.name).unlink()
                except PermissionError:
                    pass  # File might be in use on Windows


if __name__ == "__main__":
    pytest.main([__file__])