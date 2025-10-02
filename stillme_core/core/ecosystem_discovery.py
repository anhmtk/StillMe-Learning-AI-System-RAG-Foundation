"""
🔍 STILLME ECOSYSTEM DISCOVERY & MAPPING MODULE

Module này thực hiện việc discovery và mapping toàn bộ StillMe ecosystem,
bao gồm 16 core modules, dependencies, và health assessment.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Internal Integration Foundation
"""

import ast
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import networkx as nx
import psutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Thông tin chi tiết về một module"""

    name: str
    path: str
    type: str  # 'core', 'extension', 'utility'
    size_bytes: int
    line_count: int
    function_count: int
    class_count: int
    import_count: int
    dependencies: list[str]
    dependents: list[str]
    last_modified: datetime
    health_score: float
    performance_metrics: dict[str, Any]
    security_issues: list[str]
    documentation_quality: float


@dataclass
class DependencyEdge:
    """Edge trong dependency graph"""

    source: str
    target: str
    type: str  # 'import', 'inheritance', 'composition'
    strength: float  # 0.0 to 1.0
    critical: bool


@dataclass
class EcosystemHealth:
    """Tổng quan health của ecosystem"""

    overall_score: float
    critical_issues: list[str]
    performance_bottlenecks: list[str]
    security_vulnerabilities: list[str]
    circular_dependencies: list[list[str]]
    unused_modules: list[str]
    recommendations: list[str]


class StillMeEcosystemDiscovery:
    """
    Main class để discovery và mapping StillMe ecosystem
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.modules: dict[str, ModuleInfo] = {}
        self.dependency_graph = nx.DiGraph()
        self.health_metrics = {}
        self.monitoring_active = False
        self.monitoring_thread = None

        # Core module patterns
        self.core_module_patterns = [
            "conversational_core",
            "layered_memory",
            "secure_memory",
            "self_improvement",
            "daily_learning",
            "ethical_core",
            "emotionsense",
            "token_optimizer",
            "market_intel",
            "prediction_engine",
            "automated_scheduler",
            "communication_style",
            "content_integrity",
            "persona_morph",
            "input_sketcher",
            "telemetry",
        ]

        # Performance monitoring
        self.performance_baseline = {}
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "response_time": 1000.0,  # ms
            "error_rate": 5.0,  # percentage
        }

    def discover_all_modules(self) -> dict[str, ModuleInfo]:
        """
        Systematic scan toàn bộ codebase để identify modules
        """
        logger.info("🔍 Starting systematic module discovery...")

        discovered_modules = {}

        # Scan modules directory
        modules_path = self.root_path / "modules"
        if modules_path.exists():
            discovered_modules.update(self._scan_directory(modules_path, "core"))

        # Scan stillme_core directory
        stillme_core_path = self.root_path / "stillme_core"
        if stillme_core_path.exists():
            discovered_modules.update(self._scan_directory(stillme_core_path, "core"))

        # Scan adapters directory
        adapters_path = self.root_path / "adapters"
        if adapters_path.exists():
            discovered_modules.update(self._scan_directory(adapters_path, "extension"))

        # Scan clients directory
        clients_path = self.root_path / "clients"
        if clients_path.exists():
            discovered_modules.update(self._scan_directory(clients_path, "extension"))

        self.modules = discovered_modules
        logger.info(f"✅ Discovered {len(discovered_modules)} modules")

        return discovered_modules

    def _scan_directory(
        self, directory: Path, module_type: str
    ) -> dict[str, ModuleInfo]:
        """Scan một directory để tìm modules"""
        modules = {}

        for file_path in directory.rglob("*.py"):
            if file_path.name == "__init__.py":
                continue

            try:
                module_info = self._analyze_module(file_path, module_type)
                if module_info:
                    modules[module_info.name] = module_info
            except Exception as e:
                logger.warning(f"⚠️ Failed to analyze {file_path}: {e}")

        return modules

    def _analyze_module(
        self, file_path: Path, module_type: str
    ) -> Optional[ModuleInfo]:
        """Phân tích chi tiết một module"""
        try:
            # Basic file info
            stat = file_path.stat()
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Parse AST
            tree = ast.parse(content)

            # Count elements
            function_count = len(
                [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            )
            class_count = len(
                [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            )

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            # Calculate health score
            health_score = self._calculate_health_score(
                content, function_count, class_count, len(imports)
            )

            # Performance metrics
            performance_metrics = self._get_performance_metrics(file_path)

            # Security analysis
            security_issues = self._analyze_security(content)

            # Documentation quality
            doc_quality = self._assess_documentation_quality(content)

            module_info = ModuleInfo(
                name=file_path.stem,
                path=str(file_path),
                type=module_type,
                size_bytes=stat.st_size,
                line_count=len(lines),
                function_count=function_count,
                class_count=class_count,
                import_count=len(imports),
                dependencies=imports,
                dependents=[],  # Will be filled later
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                health_score=health_score,
                performance_metrics=performance_metrics,
                security_issues=security_issues,
                documentation_quality=doc_quality,
            )

            return module_info

        except Exception as e:
            logger.error(f"❌ Error analyzing {file_path}: {e}")
            return None

    def _calculate_health_score(
        self, content: str, function_count: int, class_count: int, import_count: int
    ) -> float:
        """Tính health score cho module"""
        score = 100.0

        # Penalize for very large files
        if len(content) > 10000:
            score -= 10

        # Penalize for too many functions (complexity)
        if function_count > 50:
            score -= 15

        # Penalize for too many imports (coupling)
        if import_count > 20:
            score -= 10

        # Bonus for good documentation
        if "def " in content and '"""' in content:
            score += 5

        # Bonus for type hints
        if "->" in content or ": " in content:
            score += 5

        return max(0.0, min(100.0, score))

    def _get_performance_metrics(self, file_path: Path) -> dict[str, Any]:
        """Lấy performance metrics cho module"""
        try:
            # Try to import and measure
            start_time = time.time()

            # This is a simplified version - in real implementation,
            # we would actually import and measure
            import_time = time.time() - start_time

            return {
                "import_time_ms": import_time * 1000,
                "memory_usage_kb": 0,  # Would need actual measurement
                "cpu_usage_percent": 0,  # Would need actual measurement
                "last_accessed": datetime.now().isoformat(),
            }
        except Exception:
            return {
                "import_time_ms": 0,
                "memory_usage_kb": 0,
                "cpu_usage_percent": 0,
                "last_accessed": datetime.now().isoformat(),
            }

    def _analyze_security(self, content: str) -> list[str]:
        """Phân tích security issues trong code"""
        issues = []

        # Check for hardcoded secrets
        if "password" in content.lower() and "=" in content:
            issues.append("Potential hardcoded password")

        if "api_key" in content.lower() and "=" in content:
            issues.append("Potential hardcoded API key")

        # Check for dangerous functions
        dangerous_functions = ["eval", "exec", "os.system", "subprocess.call"]
        for func in dangerous_functions:
            if func in content:
                issues.append(f"Use of potentially dangerous function: {func}")

        # Check for SQL injection patterns
        if "sql" in content.lower() and "%" in content:
            issues.append("Potential SQL injection vulnerability")

        return issues

    def _assess_documentation_quality(self, content: str) -> float:
        """Đánh giá chất lượng documentation"""
        score = 0.0

        # Check for module docstring
        if '"""' in content[:200]:
            score += 20

        # Check for function docstrings
        function_docs = content.count("def ") * 0.1
        score += min(function_docs, 30)

        # Check for comments
        comment_lines = content.count("#")
        total_lines = len(content.split("\n"))
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            score += min(comment_ratio * 50, 30)

        # Check for type hints
        if "->" in content or ": " in content:
            score += 20

        return min(score, 100.0)

    def build_dependency_graph(self) -> nx.DiGraph:
        """
        Xây dựng directed dependency graph
        """
        logger.info("🔗 Building dependency graph...")

        self.dependency_graph.clear()

        # Add nodes
        for module_name, module_info in self.modules.items():
            self.dependency_graph.add_node(module_name, **asdict(module_info))

        # Add edges based on imports
        for module_name, module_info in self.modules.items():
            for dep in module_info.dependencies:
                # Try to find matching module
                matching_module = self._find_matching_module(dep)
                if matching_module:
                    self.dependency_graph.add_edge(module_name, matching_module)
                    # Update dependents
                    if matching_module in self.modules:
                        self.modules[matching_module].dependents.append(module_name)

        logger.info(
            f"✅ Dependency graph built with {self.dependency_graph.number_of_nodes()} nodes and {self.dependency_graph.number_of_edges()} edges"
        )

        return self.dependency_graph

    def _find_matching_module(self, import_name: str) -> Optional[str]:
        """Tìm module matching với import name"""
        # Direct match
        if import_name in self.modules:
            return import_name

        # Partial match
        for module_name in self.modules.keys():
            if import_name in module_name or module_name in import_name:
                return module_name

        return None

    def analyze_circular_dependencies(self) -> list[list[str]]:
        """Phát hiện circular dependencies"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            logger.info(f"🔍 Found {len(cycles)} circular dependencies")
            return cycles
        except Exception as e:
            logger.error(f"❌ Error analyzing circular dependencies: {e}")
            return []

    def calculate_complexity_metrics(self) -> dict[str, Any]:
        """Tính toán complexity metrics"""
        metrics = {
            "total_modules": len(self.modules),
            "total_dependencies": self.dependency_graph.number_of_edges(),
            "average_dependencies_per_module": 0,
            "most_connected_module": None,
            "least_connected_module": None,
            "graph_density": 0,
            "centrality_measures": {},
        }

        if self.modules:
            # Average dependencies
            total_deps = sum(
                len(module.dependencies) for module in self.modules.values()
            )
            metrics["average_dependencies_per_module"] = total_deps / len(self.modules)

            # Most/least connected
            if self.dependency_graph.number_of_nodes() > 0:
                degree_centrality = nx.degree_centrality(self.dependency_graph)
                # Fix type issues with max/min functions
                if degree_centrality:
                    metrics["most_connected_module"] = max(
                        degree_centrality.keys(), key=lambda x: degree_centrality[x]
                    )
                    metrics["least_connected_module"] = min(
                        degree_centrality.keys(), key=lambda x: degree_centrality[x]
                    )
                else:
                    metrics["most_connected_module"] = None
                    metrics["least_connected_module"] = None
                metrics["graph_density"] = nx.density(self.dependency_graph)
                metrics["centrality_measures"] = degree_centrality

        return metrics

    def start_real_time_monitoring(self):
        """Bắt đầu real-time monitoring"""
        if self.monitoring_active:
            logger.warning("⚠️ Monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("📊 Real-time monitoring started")

    def stop_real_time_monitoring(self):
        """Dừng real-time monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("📊 Real-time monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                # Update health metrics
                self.health_metrics.update(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_usage": cpu_percent,
                        "memory_usage": memory.percent,
                        "memory_available_gb": memory.available / (1024**3),
                        "active_modules": len(self.modules),
                    }
                )

                # Check for alerts
                self._check_alerts()

                time.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error

    def _check_alerts(self):
        """Kiểm tra và trigger alerts"""
        alerts = []

        if self.health_metrics.get("cpu_usage", 0) > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"High CPU usage: {self.health_metrics['cpu_usage']:.1f}%")

        if (
            self.health_metrics.get("memory_usage", 0)
            > self.alert_thresholds["memory_usage"]
        ):
            alerts.append(
                f"High memory usage: {self.health_metrics['memory_usage']:.1f}%"
            )

        if alerts:
            logger.warning(f"🚨 ALERTS: {'; '.join(alerts)}")

    def generate_ecosystem_report(self) -> dict[str, Any]:
        """Tạo comprehensive ecosystem report"""
        logger.info("📊 Generating ecosystem report...")

        # Calculate overall health
        health_scores = [module.health_score for module in self.modules.values()]
        overall_health = sum(health_scores) / len(health_scores) if health_scores else 0

        # Find critical issues
        critical_issues = []
        for module in self.modules.values():
            if module.health_score < 50:
                critical_issues.append(
                    f"Module {module.name} has low health score: {module.health_score:.1f}"
                )
            critical_issues.extend(module.security_issues)

        # Performance bottlenecks
        performance_bottlenecks = []
        for module in self.modules.values():
            if module.performance_metrics.get("import_time_ms", 0) > 100:
                performance_bottlenecks.append(
                    f"Module {module.name} has slow import time: {module.performance_metrics['import_time_ms']:.1f}ms"
                )

        # Circular dependencies
        circular_deps = self.analyze_circular_dependencies()

        # Complexity metrics
        complexity_metrics = self.calculate_complexity_metrics()

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": overall_health,
            "total_modules": len(self.modules),
            "core_modules_found": len(
                [m for m in self.modules.values() if m.type == "core"]
            ),
            "extension_modules": len(
                [m for m in self.modules.values() if m.type == "extension"]
            ),
            "critical_issues": critical_issues,
            "performance_bottlenecks": performance_bottlenecks,
            "circular_dependencies": circular_deps,
            "complexity_metrics": complexity_metrics,
            "health_metrics": self.health_metrics,
            "module_details": {
                name: asdict(module) for name, module in self.modules.items()
            },
            "recommendations": self._generate_recommendations(),
        }

        logger.info("✅ Ecosystem report generated")
        return report

    def _generate_recommendations(self) -> list[str]:
        """Tạo recommendations dựa trên analysis"""
        recommendations = []

        # Health recommendations
        low_health_modules = [m for m in self.modules.values() if m.health_score < 70]
        if low_health_modules:
            recommendations.append(
                f"Improve health of {len(low_health_modules)} modules with low health scores"
            )

        # Security recommendations
        modules_with_security_issues = [
            m for m in self.modules.values() if m.security_issues
        ]
        if modules_with_security_issues:
            recommendations.append(
                f"Address security issues in {len(modules_with_security_issues)} modules"
            )

        # Performance recommendations
        slow_modules = [
            m
            for m in self.modules.values()
            if m.performance_metrics.get("import_time_ms", 0) > 50
        ]
        if slow_modules:
            recommendations.append(
                f"Optimize performance of {len(slow_modules)} slow modules"
            )

        # Documentation recommendations
        poorly_documented = [
            m for m in self.modules.values() if m.documentation_quality < 50
        ]
        if poorly_documented:
            recommendations.append(
                f"Improve documentation for {len(poorly_documented)} modules"
            )

        return recommendations

    def save_report(self, report: dict[str, Any], filename: Optional[str] = None):
        """Lưu report ra file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ecosystem_report_{timestamp}.json"

        filepath = self.root_path / "reports" / filename
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Report saved to {filepath}")
        return filepath


def main():
    """Main function để test module"""
    discovery = StillMeEcosystemDiscovery()

    # Discover modules
    discovery.discover_all_modules()

    # Build dependency graph
    discovery.build_dependency_graph()

    # Generate report
    report = discovery.generate_ecosystem_report()

    # Save report
    discovery.save_report(report)

    # Start monitoring
    discovery.start_real_time_monitoring()

    try:
        # Keep monitoring for a while
        time.sleep(60)
    finally:
        discovery.stop_real_time_monitoring()

    print("✅ Ecosystem discovery completed!")


if __name__ == "__main__":
    main()
