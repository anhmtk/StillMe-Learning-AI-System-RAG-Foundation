#!/usr/bin/env python3
"""
Import Cycle Scanner - Detect circular import dependencies

This tool scans Python modules to detect circular import dependencies
and reports cycles of length <= 6.
"""

import ast
import os
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_imports(file_path: Path) -> List[str]:
    """Extract import statements from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def module_name_from_path(file_path: Path, root_path: Path) -> str:
    """Convert file path to module name"""
    relative_path = file_path.relative_to(root_path)
    module_parts = list(relative_path.parts)
    
    # Remove .py extension
    if module_parts[-1].endswith('.py'):
        module_parts[-1] = module_parts[-1][:-3]
    
    # Remove __init__ if it's the last part
    if module_parts[-1] == '__init__':
        module_parts = module_parts[:-1]
    
    return '.'.join(module_parts)


def build_import_graph(root_path: Path, target_dirs: List[str]) -> Dict[str, Set[str]]:
    """Build import graph from Python files"""
    graph = defaultdict(set)
    
    for target_dir in target_dirs:
        target_path = root_path / target_dir
        if not target_path.exists():
            print(f"Warning: {target_dir} does not exist")
            continue
            
        for py_file in target_path.rglob('*.py'):
            if py_file.name.startswith('__'):
                continue
                
            module_name = module_name_from_path(py_file, root_path)
            imports = extract_imports(py_file)
            
            for import_name in imports:
                # Filter to only include imports within our target directories
                if any(import_name.startswith(d.replace('/', '.')) for d in target_dirs):
                    graph[module_name].add(import_name)
    
    return dict(graph)


def find_cycles(graph: Dict[str, Set[str]], max_length: int = 6) -> List[List[str]]:
    """Find cycles in the import graph using DFS"""
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> None:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            if len(cycle) <= max_length:
                cycles.append(cycle)
            return
        
        if node in visited:
            return
            
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor, path + [node])
        
        rec_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles


def main():
    """Main function to scan for import cycles"""
    if len(sys.argv) < 2:
        print("Usage: python import_cycle_scan.py <target_dirs...>")
        print("Example: python import_cycle_scan.py stillme_core/learning agent_dev/core")
        sys.exit(1)
    
    root_path = Path.cwd()
    target_dirs = sys.argv[1:]
    
    print(f"🔍 Scanning import cycles in: {', '.join(target_dirs)}")
    print(f"📁 Root path: {root_path}")
    print()
    
    # Build import graph
    print("📊 Building import graph...")
    graph = build_import_graph(root_path, target_dirs)
    
    print(f"📈 Found {len(graph)} modules with imports")
    print()
    
    # Find cycles
    print("🔄 Searching for cycles...")
    cycles = find_cycles(graph, max_length=6)
    
    if cycles:
        print(f"❌ Found {len(cycles)} cycles:")
        print()
        for i, cycle in enumerate(cycles, 1):
            print(f"Cycle {i} (length {len(cycle)}):")
            print("  " + " → ".join(cycle))
            print()
    else:
        print("✅ No cycles found!")
    
    # Show graph statistics
    print("📊 Graph Statistics:")
    print(f"  - Total modules: {len(graph)}")
    print(f"  - Total imports: {sum(len(imports) for imports in graph.values())}")
    print(f"  - Cycles found: {len(cycles)}")
    
    return len(cycles)


if __name__ == "__main__":
    sys.exit(main())
