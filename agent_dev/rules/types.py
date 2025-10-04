"""Type definitions for Rule Engine"""

from typing import Literal, TypedDict


class RuleCondition(TypedDict):
    """Type definition for rule condition"""
    field: str
    operator: Literal["eq", "neq", "gt", "lt", "in", "regex"]
    expected: list[str | int | float]
