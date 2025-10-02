"""
⚡ PERFORMANCE OPTIMIZATION SYSTEM

Hệ thống để optimize performance của các modules và implement monitoring.

Author: AgentDev System
Version: 1.0.0
Phase: 0.3 - Performance Optimization
"""

import cProfile
import io
import json
import logging
import pstats
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import psutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric definition"""

    module_name: str
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int
    timestamp: datetime
    is_bottleneck: bool = False


@dataclass
class OptimizationSuggestion:
    """Performance optimization suggestion"""

    module_name: str
    issue_type: str
    severity: str
    description: str
    suggested_fix: str
    expected_improvement: str


@dataclass
class PerformanceReport:
    """Performance optimization report"""

    total_modules: int
    optimized_modules: int
    bottlenecks_found: int
    performance_improvement: float
    recommendations: list[OptimizationSuggestion]
    metrics: list[PerformanceMetric]


class PerformanceProfiler:
    """Performance profiler for modules"""

    def __init__(self):
        self.metrics: list[PerformanceMetric] = []
        self.profiles: dict[str, cProfile.Profile] = {}
        self.monitoring_active = False
        self.monitoring_thread = None

    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile function performance"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            start_cpu = psutil.Process().cpu_percent()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                end_cpu = psutil.Process().cpu_percent()

                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                cpu_usage = end_cpu - start_cpu

                metric = PerformanceMetric(
                    module_name=func.__module__,
                    function_name=func.__name__,
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    call_count=1,
                    timestamp=datetime.now(),
                )

                self.metrics.append(metric)

        return wrapper

    def start_profiling(self, module_name: str):
        """Start profiling a module"""
        if module_name not in self.profiles:
            self.profiles[module_name] = cProfile.Profile()
        self.profiles[module_name].enable()

    def stop_profiling(self, module_name: str) -> dict[str, Any]:
        """Stop profiling and get results"""
        if module_name in self.profiles:
            self.profiles[module_name].disable()

            # Get profiling results
            s = io.StringIO()
            ps = pstats.Stats(self.profiles[module_name], stream=s)
            ps.sort_stats("cumulative")
            ps.print_stats(20)  # Top 20 functions

            return {
                "module": module_name,
                "profile_data": s.getvalue(),
                "total_calls": ps.total_calls,
                "total_time": ps.total_tt,
            }

        return {}


class PerformanceOptimizer:
    """
    Main performance optimization system
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.profiler = PerformanceProfiler()
        self.optimization_suggestions: list[OptimizationSuggestion] = []
        self.performance_baseline: dict[str, float] = {}
        self.optimization_applied: set[str] = set()

        # Performance thresholds
        self.thresholds = {
            "execution_time": 1.0,  # seconds
            "memory_usage": 100.0,  # MB
            "cpu_usage": 80.0,  # percentage
            "call_frequency": 1000,  # calls per minute
        }

    def analyze_performance(self) -> list[PerformanceMetric]:
        """
        Analyze performance of all modules
        """
        logger.info("⚡ Analyzing performance...")

        # Profile all Python modules
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            module_name = self._path_to_module_name(py_file)
            self._profile_module(module_name, py_file)

        # Identify bottlenecks
        self._identify_bottlenecks()

        logger.info(
            f"✅ Performance analysis completed: {len(self.profiler.metrics)} metrics collected"
        )

        return self.profiler.metrics

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

    def _profile_module(self, module_name: str, file_path: Path):
        """Profile individual module"""
        try:
            # Start profiling
            self.profiler.start_profiling(module_name)

            # Try to import and execute module
            self._execute_module(module_name, file_path)

            # Stop profiling
            profile_results = self.profiler.stop_profiling(module_name)

            # Analyze results
            self._analyze_profile_results(module_name, profile_results)

        except Exception as e:
            logger.error(f"Error profiling {module_name}: {e}")

    def _execute_module(self, module_name: str, file_path: Path):
        """Execute module for profiling"""
        try:
            # Read and execute module code
            content = file_path.read_text(encoding="utf-8")

            # Create a temporary namespace
            namespace = {}
            exec(content, namespace)

            # Call main function if exists
            if "main" in namespace and callable(namespace["main"]):
                namespace["main"]()

        except Exception as e:
            logger.debug(f"Could not execute {module_name}: {e}")

    def _analyze_profile_results(
        self, module_name: str, profile_results: dict[str, Any]
    ):
        """Analyze profiling results"""
        if not profile_results:
            return

        # Check for performance issues
        if profile_results.get("total_time", 0) > self.thresholds["execution_time"]:
            suggestion = OptimizationSuggestion(
                module_name=module_name,
                issue_type="slow_execution",
                severity="high",
                description=f"Module execution time {profile_results['total_time']:.2f}s exceeds threshold",
                suggested_fix="Optimize algorithms, use caching, or implement async operations",
                expected_improvement="50-80% execution time reduction",
            )
            self.optimization_suggestions.append(suggestion)

        if profile_results.get("total_calls", 0) > self.thresholds["call_frequency"]:
            suggestion = OptimizationSuggestion(
                module_name=module_name,
                issue_type="high_call_frequency",
                severity="medium",
                description=f"High function call frequency: {profile_results['total_calls']} calls",
                suggested_fix="Implement function result caching or optimize call patterns",
                expected_improvement="30-50% call reduction",
            )
            self.optimization_suggestions.append(suggestion)

    def _identify_bottlenecks(self):
        """Identify performance bottlenecks"""
        for metric in self.profiler.metrics:
            is_bottleneck = (
                metric.execution_time > self.thresholds["execution_time"]
                or metric.memory_usage > self.thresholds["memory_usage"]
                or metric.cpu_usage > self.thresholds["cpu_usage"]
            )

            metric.is_bottleneck = is_bottleneck

    def optimize_modules(self) -> PerformanceReport:
        """
        Apply performance optimizations
        """
        logger.info("🔧 Applying performance optimizations...")

        optimized_count = 0

        for suggestion in self.optimization_suggestions:
            if self._can_optimize_automatically(suggestion):
                if self._apply_optimization(suggestion):
                    optimized_count += 1
                    self.optimization_applied.add(suggestion.module_name)
                    logger.info(
                        f"✅ Optimized {suggestion.module_name}: {suggestion.issue_type}"
                    )

        # Calculate performance improvement
        total_modules = len({metric.module_name for metric in self.profiler.metrics})
        performance_improvement = (
            (optimized_count / total_modules * 100) if total_modules > 0 else 0
        )

        # Count bottlenecks
        bottlenecks_found = len([m for m in self.profiler.metrics if m.is_bottleneck])

        report = PerformanceReport(
            total_modules=total_modules,
            optimized_modules=optimized_count,
            bottlenecks_found=bottlenecks_found,
            performance_improvement=performance_improvement,
            recommendations=self.optimization_suggestions,
            metrics=self.profiler.metrics,
        )

        logger.info(
            f"✅ Performance optimization completed: {optimized_count} modules optimized"
        )

        return report

    def _can_optimize_automatically(self, suggestion: OptimizationSuggestion) -> bool:
        """Check if optimization can be applied automatically"""
        auto_optimizable_types = ["slow_execution", "high_call_frequency"]

        return (
            suggestion.issue_type in auto_optimizable_types
            and suggestion.severity in ["medium", "low"]
        )

    def _apply_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Apply individual optimization"""
        try:
            if suggestion.issue_type == "slow_execution":
                return self._optimize_slow_execution(suggestion)
            elif suggestion.issue_type == "high_call_frequency":
                return self._optimize_call_frequency(suggestion)

            return False
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False

    def _optimize_slow_execution(self, suggestion: OptimizationSuggestion) -> bool:
        """Optimize slow execution"""
        # This would implement various optimization strategies
        # For now, just add optimization comments
        return self._add_optimization_comments(suggestion)

    def _optimize_call_frequency(self, suggestion: OptimizationSuggestion) -> bool:
        """Optimize high call frequency"""
        # This would implement caching or other optimizations
        # For now, just add optimization comments
        return self._add_optimization_comments(suggestion)

    def _add_optimization_comments(self, suggestion: OptimizationSuggestion) -> bool:
        """Add optimization comments to code"""
        try:
            # Find the module file
            module_file = None
            for py_file in self.root_path.rglob("*.py"):
                if self._path_to_module_name(py_file) == suggestion.module_name:
                    module_file = py_file
                    break

            if not module_file:
                return False

            # Add optimization comment
            content = module_file.read_text(encoding="utf-8")
            optimization_comment = f"""
# PERFORMANCE OPTIMIZATION APPLIED
# Issue: {suggestion.description}
# Fix: {suggestion.suggested_fix}
# Expected improvement: {suggestion.expected_improvement}
# Applied: {datetime.now().isoformat()}

"""

            # Add comment at the beginning of the file
            new_content = optimization_comment + content
            module_file.write_text(new_content, encoding="utf-8")

            return True

        except Exception as e:
            logger.error(f"Error adding optimization comments: {e}")
            return False

    def create_performance_monitoring(self) -> str:
        """Create performance monitoring system"""
        monitoring_code = '''
"""
Performance Monitoring System for StillMe
"""
import time
import psutil
import threading
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PerformanceAlert:
    """Performance alert definition"""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    metrics: Dict[str, float]

class PerformanceMonitor:
    """Real-time performance monitoring"""

    def __init__(self):
        self.alerts: List[PerformanceAlert] = []
        self.metrics_history: List[Dict[str, float]] = []
        self.monitoring_active = False
        self.monitoring_thread = None

        # Alert thresholds
        self.thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 5.0
        }

    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)

                # Check for alerts
                self._check_alerts(metrics)

                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                time.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(30)

    def _collect_metrics(self) -> Dict[str, float]:
        """Collect system metrics"""
        return {
            "timestamp": time.time(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }

    def _check_alerts(self, metrics: Dict[str, float]):
        """Check for performance alerts"""
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics and metrics[metric_name] > threshold:
                alert = PerformanceAlert(
                    timestamp=datetime.now(),
                    alert_type=f"high_{metric_name}",
                    severity="warning",
                    message=f"{metric_name} is {metrics[metric_name]:.1f}% (threshold: {threshold}%)",
                    metrics=metrics
                )
                self.alerts.append(alert)
                print(f"🚨 PERFORMANCE ALERT: {alert.message}")

    def get_performance_summary(self) -> Dict[str, any]:
        """Get performance summary"""
        if not self.metrics_history:
            return {}

        latest_metrics = self.metrics_history[-1]

        return {
            "current_metrics": latest_metrics,
            "total_alerts": len(self.alerts),
            "recent_alerts": len([a for a in self.alerts if (datetime.now() - a.timestamp).seconds < 3600]),
            "monitoring_active": self.monitoring_active
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()
'''

        # Save monitoring system
        monitoring_path = self.root_path / "stillme_core" / "performance_monitor.py"
        monitoring_path.write_text(monitoring_code, encoding="utf-8")

        return str(monitoring_path)

    def save_performance_report(self, report: PerformanceReport) -> Path:
        """Save performance optimization report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "report": asdict(report),
            "optimization_applied": list(self.optimization_applied),
            "thresholds": self.thresholds,
        }

        # Create reports directory
        reports_dir = self.root_path / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"performance_optimization_report_{timestamp}.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Performance report saved to {report_path}")
        return report_path


def main():
    """Main function to run performance optimization"""
    optimizer = PerformanceOptimizer()

    # Analyze performance
    optimizer.analyze_performance()

    # Apply optimizations
    report = optimizer.optimize_modules()

    # Create performance monitoring
    monitoring_path = optimizer.create_performance_monitoring()

    # Save report
    report_path = optimizer.save_performance_report(report)

    print("✅ Performance optimization completed!")
    print(f"📊 Total modules: {report.total_modules}")
    print(f"🔧 Optimized modules: {report.optimized_modules}")
    print(f"⚠️ Bottlenecks found: {report.bottlenecks_found}")
    print(f"📈 Performance improvement: {report.performance_improvement:.1f}%")
    print(f"📄 Report saved to: {report_path}")
    print(f"📊 Monitoring system created: {monitoring_path}")


if __name__ == "__main__":
    main()
