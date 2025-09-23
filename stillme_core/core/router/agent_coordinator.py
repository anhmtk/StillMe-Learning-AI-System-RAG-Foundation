"""
Agent Coordinator - Multi-Agent Coordination and Management
==========================================================

This module provides intelligent coordination capabilities that enable AgentDev
to manage and coordinate multiple agents working on complex tasks, including:
- Agent assignment and load balancing
- Task distribution and synchronization
- Progress monitoring and error handling
- Result aggregation and quality assurance

Author: StillMe AI Framework
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from pathlib import Path

# Import StillMe core components
try:
    from ..observability.logger import get_logger
    from ..observability.metrics import get_metrics_collector, MetricType
    from ..observability.tracer import get_tracer
    from .intelligent_router import AgentType, TaskComplexity, TaskType  # type: ignore
    from .task_decomposer import Subtask, SubtaskStatus, TaskDecomposition  # type: ignore
except ImportError:
    # Fallback for standalone execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "observability"))
try:
    from stillme_core.observability.logger import get_logger
except ImportError:
    pass

try:
    from stillme_core.observability.metrics import get_metrics_collector, MetricType
except ImportError:
    pass  # type: ignore

try:
    from stillme_core.observability.tracer import get_tracer
except ImportError:
    pass
    
    # Define fallback types if imports fail
    from enum import Enum
    
    class AgentType(Enum):
        AGENTDEV = "agentdev"
        CODE_REVIEWER = "code_reviewer"
        TESTER = "tester"
        DOCUMENTER = "documenter"
        DEPLOYER = "deployer"
        ANALYST = "analyst"
        GENERAL = "general"
    
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
    
    from dataclasses import dataclass
    from typing import List, Optional, Set
    
    @dataclass
    class Subtask:
        id: str
        task_type: TaskType
        complexity: TaskComplexity
        required_skills: Set[str]
        estimated_duration: float
        dependencies: List[str]
    
    class SubtaskStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    @dataclass
    class TaskDecomposition:
        task_id: str
        original_request: str
        main_task_type: TaskType
        main_complexity: TaskComplexity
        subtasks: List[Subtask]
        success_criteria: List[str]
        parallel_groups: List[List[str]]
    
    # Mock the router imports for standalone execution

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


class CoordinationStrategy(Enum):
    """Strategies for coordinating multiple agents"""
    SEQUENTIAL = "sequential"        # Agents work one after another
    PARALLEL = "parallel"           # Agents work simultaneously
    PIPELINE = "pipeline"           # Agents work in a pipeline
    HIERARCHICAL = "hierarchical"   # One agent coordinates others
    COLLABORATIVE = "collaborative" # Agents collaborate on same task


class AgentStatus(Enum):
    """Status of agents in the coordination system"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class AgentInfo:
    """Information about an agent"""
    agent_type: AgentType
    agent_id: str
    status: AgentStatus
    capabilities: List[str]
    current_load: float  # 0.0 to 1.0
    performance_score: float  # 0.0 to 1.0
    last_activity: float
    error_count: int
    success_count: int


@dataclass
class CoordinationPlan:
    """Plan for coordinating multiple agents"""
    plan_id: str
    strategy: CoordinationStrategy
    agent_assignments: Dict[str, List[Subtask]]  # agent_id -> subtasks
    dependencies: Dict[str, List[str]]  # subtask_id -> dependent subtask_ids
    estimated_completion_time: float
    resource_requirements: Dict[str, Any]
    success_criteria: List[str]
    fallback_plans: List[str]


@dataclass
class CoordinationResult:
    """Result of agent coordination"""
    plan_id: str
    success: bool
    completed_subtasks: List[str]
    failed_subtasks: List[str]
    total_duration: float
    agent_performance: Dict[str, Dict[str, Any]]
    final_result: Optional[Dict[str, Any]]
    error_messages: List[str]


class AgentCoordinator:
    """
    Agent Coordinator for managing multiple agents
    
    This class provides intelligent coordination capabilities that enable
    AgentDev to manage and coordinate multiple agents working on complex tasks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Agent Coordinator"""
        self.config = config or {}
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer
        
        # Agent registry and management
        self.registered_agents: Dict[str, AgentInfo] = {}
        self.agent_handlers: Dict[AgentType, Callable] = {}
        self.coordination_history: List[CoordinationResult] = []
        
        # Performance tracking
        self.performance_metrics = {
            "total_coordinations": 0,
            "successful_coordinations": 0,
            "avg_coordination_time": 0.0,
            "agent_utilization": 0.0,
            "task_completion_rate": 0.0
        }
        
        # Initialize default agents
        self._initialize_default_agents()
        
from stillme_core.observability.logger import get_logger
        self.logger.info("🤝 Agent Coordinator initialized")
    
    def _initialize_default_agents(self):
        """Initialize default agents in the system"""
        default_agents = [
            {
                "agent_type": AgentType.AGENTDEV,
                "agent_id": "agentdev_main",
                "capabilities": ["code_review", "bug_fix", "feature_development", "testing", "documentation"],
                "performance_score": 0.9
            },
            {
                "agent_type": AgentType.CODE_REVIEWER,
                "agent_id": "code_reviewer_1",
                "capabilities": ["code_review", "analysis"],
                "performance_score": 0.95
            },
            {
                "agent_type": AgentType.TESTER,
                "agent_id": "tester_1",
                "capabilities": ["testing", "validation"],
                "performance_score": 0.88
            },
            {
                "agent_type": AgentType.DOCUMENTER,
                "agent_id": "documenter_1",
                "capabilities": ["documentation", "explanation"],
                "performance_score": 0.85
            },
            {
                "agent_type": AgentType.ANALYST,
                "agent_id": "analyst_1",
                "capabilities": ["analysis", "debugging", "investigation"],
                "performance_score": 0.92
            }
        ]
        
        for agent_config in default_agents:
            agent_info = AgentInfo(
                agent_type=agent_config["agent_type"],
                agent_id=agent_config["agent_id"],
                status=AgentStatus.AVAILABLE,
                capabilities=agent_config["capabilities"],
                current_load=0.0,
                performance_score=agent_config["performance_score"],
                last_activity=time.time(),
                error_count=0,
                success_count=0
            )
            self.registered_agents[agent_config["agent_id"]] = agent_info
    
    async def coordinate_task_execution(
        self, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """
        Coordinate execution of a decomposed task across multiple agents
        
        Args:
            decomposition: Task decomposition with subtasks
            
        Returns:
            CoordinationResult with execution results
        """
        start_time = time.time()
        plan_id = f"coordination_{int(time.time() * 1000)}"
        
        with self.tracer.start_span("coordinate_task_execution") as span:  # type: ignore
            span.set_attribute("plan_id", plan_id)
            span.set_attribute("subtasks_count", len(decomposition.subtasks))
            span.set_attribute("task_type", decomposition.main_task_type.value)
            
            try:
                # Step 1: Create coordination plan
                plan = await self._create_coordination_plan(decomposition, plan_id)
                span.set_attribute("strategy", plan.strategy.value)
                span.set_attribute("assigned_agents", len(plan.agent_assignments))
                
                # Step 2: Execute coordination plan
                result = await self._execute_coordination_plan(plan, decomposition)
                span.set_attribute("success", result.success)
                span.set_attribute("completed_subtasks", len(result.completed_subtasks))
                
                # Step 3: Record metrics and results
                total_duration = time.time() - start_time
                result.total_duration = total_duration
                self._record_coordination_metrics(result, total_duration)
                
                # Step 4: Log coordination results
                self._log_coordination_result(result, total_duration)
                
                return result
                
            except Exception as e:
from stillme_core.observability.logger import get_logger
                self.logger.error(f"Error coordinating task execution: {e}")
                span.record_exception(e)
                
                # Return failure result
                return CoordinationResult(
                    plan_id=plan_id,
                    success=False,
                    completed_subtasks=[],
                    failed_subtasks=[s.id for s in decomposition.subtasks],
                    total_duration=time.time() - start_time,
                    agent_performance={},
                    final_result=None,
                    error_messages=[str(e)]
                )
    
    async def _create_coordination_plan(
        self, 
        decomposition: TaskDecomposition, 
        plan_id: str
    ) -> CoordinationPlan:
        """Create a coordination plan for the decomposed task"""
        
        # Determine coordination strategy
        strategy = self._determine_coordination_strategy(decomposition)
        
        # Assign subtasks to agents
        agent_assignments = await self._assign_subtasks_to_agents(decomposition.subtasks)
        
        # Calculate dependencies
        dependencies = self._calculate_subtask_dependencies(decomposition.subtasks)
        
        # Estimate completion time
        estimated_time = self._estimate_coordination_time(agent_assignments, dependencies, strategy)
        
        # Define resource requirements
        resource_requirements = self._calculate_coordination_resources(agent_assignments)
        
        # Define success criteria
        success_criteria = decomposition.success_criteria.copy()
        
        # Create fallback plans
        fallback_plans = self._create_fallback_plans(decomposition, strategy)
        
        return CoordinationPlan(
            plan_id=plan_id,
            strategy=strategy,
            agent_assignments=agent_assignments,
            dependencies=dependencies,
            estimated_completion_time=estimated_time,
            resource_requirements=resource_requirements,
            success_criteria=success_criteria,
            fallback_plans=fallback_plans
        )
    
    def _determine_coordination_strategy(self, decomposition: TaskDecomposition) -> CoordinationStrategy:
        """Determine the best coordination strategy for the task"""
        
        # Simple heuristic based on task characteristics
        if decomposition.main_complexity == TaskComplexity.SIMPLE:
            return CoordinationStrategy.SEQUENTIAL
        
        elif decomposition.main_complexity == TaskComplexity.MEDIUM:
            # Check if there are parallel opportunities
            if len(decomposition.parallel_groups) > 0:
                return CoordinationStrategy.PARALLEL
            else:
                return CoordinationStrategy.SEQUENTIAL
        
        elif decomposition.main_complexity == TaskComplexity.COMPLEX:
            # Use hierarchical coordination for complex tasks
            return CoordinationStrategy.HIERARCHICAL
        
        else:  # CRITICAL
            # Use collaborative approach for critical tasks
            return CoordinationStrategy.COLLABORATIVE
    
    async def _assign_subtasks_to_agents(
        self, 
        subtasks: List[Subtask]
    ) -> Dict[str, List[Subtask]]:
        """Assign subtasks to available agents"""
        assignments = {}
        
        # Group subtasks by type and complexity
        subtask_groups = self._group_subtasks_by_characteristics(subtasks)
        
        # Assign each group to appropriate agents
        for group_type, group_subtasks in subtask_groups.items():
            # Find best agent for this group
            best_agent = self._find_best_agent_for_group(group_type, group_subtasks)
            
            if best_agent:
                if best_agent not in assignments:
                    assignments[best_agent] = []
                assignments[best_agent].extend(group_subtasks)
            else:
                # Fallback to AgentDev
                if "agentdev_main" not in assignments:
                    assignments["agentdev_main"] = []
                assignments["agentdev_main"].extend(group_subtasks)
        
        return assignments
    
    def _group_subtasks_by_characteristics(self, subtasks: List[Subtask]) -> Dict[str, List[Subtask]]:
        """Group subtasks by their characteristics"""
        groups = {}
        
        for subtask in subtasks:
            # Create group key based on task type and complexity
            group_key = f"{subtask.task_type.value}_{subtask.complexity.value}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(subtask)
        
        return groups
    
    def _find_best_agent_for_group(
        self, 
        group_type: str, 
        group_subtasks: List[Subtask]
    ) -> Optional[str]:
        """Find the best agent for a group of subtasks"""
        best_agent = None
        best_score = 0.0
        
        for agent_id, agent_info in self.registered_agents.items():
            # Skip if agent is not available
            if agent_info.status != AgentStatus.AVAILABLE:
                continue
            
            # Skip if agent is overloaded
            if agent_info.current_load > 0.8:
                continue
            
            # Calculate suitability score
            score = self._calculate_agent_suitability(agent_info, group_subtasks)
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        return best_agent
    
    def _calculate_agent_suitability(
        self, 
        agent_info: AgentInfo, 
        subtasks: List[Subtask]
    ) -> float:
        """Calculate how suitable an agent is for a group of subtasks"""
        if not subtasks:
            return 0.0
        
        # Base score from performance
        score = agent_info.performance_score
        
        # Adjust for current load (lower load = higher score)
        load_penalty = agent_info.current_load * 0.3
        score -= load_penalty
        
        # Check capability match
        required_skills = set()
        for subtask in subtasks:
            required_skills.update(subtask.required_skills)
        
        agent_capabilities = set(agent_info.capabilities)
        capability_match = len(required_skills.intersection(agent_capabilities)) / len(required_skills)
        score += capability_match * 0.4
        
        # Check task type specialization
        task_types = [s.task_type for s in subtasks]
        type_specialization = self._calculate_type_specialization(agent_info.agent_type, task_types)
        score += type_specialization * 0.2
        
        # Adjust for error rate
        total_tasks = agent_info.error_count + agent_info.success_count
        if total_tasks > 0:
            error_rate = agent_info.error_count / total_tasks
            score -= error_rate * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_type_specialization(
        self, 
        agent_type: AgentType, 
        task_types: List[TaskType]
    ) -> float:
        """Calculate how well an agent type specializes in the given task types"""
        specialization_map = {
            AgentType.AGENTDEV: {
                TaskType.FEATURE_DEVELOPMENT: 1.0,
                TaskType.BUG_FIX: 0.9,
                TaskType.CODE_REVIEW: 0.8,
                TaskType.TESTING: 0.7,
                TaskType.DOCUMENTATION: 0.6
            },
            AgentType.CODE_REVIEWER: {
                TaskType.CODE_REVIEW: 1.0,
                TaskType.ANALYSIS: 0.9,
                TaskType.BUG_FIX: 0.7
            },
            AgentType.TESTER: {
                TaskType.TESTING: 1.0,
                TaskType.VALIDATION: 0.9,  # type: ignore
                TaskType.BUG_FIX: 0.6
            },
            AgentType.DOCUMENTER: {
                TaskType.DOCUMENTATION: 1.0,
                TaskType.ANALYSIS: 0.7
            },
            AgentType.ANALYST: {
                TaskType.ANALYSIS: 1.0,
                TaskType.BUG_FIX: 0.8,
                TaskType.CODE_REVIEW: 0.7
            }
        }
        
        agent_specializations = specialization_map.get(agent_type, {})
        
        if not task_types:
            return 0.0
        
        total_specialization = 0.0
        for task_type in task_types:
            specialization = agent_specializations.get(task_type, 0.3)  # Default low score
            total_specialization += specialization
        
        return total_specialization / len(task_types)
    
    def _calculate_subtask_dependencies(self, subtasks: List[Subtask]) -> Dict[str, List[str]]:
        """Calculate dependencies between subtasks"""
        dependencies = {}
        
        for subtask in subtasks:
            dependencies[subtask.id] = subtask.dependencies.copy()
        
        return dependencies
    
    def _estimate_coordination_time(
        self, 
        agent_assignments: Dict[str, List[Subtask]], 
        dependencies: Dict[str, List[str]], 
        strategy: CoordinationStrategy
    ) -> float:
        """Estimate total coordination time"""
        
        if strategy == CoordinationStrategy.SEQUENTIAL:
            # Sum of all subtask durations
            total_time = 0.0
            for subtasks in agent_assignments.values():
                total_time += sum(s.estimated_duration for s in subtasks)
            return total_time
        
        elif strategy == CoordinationStrategy.PARALLEL:
            # Maximum time across all agents
            max_agent_time = 0.0
            for subtasks in agent_assignments.values():
                agent_time = sum(s.estimated_duration for s in subtasks)
                max_agent_time = max(max_agent_time, agent_time)
            return max_agent_time
        
        elif strategy == CoordinationStrategy.PIPELINE:
            # Pipeline time (simplified)
            return sum(s.estimated_duration for subtasks in agent_assignments.values() for s in subtasks) * 0.7
        
        else:  # HIERARCHICAL or COLLABORATIVE
            # Add coordination overhead
            base_time = sum(s.estimated_duration for subtasks in agent_assignments.values() for s in subtasks)
            return base_time * 1.2  # 20% overhead for coordination
    
    def _calculate_coordination_resources(
        self, 
        agent_assignments: Dict[str, List[Subtask]]
    ) -> Dict[str, Any]:
        """Calculate resource requirements for coordination"""
        resources = {
            "cpu_intensive": False,
            "memory_intensive": False,
            "network_required": False,
            "storage_required": False,
            "concurrent_agents": len(agent_assignments),
            "total_subtasks": sum(len(subtasks) for subtasks in agent_assignments.values())
        }
        
        # Analyze resource requirements from subtasks
        for subtasks in agent_assignments.values():
            for subtask in subtasks:
                if "programming" in subtask.required_skills:
                    resources["cpu_intensive"] = True
                if "testing" in subtask.required_skills:
                    resources["memory_intensive"] = True
                if "deployment" in subtask.required_skills:
                    resources["network_required"] = True
                if "documentation" in subtask.required_skills:
                    resources["storage_required"] = True
        
        return resources
    
    def _create_fallback_plans(
        self, 
        decomposition: TaskDecomposition, 
        strategy: CoordinationStrategy
    ) -> List[str]:
        """Create fallback plans for coordination"""
        fallback_plans = []
        
        # Plan 1: Fallback to sequential execution
        fallback_plans.append("Execute all subtasks sequentially using AgentDev")
        
        # Plan 2: Reduce complexity
        fallback_plans.append("Simplify subtasks and reduce scope")
        
        # Plan 3: Manual intervention
        fallback_plans.append("Request manual intervention for complex subtasks")
        
        # Plan 4: Alternative strategy
        if strategy != CoordinationStrategy.SEQUENTIAL:
            fallback_plans.append("Switch to sequential coordination strategy")
        
        return fallback_plans
    
    async def _execute_coordination_plan(
        self, 
        plan: CoordinationPlan, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """Execute the coordination plan"""
        
        completed_subtasks = []
        failed_subtasks = []
        agent_performance = {}
        error_messages = []
        
        try:
            if plan.strategy == CoordinationStrategy.SEQUENTIAL:
                result = await self._execute_sequential_coordination(plan, decomposition)
            elif plan.strategy == CoordinationStrategy.PARALLEL:
                result = await self._execute_parallel_coordination(plan, decomposition)
            elif plan.strategy == CoordinationStrategy.HIERARCHICAL:
                result = await self._execute_hierarchical_coordination(plan, decomposition)
            else:  # COLLABORATIVE
                result = await self._execute_collaborative_coordination(plan, decomposition)
            
            completed_subtasks = result.completed_subtasks
            failed_subtasks = result.failed_subtasks
            agent_performance = result.agent_performance
            error_messages = result.error_messages
            
        except Exception as e:
            error_messages.append(f"Coordination execution failed: {str(e)}")
            failed_subtasks = [s.id for s in decomposition.subtasks]
        
        # Determine overall success
        success = len(failed_subtasks) == 0 and len(completed_subtasks) > 0
        
        # Aggregate final result
        final_result = self._aggregate_coordination_results(completed_subtasks, decomposition)
        
        return CoordinationResult(
            plan_id=plan.plan_id,
            success=success,
            completed_subtasks=completed_subtasks,
            failed_subtasks=failed_subtasks,
            total_duration=0.0,  # Will be set by caller
            agent_performance=agent_performance,
            final_result=final_result,
            error_messages=error_messages
        )
    
    async def _execute_sequential_coordination(
        self, 
        plan: CoordinationPlan, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """Execute coordination using sequential strategy"""
        completed_subtasks = []
        failed_subtasks = []
        agent_performance = {}
        error_messages = []
        
        # Execute subtasks in dependency order
        remaining_subtasks = {s.id: s for s in decomposition.subtasks}
        completed_set = set()
        
        while remaining_subtasks:
            # Find subtasks that can be executed (dependencies satisfied)
            ready_subtasks = []
            for subtask_id, subtask in remaining_subtasks.items():
                if all(dep in completed_set for dep in subtask.dependencies):
                    ready_subtasks.append(subtask)
            
            if not ready_subtasks:
                # Deadlock - mark remaining as failed
                for subtask_id in remaining_subtasks:
                    failed_subtasks.append(subtask_id)
                error_messages.append("Deadlock detected in sequential execution")
                break
            
            # Execute ready subtasks
            for subtask in ready_subtasks:
                try:
                    # Find assigned agent
                    assigned_agent = None
                    for agent_id, subtasks in plan.agent_assignments.items():
                        if subtask in subtasks:
                            assigned_agent = agent_id
                            break
                    
                    if not assigned_agent:
                        assigned_agent = "agentdev_main"  # Fallback
                    
                    # Execute subtask
                    success = await self._execute_subtask(subtask, assigned_agent)
                    
                    if success:
                        completed_subtasks.append(subtask.id)
                        completed_set.add(subtask.id)
                        
                        # Update agent performance
                        if assigned_agent not in agent_performance:
                            agent_performance[assigned_agent] = {"completed": 0, "failed": 0}
                        agent_performance[assigned_agent]["completed"] += 1
                    else:
                        failed_subtasks.append(subtask.id)
                        if assigned_agent not in agent_performance:
                            agent_performance[assigned_agent] = {"completed": 0, "failed": 0}
                        agent_performance[assigned_agent]["failed"] += 1
                    
                    # Remove from remaining
                    del remaining_subtasks[subtask.id]
                    
                except Exception as e:
                    failed_subtasks.append(subtask.id)
                    error_messages.append(f"Error executing subtask {subtask.id}: {str(e)}")
                    del remaining_subtasks[subtask.id]
        
        return CoordinationResult(
            plan_id=plan.plan_id,
            success=len(failed_subtasks) == 0,
            completed_subtasks=completed_subtasks,
            failed_subtasks=failed_subtasks,
            total_duration=0.0,
            agent_performance=agent_performance,
            final_result=None,
            error_messages=error_messages
        )
    
    async def _execute_parallel_coordination(
        self, 
        plan: CoordinationPlan, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """Execute coordination using parallel strategy"""
        completed_subtasks = []
        failed_subtasks = []
        agent_performance = {}
        error_messages = []
        
        # Create tasks for parallel execution
        tasks = []
        for agent_id, subtasks in plan.agent_assignments.items():
            for subtask in subtasks:
                task = asyncio.create_task(
                    self._execute_subtask_with_agent(subtask, agent_id)
                )
                tasks.append((task, subtask.id, agent_id))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*[task for task, _, _ in tasks], return_exceptions=True)
        
        # Process results
        for (task, subtask_id, agent_id), result in zip(tasks, results):
            if isinstance(result, Exception):
                failed_subtasks.append(subtask_id)
                error_messages.append(f"Error executing subtask {subtask_id}: {str(result)}")
            elif result:
                completed_subtasks.append(subtask_id)
            else:
                failed_subtasks.append(subtask_id)
            
            # Update agent performance
            if agent_id not in agent_performance:
                agent_performance[agent_id] = {"completed": 0, "failed": 0}
            
            if isinstance(result, Exception) or not result:
                agent_performance[agent_id]["failed"] += 1
            else:
                agent_performance[agent_id]["completed"] += 1
        
        return CoordinationResult(
            plan_id=plan.plan_id,
            success=len(failed_subtasks) == 0,
            completed_subtasks=completed_subtasks,
            failed_subtasks=failed_subtasks,
            total_duration=0.0,
            agent_performance=agent_performance,
            final_result=None,
            error_messages=error_messages
        )
    
    async def _execute_hierarchical_coordination(
        self, 
        plan: CoordinationPlan, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """Execute coordination using hierarchical strategy"""
        # AgentDev acts as coordinator
        coordinator_agent = "agentdev_main"
        
        # First, AgentDev analyzes and plans
        analysis_subtask = Subtask(
            id="hierarchical_analysis",
            title="Hierarchical Analysis",
            description="Analyze task and coordinate other agents",
            task_type=TaskType.ANALYSIS,
            complexity=TaskComplexity.MEDIUM,
            estimated_duration=300,
            required_skills=["analysis", "coordination"],
            assigned_agent=AgentType.AGENTDEV,
            dependencies=[],
            dependency_type=None,  # type: ignore
            priority=1.0,
            status=SubtaskStatus.PENDING,
            created_at=time.time()
        )
        
        # Execute analysis
        analysis_success = await self._execute_subtask(analysis_subtask, coordinator_agent)
        
        if not analysis_success:
            return CoordinationResult(
                plan_id=plan.plan_id,
                success=False,
                completed_subtasks=[],
                failed_subtasks=[s.id for s in decomposition.subtasks],
                total_duration=0.0,
                agent_performance={},
                final_result=None,
                error_messages=["Hierarchical coordination analysis failed"]
            )
        
        # Then execute other subtasks with coordination
        return await self._execute_sequential_coordination(plan, decomposition)
    
    async def _execute_collaborative_coordination(
        self, 
        plan: CoordinationPlan, 
        decomposition: TaskDecomposition
    ) -> CoordinationResult:
        """Execute coordination using collaborative strategy"""
        # For collaborative strategy, we'll use a simplified approach
        # In a real system, this would involve more sophisticated collaboration
        
        completed_subtasks = []
        failed_subtasks = []
        agent_performance = {}
        error_messages = []
        
        # Group subtasks by complexity
        simple_subtasks = [s for s in decomposition.subtasks if s.complexity == TaskComplexity.SIMPLE]
        complex_subtasks = [s for s in decomposition.subtasks if s.complexity != TaskComplexity.SIMPLE]
        
        # Handle simple subtasks in parallel
        if simple_subtasks:
            simple_result = await self._execute_parallel_coordination(
                CoordinationPlan(
                    plan_id=plan.plan_id + "_simple",
                    strategy=CoordinationStrategy.PARALLEL,
                    agent_assignments={"agentdev_main": simple_subtasks},
                    dependencies={},
                    estimated_completion_time=0.0,
                    resource_requirements={},
                    success_criteria=[],
                    fallback_plans=[]
                ),
                TaskDecomposition(
                    task_id=decomposition.task_id,
                    original_request=decomposition.original_request,
                    main_task_type=decomposition.main_task_type,
                    main_complexity=decomposition.main_complexity,
                    subtasks=simple_subtasks,
                    total_estimated_duration=0.0,
                    critical_path=[],
                    parallel_groups=[],
                    resource_requirements={},
                    success_criteria=[],
                    created_at=time.time(),
                    status=SubtaskStatus.PENDING
                )
            )
            
            completed_subtasks.extend(simple_result.completed_subtasks)
            failed_subtasks.extend(simple_result.failed_subtasks)
            agent_performance.update(simple_result.agent_performance)
            error_messages.extend(simple_result.error_messages)
        
        # Handle complex subtasks collaboratively
        if complex_subtasks:
            # Use hierarchical approach for complex subtasks
            complex_result = await self._execute_hierarchical_coordination(
                CoordinationPlan(
                    plan_id=plan.plan_id + "_complex",
                    strategy=CoordinationStrategy.HIERARCHICAL,
                    agent_assignments={"agentdev_main": complex_subtasks},
                    dependencies={},
                    estimated_completion_time=0.0,
                    resource_requirements={},
                    success_criteria=[],
                    fallback_plans=[]
                ),
                TaskDecomposition(
                    task_id=decomposition.task_id,
                    original_request=decomposition.original_request,
                    main_task_type=decomposition.main_task_type,
                    main_complexity=decomposition.main_complexity,
                    subtasks=complex_subtasks,
                    total_estimated_duration=0.0,
                    critical_path=[],
                    parallel_groups=[],
                    resource_requirements={},
                    success_criteria=[],
                    created_at=time.time(),
                    status=SubtaskStatus.PENDING
                )
            )
            
            completed_subtasks.extend(complex_result.completed_subtasks)
            failed_subtasks.extend(complex_result.failed_subtasks)
            agent_performance.update(complex_result.agent_performance)
            error_messages.extend(complex_result.error_messages)
        
        return CoordinationResult(
            plan_id=plan.plan_id,
            success=len(failed_subtasks) == 0,
            completed_subtasks=completed_subtasks,
            failed_subtasks=failed_subtasks,
            total_duration=0.0,
            agent_performance=agent_performance,
            final_result=None,
            error_messages=error_messages
        )
    
    async def _execute_subtask_with_agent(self, subtask: Subtask, agent_id: str) -> bool:
        """Execute a subtask with a specific agent"""
        try:
            return await self._execute_subtask(subtask, agent_id)
        except Exception as e:
from stillme_core.observability.logger import get_logger
            self.logger.error(f"Error executing subtask {subtask.id} with agent {agent_id}: {e}")
            return False
    
    async def _execute_subtask(self, subtask: Subtask, agent_id: str) -> bool:
        """Execute a single subtask"""
        try:
            # Update agent status
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.BUSY
                self.registered_agents[agent_id].last_activity = time.time()
            
            # Simulate subtask execution
            # In a real system, this would call the actual agent
            await asyncio.sleep(min(subtask.estimated_duration / 10, 1.0))  # Simulate work
            
            # Simulate success/failure based on complexity and agent performance
            agent_info = self.registered_agents.get(agent_id)
            if agent_info:
                success_probability = agent_info.performance_score * (1.0 - subtask.complexity.value.count('complex') * 0.2)
                success = success_probability > 0.5
            else:
                success = True  # Default to success for unknown agents
            
            # Update agent status
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.AVAILABLE
                if success:
                    self.registered_agents[agent_id].success_count += 1
                else:
                    self.registered_agents[agent_id].error_count += 1
            
            return success
            
        except Exception as e:
from stillme_core.observability.logger import get_logger
            self.logger.error(f"Error executing subtask {subtask.id}: {e}")
            
            # Update agent status
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.ERROR
                self.registered_agents[agent_id].error_count += 1
            
            return False
    
    def _aggregate_coordination_results(
        self, 
        completed_subtasks: List[str], 
        decomposition: TaskDecomposition
    ) -> Dict[str, Any]:
        """Aggregate results from completed subtasks"""
        if not completed_subtasks:
            return {"status": "failed", "message": "No subtasks completed"}
        
        # Find completed subtask objects
        completed_objects = [s for s in decomposition.subtasks if s.id in completed_subtasks]
        
        # Aggregate basic information
        result = {
            "status": "success",
            "completed_subtasks": len(completed_subtasks),
            "total_subtasks": len(decomposition.subtasks),
            "completion_rate": len(completed_subtasks) / len(decomposition.subtasks),
            "task_type": decomposition.main_task_type.value,
            "complexity": decomposition.main_complexity.value,
            "subtask_results": []
        }
        
        # Add individual subtask results
        for subtask in completed_objects:
            result["subtask_results"].append({
                "id": subtask.id,
                "title": subtask.title,
                "type": subtask.task_type.value,
                "complexity": subtask.complexity.value,
                "duration": subtask.estimated_duration
            })
        
        return result
    
    def _record_coordination_metrics(
        self, 
        result: CoordinationResult, 
        duration: float
    ):
        """Record coordination performance metrics"""
        self.metrics.increment_counter("agent_coordinations_total")
        self.metrics.increment_counter(f"agent_coordinations_success_{result.success}")
        self.metrics.record_histogram("agent_coordination_duration_seconds", duration)
        self.metrics.record_histogram("agent_coordination_subtasks_completed", len(result.completed_subtasks))
        self.metrics.record_histogram("agent_coordination_subtasks_failed", len(result.failed_subtasks))
        
        # Update performance metrics
        self.performance_metrics["total_coordinations"] += 1
        if result.success:
            self.performance_metrics["successful_coordinations"] += 1
        
        # Update average coordination time
        total_coordinations = self.performance_metrics["total_coordinations"]
        current_avg = self.performance_metrics["avg_coordination_time"]
        self.performance_metrics["avg_coordination_time"] = (
            (current_avg * (total_coordinations - 1) + duration) / total_coordinations
        )
        
        # Update task completion rate
        if result.completed_subtasks or result.failed_subtasks:
            completion_rate = len(result.completed_subtasks) / (len(result.completed_subtasks) + len(result.failed_subtasks))
            self.performance_metrics["task_completion_rate"] = completion_rate
    
    def _log_coordination_result(
        self, 
        result: CoordinationResult, 
        duration: float
    ):
        """Log coordination result for debugging and analysis"""
from stillme_core.observability.logger import get_logger
        self.logger.info(
            f"Agent coordination completed",
            extra={
                "plan_id": result.plan_id,
                "success": result.success,
                "completed_subtasks": len(result.completed_subtasks),
                "failed_subtasks": len(result.failed_subtasks),
                "total_duration": duration,
                "agent_count": len(result.agent_performance),
                "error_count": len(result.error_messages)
            }
        )
    
    def register_agent(
        self, 
        agent_type: AgentType, 
        agent_id: str, 
        capabilities: List[str],
        performance_score: float = 0.8
    ):
        """Register a new agent in the coordination system"""
        agent_info = AgentInfo(
            agent_type=agent_type,
            agent_id=agent_id,
            status=AgentStatus.AVAILABLE,
            capabilities=capabilities,
            current_load=0.0,
            performance_score=performance_score,
            last_activity=time.time(),
            error_count=0,
            success_count=0
        )
        
        self.registered_agents[agent_id] = agent_info
from stillme_core.observability.logger import get_logger
        self.logger.info(f"Registered agent: {agent_id} ({agent_type.value})")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the coordination system"""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
from stillme_core.observability.logger import get_logger
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentInfo]:
        """Get status information for a specific agent"""
        return self.registered_agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get information about all registered agents"""
        return self.registered_agents.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_coordination_history(self, limit: int = 100) -> List[CoordinationResult]:
        """Get recent coordination history"""
        return self.coordination_history[-limit:]
    
    def export_coordination_data(self) -> Dict[str, Any]:
        """Export coordination data for analysis"""
        return {
            "registered_agents": {k: asdict(v) for k, v in self.registered_agents.items()},
            "performance_metrics": self.performance_metrics,
            "recent_history": [asdict(r) for r in self.coordination_history[-50:]]
        }


# Global coordinator instance
_coordinator_instance: Optional[AgentCoordinator] = None


def get_agent_coordinator(config: Optional[Dict[str, Any]] = None) -> AgentCoordinator:
    """Get or create global AgentCoordinator instance"""
    global _coordinator_instance
    
    if _coordinator_instance is None:
        _coordinator_instance = AgentCoordinator(config)
    
    return _coordinator_instance


# Convenience functions for common operations
async def coordinate_task_execution(decomposition: TaskDecomposition) -> CoordinationResult:
    """Convenience function to coordinate task execution"""
    coordinator = get_agent_coordinator()
    return await coordinator.coordinate_task_execution(decomposition)
