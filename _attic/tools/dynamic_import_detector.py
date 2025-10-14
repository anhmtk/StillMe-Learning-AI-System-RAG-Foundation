#!/usr/bin/env python3
"""
Dynamic Import/Registry Detection Tool
Detects modules that use dynamic imports or registry patterns
"""

import os
import re
import json
from pathlib import Path

def detect_dynamic_imports(root_path: str = ".") -> dict:
    """Detect dynamic import patterns in Python files"""
    
    patterns = [
        r"importlib\.import_module",
        r"pkgutil\.iter_modules", 
        r"pkg_resources",
        r"entry_points",
        r"PluginRegistry\.add",
        r"load_plugins",
        r"registry\.register",
        r"router\.add_route",
        r"Blueprint\(",
        r"__import__\(",
        r"exec\(",
        r"eval\(",
        r"getattr\(",
        r"setattr\(",
        r"globals\(\)",
        r"locals\(\)"
    ]
    
    dynamic_paths = set()
    pattern_matches = {}
    
    # Global excludes
    excludes = [
        ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/", 
        "dist/", "build/", "node_modules/", "artifacts/", "reports/", 
        "htmlcov", "__pycache__/", "*.egg-info/", ".sandbox/"
    ]
    
    def should_exclude(file_path: str) -> bool:
        """Check if file should be excluded"""
        path = Path(file_path).as_posix()
        for exclude in excludes:
            if exclude.endswith('/') and f"/{exclude}" in path:
                return True
            elif exclude.startswith('*') and path.endswith(exclude[1:]):
                return True
            elif exclude in path:
                return True
        return False
    
    # Scan Python files
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if should_exclude(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check for patterns
                    for pattern in patterns:
                        if re.search(pattern, content):
                            rel_path = os.path.relpath(file_path, root_path)
                            dynamic_paths.add(rel_path)
                            
                            if pattern not in pattern_matches:
                                pattern_matches[pattern] = []
                            pattern_matches[pattern].append(rel_path)
                            
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    # Identify module directories that contain dynamic imports
    module_dirs = set()
    for path in dynamic_paths:
        path_parts = Path(path).parts
        if len(path_parts) > 1:
            # Add parent directory as module
            module_dirs.add(str(Path(path).parent))
    
    return {
        "dynamic_files": sorted(list(dynamic_paths)),
        "dynamic_modules": sorted(list(module_dirs)),
        "pattern_matches": {k: sorted(v) for k, v in pattern_matches.items()},
        "total_files_scanned": len(dynamic_paths),
        "total_modules": len(module_dirs)
    }

def main():
    """Main function"""
    print("🔍 Detecting dynamic imports and registry patterns...")
    
    results = detect_dynamic_imports()
    
    # Save results
    output_file = "artifacts/dynamic_registry_paths.json"
    os.makedirs("artifacts", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Results:")
    print(f"  - Dynamic files found: {results['total_files_scanned']}")
    print(f"  - Dynamic modules: {results['total_modules']}")
    print(f"  - Output saved to: {output_file}")
    
    if results['dynamic_modules']:
        print(f"\n📁 Dynamic modules detected:")
        for module in results['dynamic_modules'][:10]:  # Show first 10
            print(f"  - {module}")
        if len(results['dynamic_modules']) > 10:
            print(f"  ... and {len(results['dynamic_modules']) - 10} more")

if __name__ == "__main__":
    main()
