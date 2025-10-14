#!/usr/bin/env python3
"""
Import Analysis Report
======================

Phân tích chi tiết imports để tìm các vấn đề tiềm ẩn và cơ hội tối ưu hóa.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter


class ImportAnalyzer:
    """Analyzer để phân tích imports và tìm vấn đề"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.imports = defaultdict(set)
        self.files = {}
        self.import_counts = Counter()
        self.heavy_imports = []  # Imports có thể gây chậm
        self.type_only_imports = []  # Imports chỉ dùng cho type hints
        
    def analyze_directory(self, directory: str = "stillme_core/learning") -> None:
        """Phân tích một thư mục"""
        scan_path = self.root_dir / directory
        if not scan_path.exists():
            print(f"⚠️  Directory {scan_path} does not exist")
            return
            
        print(f"🔍 Analyzing directory: {scan_path}")
        
        for py_file in scan_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                self._analyze_file(py_file)
            except Exception as e:
                print(f"⚠️  Error analyzing {py_file}: {e}")
    
    def _analyze_file(self, file_path: Path) -> None:
        """Phân tích một file Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            module_name = self._get_module_name(file_path)
            self.files[module_name] = file_path
            
            # Phân tích imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports[module_name].add(alias.name)
                        self.import_counts[alias.name] += 1
                        self._check_heavy_import(alias.name, file_path)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports[module_name].add(node.module)
                        self.import_counts[node.module] += 1
                        self._check_heavy_import(node.module, file_path)
                        
            # Tìm type-only imports
            self._find_type_only_imports(tree, file_path)
                        
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative_path = file_path.relative_to(self.root_dir)
        module_parts = list(relative_path.parts)
        
        if module_parts[-1].endswith('.py'):
            module_parts[-1] = module_parts[-1][:-3]
        
        if module_parts[-1] == '__init__':
            module_parts = module_parts[:-1]
        
        return '.'.join(module_parts)
    
    def _check_heavy_import(self, import_name: str, file_path: Path) -> None:
        """Kiểm tra imports có thể gây chậm"""
        heavy_modules = {
            'torch', 'tensorflow', 'sklearn', 'numpy', 'pandas',
            'transformers', 'sentence_transformers', 'httpx', 'aiohttp',
            'fastapi', 'uvicorn', 'sqlalchemy', 'psutil'
        }
        
        if any(heavy in import_name for heavy in heavy_modules):
            self.heavy_imports.append((import_name, file_path))
    
    def _find_type_only_imports(self, tree: ast.AST, file_path: Path) -> None:
        """Tìm imports chỉ dùng cho type hints"""
        # Tìm các TYPE_CHECKING blocks
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if (isinstance(node.test, ast.Name) and 
                    node.test.id == 'TYPE_CHECKING'):
                    for stmt in node.body:
                        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                            self.type_only_imports.append((stmt, file_path))
    
    def generate_report(self) -> None:
        """Tạo báo cáo phân tích"""
        print("\n" + "="*80)
        print("📊 IMPORT ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📈 SUMMARY:")
        print(f"   • Total modules analyzed: {len(self.files)}")
        print(f"   • Total unique imports: {len(self.import_counts)}")
        print(f"   • Heavy imports found: {len(self.heavy_imports)}")
        print(f"   • Type-only imports found: {len(self.type_only_imports)}")
        
        # Top imports
        print(f"\n🔝 TOP 10 MOST IMPORTED MODULES:")
        for module, count in self.import_counts.most_common(10):
            print(f"   • {module}: {count} times")
        
        # Heavy imports
        if self.heavy_imports:
            print(f"\n⚠️  HEAVY IMPORTS (có thể gây chậm):")
            for import_name, file_path in self.heavy_imports[:10]:
                print(f"   • {import_name} in {file_path}")
        
        # Type-only imports
        if self.type_only_imports:
            print(f"\n💡 TYPE-ONLY IMPORTS (có thể dùng TYPE_CHECKING):")
            for stmt, file_path in self.type_only_imports[:10]:
                if isinstance(stmt, ast.Import):
                    names = [alias.name for alias in stmt.names]
                    print(f"   • import {', '.join(names)} in {file_path}")
                elif isinstance(stmt, ast.ImportFrom):
                    module = stmt.module or ""
                    names = [alias.name for alias in stmt.names]
                    print(f"   • from {module} import {', '.join(names)} in {file_path}")
        
        # Circular import candidates
        print(f"\n🔍 CIRCULAR IMPORT CANDIDATES:")
        circular_candidates = self._find_circular_candidates()
        for candidate in circular_candidates[:10]:
            print(f"   • {candidate}")
        
        # Optimization suggestions
        print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
        self._suggest_optimizations()
    
    def _find_circular_candidates(self) -> List[str]:
        """Tìm các imports có thể gây circular dependency"""
        candidates = []
        
        for module, imports in self.imports.items():
            for imp in imports:
                # Kiểm tra nếu module A import B và B có thể import A
                if imp in self.files:
                    if module in self.imports.get(imp, set()):
                        candidates.append(f"{module} ↔ {imp}")
        
        return candidates
    
    def _suggest_optimizations(self) -> None:
        """Đề xuất tối ưu hóa"""
        suggestions = []
        
        # 1. Heavy imports có thể lazy load
        heavy_modules = set()
        for import_name, _ in self.heavy_imports:
            heavy_modules.add(import_name.split('.')[0])
        
        if heavy_modules:
            suggestions.append(f"Consider lazy loading for: {', '.join(heavy_modules)}")
        
        # 2. Type-only imports
        if self.type_only_imports:
            suggestions.append("Move type-only imports to TYPE_CHECKING blocks")
        
        # 3. Frequent imports
        frequent_imports = [mod for mod, count in self.import_counts.most_common(5) 
                          if count > 10 and not mod.startswith('typing')]
        if frequent_imports:
            suggestions.append(f"Consider creating facade for: {', '.join(frequent_imports)}")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")


def main():
    """Main function"""
    analyzer = ImportAnalyzer()
    
    # Analyze các thư mục quan trọng
    directories_to_analyze = [
        "stillme_core/learning",
        "stillme_core/modules", 
        "agent_dev",
        "stillme_core"
    ]
    
    for directory in directories_to_analyze:
        analyzer.analyze_directory(directory)
    
    # Tạo báo cáo
    analyzer.generate_report()


if __name__ == "__main__":
    main()
