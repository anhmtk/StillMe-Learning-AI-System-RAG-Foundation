#!/usr/bin/env python3
"""
Import Graph Analysis Tool
Phân tích import graph để xác định modules được sử dụng
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import logging

# Try to import grimp and networkx, fallback to basic analysis if not available
try:
    import grimp
    import networkx as nx

    HAS_GRIMP = True
except ImportError:
    HAS_GRIMP = False
    logging.warning("grimp/networkx not available, using basic analysis")

logger = logging.getLogger(__name__)


class ImportGraphAnalyzer:
    """Analyzer for import dependencies"""

    def __init__(self, repo_root: str = ".", roots: list = None):
        self.repo_root = Path(repo_root).resolve()
        self.roots = roots or self._detect_roots()
        self.import_graph = {}
        self.inbound_counts = {}
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

    def _detect_roots(self) -> list:
        """Detect root packages in repository"""
        roots = []
        for item in self.repo_root.iterdir():
            if item.is_dir() and item.name.startswith("stillme_"):
                roots.append(item.name)
        logger.info(f"Detected roots: {roots}")
        return roots

    def _should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded"""
        path_str = str(path)
        return any(exclude in path_str for exclude in self.excludes)

    def analyze_imports(self) -> Dict[str, Any]:
        """Analyze import dependencies"""
        logger.info(f"Starting import analysis for roots: {self.roots}")

        if HAS_GRIMP:
            return self._analyze_with_grimp()
        else:
            return self._analyze_basic()

    def _analyze_with_grimp(self) -> Dict[str, Any]:
        """Advanced analysis using grimp"""
        try:
            # Build import graph for stillme_core
            graph = grimp.build_graph("stillme_core")

            # Calculate inbound imports for each module
            inbound_counts = {}
            for module in graph.modules:
                inbound_count = len(graph.get_imports(module))
                inbound_counts[module] = inbound_count

            # Convert to required format
            result = []
            for module, count in inbound_counts.items():
                result.append({"module": module, "inbound_imports": count})

            return {
                "status": "success",
                "method": "grimp",
                "modules": result,
                "total_modules": len(result),
            }

        except Exception as e:
            logger.error(f"Grimp analysis failed: {e}")
            return self._analyze_basic()

    def _analyze_basic(self) -> Dict[str, Any]:
        """Basic analysis without external dependencies"""
        logger.info("Using basic import analysis...")

        result = []

        # Analyze each root package
        for root in self.roots:
            root_path = self.repo_root / root
            if not root_path.exists():
                logger.warning(f"Root directory not found: {root}")
                continue

            python_files = list(root_path.rglob("*.py"))
            logger.info(f"Found {len(python_files)} Python files in {root}")

            # Basic import counting
            for py_file in python_files:
                try:
                    # Skip excluded paths
                    if self._should_exclude_path(py_file):
                        continue

                    # Convert file path to module name
                    rel_path = py_file.relative_to(self.repo_root)
                    module_name = str(rel_path).replace(os.sep, ".").replace(".py", "")

                    # Count imports in file
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Simple import counting
                    import_count = content.count("import ") + content.count("from ")

                    # Special protection for __init__.py
                    if py_file.name == "__init__.py":
                        import_count = max(import_count, 1)

                    result.append(
                        {"module": module_name, "inbound_imports": import_count}
                    )

                except Exception as e:
                    logger.warning(f"Error analyzing {py_file}: {e}")
                    continue

        return {
            "status": "success",
            "method": "basic",
            "roots": self.roots,
            "modules": result,
            "total_modules": len(result),
        }

    def save_results(
        self,
        results: Dict[str, Any],
        output_path: str = "artifacts/import_inbound.json",
    ):
        """Save analysis results"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")


def main():
    """Main function"""
    logging.basicConfig(level=logging.INFO)

    analyzer = ImportGraphAnalyzer()
    results = analyzer.analyze_imports()

    if results["status"] == "success":
        analyzer.save_results(results)
        print(
            f"✅ Import analysis complete: {results['total_modules']} modules analyzed"
        )
        print(f"📊 Method used: {results['method']}")
    else:
        print(f"❌ Import analysis failed: {results.get('message', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
