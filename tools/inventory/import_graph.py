#!/usr/bin/env python3
"""
Import Graph Analysis for StillMe Cleanup
Analyzes import dependencies across multiple root packages.
"""

import os
import json
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

# Global excludes
GLOBAL_EXCLUDES = [
    ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/", "dist/", 
    "build/", "node_modules/", "artifacts/", "reports/", "htmlcov", 
    "__pycache__/", "*.egg-info/", ".sandbox/"
]

def should_exclude_path(file_path: str) -> bool:
    """Check if a file path should be excluded based on global exclude patterns."""
    path = Path(file_path).as_posix()
    for exclude in GLOBAL_EXCLUDES:
        if Path(exclude).is_absolute():
            if Path(path) == Path(exclude) or Path(path).is_relative_to(Path(exclude)):
                return True
        else:
            if exclude.endswith('/') and f"/{exclude}" in path:
                return True
            elif exclude.startswith('*') and path.endswith(exclude[1:]):
                return True
            elif exclude in path:
                return True
    return False

def find_root_packages() -> List[str]:
    """Find root packages in the repository."""
    root_packages = []
    
    # Check for common package names
    potential_packages = ["stillme_core", "stillme_ethical_core", "stillme_api"]
    
    for pkg in potential_packages:
        pkg_path = REPO_ROOT / pkg
        if pkg_path.is_dir() and (pkg_path / "__init__.py").exists():
            root_packages.append(pkg)
            logger.info(f"Found root package: {pkg}")
    
    return root_packages

def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Extract import statements from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception as e:
        logger.debug(f"Could not parse {file_path}: {e}")
    
    return imports

def build_import_graph(root_packages: List[str]) -> Dict[str, Any]:
    """Build import graph for the given root packages."""
    if not root_packages:
        logger.warning("No root packages found")
        return {"modules": [], "inbound_counts": {}}
    
    all_modules = []
    inbound_counts = {}
    import_map = {}  # module -> set of modules it imports
    
    for root_pkg in root_packages:
        try:
            logger.info(f"Building import graph for {root_pkg}...")
            
            pkg_path = REPO_ROOT / root_pkg
            if not pkg_path.exists():
                logger.warning(f"Package path not found: {pkg_path}")
                continue
            
            # Find all Python files
            for py_file in pkg_path.rglob("*.py"):
                if should_exclude_path(str(py_file.relative_to(REPO_ROOT))):
                    continue
                
                # Convert file path to module name
                rel_path = py_file.relative_to(REPO_ROOT)
                module_parts = list(rel_path.parts)
                if module_parts[-1] == "__init__.py":
                    module_parts = module_parts[:-1]
                else:
                    module_parts[-1] = module_parts[-1][:-3]  # Remove .py
                
                module_name = ".".join(module_parts)
                all_modules.append(module_name)
                
                # Extract imports
                imports = extract_imports_from_file(py_file)
                import_map[module_name] = imports
                
        except Exception as e:
            logger.warning(f"Could not build graph for {root_pkg}: {e}")
            continue
    
    # Calculate inbound imports
    for module in all_modules:
        inbound_imports = 0
        for other_module, imports in import_map.items():
            if other_module != module and module in imports:
                inbound_imports += 1
        
        # Special protection for __init__.py files
        if module.endswith('.__init__') or module.endswith('__init__'):
            inbound_imports = max(inbound_imports, 1)
        
        inbound_counts[module] = inbound_imports
    
    return {
        "modules": all_modules,
        "inbound_counts": inbound_counts
    }

def save_import_data(data: Dict[str, Any], output_file: Path):
    """Save import analysis data to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to the expected format
    import_inbound = []
    for module, count in data["inbound_counts"].items():
        import_inbound.append({
            "module": module,
            "inbound_imports": count
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(import_inbound, f, indent=2)
    
    logger.info(f"Import data saved to: {output_file}")

def main():
    """Main function to analyze import graph."""
    logger.info("🎯 Starting import graph analysis...")
    
    # Find root packages
    root_packages = find_root_packages()
    if not root_packages:
        logger.error("No root packages found. Expected: stillme_core, stillme_ethical_core")
        return
    
    logger.info(f"📦 Root packages: {root_packages}")
    
    # Build import graph
    graph_data = build_import_graph(root_packages)
    
    # Save results
    output_file = REPO_ROOT / "artifacts" / "import_inbound.json"
    save_import_data(graph_data, output_file)
    
    # Print summary
    logger.info(f"📊 Analysis complete:")
    logger.info(f"  - Root packages: {len(root_packages)}")
    logger.info(f"  - Modules analyzed: {len(graph_data['modules'])}")
    logger.info(f"  - Modules with inbound imports: {len([m for m, c in graph_data['inbound_counts'].items() if c > 0])}")
    logger.info(f"  - Results saved to: {output_file}")

if __name__ == "__main__":
    main()
