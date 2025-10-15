#!/usr/bin/env python3
"""
Adaptive Strategy - Senior Developer Adaptive Strategy Module
Chiến lược thích ứng như dev chuyên nghiệp thật

Tính năng:
1. Context Analysis - Phân tích ngữ cảnh
2. Strategy Selection - Lựa chọn chiến lược
3. Performance Monitoring - Giám sát hiệu suất
4. Strategy Evolution - Tiến hóa chiến lược
5. Risk Assessment - Đánh giá rủi ro
6. Resource Optimization - Tối ưu tài nguyên
7. Dynamic Adaptation - Thích ứng động
8. Learning Integration - Tích hợp học hỏi
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class StrategyType(Enum):
    """Loại chiến lược"""

    CONSERVATIVE = "conservative"  # Bảo thủ
    BALANCED = "balanced"  # Cân bằng
    AGGRESSIVE = "aggressive"  # Tích cực
    EXPERIMENTAL = "experimental"  # Thử nghiệm
    ADAPTIVE = "adaptive"  # Thích ứng


class ContextType(Enum):
    """Loại ngữ cảnh"""

    DEVELOPMENT = "development"  # Phát triển
    DEBUGGING = "debugging"  # Debug
    OPTIMIZATION = "optimization"  # Tối ưu
    SECURITY = "security"  # Bảo mật
    BUSINESS = "business"  # Kinh doanh
    CRITICAL = "critical"  # Nghiêm trọng
    EXPERIMENTAL = "experimental"  # Thử nghiệm


class PerformanceLevel(Enum):
    """Mức độ hiệu suất"""

    EXCELLENT = "excellent"  # Xuất sắc
    GOOD = "good"  # Tốt
    AVERAGE = "average"  # Trung bình
    POOR = "poor"  # Kém
    CRITICAL = "critical"  # Nghiêm trọng


@dataclass
class Strategy:
    """Chiến lược"""

    strategy_id: str
    strategy_type: StrategyType
    name: str
    description: str
    context_types: list[ContextType]
    conditions: list[str]
    actions: list[str]
    expected_outcomes: list[str]
    success_rate: float
    performance_level: PerformanceLevel
    risk_level: float
    resource_usage: dict[str, float]
    created_at: datetime
    last_updated: datetime
    usage_count: int = 0
    success_count: int = 0


@dataclass
class Context:
    """Ngữ cảnh"""

    context_id: str
    context_type: ContextType
    description: str
    complexity: float
    urgency: float
    risk_level: float
    resource_constraints: dict[str, float]
    success_criteria: list[str]
    timestamp: datetime


@dataclass
class StrategyResult:
    """Kết quả chiến lược"""

    strategy_id: str
    context_id: str
    success: bool
    performance_metrics: dict[str, float]
    actual_outcomes: list[str]
    lessons_learned: list[str]
    execution_time: float
    timestamp: datetime


@dataclass
class AdaptiveStrategyResult:
    """Kết quả chiến lược thích ứng"""

    selected_strategy: Strategy
    context_analysis: Context
    strategy_confidence: float
    expected_performance: PerformanceLevel
    risk_assessment: float
    resource_requirements: dict[str, float]
    alternative_strategies: list[Strategy]
    recommendations: list[str]
    analysis_time: float


class AdaptiveStrategy:
    """Senior Developer Adaptive Strategy"""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.strategies_db = self.project_root / "data" / "adaptive_strategies.json"
        self.results_db = self.project_root / "data" / "strategy_results.json"

        # Ensure data directory exists
        self.strategies_db.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.strategies = self._load_strategies()
        self.strategy_results = self._load_strategy_results()

        # Initialize default strategies if none exist
        if not self.strategies:
            self._initialize_default_strategies()

        # Strategy selection parameters
        self.min_confidence_threshold = 0.6
        self.performance_weight = 0.4
        self.risk_weight = 0.3
        self.resource_weight = 0.3

    def _load_strategies(self) -> list[Strategy]:
        """Load strategies from database"""
        if not self.strategies_db.exists():
            return []

        try:
            with open(self.strategies_db, encoding="utf-8") as f:
                data = json.load(f)

            strategies: list[Strategy] = []
            for strategy_data in data:
                strategy_data["created_at"] = datetime.fromisoformat(
                    strategy_data["created_at"]
                )
                strategy_data["last_updated"] = datetime.fromisoformat(
                    strategy_data["last_updated"]
                )
                strategies.append(Strategy(**strategy_data))

            return strategies
        except Exception as e:
            print(f"Error loading strategies: {e}")
            return []

    def _load_strategy_results(self) -> list[StrategyResult]:
        """Load strategy results from database"""
        if not self.results_db.exists():
            return []

        try:
            with open(self.results_db, encoding="utf-8") as f:
                data = json.load(f)

            results: list[StrategyResult] = []
            for result_data in data:
                result_data["timestamp"] = datetime.fromisoformat(
                    result_data["timestamp"]
                )
                results.append(StrategyResult(**result_data))

            return results
        except Exception as e:
            print(f"Error loading strategy results: {e}")
            return []

    def _save_strategies(self) -> None:
        """Save strategies to database"""
        try:
            data: list[dict[str, Any]] = []
            for strategy in self.strategies:
                strategy_dict = asdict(strategy)
                strategy_dict["created_at"] = strategy.created_at.isoformat()
                strategy_dict["last_updated"] = strategy.last_updated.isoformat()
                data.append(strategy_dict)

            with open(self.strategies_db, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving strategies: {e}")

    def _save_strategy_results(self) -> None:
        """Save strategy results to database"""
        try:
            data: list[dict[str, Any]] = []
            for result in self.strategy_results:
                result_dict = asdict(result)
                result_dict["timestamp"] = result.timestamp.isoformat()
                data.append(result_dict)

            with open(self.results_db, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving strategy results: {e}")

    def _initialize_default_strategies(self) -> None:
        """Initialize default strategies"""
        default_strategies = [
            Strategy(
                strategy_id="conservative_dev",
                strategy_type=StrategyType.CONSERVATIVE,
                name="Conservative Development",
                description="Safe, well-tested approach with extensive validation",
                context_types=[ContextType.DEVELOPMENT, ContextType.CRITICAL],
                conditions=[
                    "High risk tolerance",
                    "Stable requirements",
                    "Time available",
                ],
                actions=[
                    "Extensive testing",
                    "Code review",
                    "Documentation",
                    "Gradual rollout",
                ],
                expected_outcomes=[
                    "High reliability",
                    "Low bugs",
                    "Good maintainability",
                ],
                success_rate=0.85,
                performance_level=PerformanceLevel.GOOD,
                risk_level=0.2,
                resource_usage={"time": 1.5, "team_size": 1.2, "testing": 2.0},
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            Strategy(
                strategy_id="aggressive_optimization",
                strategy_type=StrategyType.AGGRESSIVE,
                name="Aggressive Optimization",
                description="Fast, performance-focused approach with calculated risks",
                context_types=[ContextType.OPTIMIZATION],
                conditions=[
                    "Performance critical",
                    "Experienced team",
                    "Risk acceptable",
                ],
                actions=[
                    "Performance profiling",
                    "Algorithm optimization",
                    "Resource tuning",
                ],
                expected_outcomes=["High performance", "Efficient resource usage"],
                success_rate=0.75,
                performance_level=PerformanceLevel.EXCELLENT,
                risk_level=0.6,
                resource_usage={"time": 0.8, "team_size": 1.5, "testing": 1.0},
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            Strategy(
                strategy_id="balanced_approach",
                strategy_type=StrategyType.BALANCED,
                name="Balanced Approach",
                description="Balanced approach considering all factors",
                context_types=[ContextType.DEVELOPMENT, ContextType.BUSINESS],
                conditions=["Mixed requirements", "Moderate risk tolerance"],
                actions=[
                    "Iterative development",
                    "Regular testing",
                    "Stakeholder feedback",
                ],
                expected_outcomes=[
                    "Good balance",
                    "Acceptable performance",
                    "Manageable risk",
                ],
                success_rate=0.80,
                performance_level=PerformanceLevel.GOOD,
                risk_level=0.4,
                resource_usage={"time": 1.0, "team_size": 1.0, "testing": 1.5},
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            Strategy(
                strategy_id="experimental_innovation",
                strategy_type=StrategyType.EXPERIMENTAL,
                name="Experimental Innovation",
                description="Innovative approach with new technologies and methods",
                context_types=[ContextType.EXPERIMENTAL, ContextType.DEVELOPMENT],
                conditions=[
                    "Innovation required",
                    "Learning opportunity",
                    "Low risk tolerance",
                ],
                actions=["Research", "Prototyping", "Proof of concept", "Learning"],
                expected_outcomes=["Innovation", "Learning", "Future capabilities"],
                success_rate=0.60,
                performance_level=PerformanceLevel.AVERAGE,
                risk_level=0.8,
                resource_usage={"time": 2.0, "team_size": 1.0, "testing": 0.5},
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
        ]

        self.strategies = default_strategies
        self._save_strategies()

    def analyze_context(
        self,
        task_description: str,
        complexity: float = 0.5,
        urgency: float = 0.5,
        risk_level: float = 0.5,
    ) -> Context:
        """Analyze context for strategy selection"""
        context_id = hashlib.md5(task_description.encode()).hexdigest()[:12]

        # Determine context type based on task description
        task_lower = task_description.lower()
        if any(word in task_lower for word in ["debug", "fix", "error", "bug"]):
            context_type = ContextType.DEBUGGING
        elif any(
            word in task_lower
            for word in ["optimize", "performance", "speed", "efficiency"]
        ):
            context_type = ContextType.OPTIMIZATION
        elif any(
            word in task_lower
            for word in ["security", "vulnerability", "attack", "secure"]
        ):
            context_type = ContextType.SECURITY
        elif any(
            word in task_lower for word in ["business", "revenue", "customer", "market"]
        ):
            context_type = ContextType.BUSINESS
        elif any(
            word in task_lower
            for word in ["critical", "urgent", "emergency", "production"]
        ):
            context_type = ContextType.CRITICAL
        elif any(word in task_lower for word in ["experiment", "test", "try", "new"]):
            context_type = ContextType.EXPERIMENTAL
        else:
            context_type = ContextType.DEVELOPMENT

        context = Context(
            context_id=context_id,
            context_type=context_type,
            description=task_description,
            complexity=complexity,
            urgency=urgency,
            risk_level=risk_level,
            resource_constraints={"time": 1.0, "team_size": 1.0, "budget": 1.0},
            success_criteria=[
                "Task completion",
                "Quality standards",
                "Performance targets",
            ],
            timestamp=datetime.now(),
        )

        return context

    def select_strategy(
        self, context: Context | dict[str, Any]
    ) -> AdaptiveStrategyResult:
        """Select the best strategy for given context"""
        start_time = time.time()

        # Filter strategies by context type
        # Handle both Context objects and dict inputs
        if isinstance(context, dict):
            # Convert dict to Context object
            task_desc: str = context.get("task", "unknown task")
            context_obj: Context = self.analyze_context(task_desc)
            context = context_obj

        suitable_strategies = [
            strategy
            for strategy in self.strategies
            if context.context_type in strategy.context_types
        ]

        if not suitable_strategies:
            # Fallback to balanced approach
            suitable_strategies = [
                strategy
                for strategy in self.strategies
                if strategy.strategy_type == StrategyType.BALANCED
            ]

        # Score strategies based on multiple factors
        scored_strategies: list[tuple[Any, float]] = []
        for strategy in suitable_strategies:
            # Performance score
            performance_score = self._get_performance_score(strategy.performance_level)

            # Risk score (lower is better)
            risk_score = 1.0 - strategy.risk_level

            # Resource efficiency score
            resource_score = self._calculate_resource_efficiency(strategy, context)

            # Historical success score
            success_score = strategy.success_rate

            # Calculate weighted score
            total_score = (
                performance_score * self.performance_weight
                + risk_score * self.risk_weight
                + resource_score * self.resource_weight
                + success_score * 0.1
            )

            scored_strategies.append((strategy, total_score))

        # Sort by score (highest first)
        scored_strategies.sort(key=lambda x: x[1], reverse=True)

        # Select best strategy
        selected_strategy, strategy_confidence = scored_strategies[0]

        # Get alternative strategies
        alternative_strategies = [s[0] for s in scored_strategies[1:3]]

        # Generate recommendations
        recommendations = self._generate_recommendations(selected_strategy, context)

        return AdaptiveStrategyResult(
            selected_strategy=selected_strategy,
            context_analysis=context,
            strategy_confidence=strategy_confidence,
            expected_performance=selected_strategy.performance_level,
            risk_assessment=selected_strategy.risk_level,
            resource_requirements=selected_strategy.resource_usage,
            alternative_strategies=alternative_strategies,
            recommendations=recommendations,
            analysis_time=time.time() - start_time,
        )

    def _get_performance_score(self, performance_level: PerformanceLevel) -> float:
        """Convert performance level to numeric score"""
        scores = {
            PerformanceLevel.EXCELLENT: 1.0,
            PerformanceLevel.GOOD: 0.8,
            PerformanceLevel.AVERAGE: 0.6,
            PerformanceLevel.POOR: 0.4,
            PerformanceLevel.CRITICAL: 0.2,
        }
        return scores.get(performance_level, 0.5)

    def _calculate_resource_efficiency(
        self, strategy: Strategy, context: Context
    ) -> float:
        """Calculate resource efficiency score"""
        # Simple calculation based on resource usage vs constraints
        efficiency = 1.0
        for resource, usage in strategy.resource_usage.items():
            if resource in context.resource_constraints:
                constraint = context.resource_constraints[resource]
                if usage > constraint:
                    efficiency *= 0.5  # Penalty for exceeding constraints
                else:
                    efficiency *= constraint / usage  # Bonus for efficiency

        return min(1.0, efficiency)

    def _generate_recommendations(
        self, strategy: Strategy, context: Context
    ) -> list[str]:
        """Generate recommendations based on selected strategy"""
        recommendations: list[str] = []

        # Strategy-specific recommendations
        if strategy.strategy_type == StrategyType.CONSERVATIVE:
            recommendations.extend(
                [
                    "Focus on thorough testing and validation",
                    "Implement comprehensive error handling",
                    "Document all changes and decisions",
                ]
            )
        elif strategy.strategy_type == StrategyType.AGGRESSIVE:
            recommendations.extend(
                [
                    "Monitor performance metrics closely",
                    "Have rollback plan ready",
                    "Communicate risks to stakeholders",
                ]
            )
        elif strategy.strategy_type == StrategyType.EXPERIMENTAL:
            recommendations.extend(
                [
                    "Set clear success/failure criteria",
                    "Allocate time for learning and iteration",
                    "Document lessons learned",
                ]
            )

        # Context-specific recommendations
        if context.context_type == ContextType.CRITICAL:
            recommendations.append("Prioritize stability and reliability")
        elif context.context_type == ContextType.OPTIMIZATION:
            recommendations.append("Measure performance before and after")
        elif context.context_type == ContextType.SECURITY:
            recommendations.append("Conduct security review and testing")

        return recommendations

    def record_strategy_result(
        self,
        strategy_id: str,
        context_id: str,
        success: bool,
        performance_metrics: dict[str, float],
        actual_outcomes: list[str],
        execution_time: float,
    ) -> str:
        """Record the result of a strategy execution"""
        result_id = hashlib.md5(
            f"{strategy_id}_{context_id}_{time.time()}".encode()
        ).hexdigest()[:12]

        result = StrategyResult(
            strategy_id=strategy_id,
            context_id=context_id,
            success=success,
            performance_metrics=performance_metrics,
            actual_outcomes=actual_outcomes,
            lessons_learned=[],
            execution_time=execution_time,
            timestamp=datetime.now(),
        )

        self.strategy_results.append(result)

        # Update strategy statistics
        for strategy in self.strategies:
            if strategy.strategy_id == strategy_id:
                strategy.usage_count += 1
                if success:
                    strategy.success_count += 1
                strategy.success_rate = strategy.success_count / strategy.usage_count
                strategy.last_updated = datetime.now()
                break

        # Save results
        self._save_strategy_results()
        self._save_strategies()

        return result_id

    def adapt_strategy(self, strategy_id: str, feedback: dict[str, Any]) -> bool:
        """Adapt strategy based on feedback"""
        strategy = None
        for s in self.strategies:
            if s.strategy_id == strategy_id:
                strategy = s
                break

        if not strategy:
            return False

        # Update strategy based on feedback
        if "performance_feedback" in feedback:
            if feedback["performance_feedback"] == "excellent":
                strategy.performance_level = PerformanceLevel.EXCELLENT
            elif feedback["performance_feedback"] == "poor":
                strategy.performance_level = PerformanceLevel.POOR

        if "risk_feedback" in feedback:
            strategy.risk_level = feedback["risk_feedback"]

        if "success_feedback" in feedback:
            if feedback["success_feedback"]:
                strategy.success_count += 1
            strategy.usage_count += 1
            strategy.success_rate = strategy.success_count / strategy.usage_count

        strategy.last_updated = datetime.now()

        # Save updated strategy
        self._save_strategies()

        return True


# Test function
if __name__ == "__main__":
    adaptive_strategy = AdaptiveStrategy()

    # Analyze context
    context = adaptive_strategy.analyze_context(
        task_description="Optimize database performance for critical production system",
        complexity=0.8,
        urgency=0.9,
        risk_level=0.7,
    )

    # Select strategy
    result = adaptive_strategy.select_strategy(context)

    print("🎯 Adaptive Strategy Results:")
    print(f"   📊 Selected Strategy: {result.selected_strategy.name}")
    print(f"   🎯 Strategy Type: {result.selected_strategy.strategy_type.value}")
    print(f"   📈 Confidence: {result.strategy_confidence:.2f}")
    print(f"   ⚡ Expected Performance: {result.expected_performance.value}")
    print(f"   ⚠️ Risk Assessment: {result.risk_assessment:.2f}")
    print(f"   💡 Recommendations: {len(result.recommendations)}")
    print(f"   ⏱️ Analysis Time: {result.analysis_time:.3f}s")
