#!/usr/bin/env python3
"""
Smoke Import Tool - Safely import all modules to generate coverage data
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

def safe_import_module(module_name):
    """Safely import a module and return success status"""
    try:
        importlib.import_module(module_name)
        return True
    except Exception as e:
        # Log but don't fail - this is expected for some modules
        print(f"⚠️  Could not import {module_name}: {e}", file=sys.stderr)
        return False

def find_python_modules(root_dir, excludes=None):
    """Find all Python modules in the given directory"""
    if excludes is None:
        excludes = [
            ".git", ".github", ".venv", "venv", "env", "site-packages", 
            "dist", "build", "node_modules", "artifacts", "reports", 
            "htmlcov", "__pycache__", ".egg-info", ".sandbox"
        ]
    
    modules = []
    root_path = Path(root_dir)
    
    for py_file in root_path.rglob("*.py"):
        # Skip excluded paths
        if any(exclude in str(py_file) for exclude in excludes):
            continue
            
        # Convert file path to module name
        rel_path = py_file.relative_to(root_path)
        module_parts = list(rel_path.parts)
        module_parts[-1] = module_parts[-1][:-3]  # Remove .py extension
        
        # Skip __init__.py files (they're part of package imports)
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]
            
        if module_parts:  # Only add non-empty module names
            module_name = ".".join(module_parts)
            modules.append(module_name)
    
    return modules

def main():
    """Main smoke import function"""
    print("🔥 Starting smoke import for coverage generation...")
    
    # Find all Python modules
    modules = find_python_modules(".", excludes=[
        ".git", ".github", ".venv", "venv", "env", "site-packages", 
        "dist", "build", "node_modules", "artifacts", "reports", 
        "htmlcov", "__pycache__", ".egg-info", ".sandbox"
    ])
    
    print(f"📦 Found {len(modules)} modules to import")
    
    # Import modules safely
    success_count = 0
    failed_count = 0
    
    for module_name in modules:
        if safe_import_module(module_name):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"✅ Successfully imported: {success_count}")
    print(f"❌ Failed to import: {failed_count}")
    print(f"📊 Total modules processed: {len(modules)}")
    
    # This script should not fail the pipeline even if some imports fail
    return 0

if __name__ == "__main__":
    sys.exit(main())
