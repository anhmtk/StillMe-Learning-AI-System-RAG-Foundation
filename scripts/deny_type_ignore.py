#!/usr/bin/env python3
"""
Pre-commit hook để deny bất kỳ '# type: ignore' nào trong repository.
Fail nếu tìm thấy bất kỳ type ignore nào.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple


def find_type_ignores_in_file(file_path: Path) -> List[Tuple[int, str]]:
    """
    Tìm tất cả '# type: ignore' trong một file.
    
    Returns:
        List of (line_number, line_content) tuples
    """
    ignores = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                
                # Skip empty lines và comment-only lines
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                
                # Skip docstrings (triple quotes)
                if '"""' in line or "'''" in line:
                    continue
                
                # Skip nếu '# type: ignore' nằm trong string literal
                # Tìm vị trí của '# type: ignore'
                ignore_pos = line.find('# type: ignore')
                if ignore_pos == -1:
                    continue
                
                # Kiểm tra xem có nằm trong string literal không
                before_ignore = line[:ignore_pos]
                quote_count_single = before_ignore.count("'") - before_ignore.count("\\'")
                quote_count_double = before_ignore.count('"') - before_ignore.count('\\"')
                
                # Nếu số quote lẻ thì đang trong string literal
                if quote_count_single % 2 == 1 or quote_count_double % 2 == 1:
                    continue
                
                # Tìm '# type: ignore' trong code thực sự
                ignores.append((line_num, line.strip()))
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    
    return ignores


def check_staged_files() -> bool:
    """
    Kiểm tra tất cả staged files cho '# type: ignore'.
    
    Returns:
        True nếu không có type ignore, False nếu có
    """
    # Lấy danh sách staged files từ git
    import subprocess
    
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("Error: Could not get staged files from git")
        return False
    
    # Filter chỉ Python/TypeScript files
    code_extensions = {'.py', '.pyi', '.ts', '.tsx', '.js', '.jsx'}
    code_files = [
        f for f in staged_files 
        if f and Path(f).suffix in code_extensions
    ]
    
    if not code_files:
        print("No code files staged for commit")
        return True
    
    found_ignores = []
    
    for file_path in code_files:
        if not os.path.exists(file_path):
            continue
            
        ignores = find_type_ignores_in_file(Path(file_path))
        if ignores:
            found_ignores.extend([(file_path, line_num, line) for line_num, line in ignores])
    
    if found_ignores:
        print("❌ PRE-COMMIT HOOK FAILED: Found '# type: ignore' in staged files!")
        print("\nFiles with type ignores:")
        
        for file_path, line_num, line in found_ignores:
            print(f"  {file_path}:{line_num}")
            print(f"    {line}")
        
        print(f"\nTotal: {len(found_ignores)} type ignores found")
        print("\nTo fix:")
        print("1. Remove '# type: ignore' and fix the underlying type issue")
        print("2. Or unstage the file: git reset HEAD <file>")
        print("3. Or use --no-verify to bypass (NOT RECOMMENDED)")
        
        return False
    
    print("✅ No '# type: ignore' found in staged files")
    return True


def check_all_files() -> bool:
    """
    Kiểm tra toàn bộ repository cho '# type: ignore'.
    Dùng cho CI/CD hoặc manual check.
    
    Returns:
        True nếu không có type ignore, False nếu có
    """
    root_path = Path('.')
    
    # Patterns để ignore
    ignore_patterns = {
        '.git',
        '__pycache__',
        '.venv',
        'venv',
        'node_modules',
        '.pytest_cache',
        'dist',
        'build',
        '.mypy_cache',
        '.ruff_cache'
    }
    
    # File extensions để scan
    code_extensions = {'.py', '.pyi', '.ts', '.tsx', '.js', '.jsx'}
    
    found_ignores = []
    
    for file_path in root_path.rglob('*'):
        # Skip directories
        if file_path.is_dir():
            continue
            
        # Skip ignored patterns
        if any(part in ignore_patterns for part in file_path.parts):
            continue
            
        # Skip non-code files
        if file_path.suffix not in code_extensions:
            continue
        
        ignores = find_type_ignores_in_file(file_path)
        if ignores:
            found_ignores.extend([(str(file_path), line_num, line) for line_num, line in ignores])
    
    if found_ignores:
        print("❌ REPOSITORY CHECK FAILED: Found '# type: ignore' in repository!")
        print(f"\nTotal: {len(found_ignores)} type ignores found")
        print("\nFirst 20 files with type ignores:")
        
        for i, (file_path, line_num, line) in enumerate(found_ignores[:20], 1):
            print(f"{i:2d}. {file_path}:{line_num}")
            print(f"    {line}")
        
        if len(found_ignores) > 20:
            print(f"... and {len(found_ignores) - 20} more")
        
        print("\nRun 'python tools/audit_type_ignores.py' for complete report")
        return False
    
    print("✅ No '# type: ignore' found in repository!")
    return True


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Check toàn bộ repository
        success = check_all_files()
    else:
        # Check chỉ staged files (pre-commit mode)
        success = check_staged_files()
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
