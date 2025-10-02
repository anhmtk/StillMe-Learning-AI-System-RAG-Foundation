#!/usr/bin/env python3
"""
Fix syntax errors in test files
"""

import os
import re


def fix_syntax_errors():
    """Fix common syntax errors in test files"""

    # Find all Python files in tests directory
    test_files = []
    for root, dirs, files in os.walk("tests"):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'fixtures', 'cassettes', 'config', 'devops', 'ethics', 'logs', 'reports', 'safety', 'security']]

        for file in files:
            if file.endswith('.py'):
                test_files.append(os.path.join(root, file))

    fixed_count = 0

    for file_path in test_files:
        try:
            with open(file_path, encoding='utf-8', errors='replace') as f:
                content = f.read()

            original_content = content

            # Fix empty import statements
            content = re.sub(
                r'^from [^\s]+ import \(\s*\)$',
                r'# \g<0>  # Empty import',
                content,
                flags=re.MULTILINE
            )

            # Fix incomplete try blocks
            content = re.sub(
                r'^try:\s*$\n\s*$\n\s*except',
                r'try:\n    pass\nexcept',
                content,
                flags=re.MULTILINE
            )

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed: {file_path}")
                fixed_count += 1

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    fix_syntax_errors()
