#!/usr/bin/env python3
"""
Fix indentation errors in test files
"""

import os
import re


def fix_indentation_errors():
    """Fix all indentation errors in test files"""

    # Find all test files
    test_files = []
    for root, _dirs, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"Checking {test_file}")
            fix_file(test_file)


def fix_file(file_path):
    """Fix a single test file"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Fix indentation errors - lines that start with spaces followed by variable names
        content = re.sub(
            r"^(\s+)([A-Za-z_][A-Za-z0-9_]*),\s*$",
            r"\1\2 = MagicMock",
            content,
            flags=re.MULTILINE,
        )

        # Fix multiple variable assignments on same line
        content = re.sub(
            r"^(\s+)([A-Za-z_][A-Za-z0-9_]*),\s*\n\s*([A-Za-z_][A-Za-z0-9_]*),\s*\n\s*=\s*MagicMock",
            r"\1\2 = MagicMock\n\1\3 = MagicMock",
            content,
            flags=re.MULTILINE,
        )

        # Fix single variable assignment
        content = re.sub(
            r"^(\s+)([A-Za-z_][A-Za-z0-9_]*),\s*\n\s*=\s*MagicMock",
            r"\1\2 = MagicMock",
            content,
            flags=re.MULTILINE,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Fixed {file_path}")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")


if __name__ == "__main__":
    fix_indentation_errors()
