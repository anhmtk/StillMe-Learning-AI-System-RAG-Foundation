#!/usr/bin/env python3
"""
Import Dependencies Sanitizer - Fix import issues and type annotations

This script fixes common import dependency issues:
1. Adds missing type annotations
2. Fixes TYPE_CHECKING imports
3. Adds lazy imports where needed
4. Fixes Any type issues
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any


def fix_type_annotations(content: str) -> str:
    """Fix common type annotation issues"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix missing return type annotations
        if line.strip().startswith('def ') and ' -> ' not in line and line.strip().endswith(':'):
            # Add -> None for functions without return type
            if 'return' not in content[content.find(line):content.find(line) + 200]:
                line = line.replace(':', ' -> None:')
        
        # Fix Any type issues in common patterns
        if 'Expression has type "Any"' in line:
            # Skip mypy error lines
            continue
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def add_type_checking_imports(content: str) -> str:
    """Add TYPE_CHECKING imports where needed"""
    if 'from typing import TYPE_CHECKING' not in content:
        # Find the first import statement
        lines = content.split('\n')
        import_index = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_index = i
                break
        
        if import_index >= 0:
            # Insert TYPE_CHECKING import
            lines.insert(import_index, 'from typing import TYPE_CHECKING')
            content = '\n'.join(lines)
    
    return content


def fix_lazy_imports(content: str) -> str:
    """Convert problematic imports to lazy imports"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Convert imports that might cause circular dependencies to lazy imports
        if line.strip().startswith('from ') and any(module in line for module in ['stillme_core', 'agent_dev']):
            # Check if this import might cause issues
            if 'TYPE_CHECKING' not in line:
                # Convert to TYPE_CHECKING import
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + 'if TYPE_CHECKING:')
                fixed_lines.append(' ' * (indent + 4) + line.strip())
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def fix_any_types(content: str) -> str:
    """Fix Any type issues by adding proper type annotations"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix common Any type patterns
        if ': Any' in line and 'def ' in line:
            # Try to infer better type
            if 'dict' in line:
                line = line.replace(': Any', ': Dict[str, Any]')
            elif 'list' in line:
                line = line.replace(': Any', ': List[Any]')
            elif 'str' in line:
                line = line.replace(': Any', ': str')
            elif 'int' in line:
                line = line.replace(': Any', ': int')
            elif 'bool' in line:
                line = line.replace(': Any', ': bool')
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def process_file(file_path: Path) -> bool:
    """Process a single Python file to fix import dependencies"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = add_type_checking_imports(content)
        content = fix_lazy_imports(content)
        content = fix_type_annotations(content)
        content = fix_any_types(content)
        
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
    """Main function to fix import dependencies"""
    if len(sys.argv) < 2:
        print("Usage: python fix_import_dependencies.py <target_dirs...>")
        print("Example: python fix_import_dependencies.py stillme_core/learning agent_dev/core")
        sys.exit(1)
    
    target_dirs = sys.argv[1:]
    root_path = Path.cwd()
    
    print(f"🔧 Fixing import dependencies in: {', '.join(target_dirs)}")
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
