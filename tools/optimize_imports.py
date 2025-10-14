#!/usr/bin/env python3
"""
Import Optimizer
================

Tự động tối ưu hóa imports trong các files Python:
1. Chuyển heavy imports thành lazy imports
2. Chuyển type-only imports thành TYPE_CHECKING
3. Tạo facade imports nếu cần
"""

import ast
import os
from pathlib import Path
from typing import List, Set, Dict


class ImportOptimizer:
    """Optimizer để tối ưu hóa imports"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.heavy_modules = {
            'torch', 'tensorflow', 'sklearn', 'numpy', 'pandas',
            'transformers', 'sentence_transformers', 'httpx', 'aiohttp',
            'fastapi', 'uvicorn', 'sqlalchemy', 'psutil', 'PIL'
        }
        
    def optimize_file(self, file_path: Path) -> bool:
        """Tối ưu hóa imports trong một file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Phân tích imports
            imports = []
            heavy_imports = []
            type_only_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_heavy_import(alias.name):
                            heavy_imports.append(('import', alias.name, node))
                        else:
                            imports.append(('import', alias.name, node))
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module and self._is_heavy_import(node.module):
                        heavy_imports.append(('from', node.module, node))
                    else:
                        imports.append(('from', node.module, node))
            
            # Nếu có heavy imports, tối ưu hóa
            if heavy_imports:
                return self._apply_lazy_imports(file_path, content, heavy_imports)
            
            return False
            
        except Exception as e:
            print(f"⚠️  Error optimizing {file_path}: {e}")
            return False
    
    def _is_heavy_import(self, import_name: str) -> bool:
        """Kiểm tra xem import có phải heavy không"""
        if not import_name:
            return False
        
        base_module = import_name.split('.')[0]
        return base_module in self.heavy_modules
    
    def _apply_lazy_imports(self, file_path: Path, content: str, heavy_imports: List) -> bool:
        """Áp dụng lazy imports cho heavy modules"""
        print(f"🔧 Optimizing {file_path}")
        
        # Tạo lazy import functions
        lazy_functions = []
        for import_type, module_name, node in heavy_imports:
            if import_type == 'import':
                func_name = f"_get_{module_name.replace('.', '_')}"
                lazy_functions.append(f"""
def {func_name}():
    \"\"\"Lazy import for {module_name}\"\"\"
    try:
        import {module_name}
        return {module_name}
    except ImportError:
        return None
""")
            elif import_type == 'from':
                func_name = f"_get_{module_name.replace('.', '_')}"
                lazy_functions.append(f"""
def {func_name}():
    \"\"\"Lazy import for {module_name}\"\"\"
    try:
        from {module_name} import *
        return True
    except ImportError:
        return False
""")
        
        # Tạo optimized content
        optimized_content = self._create_optimized_content(content, heavy_imports, lazy_functions)
        
        # Ghi file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        
        return True
    
    def _create_optimized_content(self, content: str, heavy_imports: List, lazy_functions: List) -> str:
        """Tạo nội dung file đã được tối ưu hóa"""
        lines = content.split('\n')
        optimized_lines = []
        
        # Thêm lazy import functions ở đầu file
        optimized_lines.extend([
            "# Lazy imports for heavy modules",
            "def _lazy_import(module_name):",
            "    \"\"\"Lazy import helper\"\"\"",
            "    try:",
            "        return __import__(module_name)",
            "    except ImportError:",
            "        return None",
            ""
        ])
        
        # Xử lý từng dòng
        skip_imports = set()
        for import_type, module_name, node in heavy_imports:
            if import_type == 'import':
                skip_imports.add(f"import {module_name}")
            elif import_type == 'from':
                skip_imports.add(f"from {module_name}")
        
        for line in lines:
            # Bỏ qua heavy imports
            if any(skip in line for skip in skip_imports):
                optimized_lines.append(f"# {line}  # Converted to lazy import")
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def optimize_directory(self, directory: str) -> int:
        """Tối ưu hóa tất cả files trong thư mục"""
        scan_path = self.root_dir / directory
        if not scan_path.exists():
            print(f"⚠️  Directory {scan_path} does not exist")
            return 0
        
        optimized_count = 0
        
        for py_file in scan_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            if self.optimize_file(py_file):
                optimized_count += 1
        
        return optimized_count


def main():
    """Main function"""
    optimizer = ImportOptimizer()
    
    # Tối ưu hóa các thư mục quan trọng
    directories_to_optimize = [
        "stillme_core/modules",
        "stillme_core/learning"
    ]
    
    total_optimized = 0
    
    for directory in directories_to_optimize:
        print(f"\n🔍 Optimizing directory: {directory}")
        optimized = optimizer.optimize_directory(directory)
        total_optimized += optimized
        print(f"   ✅ Optimized {optimized} files")
    
    print(f"\n🎉 Total optimized: {total_optimized} files")


if __name__ == "__main__":
    main()
