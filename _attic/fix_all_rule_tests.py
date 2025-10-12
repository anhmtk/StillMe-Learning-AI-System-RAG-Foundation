#!/usr/bin/env python3
"""
Script to fix all rule engine tests to handle action parameter correctly
"""

import re


def fix_all_rule_tests():
    """Fix all test contexts to remove action field and update rule conditions"""

    with open("tests/rules/test_engine_extended.py", encoding="utf-8") as f:
        content = f.read()

    # Remove "action" from context dictionaries
    content = re.sub(
        r'context = \{[^}]*"action": "[^"]*",?\s*([^}]*)\}',
        r"context = {\1}",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Fix specific action values in rule conditions
    replacements = [
        ('"action": "delete"', '"action": "admin_action"'),
        ('"action": "test"', '"action": "test_action"'),
        ('"action": "claim"', '"action": "claim_action"'),
        ('"action": "modify"', '"action": "modify_action"'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    # Fix rule conditions that check for specific action values
    content = re.sub(
        r'"value": \["delete", "modify"\]',
        r'"value": ["admin_action", "modify_action"]',
        content,
    )

    content = re.sub(r'"value": \["test"\]', r'"value": ["test_action"]', content)

    content = re.sub(r'"value": \["claim"\]', r'"value": ["claim_action"]', content)

    with open("tests/rules/test_engine_extended.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Fixed all rule engine tests to handle action parameter correctly")


if __name__ == "__main__":
    fix_all_rule_tests()
