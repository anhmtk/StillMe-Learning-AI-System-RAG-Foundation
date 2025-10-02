#!/usr/bin/env python3
"""
Secrets Exposure Check
Scans for potential secrets in code and configuration
"""

import re
import sys
from pathlib import Path

# Common secret patterns
SECRET_PATTERNS = [
    # API Keys
    r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
    r'apikey["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',

    # Passwords
    r'password["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
    r'passwd["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
    r'pwd["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',

    # Tokens
    r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
    r'access[_-]?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
    r'bearer[_-]?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',

    # Secrets
    r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{16,}["\']?',
    r'private[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',

    # Database credentials
    r'db[_-]?password["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
    r'database[_-]?password["\']?\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',

    # AWS credentials
    r'aws[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[A-Z0-9]{20}["\']?',
    r'aws[_-]?secret[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9/+=]{40}["\']?',

    # JWT tokens
    r'eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',

    # Generic base64 encoded secrets
    r'["\']?[A-Za-z0-9+/]{40,}={0,2}["\']?',
]

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    '*.pyc',
    '*.pyo',
    '__pycache__/',
    '.git/',
    'node_modules/',
    '.venv/',
    'venv/',
    'env/',
    '.env',
    '*.log',
    '*.tmp',
    '*.cache',
    '.pytest_cache/',
    'coverage/',
    'htmlcov/',
    '.coverage',
    '*.egg-info/',
    'dist/',
    'build/',
    '.tox/',
    '*.so',
    '*.dll',
    '*.dylib',
]

# Safe patterns (false positives)
SAFE_PATTERNS = [
    r'example[_-]?key',
    r'test[_-]?key',
    r'demo[_-]?key',
    r'sample[_-]?key',
    r'placeholder[_-]?key',
    r'your[_-]?key[_-]?here',
    r'put[_-]?your[_-]?key[_-]?here',
    r'<your[_-]?key>',
    r'\[your[_-]?key\]',
    r'api[_-]?key[_-]?example',
    r'password[_-]?example',
    r'secret[_-]?example',
    r'token[_-]?example',
]

def should_exclude_file(file_path: Path) -> bool:
    """Check if file should be excluded from scanning"""
    import fnmatch

    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(str(file_path), pattern):
            return True
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

    return False

def is_safe_pattern(content: str, match: str) -> bool:
    """Check if match is a safe pattern (false positive)"""
    for safe_pattern in SAFE_PATTERNS:
        if re.search(safe_pattern, match, re.IGNORECASE):
            return True

    # Check if it's in a comment or documentation
    lines = content.split('\n')
    for _i, line in enumerate(lines):
        if match in line:
            # Check if line is a comment
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*'):
                return True

            # Check if it's in a docstring
            if '"""' in line or "'''" in line:
                return True

    return False

def scan_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Scan file for potential secrets"""
    findings = []

    try:
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for pattern in SECRET_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                match_text = match.group()

                # Skip if it's a safe pattern
                if is_safe_pattern(content, match_text):
                    continue

                # Get line number
                line_num = content[:match.start()].count('\n') + 1

                findings.append((line_num, match_text, pattern))

    except Exception as e:
        print(f"Error scanning {file_path}: {e}")

    return findings

def scan_directory(directory: Path) -> list[tuple[Path, int, str, str]]:
    """Scan directory for potential secrets"""
    all_findings = []

    for file_path in directory.rglob('*'):
        if file_path.is_file() and not should_exclude_file(file_path):
            findings = scan_file(file_path)
            for line_num, match_text, pattern in findings:
                all_findings.append((file_path, line_num, match_text, pattern))

    return all_findings

def main():
    """Main secrets check"""
    print("Checking for secrets exposure...")

    # Scan current directory
    current_dir = Path('.')
    findings = scan_directory(current_dir)

    if findings:
        print(f"\nFound {len(findings)} potential secrets:")

        for file_path, line_num, match_text, pattern in findings:
            print(f"  {file_path}:{line_num}")
            print(f"    Pattern: {pattern}")
            print(f"    Match: {match_text[:50]}{'...' if len(match_text) > 50 else ''}")
            print()

        print("Please review these findings and:")
        print("1. Remove hardcoded secrets")
        print("2. Use environment variables or secure configuration")
        print("3. Add to .gitignore if they are test/example values")
        print("4. Use placeholder values in documentation")

        sys.exit(1)
    else:
        print("No potential secrets found")
        sys.exit(0)

if __name__ == "__main__":
    main()
