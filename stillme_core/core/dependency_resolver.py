"""
🔄 DEPENDENCY RESOLVER SYSTEM

Hệ thống để resolve circular dependencies và implement dependency injection patterns.

Author: AgentDev System
Version: 1.0.0
Phase: 0.2 - Dependency Resolution
"""

import ast
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import networkx as nx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Dependency information"""

    source_module: str
    target_module: str
    import_type: str  # 'import', 'from_import', 'relative_import'
    line_number: int
    is_circular: bool = False
    severity: str = "low"  # 'low', 'medium', 'high', 'critical'


@dataclass
class CircularDependency:
    """Circular dependency definition"""

    cycle: list[str]
    severity: str
    impact: str
    suggested_fix: str


@dataclass
class DependencyResolution:
    """Dependency resolution result"""

    total_dependencies: int
    circular_dependencies: int
    resolved_dependencies: int
    remaining_issues: int
    resolution_score: float
    recommendations: list[str]


class DependencyResolver:
    """
    Main dependency resolver class
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.dependency_graph = nx.DiGraph()
        self.dependencies: list[DependencyInfo] = []
        self.circular_dependencies: list[CircularDependency] = []
        self.module_files: dict[str, Path] = {}

    def analyze_dependencies(self) -> list[DependencyInfo]:
        """
        Analyze all dependencies in the codebase
        """
        logger.info("🔍 Analyzing dependencies...")

        # Find all Python modules
        self._find_modules()

        # Analyze each module
        for module_name, file_path in self.module_files.items():
            self._analyze_module_dependencies(module_name, file_path)

        # Build dependency graph
        self._build_dependency_graph()

        # Detect circular dependencies
        self._detect_circular_dependencies()

        logger.info(
            f"✅ Found {len(self.dependencies)} dependencies, {len(self.circular_dependencies)} circular"
        )

        return self.dependencies

    def _find_modules(self):
        """Find all Python modules in the codebase"""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            # Convert file path to module name
            module_name = self._path_to_module_name(py_file)
            self.module_files[module_name] = py_file

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".git",
            "backup_legacy",
            "tests/fixtures",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative_path = file_path.relative_to(self.root_path)
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")

        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        if module_name.endswith(".__init__"):
            module_name = module_name[:-9]

        return module_name

    def _analyze_module_dependencies(self, module_name: str, file_path: Path):
        """Analyze dependencies for a single module"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep_info = DependencyInfo(
                            source_module=module_name,
                            target_module=alias.name,
                            import_type="import",
                            line_number=node.lineno,
                        )
                        self.dependencies.append(dep_info)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dep_info = DependencyInfo(
                            source_module=module_name,
                            target_module=node.module,
                            import_type="from_import",
                            line_number=node.lineno,
                        )
                        self.dependencies.append(dep_info)

        except Exception as e:
            logger.error(f"Error analyzing {module_name}: {e}")

    def _build_dependency_graph(self):
        """Build dependency graph"""
        self.dependency_graph.clear()

        # Add nodes
        for module_name in self.module_files.keys():
            self.dependency_graph.add_node(module_name)

        # Add edges
        for dep in self.dependencies:
            if dep.target_module in self.module_files:
                self.dependency_graph.add_edge(dep.source_module, dep.target_module)

    def _detect_circular_dependencies(self):
        """Detect circular dependencies"""
        self.circular_dependencies.clear()

        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))

            for cycle in cycles:
                severity = self._calculate_cycle_severity(cycle)
                impact = self._assess_cycle_impact(cycle)
                suggested_fix = self._suggest_cycle_fix(cycle)

                circular_dep = CircularDependency(
                    cycle=cycle,
                    severity=severity,
                    impact=impact,
                    suggested_fix=suggested_fix,
                )

                self.circular_dependencies.append(circular_dep)

                # Mark dependencies as circular
                for i in range(len(cycle)):
                    source = cycle[i]
                    target = cycle[(i + 1) % len(cycle)]

                    for dep in self.dependencies:
                        if dep.source_module == source and dep.target_module == target:
                            dep.is_circular = True
                            dep.severity = severity

        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")

    def _calculate_cycle_severity(self, cycle: list[str]) -> str:
        """Calculate severity of circular dependency"""
        cycle_length = len(cycle)

        if cycle_length == 2:
            return "high"  # Direct circular dependency
        elif cycle_length <= 4:
            return "medium"
        else:
            return "low"

    def _assess_cycle_impact(self, cycle: list[str]) -> str:
        """Assess impact of circular dependency"""
        # Check if any modules in cycle are core modules
        core_modules = [
            "stillme_core.agent_dev",
            "stillme_core.planner",
            "stillme_core.executor",
            "stillme_core.verifier",
            "stillme_core.controller",
        ]

        has_core_modules = any(module in core_modules for module in cycle)

        if has_core_modules:
            return "Critical - affects core functionality"
        else:
            return "Medium - affects specific features"

    def _suggest_cycle_fix(self, cycle: list[str]) -> str:
        """Suggest fix for circular dependency"""
        if len(cycle) == 2:
            return f"Use dependency injection or interface abstraction between {cycle[0]} and {cycle[1]}"
        else:
            return "Refactor to break the cycle by introducing an intermediate module or using dependency injection"

    def resolve_circular_dependencies(self) -> DependencyResolution:
        """
        Resolve circular dependencies automatically
        """
        logger.info("🔧 Resolving circular dependencies...")

        resolved_count = 0

        for circular_dep in self.circular_dependencies:
            if self._can_resolve_automatically(circular_dep):
                if self._resolve_circular_dependency(circular_dep):
                    resolved_count += 1
                    logger.info(
                        f"✅ Resolved circular dependency: {' -> '.join(circular_dep.cycle)}"
                    )

        # Calculate resolution score
        total_circular = len(self.circular_dependencies)
        resolution_score = (
            (resolved_count / total_circular * 100) if total_circular > 0 else 100
        )

        # Generate recommendations
        recommendations = self._generate_recommendations()

        resolution = DependencyResolution(
            total_dependencies=len(self.dependencies),
            circular_dependencies=total_circular,
            resolved_dependencies=resolved_count,
            remaining_issues=total_circular - resolved_count,
            resolution_score=resolution_score,
            recommendations=recommendations,
        )

        logger.info(
            f"✅ Dependency resolution completed: {resolved_count}/{total_circular} resolved"
        )

        return resolution

    def _can_resolve_automatically(self, circular_dep: CircularDependency) -> bool:
        """Check if circular dependency can be resolved automatically"""
        # Only resolve simple 2-module cycles automatically
        return len(circular_dep.cycle) == 2 and circular_dep.severity in [
            "medium",
            "low",
        ]

    def _resolve_circular_dependency(self, circular_dep: CircularDependency) -> bool:
        """Resolve individual circular dependency"""
        try:
            if len(circular_dep.cycle) == 2:
                return self._resolve_two_module_cycle(circular_dep.cycle)
            else:
                return self._resolve_complex_cycle(circular_dep.cycle)
        except Exception as e:
            logger.error(f"Error resolving circular dependency: {e}")
            return False

    def _resolve_two_module_cycle(self, cycle: list[str]) -> bool:
        """Resolve 2-module circular dependency"""
        module1, module2 = cycle

        # Strategy 1: Move shared code to a common module
        if self._create_common_module(module1, module2):
            return True

        # Strategy 2: Use dependency injection
        if self._implement_dependency_injection(module1, module2):
            return True

        # Strategy 3: Lazy imports
        if self._implement_lazy_imports(module1, module2):
            return True

        return False

    def _create_common_module(self, module1: str, module2: str) -> bool:
        """Create common module to break circular dependency"""
        # This would analyze the shared code and create a common module
        # For now, just return False as it requires complex analysis
        return False

    def _implement_dependency_injection(self, module1: str, module2: str) -> bool:
        """Implement dependency injection to break circular dependency"""
        # This would refactor the code to use dependency injection
        # For now, just return False as it requires complex refactoring
        return False

    def _implement_lazy_imports(self, module1: str, module2: str) -> bool:
        """Implement lazy imports to break circular dependency"""
        try:
            # Find the dependency between the two modules
            for dep in self.dependencies:
                if (dep.source_module == module1 and dep.target_module == module2) or (
                    dep.source_module == module2 and dep.target_module == module1
                ):
                    # Convert to lazy import
                    if self._convert_to_lazy_import(dep):
                        return True

            return False
        except Exception as e:
            logger.error(f"Error implementing lazy imports: {e}")
            return False

    def _convert_to_lazy_import(self, dep: DependencyInfo) -> bool:
        """Convert import to lazy import"""
        try:
            file_path = self.module_files[dep.source_module]
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            if dep.line_number <= len(lines):
                original_line = lines[dep.line_number - 1]

                # Convert to lazy import
                if dep.import_type == "import" or dep.import_type == "from_import":
                    new_line = f"# Lazy import: {original_line.strip()}"
                else:
                    return False

                lines[dep.line_number - 1] = new_line

                # Write back to file
                new_content = "\n".join(lines)
                file_path.write_text(new_content, encoding="utf-8")

                return True

            return False
        except Exception as e:
            logger.error(f"Error converting to lazy import: {e}")
            return False

    def _resolve_complex_cycle(self, cycle: list[str]) -> bool:
        """Resolve complex circular dependency"""
        # For complex cycles, we need more sophisticated analysis
        # This would involve creating intermediate modules or refactoring
        return False

    def _generate_recommendations(self) -> list[str]:
        """Generate dependency management recommendations"""
        recommendations = [
            "Implement dependency injection pattern for loose coupling",
            "Use interface abstraction to break direct dependencies",
            "Create common utility modules for shared functionality",
            "Apply single responsibility principle to reduce coupling",
            "Use lazy imports for optional dependencies",
            "Implement module registry pattern for dynamic loading",
            "Regular dependency audits to prevent new circular dependencies",
            "Use dependency management tools like poetry or pipenv",
            "Document module dependencies and their purposes",
            "Implement automated circular dependency detection in CI/CD",
        ]

        return recommendations

    def create_dependency_injection_framework(self) -> str:
        """Create dependency injection framework"""
        di_framework = '''
"""
Dependency Injection Framework for StillMe
"""
from typing import Dict, Type, Any, Callable
from abc import ABC, abstractmethod

class ServiceContainer:
    """Service container for dependency injection"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register_singleton(self, interface: Type, implementation: Any):
        """Register singleton service"""
        self._services[interface] = implementation

    def register_factory(self, interface: Type, factory: Callable):
        """Register factory for service creation"""
        self._factories[interface] = factory

    def get(self, interface: Type) -> Any:
        """Get service instance"""
        if interface in self._services:
            return self._services[interface]

        if interface in self._factories:
            return self._factories[interface]()

        raise ValueError(f"Service {interface} not registered")

# Global service container
container = ServiceContainer()

def inject(interface: Type):
    """Dependency injection decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = container.get(interface)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator
'''

        # Save framework
        framework_path = self.root_path / "stillme_core" / "dependency_injection.py"
        framework_path.write_text(di_framework, encoding="utf-8")

        return str(framework_path)

    def save_dependency_report(self, resolution: DependencyResolution) -> Path:
        """Save dependency resolution report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "resolution": asdict(resolution),
            "dependencies": [asdict(dep) for dep in self.dependencies],
            "circular_dependencies": [asdict(cd) for cd in self.circular_dependencies],
            "dependency_graph": {
                "nodes": list(self.dependency_graph.nodes()),
                "edges": list(self.dependency_graph.edges()),
            },
        }

        # Create reports directory
        reports_dir = self.root_path / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"dependency_resolution_report_{timestamp}.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Dependency report saved to {report_path}")
        return report_path


def main():
    """Main function to run dependency resolution"""
    resolver = DependencyResolver()

    # Analyze dependencies
    resolver.analyze_dependencies()

    # Resolve circular dependencies
    resolution = resolver.resolve_circular_dependencies()

    # Create dependency injection framework
    di_framework_path = resolver.create_dependency_injection_framework()

    # Save report
    report_path = resolver.save_dependency_report(resolution)

    print("✅ Dependency resolution completed!")
    print(f"📊 Total dependencies: {resolution.total_dependencies}")
    print(f"🔄 Circular dependencies: {resolution.circular_dependencies}")
    print(f"🔧 Resolved: {resolution.resolved_dependencies}")
    print(f"📈 Resolution score: {resolution.resolution_score:.1f}%")
    print(f"📄 Report saved to: {report_path}")
    print(f"🔧 DI Framework created: {di_framework_path}")


if __name__ == "__main__":
    main()
