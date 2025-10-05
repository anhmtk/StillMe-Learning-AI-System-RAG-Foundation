#!/usr/bin/env python3
"""
Comprehensive tests for agent_dev/rules/engine.py
"""

import pytest

from agent_dev.rules.engine import RuleEngine


class TestRuleEngineOperators:
    """Test all rule engine operators"""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance"""
        return RuleEngine()

    def test_all_operators_basic(self, rule_engine):
        """Test all operators with basic cases"""
        cases = [
            ("eq", "A", ["A"], True),
            ("neq", "A", ["B"], True),
            ("gt", 5, [3], True),
            ("lt", 3, [5], True),
            ("in", "x", ["x", "y"], True),
            ("regex", "abc", [r"^a.*"], True),
            ("contains", "hello world", ["world"], True),
            ("not_contains", "hello", ["bad"], True),
            ("exists", "value", [], True),
            ("not_exists", None, [], True),
        ]

        for op, field_value, expected, should_pass in cases:
            context = {"test": field_value}
            condition = {"field": "test", "operator": op, "value": expected}
            result = rule_engine._evaluate_condition(condition, context)
            assert (
                result == should_pass
            ), f"Failed for {op}: {field_value} {op} {expected}"

    def test_operators_negative_cases(self, rule_engine):
        """Test operators with negative cases"""
        cases = [
            ("eq", "A", ["B"], False),
            ("ne", "A", ["A"], False),
            ("gt", 3, [5], False),
            ("lt", 5, [3], False),
            ("in", "z", ["x", "y"], False),
            ("regex", "xyz", [r"^a.*"], False),
            ("contains", "hello", ["world"], False),
            ("not_contains", "hello world", ["hello"], False),
            ("exists", None, [], False),
            ("not_exists", "value", [], False),
        ]

        for op, field_value, expected, should_pass in cases:
            context = {"test": field_value}
            condition = {"field": "test", "operator": op, "value": expected}
            result = rule_engine._evaluate_condition(condition, context)
            assert (
                result == should_pass
            ), f"Failed for {op}: {field_value} {op} {expected}"

    def test_unsupported_operator(self, rule_engine):
        """Test unsupported operator"""
        condition = {"field": "test", "operator": "unsupported", "value": ["test"]}
        result = rule_engine._evaluate_condition(condition, {"test": "value"})
        assert result is False

    def test_missing_field(self, rule_engine):
        """Test missing field in context"""
        condition = {"field": "missing", "operator": "eq", "value": ["test"]}
        result = rule_engine._evaluate_condition(condition, {"test": "value"})
        assert result is False


class TestRuleEngineNestedContext:
    """Test rule engine with nested context"""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance"""
        return RuleEngine()

    def test_nested_field_access(self, rule_engine):
        """Test nested field access with dot notation"""
        context = {"user": {"profile": {"role": "admin"}}}

        # Test nested access
        result = rule_engine._get_nested_value(context, "user.profile.role")
        assert result == "admin"

        # Test missing nested key
        result = rule_engine._get_nested_value(context, "user.profile.missing")
        assert result is None

        # Test non-dict intermediate value
        context_bad = {"user": "not_a_dict"}
        result = rule_engine._get_nested_value(context_bad, "user.profile.role")
        assert result is None

    def test_nested_condition_evaluation(self, rule_engine):
        """Test condition evaluation with nested fields"""
        context = {"user": {"role": "admin", "permissions": ["read", "write"]}}

        # Test nested field condition
        condition = {"field": "user.role", "operator": "eq", "value": ["admin"]}
        result = rule_engine._evaluate_condition(condition, context)
        assert result is True

        # Test nested field with in operator
        condition = {
            "field": "user.permissions",
            "operator": "contains",
            "value": ["read"],
        }
        result = rule_engine._evaluate_condition(condition, context)
        assert result is True


class TestRuleEngineValidation:
    """Test rule validation"""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance"""
        return RuleEngine()

    def test_validate_rule_valid(self, rule_engine):
        """Test valid rule validation"""
        rule = {
            "rule_name": "test_rule",
            "description": "test rule",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
        }
        result = rule_engine.validate_rule(rule)
        assert result["ok"]
        assert len(result["errors"]) == 0

    def test_validate_rule_missing_fields(self, rule_engine):
        """Test rule validation with missing required fields"""
        # Missing rule_name
        rule = {"description": "test", "conditions": []}
        result = rule_engine.validate_rule(rule)
        assert not result["ok"]
        assert "rule_name" in result["errors"][0]

        # Missing conditions
        rule = {"rule_name": "test", "description": "test"}
        result = rule_engine.validate_rule(rule)
        assert not result["ok"]
        assert "conditions" in result["errors"][0]

    def test_validate_rule_invalid_operator(self, rule_engine):
        """Test rule validation with invalid operator"""
        rule = {
            "rule_name": "test",
            "description": "test",
            "conditions": [{"field": "test", "operator": "invalid", "value": ["test"]}],
        }
        result = rule_engine.validate_rule(rule)
        assert not result["ok"]
        assert "invalid operator" in result["errors"][0]

    def test_validate_rule_missing_condition_fields(self, rule_engine):
        """Test rule validation with missing condition fields"""
        rule = {
            "rule_name": "test",
            "description": "test",
            "conditions": [{"field": "test"}],  # Missing operator and value
        }
        result = rule_engine.validate_rule(rule)
        assert not result["ok"]
        assert "operator" in result["errors"][0]


class TestRuleEngineCompliance:
    """Test rule compliance checking"""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance"""
        return RuleEngine()

    def test_check_compliance_no_rules(self, rule_engine):
        """Test compliance check with no rules"""
        result = rule_engine.check_compliance("test_action", {"test": "value"})
        assert result["compliant"]
        assert len(result["violated_rules"]) == 0

    def test_check_compliance_with_rules(self, rule_engine):
        """Test compliance check with rules"""
        # Add a rule
        rule = {
            "rule_name": "block_dangerous",
            "description": "Block dangerous actions",
            "conditions": [{"field": "action", "operator": "eq", "value": ["rm -rf"]}],
            "action": {"type": "block", "message": "Dangerous action blocked"},
        }
        rule_engine.add_rule(rule)

        # Test compliant action
        result = rule_engine.check_compliance("safe_action", {"action": "safe_action"})
        assert result["compliant"]
        assert len(result["violated_rules"]) == 0

        # Test non-compliant action
        result = rule_engine.check_compliance("rm -rf", {"action": "rm -rf"})
        assert not result["compliant"]
        assert len(result["violated_rules"]) == 1
        assert "block_dangerous" in result["violated_rules"]

    def test_check_compliance_multiple_rules(self, rule_engine):
        """Test compliance check with multiple rules"""
        # Add multiple rules
        rule1 = {
            "rule_name": "block_rm",
            "description": "Block rm commands",
            "conditions": [
                {"field": "action", "operator": "contains", "value": ["rm"]}
            ],
            "action": {"type": "block", "message": "rm command blocked"},
        }
        rule2 = {
            "rule_name": "block_sudo",
            "description": "Block sudo commands",
            "conditions": [
                {"field": "action", "operator": "contains", "value": ["sudo"]}
            ],
            "action": {"type": "block", "message": "sudo command blocked"},
        }

        rule_engine.add_rule(rule1)
        rule_engine.add_rule(rule2)

        # Test action that violates both rules
        result = rule_engine.check_compliance("sudo rm -rf", {"action": "sudo rm -rf"})
        assert not result["compliant"]
        assert len(result["violated_rules"]) == 2
        assert "block_rm" in result["violated_rules"]
        assert "block_sudo" in result["violated_rules"]


class TestRuleEngineManagement:
    """Test rule management operations"""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance"""
        return RuleEngine()

    def test_add_rule_success(self, rule_engine):
        """Test successful rule addition"""
        rule = {
            "rule_name": "new_rule",
            "description": "new rule",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test rule"},
        }
        result = rule_engine.add_rule(rule)
        assert result is True
        assert len(rule_engine.rules) == 1

    def test_add_rule_duplicate(self, rule_engine):
        """Test adding duplicate rule"""
        rule = {
            "rule_name": "duplicate_rule",
            "description": "duplicate rule",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
        }
        rule_engine.add_rule(rule)
        result = rule_engine.add_rule(rule)
        assert result is False

    def test_remove_rule_success(self, rule_engine):
        """Test successful rule removal"""
        rule = {
            "rule_name": "removable_rule",
            "description": "removable rule",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test rule"},
        }
        rule_engine.add_rule(rule)
        result = rule_engine.remove_rule("removable_rule")
        assert result is True
        assert len(rule_engine.rules) == 0

    def test_remove_rule_not_found(self, rule_engine):
        """Test removing non-existent rule"""
        result = rule_engine.remove_rule("non_existent_rule")
        assert result is False

    def test_get_rule_found(self, rule_engine):
        """Test getting existing rule"""
        rule = {
            "rule_name": "found_rule",
            "description": "found rule",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test rule"},
        }
        rule_engine.add_rule(rule)
        result = rule_engine.get_rule("found_rule")
        assert result is not None
        assert result["rule_name"] == "found_rule"

    def test_get_rule_not_found(self, rule_engine):
        """Test getting non-existent rule"""
        result = rule_engine.get_rule("non_existent_rule")
        assert result is None

    def test_list_rules_empty(self, rule_engine):
        """Test listing rules when empty"""
        rules = rule_engine.list_rules()
        assert rules == []

    def test_list_rules_with_rules(self, rule_engine):
        """Test listing rules with multiple rules"""
        rule1 = {
            "rule_name": "rule1",
            "description": "rule 1",
            "conditions": [{"field": "test", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test rule 1"},
        }
        rule2 = {
            "rule_name": "rule2",
            "description": "rule 2",
            "conditions": [{"field": "test", "operator": "neq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test rule 2"},
        }
        rule_engine.add_rule(rule1)
        rule_engine.add_rule(rule2)

        rules = rule_engine.list_rules()
        assert len(rules) == 2
        assert any(r["rule_name"] == "rule1" for r in rules)
        assert any(r["rule_name"] == "rule2" for r in rules)
