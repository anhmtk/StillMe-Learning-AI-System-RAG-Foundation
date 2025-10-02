"""
Intelligent Router - Context-Aware Request Routing
=================================================

This module implements the core intelligent routing system that enables AgentDev
to make smart decisions about how to handle user requests, including:
- Intent analysis and context understanding
- Task complexity assessment
- Optimal agent/model selection
- Resource allocation and coordination

Author: StillMe AI Framework
Version: 1.0.1 (Fixed and Optimized)
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

# --- Observability Setup (Import Only Once) ---
# Import StillMe core observability components safely.
try:
    from stillme_core.observability.logger import get_logger  # type: ignore
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from stillme_core.observability.metrics import get_metrics_collector  # type: ignore
    metrics = get_metrics_collector()
except ImportError:
    metrics = None

try:
    from stillme_core.observability.tracer import get_tracer  # type: ignore
    tracer = get_tracer()
except ImportError:
    tracer = None

# Check if observability is enabled
OBSERVABILITY_ENABLED = logger is not None and metrics is not None and tracer is not None


# --- Core Enumerations (Enums) ---


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = "simple"  # Can be handled by single agent
    MEDIUM = "medium"  # Requires specialist agent
    COMPLEX = "complex"  # Needs team coordination
    CRITICAL = "critical"  # High priority, needs immediate attention


class TaskType(Enum):
    """Types of tasks that can be routed"""

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
    """Available agent types for routing"""

    AGENTDEV = "agentdev"  # Main development agent
    CODE_REVIEWER = "code_reviewer"  # Specialized code review
    TESTER = "tester"  # Testing specialist
    DOCUMENTER = "documenter"  # Documentation specialist
    DEPLOYER = "deployer"  # Deployment specialist
    ANALYST = "analyst"  # Analysis specialist
    GENERAL = "general"  # General purpose agent


# --- Data Transfer Objects (DTOs) ---


@dataclass
class RequestContext:
    """Context information for routing decisions"""

    user_id: str
    session_id: str
    timestamp: float
    urgency: str = "normal"  # low, normal, high, critical
    # Fix type hinting and default values for mutable types
    user_preferences: Optional[dict[str, Any]] = None
    previous_requests: Optional[list[dict]] = None
    system_load: Optional[dict[str, float]] = None

    def __post_init__(self):
        """Initializes default values for mutable fields."""
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.previous_requests is None:
            self.previous_requests = []
        if self.system_load is None:
            self.system_load = {}


@dataclass
class TaskAnalysis:
    """Analysis result of a user request"""

    task_type: TaskType
    complexity: TaskComplexity
    estimated_duration: float  # in seconds
    required_skills: list[str]
    dependencies: list[str]
    priority_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    suggested_agents: list[AgentType]
    reasoning: str


@dataclass
class RoutingDecision:
    """Final routing decision"""

    primary_agent: AgentType
    secondary_agents: list[AgentType]
    coordination_strategy: str
    estimated_time: float
    resource_requirements: dict[str, Any]
    fallback_plan: str
    reasoning: str
    confidence: float


# --- Core Router Implementation ---


class IntelligentRouter:
    """
    Intelligent Router for StillMe AI Framework

    This class provides context-aware routing capabilities that enable
    AgentDev to make intelligent decisions about request handling.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the Intelligent Router"""
        self.config = config or {}
        # Assign global observability objects
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer
        self.observability_enabled = OBSERVABILITY_ENABLED

        # Routing rules and patterns
        self.routing_rules = self._load_routing_rules()
        self.agent_capabilities = self._load_agent_capabilities()
        self.complexity_patterns = self._load_complexity_patterns()

        # Performance tracking
        self.routing_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_routes": 0,
            "avg_processing_time": 0.0,
            "user_satisfaction": 0.0,
        }

        if self.logger:
            self.logger.info("🧠 Intelligent Router initialized")

    def _load_routing_rules(self) -> dict[str, Any]:
        """Load routing rules from configuration (Internal Mock)"""
        return {
            "code_review": {
                "keywords": ["review", "check", "analyze", "inspect", "audit"],
                "complexity_threshold": 0.3,
                "preferred_agents": [AgentType.CODE_REVIEWER, AgentType.AGENTDEV],
            },
            "bug_fix": {
                "keywords": ["fix", "bug", "error", "issue", "problem", "debug"],
                "complexity_threshold": 0.5,
                "preferred_agents": [AgentType.AGENTDEV, AgentType.ANALYST],
            },
            "feature_development": {
                "keywords": ["create", "build", "develop", "implement", "add"],
                "complexity_threshold": 0.7,
                "preferred_agents": [AgentType.AGENTDEV],
            },
            "testing": {
                "keywords": ["test", "verify", "validate", "check"],
                "complexity_threshold": 0.4,
                "preferred_agents": [AgentType.TESTER, AgentType.AGENTDEV],
            },
            "documentation": {
                "keywords": ["document", "explain", "describe", "write"],
                "complexity_threshold": 0.2,
                "preferred_agents": [AgentType.DOCUMENTER, AgentType.AGENTDEV],
            },
        }

    def _load_agent_capabilities(self) -> dict[AgentType, dict[str, Any]]:
        """Load agent capabilities and specializations (Internal Mock)"""
        return {
            AgentType.AGENTDEV: {
                "capabilities": [
                    "code_review",
                    "bug_fix",
                    "feature_development",
                    "testing",
                    "documentation",
                ],
                "max_complexity": 1.0,
                "availability": 0.95,
                "performance_score": 0.9,
            },
            AgentType.CODE_REVIEWER: {
                "capabilities": ["code_review", "analysis"],
                "max_complexity": 0.8,
                "availability": 0.9,
                "performance_score": 0.95,
            },
            AgentType.TESTER: {
                "capabilities": ["testing", "validation"],
                "max_complexity": 0.7,
                "availability": 0.85,
                "performance_score": 0.88,
            },
            AgentType.DOCUMENTER: {
                "capabilities": ["documentation", "explanation"],
                "max_complexity": 0.6,
                "availability": 0.9,
                "performance_score": 0.85,
            },
            AgentType.DEPLOYER: {
                "capabilities": ["deployment", "infrastructure"],
                "max_complexity": 0.8,
                "availability": 0.8,
                "performance_score": 0.87,
            },
            AgentType.ANALYST: {
                "capabilities": ["analysis", "debugging", "investigation"],
                "max_complexity": 0.9,
                "availability": 0.85,
                "performance_score": 0.92,
            },
            AgentType.GENERAL: {
                "capabilities": ["general"],
                "max_complexity": 0.5,
                "availability": 0.95,
                "performance_score": 0.7,
            },
        }

    def _load_complexity_patterns(self) -> dict[str, Any]:
        """Load patterns for complexity assessment (Internal Mock)"""
        # Fix: Remove redundant type: ignore and ensure return type is correct
        return {
            "simple_keywords": ["simple", "easy", "quick", "basic"],
            "complex_keywords": [
                "complex",
                "advanced",
                "sophisticated",
                "comprehensive",
            ],
            # Fix: Ensure all thresholds are handled as floats or ints
            "length_thresholds": {"simple": 100, "medium": 500, "complex": 1000},
            "technical_indicators": {
                "architecture": 0.8,
                "microservice": 0.9,
                "distributed": 0.9,
                "scalable": 0.7,
                "optimization": 0.6,
                "security": 0.7,
                "performance": 0.6,
            },
        }

    async def route_request(
        self, request: str, context: RequestContext
    ) -> RoutingDecision:
        """
        Route a user request to the most appropriate agent(s)
        """
        start_time = time.time()
        span = None

        if self.observability_enabled and self.tracer:
            try:
                # Fix: Removed unnecessary re-import
                span = self.tracer.start_span("intelligent_route")
                if hasattr(span, "set_attribute"):
                    span.set_attribute("request_length", len(request))
                    span.set_attribute("user_id", context.user_id)
                    span.set_attribute("urgency", context.urgency)
            except Exception:
                # Handle potential errors during span creation
                span = None

        try:
            # Step 1: Analyze the request (simplified for now)
            analysis = self._simple_analyze_request(request, context)
            if span and hasattr(span, "set_attribute"):
                span.set_attribute("task_type", analysis.task_type.value)
                span.set_attribute("complexity", analysis.complexity.value)

            # Step 2: Make routing decision (simplified)
            decision = self._simple_make_decision(analysis, context)

            # Step 3: Record metrics
            processing_time = time.time() - start_time
            if self.observability_enabled and self.metrics:
                self.metrics.increment_counter("router_requests_total")
                self.metrics.record_histogram("router_processing_time_seconds", processing_time)

            return decision

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in routing request: {e}")
            if span and hasattr(span, "record_exception"):
                span.record_exception(e)

            # Fallback to simple routing
            return self._fallback_routing(request, context)

    def _simple_analyze_request(self, request: str, context: RequestContext) -> TaskAnalysis:
        """Simple request analysis"""
        # Simple task type identification
        request_lower = request.lower()
        if any(keyword in request_lower for keyword in ["review", "check", "analyze"]):
            task_type = TaskType.CODE_REVIEW
        elif any(keyword in request_lower for keyword in ["fix", "bug", "error"]):
            task_type = TaskType.BUG_FIX
        elif any(keyword in request_lower for keyword in ["create", "build", "develop"]):
            task_type = TaskType.FEATURE_DEVELOPMENT
        else:
            task_type = TaskType.GENERAL

        # Simple complexity assessment
        if len(request) < 100:
            complexity = TaskComplexity.SIMPLE
        elif len(request) < 500:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.COMPLEX

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            estimated_duration=60.0,
            required_skills=["general"],
            dependencies=[],
            priority_score=0.5,
            confidence=0.8,
            suggested_agents=[AgentType.AGENTDEV],
            reasoning="Simple analysis based on keywords and length"
        )

    def _simple_make_decision(self, analysis: TaskAnalysis, context: RequestContext) -> RoutingDecision:
        """Simple routing decision"""
        return RoutingDecision(
            primary_agent=AgentType.AGENTDEV,
            secondary_agents=[],
            coordination_strategy="direct_handling",
            estimated_time=analysis.estimated_duration,
            resource_requirements={"cpu_intensive": False, "memory_intensive": False},
            fallback_plan="Manual review",
            reasoning="Simple routing to AgentDev",
            confidence=analysis.confidence
        )

    def _fallback_routing(self, request: str, context: RequestContext) -> RoutingDecision:
        """Fallback routing when analysis fails"""
        return RoutingDecision(
            primary_agent=AgentType.AGENTDEV,
            secondary_agents=[],
            coordination_strategy="direct_handling",
            estimated_time=300.0,
            resource_requirements={"cpu_intensive": False, "memory_intensive": False},
            fallback_plan="Manual review and routing",
            reasoning="Fallback routing due to analysis error",
            confidence=0.3
        )
