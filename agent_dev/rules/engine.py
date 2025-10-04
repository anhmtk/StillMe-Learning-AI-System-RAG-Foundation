#!/usr/bin/env python3
"""
AgentDev Rule Engine
===================

Rule engine system for compliance checking and validation.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from agent_dev.persistence.repo import (
    RuleRepo,  # Giả sử RuleRepo cung cấp kiểu dữ liệu cho rule objects
)
from agent_dev.rules.types import ComplianceResult, ValidationResult


@dataclass
class RuleEvalResult:
    """Result of rule evaluation"""

    compliant: bool
    rule_name: str
    message: str
    severity: str = "medium"
    action_type: str = "warn"
    # THAY ĐỔI: Sử dụng field(default_factory=dict) để khởi tạo Dict an toàn
    metadata: dict[str, Any] = field(default_factory=lambda: {})

    # THAY ĐỔI: Xóa __post_init__ vì default_factory đã xử lý


class RuleEngine:
    """Main rule engine for compliance checking"""

    def __init__(self, rule_repo: RuleRepo | None = None):
        # THAY ĐỔI: Sử dụng Optional/Union
        self.rule_repo: RuleRepo | None = rule_repo
        self.rules: list[dict[str, Any]] = []  # THAY ĐỔI: Sử dụng List[Dict]
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from database"""
        if self.rule_repo:
            db_rules = self.rule_repo.get_active_rules()
            for rule in db_rules:
                try:
                    # THAY ĐỔI: Kiểm tra kiểu dữ liệu trả về từ repo trước khi json.loads
                    rule_definition_str: str = str(
                        getattr(rule, "rule_definition", "{}")
                    )
                    rule_def: dict[str, Any] = json.loads(rule_definition_str)

                    # Cải thiện việc đọc các thuộc tính từ object `rule`
                    rule_def["rule_name"] = str(
                        getattr(rule, "rule_name", "unknown_rule")
                    )
                    # THAY ĐỔI: Sử dụng getattr() an toàn hơn và ép kiểu rõ ràng
                    priority_value: Any = getattr(rule, "priority", 0)
                    rule_def["priority"] = int(priority_value)

                    rule_def["is_active"] = bool(getattr(rule, "is_active", False))
                    self.rules.append(rule_def)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    print(
                        f"Warning: Failed to load rule {getattr(rule, 'rule_name', 'unknown')}: {e}"
                    )

    def add_rule(self, rule: dict[str, Any]) -> bool:
        """Add a new rule to the engine"""
        # Giữ nguyên: validate_rule là hàm bên ngoài
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

    def validate_rule(self, spec: dict[str, Any]) -> ValidationResult:
        """Validate a rule specification"""
        errors: list[str] = []

        # Check required fields
        if "rule_name" not in spec:
            errors.append("Missing required field: rule_name")
        if "conditions" not in spec:
            errors.append("Missing required field: conditions")
        elif not isinstance(spec["conditions"], list):
            errors.append("conditions must be a list")
        else:
            # Validate each condition
            conditions: list[dict[str, Any]] = spec["conditions"]  # type: ignore[assignment]
            for i, condition in enumerate(conditions):
                if not isinstance(condition, dict):  # type: ignore[unnecessary-isinstance]
                    errors.append(f"Condition {i} must be a dictionary")
                    continue

                # Check required condition fields
                if "field" not in condition:
                    errors.append(f"Condition {i} missing field")
                if "operator" not in condition:
                    errors.append(f"Condition {i} missing operator")
                elif condition["operator"] not in [
                    "eq",
                    "ne",
                    "gt",
                    "lt",
                    "in",
                    "regex",
                    "contains",
                    "not_contains",
                    "exists",
                    "not_exists",
                ]:
                    errors.append(
                        f"Condition {i} has invalid operator: {condition['operator']}"
                    )
                if "value" not in condition:
                    errors.append(f"Condition {i} missing value")
                elif not isinstance(condition["value"], list):
                    errors.append(f"Condition {i} value must be a list")

        return ValidationResult(ok=len(errors) == 0, errors=errors)

    def check_compliance(
        self, action: str, context: dict[str, Any]
    ) -> ComplianceResult:
        """Check compliance against all rules"""
        violated_rules: list[str] = []

        for rule in self.rules:
            if not rule.get("is_active", True):
                continue

            result = self._evaluate_rule(rule, action, context)
            if result and not result.compliant:
                violated_rules.append(result.rule_name)

        return ComplianceResult(
            compliant=len(violated_rules) == 0, violated_rules=violated_rules
        )

    def _evaluate_rule(
        self, rule: dict[str, Any], action: str, context: dict[str, Any]
    ) -> RuleEvalResult | None:
        """Evaluate a single rule against action and context"""
        # THAY ĐỔI: Khai báo rõ ràng kiểu trả về của .get()
        conditions: list[dict[str, Any]] = rule.get("conditions", [])
        if not conditions:
            return None

        # Check if all conditions are met
        all_conditions_met = True
        # THAY ĐỔI: Khai báo rõ ràng kiểu dữ liệu cho 'condition' trong vòng lặp
        for condition in conditions:
            # Bỏ qua nếu condition không phải dict
            if not self._evaluate_condition(condition, context):
                all_conditions_met = False
                break

        if all_conditions_met:
            # Rule is violated (conditions met = violation)
            action_config: dict[str, Any] = rule.get("action", {})
            return RuleEvalResult(
                compliant=False,
                rule_name=rule.get("rule_name", "unknown"),
                message=action_config.get(
                    "message", f"Rule '{rule.get('rule_name')}' violated"
                ),
                severity=action_config.get("severity", "medium"),
                action_type=action_config.get("type", "warn"),
                metadata={
                    "priority": rule.get("priority", 0),
                    "rule_id": rule.get("rule_name"),
                    "violated_conditions": conditions,
                    "action": action,
                    "context": context,
                },
            )

        return None

    def _evaluate_condition(
        self, condition: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition"""
        field: str = condition["field"]
        operator: str = condition["operator"]
        expected: list[str | int | float] = condition["value"]

        # Get actual value from context
        actual_value: Any = self._get_nested_value(context, field)

        # Handle different operators
        if operator == "eq":
            return self._compare_values(actual_value, operator, expected)
        elif operator == "neq":
            return self._compare_values(actual_value, operator, expected)
        elif operator == "gt":
            return self._compare_values(actual_value, operator, expected)
        elif operator == "lt":
            return self._compare_values(actual_value, operator, expected)
        elif operator == "in":
            return self._check_in(actual_value, expected)
        elif operator == "regex":
            return self._check_regex(actual_value, expected)
        elif operator == "contains":
            return self._check_contains(actual_value, expected)
        elif operator == "not_contains":
            return not self._check_contains(actual_value, expected)
        elif operator == "exists":
            return actual_value is not None
        elif operator == "not_exists":
            return actual_value is None
        else:
            return False

    def _get_nested_value(self, context: dict[str, Any], field: str) -> Any:
        """Get nested value from context using dot notation"""
        keys: list[str] = field.split(".")
        # THAY ĐỔI: Khai báo rõ ràng kiểu dữ liệu và không dùng lại Any ở lần gán sau
        current_value: Any = context  # type: ignore[assignment]

        for key in keys:
            # THAY ĐỔI: Kiểm tra an toàn trước khi truy cập key
            if isinstance(current_value, dict) and key in current_value:
                current_value = current_value[key]  # type: ignore[assignment]
            else:
                return None

        return current_value  # type: ignore[return-value]

    def _compare_values(
        self, actual: Any, operator: str, expected: list[str | int | float]
    ) -> bool:
        """Compare values using specified operator"""
        if actual is None:
            return False

        if operator == "eq":
            return any(str(actual) == str(item) for item in expected)
        elif operator == "neq":
            return any(str(actual) != str(item) for item in expected)
        elif operator == "gt":
            return all(
                float(actual) > float(item)
                for item in expected
                if isinstance(item, int | float) and isinstance(actual, int | float)
            )
        elif operator == "lt":
            return all(
                float(actual) < float(item)
                for item in expected
                if isinstance(item, int | float) and isinstance(actual, int | float)
            )
        else:
            return False

    def _check_in(self, actual: Any, expected: list[str | int | float]) -> bool:
        """Check if actual value is in expected list"""
        if actual is None:
            return False

        return str(actual) in [str(item) for item in expected]

    def _check_contains(self, actual: Any, expected: list[str | int | float]) -> bool:
        """Check if actual string contains expected string"""
        if isinstance(actual, str):
            return any(
                str(item) in actual for item in expected if isinstance(item, str)
            )
        elif isinstance(actual, list):
            return any(
                str(item) in actual for item in expected if isinstance(item, str)
            )
        else:
            return False

    def _check_regex(self, actual: Any, expected: list[str | int | float]) -> bool:
        """Check if actual string matches expected regex"""
        if not isinstance(actual, str):
            return False

        try:
            return any(
                re.search(str(item), actual)
                for item in expected
                if isinstance(item, str)
            )
        except re.error:
            return False


# --- CÁC HÀM BÊN NGOÀI ---


# THAY ĐỔI: Hàm này hiện KHÔNG được sử dụng trong RuleEngine._load_rules, nhưng được sửa lỗi priority
def load_rules_from_db(rule_repo: RuleRepo) -> list[dict[str, Any]]:
    """Load rules from database repository"""
    rules: list[dict[str, Any]] = []
    db_rules = rule_repo.get_active_rules()

    for rule in db_rules:
        try:
            # Sửa lỗi: Sử dụng getattr an toàn hơn
            rule_definition_str: str = str(getattr(rule, "rule_definition", "{}"))
            rule_def: dict[str, Any] = json.loads(rule_definition_str)

            rule_def["rule_name"] = str(getattr(rule, "rule_name", "unknown_rule"))

            # SỬA LỖI: Dùng getattr và ép kiểu an toàn
            priority_value: Any = getattr(rule, "priority", 0)
            rule_def["priority"] = int(priority_value)

            rule_def["is_active"] = bool(getattr(rule, "is_active", False))
            rules.append(rule_def)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(
                f"Warning: Failed to load rule {getattr(rule, 'rule_name', 'unknown')}: {e}"
            )

    return rules


def validate_rule(rule: dict[str, Any]) -> bool:
    """Validate rule structure and content"""
    # THAY ĐỔI: Khai báo rõ ràng kiểu dữ liệu
    required_fields: list[str] = ["rule_name", "description", "conditions", "action"]

    # Check required fields
    for field_name in required_fields:
        if field_name not in rule:
            return False

    # Validate conditions
    conditions: list[dict[str, Any]] = rule.get("conditions", [])
    if not conditions:
        return False

    for condition in conditions:
        required_condition_fields: list[str] = ["field", "operator", "value"]
        for field_name in required_condition_fields:
            if field_name not in condition:
                return False

        # Validate operator
        valid_operators: list[str] = [
            "eq",
            "neq",
            "gt",
            "gte",
            "lt",
            "lte",
            "in",
            "nin",
            "contains",
            "not_contains",
            "regex",
            "exists",
            "not_exists",
        ]
        # Get operator from condition with safe type handling
        operator: str | None = None
        if "operator" in condition:
            operator_value = condition["operator"]
            if isinstance(operator_value, str):
                operator = operator_value
            elif isinstance(operator_value, int | float):
                operator = str(operator_value)
            else:
                # Safe string conversion for unknown types
                try:
                    operator = str(operator_value)
                except (TypeError, ValueError):
                    pass

        if operator is None or operator not in valid_operators:
            return False

    # Validate action
    action: dict[str, Any] = rule.get("action", {})
    if "type" not in action:
        return False

    valid_action_types: list[str] = ["block", "warn", "log", "redirect", "transform"]
    if action.get("type") not in valid_action_types:
        return False

    return True


def check_compliance(
    action: str, context: dict[str, Any], rule_engine: RuleEngine | None = None
) -> ComplianceResult:
    """Check compliance for an action against context"""
    if rule_engine is None:
        rule_engine = RuleEngine()

    return rule_engine.check_compliance(action, context)
