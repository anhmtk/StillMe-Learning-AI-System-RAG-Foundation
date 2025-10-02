#!/usr/bin/env python3
"""
🔍 Symbol Index for AgentDev
============================

Tạo chỉ mục symbol để biết symbol tồn tại ở đâu trong codebase.
"""

import ast
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

@dataclass
class SymbolInfo:
    """Thông tin về một symbol"""
    name: str
    module_path: str
    symbol_type: str  # 'function', 'class', 'variable'
    line_number: int
    is_exported: bool = True  # Có thể import được không

class SymbolIndex:
    """Chỉ mục symbol trong codebase"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.symbols: Dict[str, List[SymbolInfo]] = {}
        self.cache_file = self.project_root / "agentdev_symbol_cache.json"
        self.excluded_dirs = {'.git', '.venv', 'venv', 'env', 'artifacts', 'reports', '__pycache__', 'node_modules', 'dist', 'build'}

    def build_index(self, force_rebuild: bool = False) -> Dict[str, int]:
        """Xây dựng chỉ mục symbol"""
        stats = {"files_scanned": 0, "symbols_found": 0, "modules_indexed": 0}

        # Load cache nếu có
        if not force_rebuild and self.cache_file.exists():
            try:
                self._load_cache()
                logger.info("Loaded symbol cache with %d symbols", len(self.symbols))
                return stats
            except Exception as e:
                logger.warning("Failed to load cache: %s", e)

        # Scan stillme_core/ directory (correct path)
        stillme_dir = self.project_root / "stillme_core"
        if not stillme_dir.exists():
            logger.warning("stillme_core directory not found")
            return stats

        for py_file in stillme_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                symbols = self._extract_symbols_from_file(py_file)
                self._add_symbols_to_index(symbols, py_file)
                stats["files_scanned"] += 1
                stats["symbols_found"] += len(symbols)

            except Exception as e:
                logger.debug("Error scanning %s: %s", py_file, e)

        stats["modules_indexed"] = len(self.symbols)
        self._save_cache()

        logger.info("Built symbol index: %d files, %d symbols, %d modules",
                   stats["files_scanned"], stats["symbols_found"], stats["modules_indexed"])
        return stats

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        # Skip if in excluded directory
        for part in file_path.parts:
            if part in self.excluded_dirs:
                return True
        return False

    def _extract_symbols_from_file(self, file_path: Path) -> List[SymbolInfo]:
        """Extract symbols from a Python file using AST"""
        symbols = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(SymbolInfo(
                        name=node.name,
                        module_path=str(file_path.relative_to(self.project_root)).replace('\\', '/'),
                        symbol_type='function',
                        line_number=node.lineno,
                        is_exported=not node.name.startswith('_')
                    ))
                elif isinstance(node, ast.ClassDef):
                    symbols.append(SymbolInfo(
                        name=node.name,
                        module_path=str(file_path.relative_to(self.project_root)).replace('\\', '/'),
                        symbol_type='class',
                        line_number=node.lineno,
                        is_exported=not node.name.startswith('_')
                    ))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append(SymbolInfo(
                                name=target.id,
                                module_path=str(file_path.relative_to(self.project_root)).replace('\\', '/'),
                                symbol_type='variable',
                                line_number=node.lineno,
                                is_exported=not target.id.startswith('_')
                            ))

        except Exception as e:
            logger.debug("Error parsing %s: %s", file_path, e)

        return symbols

    def _add_symbols_to_index(self, symbols: List[SymbolInfo], file_path: Path):
        """Add symbols to index"""
        for symbol in symbols:
            if symbol.name not in self.symbols:
                self.symbols[symbol.name] = []
            self.symbols[symbol.name].append(symbol)

    def find_symbol(self, symbol_name: str) -> List[SymbolInfo]:
        """Tìm symbol trong index"""
        return self.symbols.get(symbol_name, [])

    def get_import_for_symbol(self, symbol_name: str, target_file: str) -> Optional[str]:
        """Tạo import statement cho symbol"""
        symbols = self.find_symbol(symbol_name)
        if not symbols:
            return None

        # Tìm symbol phù hợp nhất (exported, trong stillme_ai)
        best_symbol = None
        for symbol in symbols:
            if symbol.is_exported and 'stillme_ai' in symbol.module_path:
                best_symbol = symbol
                break

        if not best_symbol:
            return None

        # Tạo import statement
        module_path = best_symbol.module_path.replace('/', '.').replace('\\', '.')
        if module_path.endswith('.py'):
            module_path = module_path[:-3]

        if best_symbol.symbol_type == 'class':
            return f"from {module_path} import {symbol_name}"
        else:
            return f"from {module_path} import {symbol_name}"

    def _load_cache(self):
        """Load symbol cache from file"""
        with open(self.cache_file, encoding='utf-8') as f:
            data = json.load(f)

        self.symbols = {}
        for symbol_name, symbol_list in data.items():
            self.symbols[symbol_name] = [
                SymbolInfo(**symbol_data) for symbol_data in symbol_list
            ]

    def _save_cache(self):
        """Save symbol cache to file"""
        data = {}
        for symbol_name, symbol_list in self.symbols.items():
            data[symbol_name] = [asdict(symbol) for symbol in symbol_list]

        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# Test
if __name__ == "__main__":
    index = SymbolIndex(".")
    stats = index.build_index()
    print(f"Index built: {stats}")

    # Test find symbol
    symbols = index.find_symbol("Path")
    print(f"Found Path: {symbols}")

    import_stmt = index.get_import_for_symbol("Path", "test.py")
    print(f"Import for Path: {import_stmt}")
