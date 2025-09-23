#!/usr/bin/env python3
"""
Pre-commit hook to check for null bytes in test files
"""

import sys
from pathlib import Path

def check_file_for_null_bytes(file_path):
    """Check if file contains null bytes"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if b'\x00' in content:
                return True, f"File contains null bytes"
        return False, "OK"
    except Exception as e:
        return True, f"Error reading file: {e}"

def main():
    """Main check function"""
    if len(sys.argv) < 2:
        print("Usage: python check_null_bytes_precommit.py <file1> [file2] ...")
        return 1
    
    failed_files = []
    
    for file_path in sys.argv[1:]:
        has_null, message = check_file_for_null_bytes(file_path)
        if has_null:
            failed_files.append((file_path, message))
    
    if failed_files:
        print("❌ Files with null bytes detected:")
        for file_path, message in failed_files:
            print(f"  - {file_path}: {message}")
        print("\n💡 Run 'python tools/normalize_encoding.py' to fix encoding issues")
        return 1
    
    print("✅ No null bytes found in test files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
