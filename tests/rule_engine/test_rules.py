#!/usr/bin/env python3
"""
AgentDev Rule Engine Tests
==========================

Test cases for the Rule Engine system.
"""

import pytest
from unittest.mock import Mock

from agent_dev.rules.engine import (
    RuleEngine,
    RuleEvalResult,
    load_rules_from_db,
    validate_rule,
    check_compliance,
)


class TestRuleEngine:
    """Test RuleEngine class"""
    
    def test_rule_engine_init(self):
        """Test rule engine initialization"""
        engine = RuleEngine()
        assert engine.rules == []
        assert engine.rule_repo is None
    
    def test_rule_engine_with_repo(self):
        """Test rule engine with repository"""
        mock_repo = Mock()
        mock_repo.get_active_rules.return_value = []
        engine = RuleEngine(rule_repo=mock_repo)
        assert engine.rule_repo == mock_repo
    
    def test_add_valid_rule(self):
        """Test adding a valid rule"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"}
            ],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        result = engine.add_rule(rule)
        assert result is True
        assert len(engine.rules) == 1
        assert engine.rules[0]["rule_name"] == "test_rule"
    
    def test_add_invalid_rule(self):
        """Test adding an invalid rule"""
        engine = RuleEngine()
        invalid_rule = {
            "rule_name": "test_rule",
            # Missing required fields
        }
        
        result = engine.add_rule(invalid_rule)
        assert result is False
        assert len(engine.rules) == 0
    
    def test_remove_rule(self):
        """Test removing a rule"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        engine.add_rule(rule)
        assert len(engine.rules) == 1
        
        result = engine.remove_rule("test_rule")
        assert result is True
        assert len(engine.rules) == 0
    
    def test_remove_nonexistent_rule(self):
        """Test removing a non-existent rule"""
        engine = RuleEngine()
        result = engine.remove_rule("nonexistent")
        assert result is False
    
    def test_get_rule(self):
        """Test getting a rule by name"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        engine.add_rule(rule)
        retrieved_rule = engine.get_rule("test_rule")
        assert retrieved_rule is not None
        assert retrieved_rule["rule_name"] == "test_rule"
    
    def test_get_nonexistent_rule(self):
        """Test getting a non-existent rule"""
        engine = RuleEngine()
        rule = engine.get_rule("nonexistent")
        assert rule is None
    
    def test_list_rules(self):
        """Test listing active rules"""
        engine = RuleEngine()
        
        # Add active rule
        active_rule = {
            "rule_name": "active_rule",
            "description": "Active rule",
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Active warning"},
            "is_active": True
        }
        
        # Add inactive rule
        inactive_rule = {
            "rule_name": "inactive_rule",
            "description": "Inactive rule",
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Inactive warning"},
            "is_active": False
        }
        
        engine.add_rule(active_rule)
        engine.add_rule(inactive_rule)
        
        active_rules = engine.list_rules()
        assert len(active_rules) == 1
        assert active_rules[0]["rule_name"] == "active_rule"


class TestRuleEvaluation:
    """Test rule evaluation logic"""
    
    def test_compliant_action(self):
        """Test compliant action (no rule violations)"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"}
            ],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        engine.add_rule(rule)
        
        # Action that doesn't match rule conditions
        context = {"task": "fix", "tested": True}
        results = engine.check_compliance("fix_bug", context)
        
        assert len(results) == 0  # No violations
    
    def test_non_compliant_action(self):
        """Test non-compliant action (rule violation)"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"}
            ],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        engine.add_rule(rule)
        
        # Action that matches rule conditions
        context = {"task": "claim", "tested": False}
        results = engine.check_compliance("claim_task", context)
        
        assert len(results) == 1
        assert results[0].compliant is False
        assert results[0].rule_name == "test_rule"
        assert "Test warning" in results[0].message
    
    def test_test_before_claim_rule(self):
        """Test 'test_before_claim' rule: if task='claim' and tested=False => non-compliant"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_before_claim",
            "description": "Must test before claiming",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"},
                {"field": "tested", "operator": "eq", "value": False}
            ],
            "action": {
                "type": "block",
                "message": "Must test before claiming task",
                "severity": "high"
            }
        }
        
        engine.add_rule(rule)
        
        # Non-compliant: claim without testing
        context = {"task": "claim", "tested": False}
        results = engine.check_compliance("claim_task", context)
        
        assert len(results) == 1
        assert results[0].compliant is False
        assert results[0].rule_name == "test_before_claim"
        assert results[0].action_type == "block"
        assert results[0].severity == "high"
        
        # Compliant: claim after testing
        context = {"task": "claim", "tested": True}
        results = engine.check_compliance("claim_task", context)
        
        assert len(results) == 0  # No violations
    
    def test_forbid_dangerous_shell_rule(self):
        """Test 'forbid_dangerous_shell' rule: if context['cmd'] contains 'rm -rf' => block"""
        engine = RuleEngine()
        rule = {
            "rule_name": "forbid_dangerous_shell",
            "description": "Block dangerous shell commands",
            "conditions": [
                {"field": "cmd", "operator": "contains", "value": "rm -rf"}
            ],
            "action": {
                "type": "block",
                "message": "Dangerous shell command detected",
                "severity": "critical"
            }
        }
        
        engine.add_rule(rule)
        
        # Non-compliant: dangerous command
        context = {"cmd": "rm -rf /tmp/*", "user": "admin"}
        results = engine.check_compliance("execute_shell", context)
        
        assert len(results) == 1
        assert results[0].compliant is False
        assert results[0].rule_name == "forbid_dangerous_shell"
        assert results[0].action_type == "block"
        assert results[0].severity == "critical"
        
        # Compliant: safe command
        context = {"cmd": "ls -la", "user": "admin"}
        results = engine.check_compliance("execute_shell", context)
        
        assert len(results) == 0  # No violations
    
    def test_multiple_conditions(self):
        """Test rule with multiple conditions (AND logic)"""
        engine = RuleEngine()
        rule = {
            "rule_name": "complex_rule",
            "description": "Complex rule with multiple conditions",
            "conditions": [
                {"field": "user.role", "operator": "eq", "value": "admin"},
                {"field": "action", "operator": "eq", "value": "delete"},
                {"field": "resource", "operator": "contains", "value": "important"}
            ],
            "action": {
                "type": "warn",
                "message": "Admin deleting important resource",
                "severity": "high"
            }
        }
        
        engine.add_rule(rule)
        
        # Non-compliant: all conditions met
        context = {
            "user": {"role": "admin"},
            "action": "delete",
            "resource": "important_database"
        }
        results = engine.check_compliance("delete_resource", context)
        
        assert len(results) == 1
        assert results[0].rule_name == "complex_rule"
        
        # Compliant: one condition not met
        context = {
            "user": {"role": "user"},
            "action": "delete",
            "resource": "important_database"
        }
        results = engine.check_compliance("delete_resource", context)
        
        assert len(results) == 0  # No violations
    
    def test_priority_ordering(self):
        """Test that results are ordered by priority"""
        engine = RuleEngine()
        
        # Low priority rule
        low_priority_rule = {
            "rule_name": "low_priority",
            "description": "Low priority rule",
            "priority": 1,
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Low priority warning"}
        }
        
        # High priority rule
        high_priority_rule = {
            "rule_name": "high_priority",
            "description": "High priority rule",
            "priority": 10,
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "block", "message": "High priority block"}
        }
        
        engine.add_rule(low_priority_rule)
        engine.add_rule(high_priority_rule)
        
        context = {"task": "claim"}
        results = engine.check_compliance("claim_task", context)
        
        assert len(results) == 2
        # High priority should come first
        assert results[0].rule_name == "high_priority"
        assert results[1].rule_name == "low_priority"


class TestRuleOperators:
    """Test different rule operators"""
    
    def test_equality_operators(self):
        """Test equality operators (eq, ne)"""
        engine = RuleEngine()
        
        # Test eq operator
        rule = {
            "rule_name": "eq_rule",
            "description": "Equality rule",
            "conditions": [{"field": "status", "operator": "eq", "value": "active"}],
            "action": {"type": "warn", "message": "Status is active"}
        }
        engine.add_rule(rule)
        
        context = {"status": "active"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {"status": "inactive"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0
    
    def test_comparison_operators(self):
        """Test comparison operators (gt, gte, lt, lte)"""
        engine = RuleEngine()
        
        rule = {
            "rule_name": "gt_rule",
            "description": "Greater than rule",
            "conditions": [{"field": "score", "operator": "gt", "value": 80}],
            "action": {"type": "warn", "message": "High score"}
        }
        engine.add_rule(rule)
        
        context = {"score": 90}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {"score": 70}
        results = engine.check_compliance("test", context)
        assert len(results) == 0
    
    def test_in_operator(self):
        """Test 'in' operator"""
        engine = RuleEngine()
        
        rule = {
            "rule_name": "in_rule",
            "description": "In rule",
            "conditions": [{"field": "role", "operator": "in", "value": ["admin", "moderator"]}],
            "action": {"type": "warn", "message": "Privileged role"}
        }
        engine.add_rule(rule)
        
        context = {"role": "admin"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {"role": "user"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0
    
    def test_contains_operator(self):
        """Test 'contains' operator"""
        engine = RuleEngine()
        
        rule = {
            "rule_name": "contains_rule",
            "description": "Contains rule",
            "conditions": [{"field": "message", "operator": "contains", "value": "error"}],
            "action": {"type": "warn", "message": "Error message detected"}
        }
        engine.add_rule(rule)
        
        context = {"message": "System error occurred"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {"message": "System success"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0
    
    def test_regex_operator(self):
        """Test 'regex' operator"""
        engine = RuleEngine()
        
        rule = {
            "rule_name": "regex_rule",
            "description": "Regex rule",
            "conditions": [{"field": "email", "operator": "regex", "value": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}],
            "action": {"type": "warn", "message": "Valid email format"}
        }
        engine.add_rule(rule)
        
        context = {"email": "user@example.com"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {"email": "invalid-email"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0
    
    def test_exists_operator(self):
        """Test 'exists' and 'not_exists' operators"""
        engine = RuleEngine()
        
        rule = {
            "rule_name": "exists_rule",
            "description": "Exists rule",
            "conditions": [{"field": "token", "operator": "exists", "value": None}],
            "action": {"type": "warn", "message": "Token exists"}
        }
        engine.add_rule(rule)
        
        context = {"token": "abc123"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        
        context = {}
        results = engine.check_compliance("test", context)
        assert len(results) == 0


class TestRuleValidation:
    """Test rule validation functions"""
    
    def test_validate_valid_rule(self):
        """Test validation of valid rule"""
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"}
            ],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        result = validate_rule(rule)
        assert result is True
    
    def test_validate_invalid_rule_missing_fields(self):
        """Test validation of rule missing required fields"""
        rule = {
            "rule_name": "test_rule",
            # Missing description, conditions, action
        }
        
        result = validate_rule(rule)
        assert result is False
    
    def test_validate_invalid_rule_bad_operator(self):
        """Test validation of rule with invalid operator"""
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "invalid_op", "value": "claim"}
            ],
            "action": {"type": "warn", "message": "Test warning"}
        }
        
        result = validate_rule(rule)
        assert result is False
    
    def test_validate_invalid_rule_bad_action_type(self):
        """Test validation of rule with invalid action type"""
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [
                {"field": "task", "operator": "eq", "value": "claim"}
            ],
            "action": {"type": "invalid_action", "message": "Test warning"}
        }
        
        result = validate_rule(rule)
        assert result is False


class TestStandaloneFunctions:
    """Test standalone functions"""
    
    def test_check_compliance_standalone(self):
        """Test check_compliance standalone function"""
        context = {"task": "claim", "tested": False}
        results = check_compliance("claim_task", context)
        
        # Should return empty list since no rules are loaded
        assert isinstance(results, list)
    
    def test_check_compliance_with_engine(self):
        """Test check_compliance with custom engine"""
        engine = RuleEngine()
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [{"field": "task", "operator": "eq", "value": "claim"}],
            "action": {"type": "warn", "message": "Test warning"}
        }
        engine.add_rule(rule)
        
        context = {"task": "claim"}
        results = check_compliance("claim_task", context, engine)
        
        assert len(results) == 1
        assert results[0].rule_name == "test_rule"


class TestIntegration:
    """Integration tests"""
    
    def test_full_rule_workflow(self):
        """Test complete rule workflow"""
        engine = RuleEngine()
        
        # Add multiple rules
        rules = [
            {
                "rule_name": "test_before_claim",
                "description": "Must test before claiming",
                "priority": 10,
                "conditions": [
                    {"field": "task", "operator": "eq", "value": "claim"},
                    {"field": "tested", "operator": "eq", "value": False}
                ],
                "action": {
                    "type": "block",
                    "message": "Must test before claiming task",
                    "severity": "high"
                }
            },
            {
                "rule_name": "forbid_dangerous_shell",
                "description": "Block dangerous shell commands",
                "priority": 5,
                "conditions": [
                    {"field": "cmd", "operator": "contains", "value": "rm -rf"}
                ],
                "action": {
                    "type": "block",
                    "message": "Dangerous shell command detected",
                    "severity": "critical"
                }
            }
        ]
        
        for rule in rules:
            engine.add_rule(rule)
        
        # Test claim without testing (should be blocked)
        context = {"task": "claim", "tested": False}
        results = engine.check_compliance("claim_task", context)
        
        assert len(results) == 1
        assert results[0].rule_name == "test_before_claim"
        assert results[0].action_type == "block"
        
        # Test dangerous command (should be blocked)
        context = {"cmd": "rm -rf /tmp/*"}
        results = engine.check_compliance("execute_shell", context)
        
        assert len(results) == 1
        assert results[0].rule_name == "forbid_dangerous_shell"
        assert results[0].action_type == "block"
        
        # Test safe action (should pass)
        context = {"task": "fix", "tested": True}
        results = engine.check_compliance("fix_bug", context)
        
        assert len(results) == 0  # No violations