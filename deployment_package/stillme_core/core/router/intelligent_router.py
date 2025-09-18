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
Version: 1.0.0
"""

import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# Import StillMe core components
try:
    from stillme_core.observability.logger import get_logger
except ImportError:
    pass

try:
    from stillme_core.observability.metrics import MetricType, get_metrics_collector
except ImportError:
    pass

try:
    from stillme_core.observability.tracer import get_tracer
except ImportError:
    pass

# Initialize observability components safely
try:
    logger = get_logger(__name__)
except NameError:
    logger = None

try:
    metrics = get_metrics_collector()
except NameError:
    metrics = None

try:
    tracer = get_tracer()
except NameError:
    tracer = None


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


@dataclass
class RequestContext:
    """Context information for routing decisions"""

    user_id: str
    session_id: str
    timestamp: float
    urgency: str = "normal"  # low, normal, high, critical
    user_preferences: Dict[str, Any] = None  # type: ignore
    previous_requests: List[Dict] = None  # type: ignore
    system_load: Dict[str, float] = None  # type: ignore

    def __post_init__(self):
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
    required_skills: List[str]
    dependencies: List[str]
    priority_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    suggested_agents: List[AgentType]
    reasoning: str


@dataclass
class RoutingDecision:
    """Final routing decision"""

    primary_agent: AgentType
    secondary_agents: List[AgentType]
    coordination_strategy: str
    estimated_time: float
    resource_requirements: Dict[str, Any]
    fallback_plan: str
    reasoning: str
    confidence: float


class IntelligentRouter:
    """
    Intelligent Router for StillMe AI Framework

    This class provides context-aware routing capabilities that enable
    AgentDev to make intelligent decisions about request handling.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Intelligent Router"""
        self.config = config or {}
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer

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

from stillme_core.observability.logger import get_logger
        self.logger.info("🧠 Intelligent Router initialized")

    def _load_routing_rules(self) -> Dict[str, Any]:
        """Load routing rules from configuration"""
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

    def _load_agent_capabilities(self) -> Dict[AgentType, Dict[str, Any]]:
        """Load agent capabilities and specializations"""
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

    def _load_complexity_patterns(self) -> Dict[str, float]:
        """Load patterns for complexity assessment"""
        return {  # type: ignore
            "simple_keywords": ["simple", "easy", "quick", "basic"],
            "complex_keywords": [
                "complex",
                "advanced",
                "sophisticated",
                "comprehensive",
            ],
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

        Args:
            request: User request text
            context: Request context information

        Returns:
            RoutingDecision with routing strategy
        """
        start_time = time.time()

        try:
from stillme_core.observability.tracer import get_tracer
            span = self.tracer.start_span("intelligent_route")
            if hasattr(span, "set_attribute"):
                span.set_attribute("request_length", len(request))
                span.set_attribute("user_id", context.user_id)
                span.set_attribute("urgency", context.urgency)
        except:
            span = None

        try:
            # Step 1: Analyze the request
            analysis = await self._analyze_request(request, context)
            if span and hasattr(span, "set_attribute"):
                span.set_attribute("task_type", analysis.task_type.value)
                span.set_attribute("complexity", analysis.complexity.value)
                span.set_attribute("confidence", analysis.confidence)

            # Step 2: Make routing decision
            decision = await self._make_routing_decision(analysis, context)
            if span and hasattr(span, "set_attribute"):
                span.set_attribute("primary_agent", decision.primary_agent.value)
                span.set_attribute("decision_confidence", decision.confidence)

            # Step 3: Record metrics
            processing_time = time.time() - start_time
            self._record_routing_metrics(analysis, decision, processing_time)

            # Step 4: Log decision
            self._log_routing_decision(request, analysis, decision, processing_time)

            return decision

        except Exception as e:
from stillme_core.observability.logger import get_logger
            self.logger.error(f"Error in routing request: {e}")
            if span and hasattr(span, "record_exception"):
                span.record_exception(e)

            # Fallback to simple routing
            return self._fallback_routing(request, context)

    async def _analyze_request(
        self, request: str, context: RequestContext
    ) -> TaskAnalysis:
        """Analyze user request to determine task characteristics"""

        # Analyze task type
        task_type = self._identify_task_type(request)

        # Assess complexity
        complexity = self._assess_complexity(request, context)

        # Estimate duration
        estimated_duration = self._estimate_duration(request, complexity)

        # Identify required skills
        required_skills = self._identify_required_skills(request, task_type)

        # Find dependencies
        dependencies = self._find_dependencies(request, context)

        # Calculate priority
        priority_score = self._calculate_priority(request, context, complexity)

        # Calculate confidence
        confidence = self._calculate_confidence(request, task_type, complexity)

        # Suggest agents
        suggested_agents = self._suggest_agents(task_type, complexity, required_skills)

        # Generate reasoning
        reasoning = self._generate_reasoning(task_type, complexity, suggested_agents)

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            estimated_duration=estimated_duration,
            required_skills=required_skills,
            dependencies=dependencies,
            priority_score=priority_score,
            confidence=confidence,
            suggested_agents=suggested_agents,
            reasoning=reasoning,
        )

    def _identify_task_type(self, request: str) -> TaskType:
        """Identify the type of task from request text"""
        request_lower = request.lower()

        # Check against routing rules
        for task_name, rules in self.routing_rules.items():
            keywords = rules["keywords"]
            if any(keyword in request_lower for keyword in keywords):
                return TaskType(task_name)

        # Default to general if no specific type identified
        return TaskType.GENERAL

    def _assess_complexity(
        self, request: str, context: RequestContext
    ) -> TaskComplexity:
        """Assess task complexity based on various factors"""

        complexity_score = 0.0
        request_lower = request.lower()

        # Factor 1: Request length
        length = len(request)
        if length < self.complexity_patterns["length_thresholds"]["simple"]:  # type: ignore
            complexity_score += 0.1
        elif length < self.complexity_patterns["length_thresholds"]["medium"]:  # type: ignore
            complexity_score += 0.3
        elif length < self.complexity_patterns["length_thresholds"]["complex"]:  # type: ignore
            complexity_score += 0.6
        else:
            complexity_score += 0.8

        # Factor 2: Technical indicators
        for indicator, weight in self.complexity_patterns[
            "technical_indicators"
        ].items():
            if indicator in request_lower:
                complexity_score += weight * 0.2

        # Factor 3: Complexity keywords
        if any(
            keyword in request_lower
            for keyword in self.complexity_patterns["simple_keywords"]
        ):
            complexity_score -= 0.2
        elif any(
            keyword in request_lower
            for keyword in self.complexity_patterns["complex_keywords"]
        ):
            complexity_score += 0.3

        # Factor 4: Urgency
        if context.urgency == "critical":
            complexity_score += 0.2
        elif context.urgency == "high":
            complexity_score += 0.1

        # Factor 5: Previous similar requests
        if context.previous_requests:
            similar_complexity = self._analyze_historical_complexity(
                context.previous_requests
            )
            complexity_score = (complexity_score + similar_complexity) / 2

        # Normalize and map to enum
        complexity_score = max(0.0, min(1.0, complexity_score))

        if complexity_score < 0.3:
            return TaskComplexity.SIMPLE
        elif complexity_score < 0.6:
            return TaskComplexity.MEDIUM
        elif complexity_score < 0.8:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.CRITICAL

    def _estimate_duration(self, request: str, complexity: TaskComplexity) -> float:
        """Estimate task duration in seconds"""
        base_duration = {
            TaskComplexity.SIMPLE: 60,  # 1 minute
            TaskComplexity.MEDIUM: 300,  # 5 minutes
            TaskComplexity.COMPLEX: 900,  # 15 minutes
            TaskComplexity.CRITICAL: 1800,  # 30 minutes
        }

        # Adjust based on request length
        length_factor = len(request) / 1000  # Normalize to 1000 chars
        duration = base_duration[complexity] * (1 + length_factor * 0.5)

        return duration

    def _identify_required_skills(self, request: str, task_type: TaskType) -> List[str]:
        """Identify required skills for the task"""
        skills = []
        request_lower = request.lower()

        # Technical skills
        if any(
            tech in request_lower for tech in ["python", "javascript", "java", "c++"]
        ):
            skills.append("programming")

        if any(
            tech in request_lower for tech in ["api", "rest", "graphql", "microservice"]
        ):
            skills.append("api_development")

        if any(
            tech in request_lower for tech in ["database", "sql", "mongodb", "redis"]
        ):
            skills.append("database")

        if any(
            tech in request_lower for tech in ["test", "testing", "unit", "integration"]
        ):
            skills.append("testing")

        if any(
            tech in request_lower
            for tech in ["deploy", "docker", "kubernetes", "ci/cd"]
        ):
            skills.append("devops")

        # Task-specific skills
        if task_type == TaskType.CODE_REVIEW:
            skills.extend(["code_analysis", "best_practices"])
        elif task_type == TaskType.BUG_FIX:
            skills.extend(["debugging", "problem_solving"])
        elif task_type == TaskType.FEATURE_DEVELOPMENT:
            skills.extend(["architecture", "design"])

        return list(set(skills))  # Remove duplicates

    def _find_dependencies(self, request: str, context: RequestContext) -> List[str]:
        """Find task dependencies"""
        dependencies = []
        request_lower = request.lower()

        # Check for dependency keywords
        if "after" in request_lower or "then" in request_lower:
            dependencies.append("sequential_execution")

        if "parallel" in request_lower or "simultaneous" in request_lower:
            dependencies.append("parallel_execution")

        if "database" in request_lower:
            dependencies.append("database_access")

        if "api" in request_lower:
            dependencies.append("api_access")

        if "file" in request_lower or "upload" in request_lower:
            dependencies.append("file_system")

        return dependencies

    def _calculate_priority(
        self, request: str, context: RequestContext, complexity: TaskComplexity
    ) -> float:
        """Calculate task priority score (0.0 to 1.0)"""
        priority = 0.5  # Base priority

        # Urgency factor
        urgency_weights = {"low": 0.2, "normal": 0.5, "high": 0.7, "critical": 0.9}
        priority = urgency_weights.get(context.urgency, 0.5)

        # Complexity factor (complex tasks often higher priority)
        if complexity == TaskComplexity.CRITICAL:
            priority += 0.2
        elif complexity == TaskComplexity.COMPLEX:
            priority += 0.1

        # User preference factor
        if context.user_preferences.get("high_priority", False):
            priority += 0.1

        return max(0.0, min(1.0, priority))

    def _calculate_confidence(
        self, request: str, task_type: TaskType, complexity: TaskComplexity
    ) -> float:
        """Calculate confidence in analysis (0.0 to 1.0)"""
        confidence = 0.7  # Base confidence

        # Task type confidence
        if task_type != TaskType.GENERAL:
            confidence += 0.2

        # Complexity confidence (clear complexity is easier to assess)
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.CRITICAL]:
            confidence += 0.1

        # Request clarity
        if len(request) > 50:  # Longer requests often clearer
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def _suggest_agents(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        required_skills: List[str],
    ) -> List[AgentType]:
        """Suggest appropriate agents for the task"""
        suggestions = []

        # Get task-specific preferences
        task_rules = self.routing_rules.get(task_type.value, {})
        preferred_agents = task_rules.get("preferred_agents", [AgentType.AGENTDEV])

        # Filter by complexity and capabilities
        for agent in preferred_agents:
            capabilities = self.agent_capabilities.get(agent, {})
            max_complexity = capabilities.get("max_complexity", 0.5)

            # Check if agent can handle the complexity
            complexity_value = {
                TaskComplexity.SIMPLE: 0.2,
                TaskComplexity.MEDIUM: 0.5,
                TaskComplexity.COMPLEX: 0.8,
                TaskComplexity.CRITICAL: 1.0,
            }[complexity]

            if complexity_value <= max_complexity:
                suggestions.append(agent)

        # Always include AgentDev as fallback
        if AgentType.AGENTDEV not in suggestions:
            suggestions.append(AgentType.AGENTDEV)

        return suggestions[:3]  # Limit to top 3 suggestions

    def _generate_reasoning(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        suggested_agents: List[AgentType],
    ) -> str:
        """Generate human-readable reasoning for the analysis"""
        reasoning_parts = []

        # Task type reasoning
        reasoning_parts.append(f"Identified as {task_type.value} task")

        # Complexity reasoning
        complexity_reasons = {
            TaskComplexity.SIMPLE: "Simple task that can be handled quickly",
            TaskComplexity.MEDIUM: "Medium complexity requiring some expertise",
            TaskComplexity.COMPLEX: "Complex task requiring specialized knowledge",
            TaskComplexity.CRITICAL: "Critical task requiring immediate attention",
        }
        reasoning_parts.append(complexity_reasons[complexity])

        # Agent selection reasoning
        if len(suggested_agents) == 1:
            reasoning_parts.append(f"Best handled by {suggested_agents[0].value}")
        else:
            agent_names = [agent.value for agent in suggested_agents]
            reasoning_parts.append(f"Can be handled by: {', '.join(agent_names)}")

        return ". ".join(reasoning_parts) + "."

    async def _make_routing_decision(
        self, analysis: TaskAnalysis, context: RequestContext
    ) -> RoutingDecision:
        """Make final routing decision based on analysis"""

        # Select primary agent
        primary_agent = analysis.suggested_agents[0]

        # Select secondary agents for coordination
        secondary_agents = (
            analysis.suggested_agents[1:] if len(analysis.suggested_agents) > 1 else []
        )

        # Determine coordination strategy
        if analysis.complexity == TaskComplexity.SIMPLE:
            coordination_strategy = "direct_handling"
        elif analysis.complexity == TaskComplexity.MEDIUM:
            coordination_strategy = "specialist_assignment"
        elif analysis.complexity == TaskComplexity.COMPLEX:
            coordination_strategy = "team_coordination"
        else:  # CRITICAL
            coordination_strategy = "emergency_response"

        # Estimate total time
        estimated_time = analysis.estimated_duration

        # Define resource requirements
        resource_requirements = {
            "cpu_intensive": analysis.complexity
            in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL],
            "memory_intensive": len(analysis.required_skills) > 3,
            "network_required": "api_access" in analysis.dependencies,
            "storage_required": "file_system" in analysis.dependencies,
        }

        # Create fallback plan
        fallback_plan = self._create_fallback_plan(analysis, primary_agent)

        # Generate decision reasoning
        reasoning = self._generate_decision_reasoning(
            analysis, primary_agent, coordination_strategy
        )

        return RoutingDecision(
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            coordination_strategy=coordination_strategy,
            estimated_time=estimated_time,
            resource_requirements=resource_requirements,
            fallback_plan=fallback_plan,
            reasoning=reasoning,
            confidence=analysis.confidence,
        )

    def _create_fallback_plan(
        self, analysis: TaskAnalysis, primary_agent: AgentType
    ) -> str:
        """Create fallback plan if primary agent fails"""
        if primary_agent == AgentType.AGENTDEV:
            return "Fallback to general agent with simplified approach"
        else:
            return (
                f"Fallback to AgentDev with {analysis.task_type.value} specialization"
            )

    def _generate_decision_reasoning(
        self,
        analysis: TaskAnalysis,
        primary_agent: AgentType,
        coordination_strategy: str,
    ) -> str:
        """Generate reasoning for routing decision"""
        reasoning_parts = [
            f"Selected {primary_agent.value} as primary agent",
            f"Using {coordination_strategy} strategy",
            f"Estimated time: {analysis.estimated_duration:.0f} seconds",
            f"Confidence: {analysis.confidence:.1%}",
        ]

        if analysis.required_skills:
            skills_str = ", ".join(analysis.required_skills[:3])
            reasoning_parts.append(f"Required skills: {skills_str}")

        return ". ".join(reasoning_parts) + "."

    def _analyze_historical_complexity(self, previous_requests: List[Dict]) -> float:
        """Analyze complexity of similar historical requests"""
        if not previous_requests:
            return 0.5

        # Simple heuristic: average complexity of last 5 similar requests
        recent_requests = previous_requests[-5:]
        complexities = []

        for req in recent_requests:
            if "complexity" in req:
                complexity_map = {
                    "simple": 0.2,
                    "medium": 0.5,
                    "complex": 0.8,
                    "critical": 1.0,
                }
                complexities.append(complexity_map.get(req["complexity"], 0.5))

        return sum(complexities) / len(complexities) if complexities else 0.5

    def _fallback_routing(
        self, request: str, context: RequestContext
    ) -> RoutingDecision:
        """Fallback routing when analysis fails"""
        return RoutingDecision(
            primary_agent=AgentType.AGENTDEV,
            secondary_agents=[],
            coordination_strategy="direct_handling",
            estimated_time=300,  # 5 minutes default
            resource_requirements={"cpu_intensive": False, "memory_intensive": False},
            fallback_plan="Manual review and routing",
            reasoning="Fallback routing due to analysis error",
            confidence=0.3,
        )

    def _record_routing_metrics(
        self, analysis: TaskAnalysis, decision: RoutingDecision, processing_time: float
    ):
        """Record routing performance metrics"""
        self.metrics.increment_counter("router_requests_total")
        self.metrics.increment_counter(
            f"router_requests_by_type_{analysis.task_type.value}"
        )
        self.metrics.increment_counter(
            f"router_requests_by_complexity_{analysis.complexity.value}"
        )
        self.metrics.record_histogram("router_processing_time_seconds", processing_time)
        self.metrics.record_histogram("router_confidence", decision.confidence)

        # Update performance metrics
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["successful_routes"] += 1

        # Update average processing time
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["avg_processing_time"]
        self.performance_metrics["avg_processing_time"] = (
            current_avg * (total_requests - 1) + processing_time
        ) / total_requests

    def _log_routing_decision(
        self,
        request: str,
        analysis: TaskAnalysis,
        decision: RoutingDecision,
        processing_time: float,
    ):
        """Log routing decision for debugging and analysis"""
from stillme_core.observability.logger import get_logger
        self.logger.info(
            "Routing decision made",
            extra={
                "request_preview": (
                    request[:100] + "..." if len(request) > 100 else request
                ),
                "task_type": analysis.task_type.value,
                "complexity": analysis.complexity.value,
                "primary_agent": decision.primary_agent.value,
                "coordination_strategy": decision.coordination_strategy,
                "estimated_time": decision.estimated_time,
                "confidence": decision.confidence,
                "processing_time": processing_time,
            },
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def get_routing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent routing history"""
        return self.routing_history[-limit:]

    async def update_routing_rules(self, new_rules: Dict[str, Any]):
        """Update routing rules based on learning"""
        self.routing_rules.update(new_rules)
from stillme_core.observability.logger import get_logger
        self.logger.info(f"Updated routing rules: {list(new_rules.keys())}")

    async def learn_from_outcome(
        self, request: str, decision: RoutingDecision, outcome: Dict[str, Any]
    ):
        """Learn from routing outcomes to improve future decisions"""
        # Record outcome
        learning_record = {
            "timestamp": time.time(),
            "request": request,
            "decision": asdict(decision),
            "outcome": outcome,
        }

        self.routing_history.append(learning_record)

        # Keep only recent history
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]

        # Update performance metrics
        if outcome.get("success", False):
            self.performance_metrics["successful_routes"] += 1

        # Calculate success rate
        success_rate = (
            self.performance_metrics["successful_routes"]
            / self.performance_metrics["total_requests"]
        )
        self.performance_metrics["user_satisfaction"] = success_rate

from stillme_core.observability.logger import get_logger
        self.logger.info(
            f"Learned from outcome: success={outcome.get('success', False)}"
        )

    def export_routing_data(self) -> Dict[str, Any]:
        """Export routing data for analysis"""
        return {
            "routing_rules": self.routing_rules,
            "agent_capabilities": self.agent_capabilities,
            "performance_metrics": self.performance_metrics,
            "recent_history": self.routing_history[-50:],  # Last 50 decisions
        }


# Global router instance
_router_instance: Optional[IntelligentRouter] = None


def get_intelligent_router(
    config: Optional[Dict[str, Any]] = None,
) -> IntelligentRouter:
    """Get or create global IntelligentRouter instance"""
    global _router_instance

    if _router_instance is None:
        _router_instance = IntelligentRouter(config)

    return _router_instance


# Convenience functions for common operations
async def route_request(request: str, context: RequestContext) -> RoutingDecision:
    """Convenience function to route a request"""
    router = get_intelligent_router()
    return await router.route_request(request, context)


async def analyze_request(request: str, context: RequestContext) -> TaskAnalysis:
    """Convenience function to analyze a request"""
    router = get_intelligent_router()
    return await router._analyze_request(request, context)
