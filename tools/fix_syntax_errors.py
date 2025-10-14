#!/usr/bin/env python3
"""
Fix syntax errors in Python files

This script fixes common syntax errors introduced by the import fixer.
"""

import re
from pathlib import Path


def fix_syntax_errors(content: str) -> str:
    """Fix common syntax errors"""
    # Fix incorrect type annotation syntax: param -> None: Type = default
    # Should be: param: Type = default
    content = re.sub(r'(\w+)\s*->\s*None:\s*(\w+)\s*=', r'\1: \2 =', content)
    
    # Fix other similar patterns
    content = re.sub(r'(\w+)\s*->\s*(\w+):\s*(\w+)\s*=', r'\1: \2 =', content)
    
    return content


def process_file(file_path: Path) -> bool:
    """Process a single Python file to fix syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_syntax_errors(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix syntax errors"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_syntax_errors.py <target_dirs...>")
        print("Example: python fix_syntax_errors.py stillme_core/learning agent_dev/core")
        sys.exit(1)
    
    target_dirs = sys.argv[1:]
    root_path = Path.cwd()
    
    print(f"🔧 Fixing syntax errors in: {', '.join(target_dirs)}")
    print(f"📁 Root path: {root_path}")
    print()
    
    total_files = 0
    fixed_files = 0
    
    for target_dir in target_dirs:
        target_path = root_path / target_dir
        if not target_path.exists():
            print(f"Warning: {target_dir} does not exist")
            continue
            
        print(f"📂 Processing {target_dir}...")
        
        for py_file in target_path.rglob('*.py'):
            if py_file.name.startswith('__'):
                continue
                
            total_files += 1
            if process_file(py_file):
                fixed_files += 1
                print(f"  ✅ Fixed: {py_file.relative_to(root_path)}")
    
    print()
    print(f"📊 Summary:")
    print(f"  - Total files processed: {total_files}")
    print(f"  - Files fixed: {fixed_files}")
    print(f"  - Files unchanged: {total_files - fixed_files}")


if __name__ == "__main__":
    main()
