#!/usr/bin/env python3
"""
Null bytes and encoding scanner for test files
Scans tests/, conftest.py, pytest.ini for encoding issues
"""

import os
import sys
from pathlib import Path

import chardet


def scan_file_for_issues(file_path):
    """Scan a single file for null bytes and encoding issues"""
    issues = []

    try:
        # Read file as binary first
        with open(file_path, 'rb') as f:
            content = f.read()

        # Check for null bytes
        if b'\x00' in content:
            issues.append("Contains null bytes (\\x00)")

        # Check if file is binary (heuristic)
        if b'\x00' in content[:1024]:  # Check first 1KB
            issues.append("Appears to be binary file")

        # Try to detect encoding
        detected = chardet.detect(content)
        if detected['encoding'] and detected['confidence'] > 0.7:
            if detected['encoding'].lower() not in ['utf-8', 'ascii', 'utf-8-sig']:
                issues.append(f"Non-UTF-8 encoding detected: {detected['encoding']}")

        # Try to decode as UTF-8
        try:
            content.decode('utf-8')
        except UnicodeDecodeError as e:
            issues.append(f"UTF-8 decode error: {e}")

        # Check for suspicious patterns
        if b'\xff\xfe' in content[:2] or b'\xfe\xff' in content[:2]:
            issues.append("Contains BOM (Byte Order Mark)")

    except Exception as e:
        issues.append(f"File read error: {e}")

    return issues

def scan_test_files():
    """Scan all test-related files for issues"""
    scan_paths = [
        Path("tests/"),
        Path("tests/conftest.py"),
        Path("pytest.ini")
    ]

    problematic_files = []

    for scan_path in scan_paths:
        if not scan_path.exists():
            continue

        if scan_path.is_file():
            # Single file
            issues = scan_file_for_issues(scan_path)
            if issues:
                problematic_files.append({
                    'path': str(scan_path),
                    'issues': issues
                })
        else:
            # Directory - scan all Python files
            for py_file in scan_path.rglob("*.py"):
                issues = scan_file_for_issues(py_file)
                if issues:
                    problematic_files.append({
                        'path': str(py_file),
                        'issues': issues
                    })

    return problematic_files

def quarantine_file(file_path):
    """Quarantine a problematic file by renaming it"""
    try:
        quarantined_path = f"{file_path}.quarantined"
        os.rename(file_path, quarantined_path)
        return quarantined_path
    except Exception as e:
        print(f"Failed to quarantine {file_path}: {e}")
        return None

def generate_report(problematic_files):
    """Generate scan report"""
    report_path = Path("reports/test_null_scan.txt")
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Null Bytes and Encoding Scan Report\n")
        f.write("=" * 50 + "\n\n")

        if not problematic_files:
            f.write("✅ No problematic files found.\n")
            f.write("All test files are clean.\n")
        else:
            f.write(f"❌ Found {len(problematic_files)} problematic files:\n\n")

            for file_info in problematic_files:
                f.write(f"File: {file_info['path']}\n")
                f.write("Issues:\n")
                for issue in file_info['issues']:
                    f.write(f"  - {issue}\n")
                f.write("\n")

    return report_path

def main():
    """Main scanning function"""
    print("🔍 Scanning test files for null bytes and encoding issues...")

    # Scan files
    problematic_files = scan_test_files()

    if not problematic_files:
        print("✅ All test files are clean!")
        generate_report(problematic_files)
        return 0

    print(f"❌ Found {len(problematic_files)} problematic files:")

    quarantined_files = []

    for file_info in problematic_files:
        print(f"\n📁 {file_info['path']}")
        for issue in file_info['issues']:
            print(f"  - {issue}")

        # Quarantine the file
        quarantined_path = quarantine_file(file_info['path'])
        if quarantined_path:
            quarantined_files.append(quarantined_path)
            print(f"  🔒 Quarantined as: {quarantined_path}")

    # Generate report
    report_path = generate_report(problematic_files)
    print(f"\n📊 Report saved to: {report_path}")

    if quarantined_files:
        print(f"\n🔒 Quarantined {len(quarantined_files)} files:")
        for qf in quarantined_files:
            print(f"  - {qf}")

    return len(problematic_files)

if __name__ == "__main__":
    sys.exit(main())
