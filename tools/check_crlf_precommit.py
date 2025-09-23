#!/usr/bin/env python3
"""
Pre-commit hook to check for CRLF line endings in test files
"""

import sys
from pathlib import Path

def check_file_for_crlf(file_path):
    """Check if file contains CRLF line endings"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if b'\r\n' in content:
                return True, f"File contains CRLF line endings"
        return False, "OK"
    except Exception as e:
        return True, f"Error reading file: {e}"

def main():
    """Main check function"""
    if len(sys.argv) < 2:
        print("Usage: python check_crlf_precommit.py <file1> [file2] ...")
        return 1
    
    failed_files = []
    
    for file_path in sys.argv[1:]:
        has_crlf, message = check_file_for_crlf(file_path)
        if has_crlf:
            failed_files.append((file_path, message))
    
    if failed_files:
        print("❌ Files with CRLF line endings detected:")
        for file_path, message in failed_files:
            print(f"  - {file_path}: {message}")
        print("\n💡 Run 'python tools/normalize_encoding.py' to fix line endings")
        return 1
    
    print("✅ No CRLF line endings found in test files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
