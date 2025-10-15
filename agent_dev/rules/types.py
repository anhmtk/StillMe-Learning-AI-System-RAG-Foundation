"""Type definitions for Rule Engine"""

from typing import Any, Literal, TypedDict

ExpectedValue = list[str | int | float]
OperatorType = Literal[
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
]


class RuleCondition(TypedDict):
    """Type definition for rule condition"""

    field: str
    operator: OperatorType
    value: ExpectedValue


class RuleSpec(TypedDict):
    """Type definition for rule specification"""

    rule_name: str
    description: str
    conditions: list[RuleCondition]
    action: dict[str, Any]
    priority: int
    is_active: bool


class ValidationResult(TypedDict):
    """Type definition for validation result"""

    ok: bool
    errors: list[str]


class ComplianceResult(TypedDict):
    """Type definition for compliance result"""

    compliant: bool
    violated_rules: list[str]
