#!/usr/bin/env python3
"""
Script to fix test_engine_extended.py to expect ComplianceResult instead of list
"""

import re


def fix_rule_engine_tests():
    """Fix all test assertions to expect ComplianceResult format"""

    with open("tests/rules/test_engine_extended.py", encoding="utf-8") as f:
        content = f.read()

    # Fix patterns where tests expect list format but get ComplianceResult
    patterns = [
        # Pattern 1: assert len(results) == 1
        (r"assert len\(results\) == 1", 'assert results["compliant"] is False'),
        # Pattern 2: assert len(results) == 0
        (r"assert len\(results\) == 0", 'assert results["compliant"] is True'),
        # Pattern 3: assert len(results) == 2
        (r"assert len\(results\) == 2", 'assert len(results["violated_rules"]) == 2'),
        # Pattern 4: results[0].compliant
        (r"results\[0\]\.compliant", 'results["compliant"]'),
        # Pattern 5: results[0].rule_name
        (r"results\[0\]\.rule_name", 'results["violated_rules"][0]'),
        # Pattern 6: any(r.rule_name for r in results)
        (
            r'any\(r\.rule_name == "([^"]+)" for r in results\)',
            r'"\1" in results["violated_rules"]',
        ),
        # Pattern 7: isinstance(results, list)
        (r"assert isinstance\(results, list\)", "assert isinstance(results, dict)"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Special cases that need more specific handling
    content = content.replace(
        'assert results[0].rule_name == "high_priority_rule"',
        'assert "high_priority_rule" in results["violated_rules"]',
    )

    content = content.replace(
        'assert any(r.rule_name == "repo_rule" for r in results)',
        'assert "repo_rule" in results["violated_rules"]',
    )

    with open("tests/rules/test_engine_extended.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Fixed test_engine_extended.py to expect ComplianceResult format")


if __name__ == "__main__":
    fix_rule_engine_tests()
