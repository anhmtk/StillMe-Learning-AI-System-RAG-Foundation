#!/usr/bin/env python3
"""
AST Hash Analysis Tool
Phân tích AST hash để phát hiện code trùng lặp
"""

import ast
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ASTHashAnalyzer:
    """Analyzer for AST-based duplicate detection"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.ast_hashes = {}
        self.duplicate_groups = {}
        self.excludes = [
            ".git",
            ".github",
            ".venv",
            "venv",
            "env",
            "site-packages",
            "dist",
            "build",
            "node_modules",
            "artifacts",
            "reports",
            "htmlcov",
            "__pycache__",
            ".egg-info",
        ]

    def _should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded"""
        path_str = str(path)
        return any(exclude in path_str for exclude in self.excludes)

    def _get_file_loc(self, file_path: Path) -> int:
        """Get lines of code for a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return len(f.readlines())
        except:
            return 0

    def _is_meaningful_file(self, file_path: Path) -> bool:
        """Check if file is meaningful (not just docstring/license)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Skip files that are mostly docstring/license
            if len(content) < 200:  # Less than 200 chars
                return False

            # Skip files that are mostly comments/docstrings
            lines = content.split("\n")
            code_lines = [
                line
                for line in lines
                if line.strip()
                and not line.strip().startswith("#")
                and not line.strip().startswith('"""')
                and not line.strip().startswith("'''")
            ]

            if len(code_lines) < 5:  # Less than 5 lines of actual code
                return False

            return True
        except:
            return False

    def analyze_ast_duplicates(self) -> Dict[str, Any]:
        """Analyze AST duplicates with noise filtering"""
        logger.info("Starting AST duplicate analysis with noise filtering...")

        # Find all Python files
        python_files = list(self.repo_root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        analyzed_count = 0
        for py_file in python_files:
            # Skip if in excluded directory
            if self._should_exclude_path(py_file):
                continue

            # Skip __init__.py files (usually just imports)
            if py_file.name == "__init__.py":
                continue

            # Skip small files (< 25 LOC)
            if self._get_file_loc(py_file) < 25:
                continue

            # Skip non-meaningful files
            if not self._is_meaningful_file(py_file):
                continue

            try:
                ast_hash = self._get_ast_hash(py_file)
                if ast_hash:
                    if ast_hash not in self.ast_hashes:
                        self.ast_hashes[ast_hash] = []
                    self.ast_hashes[ast_hash].append(
                        str(py_file.relative_to(self.repo_root))
                    )
                    analyzed_count += 1

            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
                continue

        # Find duplicate groups with filtering
        duplicate_groups = []
        for ast_hash, files in self.ast_hashes.items():
            if len(files) >= 2:  # At least 2 files
                # Calculate average LOC
                total_loc = sum(self._get_file_loc(self.repo_root / f) for f in files)
                avg_loc = total_loc / len(files)

                # Only include groups with average LOC >= 50
                if avg_loc >= 50:
                    duplicate_groups.append(
                        {
                            "ast_hash": ast_hash,
                            "files": files,
                            "count": len(files),
                            "avg_loc": avg_loc,
                            "total_loc": total_loc,
                        }
                    )

        return {
            "status": "success",
            "total_files_found": len(python_files),
            "files_analyzed": analyzed_count,
            "unique_ast_hashes": len(self.ast_hashes),
            "duplicate_groups": duplicate_groups,
            "total_duplicates": len(duplicate_groups),
        }

    def _get_ast_hash(self, file_path: Path) -> str:
        """Get AST hash for a Python file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Normalize AST (remove comments, docstrings, etc.)
            normalized_tree = self._normalize_ast(tree)

            # Convert to string and hash
            ast_str = ast.dump(normalized_tree, indent=2)
            return hashlib.md5(ast_str.encode()).hexdigest()

        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            return None

    def _normalize_ast(self, tree: ast.AST) -> ast.AST:
        """Normalize AST by removing non-essential elements"""

        class ASTNormalizer(ast.NodeTransformer):
            def visit_Expr(self, node):
                # Remove docstrings and comments
                if isinstance(node.value, ast.Constant) and isinstance(
                    node.value.value, str
                ):
                    return None
                return node

            def visit_Constant(self, node):
                # Normalize string constants
                if isinstance(node.value, str):
                    return ast.Constant(value="", kind=node.kind)
                return node

        normalizer = ASTNormalizer()
        return normalizer.visit(tree)

    def save_results(
        self, results: Dict[str, Any], output_path: str = "artifacts/ast_dupes.json"
    ):
        """Save analysis results"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")


def main():
    """Main function"""
    logging.basicConfig(level=logging.INFO)

    analyzer = ASTHashAnalyzer()
    results = analyzer.analyze_ast_duplicates()

    if results["status"] == "success":
        analyzer.save_results(results)
        print("✅ AST duplicate analysis complete")
        print(f"📊 Files found: {results['total_files_found']}")
        print(f"📊 Files analyzed: {results['files_analyzed']}")
        print(f"🔍 Unique AST hashes: {results['unique_ast_hashes']}")
        print(f"🔄 Duplicate groups: {results['total_duplicates']}")
    else:
        print("❌ AST analysis failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
