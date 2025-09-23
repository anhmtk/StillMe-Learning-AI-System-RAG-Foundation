#!/usr/bin/env python3
"""
Pytest bisect tool to find problematic test files
"""

import os
import sys
import subprocess
from pathlib import Path

def run_pytest_collect(test_files):
    """Run pytest collect on specific files"""
    try:
        cmd = [
            sys.executable, '-X', 'utf8', '-m', 'pytest',
            '--collect-only', '-q', '--disable-warnings'
        ] + test_files
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
        )
        
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def find_test_files():
    """Find all test files in tests/ directory"""
    test_files = []
    tests_dir = Path("tests")
    
    if tests_dir.exists():
        for py_file in tests_dir.rglob("test_*.py"):
            test_files.append(str(py_file))
    
    return sorted(test_files)

def bisect_test_files(test_files):
    """Bisect test files to find problematic ones"""
    if not test_files:
        return [], "No test files found"
    
    # Test all files first
    all_ok, error = run_pytest_collect(test_files)
    if all_ok:
        return [], "All test files are OK"
    
    # Binary search to find problematic files
    problematic_files = []
    
    def bisect_range(start, end):
        if start >= end:
            return
        
        mid = (start + end) // 2
        left_files = test_files[start:mid+1]
        right_files = test_files[mid+1:end+1]
        
        # Test left half
        if left_files:
            left_ok, left_error = run_pytest_collect(left_files)
            if not left_ok:
                if len(left_files) == 1:
                    problematic_files.append(left_files[0])
                else:
                    bisect_range(start, mid)
        
        # Test right half
        if right_files:
            right_ok, right_error = run_pytest_collect(right_files)
            if not right_ok:
                if len(right_files) == 1:
                    problematic_files.append(right_files[0])
                else:
                    bisect_range(mid+1, end)
    
    bisect_range(0, len(test_files) - 1)
    return problematic_files, error

def generate_bisect_report(problematic_files, error_message):
    """Generate bisect report"""
    report_path = Path("reports/pytest_bisect.txt")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Pytest Bisect Report\n")
        f.write("=" * 30 + "\n\n")
        
        if problematic_files:
            f.write(f"Found {len(problematic_files)} problematic files:\n\n")
            for file_path in problematic_files:
                f.write(f"❌ {file_path}\n")
        else:
            f.write("✅ No problematic files found\n")
        
        if error_message:
            f.write(f"\nError details:\n{error_message}\n")
    
    return report_path

def main():
    """Main bisect function"""
    print("🔍 Running pytest bisect to find problematic files...")
    
    # Find all test files
    test_files = find_test_files()
    print(f"📁 Found {len(test_files)} test files")
    
    if not test_files:
        print("❌ No test files found in tests/ directory")
        return 1
    
    # Run bisect
    problematic_files, error_message = bisect_test_files(test_files)
    
    # Generate report
    report_path = generate_bisect_report(problematic_files, error_message)
    
    if problematic_files:
        print(f"❌ Found {len(problematic_files)} problematic files:")
        for file_path in problematic_files:
            print(f"  - {file_path}")
    else:
        print("✅ No problematic files found")
    
    print(f"📄 Report saved to: {report_path}")
    
    return len(problematic_files)

if __name__ == "__main__":
    sys.exit(main())
