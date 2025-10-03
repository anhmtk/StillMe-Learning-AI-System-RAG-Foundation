"""
🧠 StillMe Performance Analyzer for AGI
======================================

Advanced performance analysis system for AGI learning optimization.
Analyzes learning patterns, identifies bottlenecks, and provides
intelligent recommendations for AGI evolution.

Tính năng:
- Learning pattern analysis và optimization
- Performance bottleneck identification
- AGI evolution recommendations
- Memory leak detection
- Algorithm efficiency analysis
- Predictive performance modeling
- Self-improvement suggestions

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis"""

    timestamp: datetime
    session_id: str
    learning_stage: str
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    tokens_consumed: int
    accuracy_score: float
    learning_rate: float
    convergence_rate: float
    error_rate: float
    throughput_items_per_second: float
    efficiency_score: float


@dataclass
class PerformancePattern:
    """Identified performance pattern"""

    pattern_id: str
    pattern_type: str  # improvement, degradation, oscillation, stable
    start_time: datetime
    end_time: datetime | None
    metrics: list[PerformanceMetrics]
    trend: str  # increasing, decreasing, stable, oscillating
    confidence: float
    description: str
    recommendations: list[str]


@dataclass
class BottleneckAnalysis:
    """Bottleneck analysis result"""

    bottleneck_id: str
    bottleneck_type: str  # cpu, memory, disk, network, algorithm, data
    severity: str  # low, medium, high, critical
    affected_metrics: list[str]
    impact_percentage: float
    root_cause: str
    recommendations: list[str]
    estimated_fix_time: str


@dataclass
class AGIRecommendation:
    """AGI evolution recommendation"""

    recommendation_id: str
    category: str  # architecture, algorithm, data, resource, learning
    priority: str  # low, medium, high, critical
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str
    risk_level: str
    dependencies: list[str]
    metrics_to_track: list[str]


class PerformanceAnalyzer:
    """
    Advanced performance analyzer for AGI learning optimization
    """

    def __init__(self, analysis_window_hours: int = 24):
        self.analysis_window_hours = analysis_window_hours
        self.logger = logging.getLogger(__name__)

        # Data storage
        self.performance_history = deque(maxlen=10000)
        self.identified_patterns: list[PerformancePattern] = []
        self.bottlenecks: list[BottleneckAnalysis] = []
        self.agi_recommendations: list[AGIRecommendation] = []

        # Analysis state
        self.is_analyzing = False
        self.analysis_task: asyncio.Task | None = None
        self.last_analysis_time = None

        # Performance baselines
        self.baselines = {
            "response_time": 1000.0,  # 1 second
            "memory_usage": 512.0,  # 512 MB
            "cpu_usage": 50.0,  # 50%
            "accuracy": 0.8,  # 80%
            "efficiency": 0.7,  # 70%
        }

        # Pattern detection thresholds
        self.pattern_thresholds = {
            "improvement_threshold": 0.1,  # 10% improvement
            "degradation_threshold": 0.15,  # 15% degradation
            "oscillation_threshold": 0.2,  # 20% variation
            "stability_threshold": 0.05,  # 5% variation
        }

        # AGI evolution tracking
        self.evolution_milestones = []
        self.learning_curves = defaultdict(list)
        self.optimization_history = []

    async def start_analysis(self, interval: int = 300):  # 5 minutes
        """Start performance analysis"""
        if self.is_analyzing:
            self.logger.warning("Performance analysis already started")
            return

        self.is_analyzing = True
        self.analysis_task = asyncio.create_task(self._analysis_loop(interval))
        self.logger.info(f"Performance analysis started with {interval}s interval")

    async def stop_analysis(self):
        """Stop performance analysis"""
        if not self.is_analyzing:
            return

        self.is_analyzing = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Performance analysis stopped")

    async def _analysis_loop(self, interval: int):
        """Main analysis loop"""
        while self.is_analyzing:
            try:
                # Perform comprehensive analysis
                await self._analyze_performance_patterns()
                await self._identify_bottlenecks()
                await self._generate_agi_recommendations()
                await self._update_learning_curves()

                self.last_analysis_time = datetime.now()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(interval)

    def add_performance_metrics(self, metrics: PerformanceMetrics):
        """Add performance metrics for analysis"""
        self.performance_history.append(metrics)

        # Update learning curves
        self.learning_curves[metrics.learning_stage].append(metrics)

        # Keep only recent data
        cutoff_time = datetime.now() - timedelta(hours=self.analysis_window_hours)
        for stage in self.learning_curves:
            self.learning_curves[stage] = [
                m for m in self.learning_curves[stage] if m.timestamp > cutoff_time
            ]

    async def _analyze_performance_patterns(self):
        """Analyze performance patterns"""
        if len(self.performance_history) < 10:
            return

        recent_metrics = list(self.performance_history)[-100:]  # Last 100 measurements

        # Analyze trends for each metric
        patterns = []

        # Response time pattern
        response_times = [m.response_time_ms for m in recent_metrics]
        response_pattern = self._detect_trend(response_times, "response_time")
        if response_pattern:
            patterns.append(response_pattern)

        # Memory usage pattern
        memory_usage = [m.memory_usage_mb for m in recent_metrics]
        memory_pattern = self._detect_trend(memory_usage, "memory_usage")
        if memory_pattern:
            patterns.append(memory_pattern)

        # Accuracy pattern
        accuracy_scores = [m.accuracy_score for m in recent_metrics]
        accuracy_pattern = self._detect_trend(accuracy_scores, "accuracy")
        if accuracy_pattern:
            patterns.append(accuracy_pattern)

        # Efficiency pattern
        efficiency_scores = [m.efficiency_score for m in recent_metrics]
        efficiency_pattern = self._detect_trend(efficiency_scores, "efficiency")
        if efficiency_pattern:
            patterns.append(efficiency_pattern)

        # Add new patterns
        for pattern in patterns:
            if not any(
                p.pattern_id == pattern.pattern_id for p in self.identified_patterns
            ):
                self.identified_patterns.append(pattern)
                self.logger.info(
                    f"Identified performance pattern: {pattern.pattern_type} - {pattern.description}"
                )

    def _detect_trend(
        self, values: list[float], metric_name: str
    ) -> PerformancePattern | None:
        """Detect trend in metric values"""
        if len(values) < 5:
            return None

        # Calculate trend
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        change_percent = (second_avg - first_avg) / first_avg if first_avg > 0 else 0

        # Determine pattern type
        if change_percent > self.pattern_thresholds["improvement_threshold"]:
            pattern_type = "improvement"
            trend = "increasing"
            description = (
                f"{metric_name} showing improvement trend ({change_percent:.1%})"
            )
        elif change_percent < -self.pattern_thresholds["degradation_threshold"]:
            pattern_type = "degradation"
            trend = "decreasing"
            description = (
                f"{metric_name} showing degradation trend ({change_percent:.1%})"
            )
        elif abs(change_percent) < self.pattern_thresholds["stability_threshold"]:
            pattern_type = "stable"
            trend = "stable"
            description = f"{metric_name} showing stable performance"
        else:
            # Check for oscillation
            variance = statistics.variance(values)
            mean_val = statistics.mean(values)
            cv = variance / mean_val if mean_val > 0 else 0

            if cv > self.pattern_thresholds["oscillation_threshold"]:
                pattern_type = "oscillation"
                trend = "oscillating"
                description = f"{metric_name} showing oscillating behavior"
            else:
                return None

        # Generate recommendations
        recommendations = self._generate_pattern_recommendations(
            pattern_type, metric_name, change_percent
        )

        return PerformancePattern(
            pattern_id=f"{metric_name}_{pattern_type}_{int(time.time())}",
            pattern_type=pattern_type,
            start_time=datetime.now() - timedelta(minutes=len(values)),
            end_time=None,
            metrics=[],  # Would be populated with actual metrics
            trend=trend,
            confidence=min(
                1.0, abs(change_percent) * 2
            ),  # Simple confidence calculation
            description=description,
            recommendations=recommendations,
        )

    def _generate_pattern_recommendations(
        self, pattern_type: str, metric_name: str, change_percent: float
    ) -> list[str]:
        """Generate recommendations based on pattern"""
        recommendations = []

        if pattern_type == "improvement":
            recommendations.extend(
                [
                    f"Continue current approach for {metric_name}",
                    "Consider scaling up successful strategies",
                    "Document best practices for replication",
                ]
            )
        elif pattern_type == "degradation":
            recommendations.extend(
                [
                    f"Investigate root cause of {metric_name} degradation",
                    "Consider rolling back recent changes",
                    "Implement monitoring alerts for early detection",
                ]
            )
        elif pattern_type == "oscillation":
            recommendations.extend(
                [
                    f"Stabilize {metric_name} performance",
                    "Investigate external factors causing variation",
                    "Consider implementing smoothing algorithms",
                ]
            )
        elif pattern_type == "stable":
            recommendations.extend(
                [
                    f"Maintain current {metric_name} performance",
                    "Look for optimization opportunities",
                    "Consider pushing performance boundaries",
                ]
            )

        return recommendations

    async def _identify_bottlenecks(self):
        """Identify performance bottlenecks"""
        if len(self.performance_history) < 20:
            return

        recent_metrics = list(self.performance_history)[-50:]
        bottlenecks = []

        # CPU bottleneck
        cpu_usage = [m.cpu_usage_percent for m in recent_metrics]
        avg_cpu = statistics.mean(cpu_usage)
        if avg_cpu > 80:
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_id=f"cpu_bottleneck_{int(time.time())}",
                    bottleneck_type="cpu",
                    severity="high" if avg_cpu > 90 else "medium",
                    affected_metrics=["response_time", "throughput"],
                    impact_percentage=min(100, (avg_cpu - 70) * 2),
                    root_cause="High CPU utilization limiting processing capacity",
                    recommendations=[
                        "Optimize algorithms for better CPU efficiency",
                        "Implement parallel processing where possible",
                        "Consider CPU scaling or load balancing",
                    ],
                    estimated_fix_time="2-4 weeks",
                )
            )

        # Memory bottleneck
        memory_usage = [m.memory_usage_mb for m in recent_metrics]
        avg_memory = statistics.mean(memory_usage)
        if avg_memory > 1024:  # 1GB
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_id=f"memory_bottleneck_{int(time.time())}",
                    bottleneck_type="memory",
                    severity="high" if avg_memory > 2048 else "medium",
                    affected_metrics=["response_time", "efficiency"],
                    impact_percentage=min(100, (avg_memory - 512) / 20),
                    root_cause="High memory usage causing performance degradation",
                    recommendations=[
                        "Implement memory pooling and reuse",
                        "Optimize data structures for memory efficiency",
                        "Consider memory scaling or garbage collection tuning",
                    ],
                    estimated_fix_time="1-3 weeks",
                )
            )

        # Response time bottleneck
        response_times = [m.response_time_ms for m in recent_metrics]
        avg_response = statistics.mean(response_times)
        if avg_response > 5000:  # 5 seconds
            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_id=f"response_bottleneck_{int(time.time())}",
                    bottleneck_type="algorithm",
                    severity="high" if avg_response > 10000 else "medium",
                    affected_metrics=["user_experience", "throughput"],
                    impact_percentage=min(100, (avg_response - 1000) / 100),
                    root_cause="Slow response times affecting user experience",
                    recommendations=[
                        "Optimize critical path algorithms",
                        "Implement caching strategies",
                        "Consider asynchronous processing",
                    ],
                    estimated_fix_time="2-6 weeks",
                )
            )

        # Add new bottlenecks
        for bottleneck in bottlenecks:
            if not any(
                b.bottleneck_id == bottleneck.bottleneck_id for b in self.bottlenecks
            ):
                self.bottlenecks.append(bottleneck)
                self.logger.warning(
                    f"Identified bottleneck: {bottleneck.bottleneck_type} - {bottleneck.severity}"
                )

    async def _generate_agi_recommendations(self):
        """Generate AGI evolution recommendations"""
        recommendations = []

        # Analyze current performance
        if len(self.performance_history) < 10:
            return

        recent_metrics = list(self.performance_history)[-20:]

        # Architecture recommendations
        avg_efficiency = statistics.mean([m.efficiency_score for m in recent_metrics])
        if avg_efficiency < 0.6:
            recommendations.append(
                AGIRecommendation(
                    recommendation_id=f"architecture_optimization_{int(time.time())}",
                    category="architecture",
                    priority="high",
                    title="Architecture Optimization for AGI",
                    description="Current architecture shows low efficiency. Consider redesigning for better AGI performance.",
                    expected_improvement="20-40% efficiency gain",
                    implementation_effort="3-6 months",
                    risk_level="medium",
                    dependencies=["performance_analysis", "architecture_review"],
                    metrics_to_track=[
                        "efficiency_score",
                        "response_time",
                        "memory_usage",
                    ],
                )
            )

        # Algorithm recommendations
        avg_accuracy = statistics.mean([m.accuracy_score for m in recent_metrics])
        if avg_accuracy < 0.8:
            recommendations.append(
                AGIRecommendation(
                    recommendation_id=f"algorithm_improvement_{int(time.time())}",
                    category="algorithm",
                    priority="high",
                    title="Algorithm Enhancement for Better Learning",
                    description="Current algorithms show suboptimal accuracy. Implement advanced learning techniques.",
                    expected_improvement="15-30% accuracy improvement",
                    implementation_effort="2-4 months",
                    risk_level="low",
                    dependencies=["data_quality_analysis", "algorithm_research"],
                    metrics_to_track=[
                        "accuracy_score",
                        "learning_rate",
                        "convergence_rate",
                    ],
                )
            )

        # Resource recommendations
        avg_memory = statistics.mean([m.memory_usage_mb for m in recent_metrics])
        if avg_memory > 1024:
            recommendations.append(
                AGIRecommendation(
                    recommendation_id=f"resource_scaling_{int(time.time())}",
                    category="resource",
                    priority="medium",
                    title="Resource Scaling for AGI Growth",
                    description="Memory usage is high. Consider scaling resources to support AGI evolution.",
                    expected_improvement="Better handling of complex tasks",
                    implementation_effort="1-2 months",
                    risk_level="low",
                    dependencies=["resource_analysis", "infrastructure_planning"],
                    metrics_to_track=["memory_usage", "cpu_usage", "response_time"],
                )
            )

        # Learning recommendations
        avg_learning_rate = statistics.mean([m.learning_rate for m in recent_metrics])
        if avg_learning_rate < 0.1:
            recommendations.append(
                AGIRecommendation(
                    recommendation_id=f"learning_optimization_{int(time.time())}",
                    category="learning",
                    priority="high",
                    title="Learning Rate Optimization",
                    description="Learning rate is low. Implement adaptive learning strategies for faster AGI evolution.",
                    expected_improvement="2-5x faster learning",
                    implementation_effort="1-3 months",
                    risk_level="medium",
                    dependencies=["learning_analysis", "adaptive_algorithms"],
                    metrics_to_track=[
                        "learning_rate",
                        "convergence_rate",
                        "accuracy_score",
                    ],
                )
            )

        # Add new recommendations
        for rec in recommendations:
            if not any(
                r.recommendation_id == rec.recommendation_id
                for r in self.agi_recommendations
            ):
                self.agi_recommendations.append(rec)
                self.logger.info(f"Generated AGI recommendation: {rec.title}")

    async def _update_learning_curves(self):
        """Update learning curves for AGI evolution tracking"""
        for stage, metrics in self.learning_curves.items():
            if len(metrics) < 5:
                continue

            # Calculate learning curve metrics
            accuracy_curve = [m.accuracy_score for m in metrics]
            efficiency_curve = [m.efficiency_score for m in metrics]

            # Store curve data
            curve_data = {
                "stage": stage,
                "timestamp": datetime.now(),
                "accuracy_trend": self._calculate_trend(accuracy_curve),
                "efficiency_trend": self._calculate_trend(efficiency_curve),
                "data_points": len(metrics),
                "latest_accuracy": accuracy_curve[-1],
                "latest_efficiency": efficiency_curve[-1],
            }

            # Check for evolution milestones
            if self._is_evolution_milestone(curve_data):
                self.evolution_milestones.append(
                    {
                        "milestone_id": f"{stage}_milestone_{int(time.time())}",
                        "stage": stage,
                        "timestamp": datetime.now(),
                        "achievement": f"Significant improvement in {stage}",
                        "metrics": curve_data,
                    }
                )
                self.logger.info(f"AGI evolution milestone reached: {stage}")

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        change_percent = (second_avg - first_avg) / first_avg if first_avg > 0 else 0

        if change_percent > 0.1:
            return "improving"
        elif change_percent < -0.1:
            return "declining"
        else:
            return "stable"

    def _is_evolution_milestone(self, curve_data: dict[str, Any]) -> bool:
        """Check if this represents an evolution milestone"""
        # Simple milestone detection - can be enhanced
        return (
            curve_data["accuracy_trend"] == "improving"
            and curve_data["latest_accuracy"] > 0.9
        )

    def get_analysis_report(self) -> dict[str, Any]:
        """Get comprehensive analysis report"""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_window_hours": self.analysis_window_hours,
            "performance_summary": {
                "total_metrics": len(self.performance_history),
                "active_patterns": len(
                    [p for p in self.identified_patterns if p.end_time is None]
                ),
                "active_bottlenecks": len(
                    [b for b in self.bottlenecks if b.severity in ["high", "critical"]]
                ),
                "pending_recommendations": len(
                    [
                        r
                        for r in self.agi_recommendations
                        if r.priority in ["high", "critical"]
                    ]
                ),
            },
            "patterns": [asdict(p) for p in self.identified_patterns[-10:]],  # Last 10
            "bottlenecks": [asdict(b) for b in self.bottlenecks[-5:]],  # Last 5
            "agi_recommendations": [
                asdict(r) for r in self.agi_recommendations[-10:]
            ],  # Last 10
            "evolution_milestones": self.evolution_milestones[-5:],  # Last 5
            "learning_curves": {
                stage: {
                    "data_points": len(metrics),
                    "latest_accuracy": metrics[-1].accuracy_score if metrics else 0,
                    "latest_efficiency": metrics[-1].efficiency_score if metrics else 0,
                    "trend": self._calculate_trend([m.accuracy_score for m in metrics])
                    if metrics
                    else "no_data",
                }
                for stage, metrics in self.learning_curves.items()
            },
            "baselines": self.baselines,
            "thresholds": self.pattern_thresholds,
        }

    def export_analysis(self, file_path: str):
        """Export analysis to JSON file"""
        try:
            export_data = self.get_analysis_report()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Performance analysis exported to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export analysis: {e}")


# Global performance analyzer instance
_performance_analyzer_instance: PerformanceAnalyzer | None = None


def get_performance_analyzer(analysis_window_hours: int = 24) -> PerformanceAnalyzer:
    """Get global performance analyzer instance"""
    global _performance_analyzer_instance
    if _performance_analyzer_instance is None:
        _performance_analyzer_instance = PerformanceAnalyzer(analysis_window_hours)
    return _performance_analyzer_instance


async def initialize_performance_analysis(
    analysis_window_hours: int = 24, interval: int = 300
) -> PerformanceAnalyzer:
    """Initialize and start performance analysis"""
    analyzer = get_performance_analyzer(analysis_window_hours)
    await analyzer.start_analysis(interval)
    return analyzer
