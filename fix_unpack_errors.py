#!/usr/bin/env python3
"""
Fix unpack errors in test files
"""

import os
import re


def fix_unpack_errors():
    """Fix all unpack errors in test files"""

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

        # Fix unpack errors like "a, b, c = MagicMock"
        content = re.sub(
            r"(\w+(?:, \w+)*) = MagicMock",
            lambda m: "\n".join(
                [f"{name.strip()} = MagicMock" for name in m.group(1).split(",")]
            ),
            content,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Fixed {file_path}")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")


if __name__ == "__main__":
    fix_unpack_errors()
