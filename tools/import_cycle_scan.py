#!/usr/bin/env python3
"""
Import Cycle Scanner
====================

Phát hiện circular imports trong codebase bằng cách phân tích AST
và xây dựng dependency graph.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque


class ImportCycleScanner:
    """Scanner để phát hiện circular imports"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.imports = defaultdict(set)  # module -> set of imported modules
        self.files = {}  # module -> file path
        self.cycles = []  # list of cycles found
        
    def scan_directory(self, directory: str = "stillme_core/learning") -> None:
        """Scan một thư mục để tìm imports"""
        scan_path = self.root_dir / directory
        if not scan_path.exists():
            print(f"⚠️  Directory {scan_path} does not exist")
            return
            
        print(f"🔍 Scanning directory: {scan_path}")
        
        for py_file in scan_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                self._scan_file(py_file)
            except Exception as e:
                print(f"⚠️  Error scanning {py_file}: {e}")
    
    def _scan_file(self, file_path: Path) -> None:
        """Scan một file Python để extract imports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            module_name = self._get_module_name(file_path)
            self.files[module_name] = file_path
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports[module_name].add(node.module)
                        
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative_path = file_path.relative_to(self.root_dir)
        module_parts = list(relative_path.parts)
        
        # Remove .py extension
        if module_parts[-1].endswith('.py'):
            module_parts[-1] = module_parts[-1][:-3]
        
        # Remove __init__ if it's the last part
        if module_parts[-1] == '__init__':
            module_parts = module_parts[:-1]
        
        return '.'.join(module_parts)
    
    def find_cycles(self, max_length: int = 6) -> List[List[str]]:
        """Tìm cycles trong dependency graph"""
        self.cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if len(cycle) <= max_length + 1:  # +1 because we include the start node twice
                    self.cycles.append(cycle[:-1])  # Remove duplicate start node
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visit all dependencies
            for dep in self.imports[node]:
                if dep in self.files:  # Only consider modules we've scanned
                    dfs(dep)
            
            rec_stack.remove(node)
            path.pop()
        
        # Start DFS from each module
        for module in self.files.keys():
            if module not in visited:
                dfs(module)
        
        return self.cycles
    
    def print_report(self) -> None:
        """In báo cáo chi tiết về cycles"""
        print("\n" + "="*80)
        print("🔍 IMPORT CYCLE SCAN REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Total modules scanned: {len(self.files)}")
        print(f"   • Total imports found: {sum(len(imports) for imports in self.imports.values())}")
        print(f"   • Cycles detected: {len(self.cycles)}")
        
        if self.cycles:
            print(f"\n🚨 CYCLES FOUND:")
            for i, cycle in enumerate(self.cycles, 1):
                print(f"\n   Cycle #{i} (length: {len(cycle)}):")
                for j, module in enumerate(cycle):
                    arrow = " → " if j < len(cycle) - 1 else " → (back to start)"
                    print(f"      {module}{arrow}")
                
                # Show files involved
                print(f"   Files involved:")
                for module in cycle:
                    if module in self.files:
                        print(f"      • {module}: {self.files[module]}")
        else:
            print(f"\n✅ NO CYCLES FOUND!")
        
        print(f"\n📁 MODULES SCANNED:")
        for module, file_path in sorted(self.files.items()):
            import_count = len(self.imports[module])
            print(f"   • {module} ({import_count} imports): {file_path}")
        
        print(f"\n🔗 IMPORT DEPENDENCIES:")
        for module, imports in sorted(self.imports.items()):
            if imports:
                print(f"   {module}:")
                for imp in sorted(imports):
                    if imp in self.files:
                        print(f"      → {imp}")
                    else:
                        print(f"      → {imp} (external)")
    
    def get_cycle_edges(self) -> List[Tuple[str, str]]:
        """Lấy danh sách các cạnh trong cycles để có thể 'bẻ'"""
        edges = []
        for cycle in self.cycles:
            for i in range(len(cycle)):
                current = cycle[i]
                next_module = cycle[(i + 1) % len(cycle)]
                edges.append((current, next_module))
        return edges
    
    def suggest_break_points(self) -> List[Tuple[str, str, str]]:
        """Đề xuất các điểm có thể 'bẻ' cycle"""
        suggestions = []
        edges = self.get_cycle_edges()
        
        # Đếm số lần mỗi cạnh xuất hiện
        edge_count = defaultdict(int)
        for edge in edges:
            edge_count[edge] += 1
        
        # Sắp xếp theo tần suất (cạnh xuất hiện nhiều nhất = ưu tiên bẻ)
        sorted_edges = sorted(edge_count.items(), key=lambda x: x[1], reverse=True)
        
        for (from_module, to_module), count in sorted_edges:
            reason = f"Appears in {count} cycle(s)"
            suggestions.append((from_module, to_module, reason))
        
        return suggestions


def main():
    """Main function để chạy scan"""
    scanner = ImportCycleScanner()
    
    # Scan các thư mục quan trọng
    directories_to_scan = [
        "stillme_core/learning",
        "stillme_core/modules", 
        "agent_dev",
        "stillme_core"
    ]
    
    for directory in directories_to_scan:
        scanner.scan_directory(directory)
    
    # Tìm cycles
    cycles = scanner.find_cycles(max_length=6)
    
    # In báo cáo
    scanner.print_report()
    
    # Đề xuất break points
    if cycles:
        print(f"\n💡 SUGGESTED BREAK POINTS:")
        suggestions = scanner.suggest_break_points()
        for i, (from_module, to_module, reason) in enumerate(suggestions[:10], 1):
            print(f"   {i}. {from_module} → {to_module} ({reason})")
    
    return len(cycles)


if __name__ == "__main__":
    cycle_count = main()
    sys.exit(0 if cycle_count == 0 else 1)
