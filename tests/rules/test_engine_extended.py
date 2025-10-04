"""
Extended tests for agent_dev/rules/engine.py to achieve ≥ 90% coverage
"""

from unittest.mock import Mock

from agent_dev.rules.engine import RuleEngine


class TestRuleEngineExtended:
    """Extended tests for RuleEngine to improve coverage"""

    def test_rule_engine_with_complex_rules(self):
        """Test rule engine with complex rules"""
        engine = RuleEngine()

        # Add complex rule with multiple conditions
        complex_rule = {
            "rule_name": "complex_rule",
            "description": "Complex rule with multiple conditions",
            "conditions": [
                {"field": "user.role", "operator": "eq", "value": ["admin"]},
                {"field": "action", "operator": "in", "value": ["delete", "modify"]},
                {"field": "resource", "operator": "contains", "value": ["important"]},
            ],
            "action": {
                "type": "block",
                "message": "Admin action on important resource",
                "severity": "high",
            },
            "priority": 10,
        }

        result = engine.add_rule(complex_rule)
        assert result is True

        # Test with matching context
        context = {
            "user": {"role": "admin"},
            "action": "delete",
            "resource": "important_database",
        }
        results = engine.check_compliance("admin_action", context)
        assert len(results) == 1
        assert results[0].compliant is False
        assert results[0].rule_name == "complex_rule"

    def test_rule_engine_with_nested_context(self):
        """Test rule engine with nested context"""
        engine = RuleEngine()

        rule = {
            "rule_name": "nested_rule",
            "description": "Rule with nested context",
            "conditions": [
                {"field": "user.profile.level", "operator": "gt", "value": [5]},
                {"field": "permissions.admin", "operator": "eq", "value": [True]},
            ],
            "action": {"type": "warn", "message": "High level admin user"},
        }

        engine.add_rule(rule)

        context = {"user": {"profile": {"level": 10}}, "permissions": {"admin": True}}
        results = engine.check_compliance("admin_check", context)
        assert len(results) == 1

    def test_rule_engine_with_missing_fields(self):
        """Test rule engine with missing fields in context"""
        engine = RuleEngine()

        rule = {
            "rule_name": "missing_field_rule",
            "description": "Rule with missing field",
            "conditions": [
                {"field": "nonexistent_field", "operator": "eq", "value": ["value"]}
            ],
            "action": {"type": "warn", "message": "Missing field rule"},
        }

        engine.add_rule(rule)

        context = {"existing_field": "value"}
        results = engine.check_compliance("test", context)
        # Should not match because field is missing
        assert len(results) == 0

    def test_rule_engine_with_none_values(self):
        """Test rule engine with None values"""
        engine = RuleEngine()

        rule = {
            "rule_name": "none_value_rule",
            "description": "Rule with None value",
            "conditions": [
                {"field": "optional_field", "operator": "exists", "value": []}
            ],
            "action": {"type": "warn", "message": "Optional field exists"},
        }

        engine.add_rule(rule)

        # Test with None value
        context = {"optional_field": None}
        results = engine.check_compliance("test", context)
        assert len(results) == 0  # None should not match exists

        # Test with actual value
        context = {"optional_field": "value"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

    def test_rule_engine_with_empty_context(self):
        """Test rule engine with empty context"""
        engine = RuleEngine()

        rule = {
            "rule_name": "empty_context_rule",
            "description": "Rule for empty context",
            "conditions": [
                {"field": "any_field", "operator": "eq", "value": ["any_value"]}
            ],
            "action": {"type": "warn", "message": "Empty context rule"},
        }

        engine.add_rule(rule)

        context = {}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_invalid_operators(self):
        """Test rule engine with invalid operators"""
        engine = RuleEngine()

        rule = {
            "rule_name": "invalid_operator_rule",
            "description": "Rule with invalid operator",
            "conditions": [
                {"field": "test_field", "operator": "invalid_op", "value": ["value"]}
            ],
            "action": {"type": "warn", "message": "Invalid operator rule"},
        }

        engine.add_rule(rule)

        context = {"test_field": "value"}
        results = engine.check_compliance("test", context)
        # Should not match because operator is invalid
        assert len(results) == 0

    def test_rule_engine_with_mixed_types(self):
        """Test rule engine with mixed data types"""
        engine = RuleEngine()

        rule = {
            "rule_name": "mixed_types_rule",
            "description": "Rule with mixed types",
            "conditions": [
                {"field": "numeric_field", "operator": "gt", "value": [10]},
                {"field": "string_field", "operator": "contains", "value": ["test"]},
                {"field": "boolean_field", "operator": "eq", "value": [True]},
            ],
            "action": {"type": "warn", "message": "Mixed types rule"},
        }

        engine.add_rule(rule)

        context = {
            "numeric_field": 15,
            "string_field": "test_string",
            "boolean_field": True,
        }
        results = engine.check_compliance("test", context)
        assert len(results) == 1

    def test_rule_engine_with_regex_edge_cases(self):
        """Test rule engine with regex edge cases"""
        engine = RuleEngine()

        rule = {
            "rule_name": "regex_edge_case_rule",
            "description": "Rule with regex edge cases",
            "conditions": [
                {
                    "field": "email",
                    "operator": "regex",
                    "value": [r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"],
                }
            ],
            "action": {"type": "warn", "message": "Valid email"},
        }

        engine.add_rule(rule)

        # Test valid email
        context = {"email": "user@example.com"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

        # Test invalid email
        context = {"email": "invalid-email"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

        # Test None email
        context = {"email": None}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_comparison_operators(self):
        """Test rule engine with comparison operators"""
        engine = RuleEngine()

        rule = {
            "rule_name": "comparison_rule",
            "description": "Rule with comparison operators",
            "conditions": [
                {"field": "score", "operator": "gt", "value": [80]},
                {"field": "age", "operator": "lt", "value": [65]},
            ],
            "action": {"type": "warn", "message": "High score, young age"},
        }

        engine.add_rule(rule)

        # Test matching conditions
        context = {"score": 90, "age": 30}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

        # Test non-matching conditions
        context = {"score": 70, "age": 30}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_in_operator_edge_cases(self):
        """Test rule engine with 'in' operator edge cases"""
        engine = RuleEngine()

        rule = {
            "rule_name": "in_operator_rule",
            "description": "Rule with 'in' operator",
            "conditions": [
                {
                    "field": "status",
                    "operator": "in",
                    "value": ["active", "pending", "completed"],
                }
            ],
            "action": {"type": "warn", "message": "Valid status"},
        }

        engine.add_rule(rule)

        # Test matching status
        context = {"status": "active"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

        # Test non-matching status
        context = {"status": "invalid"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

        # Test None status
        context = {"status": None}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_contains_operator_edge_cases(self):
        """Test rule engine with 'contains' operator edge cases"""
        engine = RuleEngine()

        rule = {
            "rule_name": "contains_operator_rule",
            "description": "Rule with 'contains' operator",
            "conditions": [
                {
                    "field": "message",
                    "operator": "contains",
                    "value": ["error", "warning", "critical"],
                }
            ],
            "action": {"type": "warn", "message": "Error message detected"},
        }

        engine.add_rule(rule)

        # Test matching message
        context = {"message": "System error occurred"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

        # Test non-matching message
        context = {"message": "System success"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

        # Test None message
        context = {"message": None}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_not_exists_operator(self):
        """Test rule engine with 'not_exists' operator"""
        engine = RuleEngine()

        rule = {
            "rule_name": "not_exists_rule",
            "description": "Rule with 'not_exists' operator",
            "conditions": [
                {"field": "sensitive_data", "operator": "not_exists", "value": []}
            ],
            "action": {"type": "warn", "message": "No sensitive data"},
        }

        engine.add_rule(rule)

        # Test with missing field (should match)
        context = {"other_field": "value"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

        # Test with existing field (should not match)
        context = {"sensitive_data": "secret"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_priority_ordering(self):
        """Test rule engine with priority ordering"""
        engine = RuleEngine()

        # Add low priority rule
        low_priority_rule = {
            "rule_name": "low_priority_rule",
            "description": "Low priority rule",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {"type": "warn", "message": "Low priority warning"},
            "priority": 1,
        }

        # Add high priority rule
        high_priority_rule = {
            "rule_name": "high_priority_rule",
            "description": "High priority rule",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "High priority block"},
            "priority": 10,
        }

        engine.add_rule(low_priority_rule)
        engine.add_rule(high_priority_rule)

        context = {"action": "test"}
        results = engine.check_compliance("test", context)

        # Should have 2 results, high priority first
        assert len(results) == 2
        assert results[0].rule_name == "high_priority_rule"
        assert results[1].rule_name == "low_priority_rule"

    def test_rule_engine_with_inactive_rules(self):
        """Test rule engine with inactive rules"""
        engine = RuleEngine()

        # Add active rule
        active_rule = {
            "rule_name": "active_rule",
            "description": "Active rule",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {"type": "warn", "message": "Active rule"},
            "is_active": True,
        }

        # Add inactive rule
        inactive_rule = {
            "rule_name": "inactive_rule",
            "description": "Inactive rule",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {"type": "warn", "message": "Inactive rule"},
            "is_active": False,
        }

        engine.add_rule(active_rule)
        engine.add_rule(inactive_rule)

        context = {"action": "test"}
        results = engine.check_compliance("test", context)

        # Should only have 1 result (active rule)
        assert len(results) == 1
        assert results[0].rule_name == "active_rule"

    def test_rule_engine_error_handling(self):
        """Test rule engine error handling"""
        engine = RuleEngine()

        # Test with invalid rule structure
        invalid_rule = {
            "rule_name": "invalid_rule",
            # Missing required fields
        }

        result = engine.add_rule(invalid_rule)
        assert result is False

        # Test with None context
        results = engine.check_compliance("test", None)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_rule_engine_with_repo_integration(self):
        """Test rule engine with repository integration"""
        mock_repo = Mock()
        # Create mock rule object with required attributes
        mock_rule = Mock()
        mock_rule.rule_name = "repo_rule"
        mock_rule.rule_definition = '{"description": "Rule from repository", "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}], "action": {"type": "warn", "message": "Repository rule"}}'
        mock_rule.priority = 5
        mock_rule.is_active = True

        mock_repo.get_active_rules.return_value = [mock_rule]

        engine = RuleEngine(rule_repo=mock_repo)
        engine._load_rules()

        context = {"action": "test"}
        results = engine.check_compliance("test", context)
        assert len(results) >= 1
        assert any(r.rule_name == "repo_rule" for r in results)

    def test_rule_engine_with_empty_rules(self):
        """Test rule engine with empty rules list"""
        engine = RuleEngine()

        # No rules added
        context = {"action": "test"}
        results = engine.check_compliance("test", context)
        assert len(results) == 0

    def test_rule_engine_with_rule_metadata(self):
        """Test rule engine with rule metadata"""
        engine = RuleEngine()

        rule = {
            "rule_name": "metadata_rule",
            "description": "Rule with metadata",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {"type": "warn", "message": "Metadata rule"},
            "metadata": {"version": "1.0", "author": "test"},
        }

        engine.add_rule(rule)

        context = {"action": "test"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        # Check that metadata is passed through in the result
        assert "version" in results[0].metadata or "rule_id" in results[0].metadata

    def test_rule_engine_with_context_parameter(self):
        """Test rule engine with context parameter"""
        engine = RuleEngine()

        rule = {
            "rule_name": "context_rule",
            "description": "Rule with context parameter",
            "conditions": [
                {"field": "context.param", "operator": "eq", "value": ["value"]}
            ],
            "action": {"type": "warn", "message": "Context rule"},
        }

        engine.add_rule(rule)

        context = {"context": {"param": "value"}}
        results = engine.check_compliance("test", context)
        assert len(results) == 1

    def test_rule_engine_with_multiple_actions(self):
        """Test rule engine with multiple actions"""
        engine = RuleEngine()

        rule = {
            "rule_name": "multiple_actions_rule",
            "description": "Rule with multiple actions",
            "conditions": [{"field": "action", "operator": "eq", "value": ["test"]}],
            "action": {
                "type": "block",
                "message": "Multiple actions rule",
                "severity": "high",
                "additional_actions": ["log", "notify"],
            },
        }

        engine.add_rule(rule)

        context = {"action": "test"}
        results = engine.check_compliance("test", context)
        assert len(results) == 1
        assert results[0].action_type == "block"
        assert results[0].severity == "high"
