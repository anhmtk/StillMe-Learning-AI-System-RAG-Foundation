#!/usr/bin/env python3
"""
AgentDev Rule Engine
===================

Rule engine system for compliance checking and validation.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from agent_dev.persistence.repo import RuleRepo


@dataclass
class RuleEvalResult:
    """Result of rule evaluation"""
    
    compliant: bool
    rule_name: str
    message: str
    severity: str = "medium"
    action_type: str = "warn"
    metadata: dict[str, Any] | None = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RuleEngine:
    """Main rule engine for compliance checking"""
    
    def __init__(self, rule_repo: RuleRepo | None = None):
        self.rule_repo = rule_repo
        self.rules: list[dict[str, Any]] = []
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load rules from database"""
        if self.rule_repo:
            db_rules = self.rule_repo.get_active_rules()
            for rule in db_rules:
                try:
                    rule_def = json.loads(str(rule.rule_definition))
                    rule_def["rule_name"] = str(rule.rule_name)
                    rule_def["priority"] = int(getattr(rule, 'priority', 0))
                    rule_def["is_active"] = bool(rule.is_active)
                    self.rules.append(rule_def)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    print(f"Warning: Failed to load rule {rule.rule_name}: {e}")
    
    def add_rule(self, rule: dict[str, Any]) -> bool:
        """Add a new rule to the engine"""
        if validate_rule(rule):
            self.rules.append(rule)
            return True
        return False
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name"""
        for i, rule in enumerate(self.rules):
            if rule.get("rule_name") == rule_name:
                del self.rules[i]
                return True
        return False
    
    def get_rule(self, rule_name: str) -> dict[str, Any] | None:
        """Get a rule by name"""
        for rule in self.rules:
            if rule.get("rule_name") == rule_name:
                return rule
        return None
    
    def list_rules(self) -> list[dict[str, Any]]:
        """List all active rules"""
        return [rule for rule in self.rules if rule.get("is_active", True)]
    
    def check_compliance(self, action: str, context: dict[str, Any]) -> list[RuleEvalResult]:
        """Check compliance against all rules"""
        results: list[RuleEvalResult] = []
        
        for rule in self.rules:
            if not rule.get("is_active", True):
                continue
                
            result = self._evaluate_rule(rule, action, context)
            if result:
                results.append(result)
        
        # Sort by priority (higher priority first)
        results.sort(key=lambda r: r.metadata.get("priority", 0), reverse=True)
        return results
    
    def _evaluate_rule(self, rule: dict[str, Any], action: str, context: dict[str, Any]) -> RuleEvalResult | None:
        """Evaluate a single rule against action and context"""
        conditions = rule.get("conditions", [])
        if not conditions:
            return None
        
        # Check if all conditions are met
        all_conditions_met = True
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                all_conditions_met = False
                break
        
        if all_conditions_met:
            # Rule is violated (conditions met = violation)
            action_config = rule.get("action", {})
            return RuleEvalResult(
                compliant=False,
                rule_name=rule.get("rule_name", "unknown"),
                message=action_config.get("message", f"Rule '{rule.get('rule_name')}' violated"),
                severity=action_config.get("severity", "medium"),
                action_type=action_config.get("type", "warn"),
                metadata={
                    "priority": rule.get("priority", 0),
                    "rule_id": rule.get("rule_name"),
                    "violated_conditions": conditions,
                    "action": action,
                    "context": context
                }
            )
        
        return None
    
    def _evaluate_condition(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        field: str = condition.get("field", "")
        operator: str = condition.get("operator", "eq")
        expected_value: Any = condition.get("value")
        case_sensitive: bool = condition.get("case_sensitive", True)
        
        # Get actual value from context
        actual_value: Any = self._get_nested_value(context, field)
        
        # Handle different operators
        if operator == "eq":
            return self._compare_values(actual_value, expected_value, case_sensitive, "==")
        elif operator == "ne":
            return self._compare_values(actual_value, expected_value, case_sensitive, "!=")
        elif operator == "gt":
            return self._compare_values(actual_value, expected_value, case_sensitive, ">")
        elif operator == "gte":
            return self._compare_values(actual_value, expected_value, case_sensitive, ">=")
        elif operator == "lt":
            return self._compare_values(actual_value, expected_value, case_sensitive, "<")
        elif operator == "lte":
            return self._compare_values(actual_value, expected_value, case_sensitive, "<=")
        elif operator == "in":
            return self._check_in(actual_value, expected_value, case_sensitive)
        elif operator == "nin":
            return not self._check_in(actual_value, expected_value, case_sensitive)
        elif operator == "contains":
            return self._check_contains(actual_value, expected_value, case_sensitive)
        elif operator == "not_contains":
            return not self._check_contains(actual_value, expected_value, case_sensitive)
        elif operator == "regex":
            return self._check_regex(actual_value, expected_value, case_sensitive)
        elif operator == "exists":
            return actual_value is not None
        elif operator == "not_exists":
            return actual_value is None
        else:
            return False
    
    def _get_nested_value(self, context: dict[str, Any], field: str) -> Any:
        """Get nested value from context using dot notation"""
        keys = field.split(".")
        value: Any = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value: Any = value[key]
            else:
                return None
        
        return value
    
    def _compare_values(self, actual: Any, expected: Any, case_sensitive: bool, op: str) -> bool:
        """Compare two values using specified operator"""
        if actual is None or expected is None:
            return False
        
        # Handle string comparison
        if isinstance(actual, str) and isinstance(expected, str):
            if not case_sensitive:
                actual = actual.lower()
                expected = expected.lower()
        
        try:
            if op == "==":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == ">":
                return actual > expected
            elif op == ">=":
                return actual >= expected
            elif op == "<":
                return actual < expected
            elif op == "<=":
                return actual <= expected
        except TypeError:
            return False
        
        return False
    
    def _check_in(self, actual: Any, expected: Any, case_sensitive: bool) -> bool:
        """Check if actual value is in expected list"""
        if not isinstance(expected, list):
            return False
        
        if isinstance(actual, str) and not case_sensitive:
            expected_lower: list[str] = [str(item).lower() for item in expected if isinstance(item, str)]
            return str(actual).lower() in expected_lower
        
        return actual in expected
    
    def _check_contains(self, actual: Any, expected: Any, case_sensitive: bool) -> bool:
        """Check if actual string contains expected string"""
        if not isinstance(actual, str) or not isinstance(expected, str):
            return False
        
        if not case_sensitive:
            return expected.lower() in actual.lower()
        
        return expected in actual
    
    def _check_regex(self, actual: Any, expected: Any, case_sensitive: bool) -> bool:
        """Check if actual string matches expected regex"""
        if not isinstance(actual, str) or not isinstance(expected, str):
            return False
        
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(expected, actual, flags))
        except re.error:
            return False


def load_rules_from_db(rule_repo: RuleRepo) -> list[dict[str, Any]]:
    """Load rules from database repository"""
    rules = []
    db_rules = rule_repo.get_active_rules()
    
    for rule in db_rules:
        try:
            rule_def = json.loads(str(rule.rule_definition))
            rule_def["rule_name"] = str(rule.rule_name)
            rule_def["priority"] = int(rule.priority)
            rule_def["is_active"] = bool(rule.is_active)
            rules.append(rule_def)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Warning: Failed to load rule {rule.rule_name}: {e}")
    
    return rules


def validate_rule(rule: dict[str, Any]) -> bool:
    """Validate rule structure and content"""
    required_fields = ["rule_name", "description", "conditions", "action"]
    
    # Check required fields
    for field in required_fields:
        if field not in rule:
            return False
    
    # Validate conditions
    conditions = rule.get("conditions", [])
    if not isinstance(conditions, list) or not conditions:
        return False
    
    for condition in conditions:
        if not isinstance(condition, dict):
            return False
        
        required_condition_fields = ["field", "operator", "value"]
        for field in required_condition_fields:
            if field not in condition:
                return False
        
        # Validate operator
        valid_operators = ["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", 
                          "contains", "not_contains", "regex", "exists", "not_exists"]
        if condition.get("operator") not in valid_operators:
            return False
    
    # Validate action
    action = rule.get("action", {})
    if not isinstance(action, dict) or "type" not in action:
        return False
    
    valid_action_types = ["block", "warn", "log", "redirect", "transform"]
    if action.get("type") not in valid_action_types:
        return False
    
    return True


def check_compliance(action: str, context: dict[str, Any], 
                    rule_engine: RuleEngine | None = None) -> list[RuleEvalResult]:
    """Check compliance for an action against context"""
    if rule_engine is None:
        rule_engine = RuleEngine()
    
    return rule_engine.check_compliance(action, context)