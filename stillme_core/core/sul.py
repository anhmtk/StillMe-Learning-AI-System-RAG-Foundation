"""
System Understanding Layer (SUL) - Minimal implementation
Provides system map, risk scoring, and dependency analysis
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SUL")


@dataclass
class ModuleInfo:
    """Information about a module"""

    name: str
    file_path: str
    imports: List[str]
    exports: List[str]
    functions: List[str]
    classes: List[str]
    test_files: List[str]
    risk_score: float


class SystemUnderstandingLayer:
    """
    System Understanding Layer for StillMe
    Provides static analysis and risk scoring
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.stillme_core_path = self.repo_root / "stillme_core"
        self.modules_path = self.repo_root / "modules"
        self.tests_path = self.repo_root / "tests"
        self.modules: Dict[str, ModuleInfo] = {}

    def analyze_module(self, module_name: str) -> ModuleInfo:
        """Analyze a single module and return its information"""
        # Try stillme_core first, then modules
        module_path = self.stillme_core_path / f"{module_name}.py"
        if not module_path.exists():
            module_path = self.modules_path / f"{module_name}.py"

        if not module_path.exists():
            return ModuleInfo(
                name=module_name,
                file_path="",
                imports=[],
                exports=[],
                functions=[],
                classes=[],
                test_files=[],
                risk_score=0.0,
            )

        # Parse Python file
        with open(module_path, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {module_path}: {e}")
            return ModuleInfo(
                name=module_name,
                file_path=str(module_path),
                imports=[],
                exports=[],
                functions=[],
                classes=[],
                test_files=[],
                risk_score=1.0,  # High risk due to syntax error
            )

        imports = []
        exports = []
        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                if not node.name.startswith("_"):
                    exports.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                if not node.name.startswith("_"):
                    exports.append(node.name)

        # Find test files
        test_files = []
        if self.tests_path.exists():
            for test_file in self.tests_path.glob(f"test_{module_name}*.py"):
                test_files.append(str(test_file))

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            imports, exports, functions, classes, test_files
        )

        return ModuleInfo(
            name=module_name,
            file_path=str(module_path),
            imports=imports,
            exports=exports,
            functions=functions,
            classes=classes,
            test_files=test_files,
            risk_score=risk_score,
        )

    def _calculate_risk_score(
        self,
        imports: List[str],
        exports: List[str],
        functions: List[str],
        classes: List[str],
        test_files: List[str],
    ) -> float:
        """Calculate risk score for a module"""
        score = 0.0

        # Base score from complexity
        score += len(functions) * 0.1
        score += len(classes) * 0.2
        score += len(imports) * 0.05

        # Penalty for no tests
        if not test_files:
            score += 0.5

        # Bonus for having tests
        score -= len(test_files) * 0.1

        # Penalty for many external dependencies
        external_deps = [imp for imp in imports if not imp.startswith("stillme_core")]
        score += len(external_deps) * 0.1

        return max(0.0, min(1.0, score))

    def get_dependencies(self, module_name: str) -> Dict[str, Any]:
        """Get dependencies and risk score for a module"""
        module_info = self.analyze_module(module_name)

        # Find modules that depend on this one
        dependents = []
        for search_path in [self.stillme_core_path, self.modules_path]:
            if not search_path.exists():
                continue

            for other_module in search_path.glob("*.py"):
                if other_module.name == f"{module_name}.py":
                    continue

                other_name = other_module.stem
                other_info = self.analyze_module(other_name)

                # Check if this module imports from the target module
                import_patterns = [
                    f"stillme_core.{module_name}",
                    f"modules.{module_name}",
                    module_name,
                ]

                for pattern in import_patterns:
                    if pattern in other_info.imports:
                        dependents.append(
                            {
                                "module": other_name,
                                "file": str(other_module),
                                "risk_score": other_info.risk_score,
                            }
                        )
                        break

        return {
            "module": module_name,
            "risk_score": module_info.risk_score,
            "dependents": dependents,
            "test_files": module_info.test_files,
            "functions": module_info.functions,
            "classes": module_info.classes,
            "imports": module_info.imports,
        }

    def find_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Find where a symbol is defined and used"""
        results = {"symbol": symbol_name, "definitions": [], "usages": []}

        for search_path in [self.stillme_core_path, self.modules_path]:
            if not search_path.exists():
                continue

            for module_file in search_path.glob("*.py"):
                module_name = module_file.stem

                with open(module_file, encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if node.name == symbol_name:
                            results["definitions"].append(
                                {
                                    "module": module_name,
                                    "file": str(module_file),
                                    "type": type(node).__name__,
                                    "line": node.lineno,
                                }
                            )

                    elif isinstance(node, ast.Name):
                        if node.id == symbol_name:
                            results["usages"].append(
                                {
                                    "module": module_name,
                                    "file": str(module_file),
                                    "line": node.lineno,
                                }
                            )

        return results


# Global SUL instance
_sul_instance: Optional[SystemUnderstandingLayer] = None


def get_sul() -> SystemUnderstandingLayer:
    """Get global SUL instance"""
    global _sul_instance
    if _sul_instance is None:
        _sul_instance = SystemUnderstandingLayer()
    return _sul_instance
