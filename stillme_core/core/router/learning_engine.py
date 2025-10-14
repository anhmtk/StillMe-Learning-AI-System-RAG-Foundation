"""
Learning Engine - Adaptive Routing Improvements
==============================================

This module provides learning capabilities that enable AgentDev to improve
routing decisions over time based on outcomes and user feedback.

Author: StillMe AI Framework
Version: 1.0.0
"""

import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Import StillMe core components
try:
    from ..observability.logger import get_logger
    from ..observability.metrics import get_metrics_collector
    from ..observability.tracer import get_tracer
    from .intelligent_router import (
        AgentType,  # type: ignore
        RoutingDecision,  # type: ignore
        TaskComplexity,  # type: ignore
        TaskType,  # type: ignore
    )
except ImportError:
    # Fallback for standalone execution
    import sys

    sys.path.append(str(Path(__file__).parent.parent / "observability"))

try:
    from ...core.observability.logger import get_logger
except ImportError:
    pass

try:
    from ...core.observability.metrics import get_metrics_collector
except ImportError:
    pass

try:
    from ...core.observability.tracer import get_tracer
except ImportError:
    pass

    # Mock the router imports for standalone execution
    class TaskComplexity(Enum):
        SIMPLE = "simple"
        MEDIUM = "medium"
        COMPLEX = "complex"
        CRITICAL = "critical"

    class TaskType(Enum):
        CODE_REVIEW = "code_review"
        BUG_FIX = "bug_fix"
        FEATURE_DEVELOPMENT = "feature_development"
        TESTING = "testing"
        DOCUMENTATION = "documentation"
        REFACTORING = "refactoring"
        DEPLOYMENT = "deployment"
        MONITORING = "monitoring"
        ANALYSIS = "analysis"
        GENERAL = "general"

    class AgentType(Enum):
        AGENTDEV = "agentdev"
        CODE_REVIEWER = "code_reviewer"
        TESTER = "tester"
        DOCUMENTER = "documenter"
        DEPLOYER = "deployer"
        ANALYST = "analyst"
        GENERAL = "general"

    class RoutingDecision:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


# Initialize observability components safely
try:
    logger = get_logger(__name__)
except (NameError, ImportError):
    logger = None

try:
    metrics = get_metrics_collector()
except (NameError, ImportError):
    metrics = None

try:
    tracer = get_tracer()
except (NameError, ImportError):
    tracer = None


class LearningEventType(Enum):
    """Types of learning events"""

    ROUTING_DECISION = "routing_decision"
    TASK_COMPLETION = "task_completion"
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_EVENT = "error_event"


@dataclass
class LearningEvent:
    """A learning event for the system"""

    event_id: str
    event_type: LearningEventType
    timestamp: float
    data: dict[str, Any]
    context: dict[str, Any]


@dataclass
class LearningPattern:
    """A learned pattern from events"""

    pattern_id: str
    pattern_type: str
    conditions: dict[str, Any]
    outcomes: dict[str, Any]
    confidence: float
    frequency: int
    last_updated: float


class LearningEngine:
    """
    Learning Engine for improving routing decisions

    This class provides learning capabilities that enable AgentDev to improve
    routing decisions over time based on outcomes and user feedback.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the Learning Engine"""
        self.config = config or {}
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer

        # Learning data storage
        self.learning_events: list[LearningEvent] = []
        self.learned_patterns: dict[str, LearningPattern] = {}
        self.routing_improvements: dict[str, Any] = {}

        # Performance tracking
        self.learning_metrics = {
            "total_events": 0,
            "patterns_learned": 0,
            "improvements_applied": 0,
            "accuracy_improvement": 0.0,
        }

        if self.logger:
            self.logger.info("🧠 Learning Engine initialized")

    async def record_learning_event(
        self,
        event_type: LearningEventType,
        data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ):
        """Record a learning event"""
        event_id = f"event_{int(time.time() * 1000)}"
        event = LearningEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            data=data,
            context=context or {},
        )

        self.learning_events.append(event)
        self.learning_metrics["total_events"] += 1

        # Keep only recent events (last 1000)
        if len(self.learning_events) > 1000:
            self.learning_events = self.learning_events[-1000:]

        # Trigger pattern learning
        await self._learn_from_event(event)
        if self.logger:
            self.logger.debug(f"Recorded learning event: {event_type.value}")

    async def _learn_from_event(self, event: LearningEvent):
        """Learn patterns from a learning event"""
        try:
            if event.event_type == LearningEventType.ROUTING_DECISION:
                await self._learn_from_routing_decision(event)
            elif event.event_type == LearningEventType.TASK_COMPLETION:
                await self._learn_from_task_completion(event)
            elif event.event_type == LearningEventType.USER_FEEDBACK:
                await self._learn_from_user_feedback(event)
            elif event.event_type == LearningEventType.ERROR_EVENT:
                await self._learn_from_error_event(event)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error learning from event: {e}")

    async def _learn_from_routing_decision(self, event: LearningEvent):
        """Learn from routing decisions"""
        data = event.data

        # Extract routing information
        task_type = data.get("task_type")
        complexity = data.get("complexity")
        selected_agent = data.get("selected_agent")
        confidence = data.get("confidence", 0.0)

        # Create pattern key
        pattern_key = f"routing_{task_type}_{complexity}"

        # Update or create pattern
        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_updated = time.time()
        else:
            pattern = LearningPattern(
                pattern_id=pattern_key,
                pattern_type="routing_decision",
                conditions={"task_type": task_type, "complexity": complexity},
                outcomes={"selected_agent": selected_agent, "confidence": confidence},
                confidence=confidence,
                frequency=1,
                last_updated=time.time(),
            )
            self.learned_patterns[pattern_key] = pattern
            self.learning_metrics["patterns_learned"] += 1

    async def _learn_from_task_completion(self, event: LearningEvent):
        """Learn from task completion outcomes"""
        data = event.data

        # Extract completion information
        success = data.get("success", False)
        duration = data.get("duration", 0.0)
        agent_used = data.get("agent_used")
        task_type = data.get("task_type")

        # Update routing improvements based on outcomes
        improvement_key = f"outcome_{task_type}_{agent_used}"

        if improvement_key not in self.routing_improvements:
            self.routing_improvements[improvement_key] = {
                "success_count": 0,
                "failure_count": 0,
                "avg_duration": 0.0,
                "total_duration": 0.0,
            }

        improvement = self.routing_improvements[improvement_key]

        if success:
            improvement["success_count"] += 1
        else:
            improvement["failure_count"] += 1

        improvement["total_duration"] += duration
        improvement["avg_duration"] = improvement["total_duration"] / (
            improvement["success_count"] + improvement["failure_count"]
        )

    async def _learn_from_user_feedback(self, event: LearningEvent):
        """Learn from user feedback"""
        data = event.data

        # Extract feedback information
        satisfaction = data.get("satisfaction", 0.0)  # 0.0 to 1.0
        data.get("feedback_type", "general")
        data.get("task_context", {})

        # Update learning metrics
        if satisfaction > 0.7:  # Positive feedback
            self.learning_metrics["accuracy_improvement"] += 0.01
        elif satisfaction < 0.3:  # Negative feedback
            self.learning_metrics["accuracy_improvement"] -= 0.01

        # Keep accuracy improvement in reasonable bounds
        self.learning_metrics["accuracy_improvement"] = max(
            -0.5, min(0.5, self.learning_metrics["accuracy_improvement"])
        )

    async def _learn_from_error_event(self, event: LearningEvent):
        """Learn from error events"""
        data = event.data

        # Extract error information
        error_type = data.get("error_type", "unknown")
        error_context = data.get("context", {})
        severity = data.get("severity", "medium")

        # Create error pattern
        pattern_key = f"error_{error_type}_{severity}"

        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_updated = time.time()
        else:
            pattern = LearningPattern(
                pattern_id=pattern_key,
                pattern_type="error_pattern",
                conditions={"error_type": error_type, "severity": severity},
                outcomes={"context": error_context},
                confidence=0.8,
                frequency=1,
                last_updated=time.time(),
            )
            self.learned_patterns[pattern_key] = pattern
            self.learning_metrics["patterns_learned"] += 1

    async def get_routing_suggestions(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get routing suggestions based on learned patterns"""

        suggestions = {
            "recommended_agent": None,
            "confidence": 0.0,
            "reasoning": "No learned patterns available",
            "alternatives": [],
            "warnings": [],
        }

        # Look for learned patterns
        pattern_key = f"routing_{task_type.value}_{complexity.value}"

        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            suggestions["recommended_agent"] = pattern.outcomes.get("selected_agent")
            suggestions["confidence"] = pattern.confidence
            suggestions["reasoning"] = f"Based on {pattern.frequency} similar cases"

        # Check outcome improvements
        for agent_type in AgentType:
            improvement_key = f"outcome_{task_type.value}_{agent_type.value}"
            if improvement_key in self.routing_improvements:
                improvement = self.routing_improvements[improvement_key]
                success_rate = improvement["success_count"] / (
                    improvement["success_count"] + improvement["failure_count"]
                )

                if success_rate > 0.8:  # High success rate
                    suggestions["alternatives"].append(
                        {
                            "agent": agent_type.value,
                            "success_rate": success_rate,
                            "avg_duration": improvement["avg_duration"],
                        }
                    )
                elif success_rate < 0.3:  # Low success rate
                    suggestions["warnings"].append(
                        f"Avoid {agent_type.value} for this task type"
                    )

        # Sort alternatives by success rate
        suggestions["alternatives"].sort(key=lambda x: x["success_rate"], reverse=True)

        return suggestions

    async def apply_learned_improvements(self) -> dict[str, Any]:
        """Apply learned improvements to the system"""
        improvements_applied = {
            "routing_rules_updated": 0,
            "agent_preferences_updated": 0,
            "error_handling_improved": 0,
            "performance_optimizations": 0,
        }

        # Update routing rules based on learned patterns
        for _pattern_id, pattern in self.learned_patterns.items():
            if pattern.pattern_type == "routing_decision" and pattern.confidence > 0.8:
                improvements_applied["routing_rules_updated"] += 1

        # Update agent preferences based on outcomes
        for _improvement_key, improvement in self.routing_improvements.items():
            success_rate = improvement["success_count"] / (
                improvement["success_count"] + improvement["failure_count"]
            )
            if success_rate > 0.9:  # Very high success rate
                improvements_applied["agent_preferences_updated"] += 1

        # Count error handling improvements
        error_patterns = [
            p
            for p in self.learned_patterns.values()
            if p.pattern_type == "error_pattern"
        ]
        improvements_applied["error_handling_improved"] = len(error_patterns)

        # Count performance optimizations
        if self.learning_metrics["accuracy_improvement"] > 0:
            improvements_applied["performance_optimizations"] += 1

        self.learning_metrics["improvements_applied"] += sum(
            improvements_applied.values()
        )

        return improvements_applied

    def get_learning_metrics(self) -> dict[str, Any]:
        """Get current learning metrics"""
        return self.learning_metrics.copy()

    def get_learned_patterns(
        self, pattern_type: str | None = None
    ) -> dict[str, LearningPattern]:
        """Get learned patterns, optionally filtered by type"""
        if pattern_type:
            return {
                k: v
                for k, v in self.learned_patterns.items()
                if v.pattern_type == pattern_type
            }
        return self.learned_patterns.copy()

    def export_learning_data(self) -> dict[str, Any]:
        """Export learning data for analysis"""
        return {
            "learning_metrics": self.learning_metrics,
            "learned_patterns": {
                k: asdict(v) for k, v in self.learned_patterns.items()
            },
            "routing_improvements": self.routing_improvements,
            "recent_events": [asdict(e) for e in self.learning_events[-100:]],
        }


# Global learning engine instance
_learning_engine_instance: LearningEngine | None = None


def get_learning_engine(config: dict[str, Any] | None = None) -> LearningEngine:
    """Get or create global LearningEngine instance"""
    global _learning_engine_instance

    if _learning_engine_instance is None:
        _learning_engine_instance = LearningEngine(config)

    return _learning_engine_instance


# Convenience functions for common operations
async def record_routing_decision(
    task_type: TaskType,
    complexity: TaskComplexity,
    selected_agent: AgentType,
    confidence: float,
    context: dict[str, Any] | None = None,
):
    """Convenience function to record a routing decision"""
    engine = get_learning_engine()
    await engine.record_learning_event(
        LearningEventType.ROUTING_DECISION,
        {
            "task_type": task_type.value,
            "complexity": complexity.value,
            "selected_agent": selected_agent.value,
            "confidence": confidence,
        },
        context,
    )


async def record_task_completion(
    success: bool,
    duration: float,
    agent_used: AgentType,
    task_type: TaskType,
    context: dict[str, Any] | None = None,
):
    """Convenience function to record task completion"""
    engine = get_learning_engine()
    await engine.record_learning_event(
        LearningEventType.TASK_COMPLETION,
        {
            "success": success,
            "duration": duration,
            "agent_used": agent_used.value,
            "task_type": task_type.value,
        },
        context,
    )