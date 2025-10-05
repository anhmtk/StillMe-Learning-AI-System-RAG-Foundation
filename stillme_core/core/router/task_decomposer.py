"""
Task Decomposer - Complex Task Breakdown and Planning
====================================================

This module provides intelligent task decomposition capabilities that enable
AgentDev to break down complex requests into manageable subtasks with proper
dependencies, sequencing, and resource allocation.

Author: StillMe AI Framework
Version: 1.0.0
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Import StillMe core components
try:
    from ..observability.logger import get_logger
    from ..observability.metrics import get_metrics_collector
    from ..observability.tracer import get_tracer
    from .intelligent_router import AgentType, TaskComplexity, TaskType
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


class SubtaskStatus(Enum):
    """Status of subtasks"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class DependencyType(Enum):
    """Types of dependencies between subtasks"""

    SEQUENTIAL = "sequential"  # Must complete before next
    PARALLEL = "parallel"  # Can run simultaneously
    CONDITIONAL = "conditional"  # Depends on condition
    RESOURCE = "resource"  # Shares resource


@dataclass
class Subtask:
    """Individual subtask in a decomposed task"""

    id: str
    title: str
    description: str
    task_type: TaskType
    complexity: TaskComplexity
    estimated_duration: float  # in seconds
    required_skills: list[str]
    assigned_agent: AgentType | None
    dependencies: list[str]  # IDs of dependent subtasks
    dependency_type: DependencyType
    priority: float  # 0.0 to 1.0
    status: SubtaskStatus
    created_at: float
    started_at: float | None = None
    completed_at: float | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None


@dataclass
class TaskDecomposition:
    """Complete decomposition of a complex task"""

    task_id: str
    original_request: str
    main_task_type: TaskType
    main_complexity: TaskComplexity
    subtasks: list[Subtask]
    total_estimated_duration: float
    critical_path: list[str]  # IDs of subtasks on critical path
    parallel_groups: list[list[str]]  # Groups of subtasks that can run in parallel
    resource_requirements: dict[str, Any]
    success_criteria: list[str]
    created_at: float
    status: SubtaskStatus
    progress_percentage: float = 0.0


class TaskDecomposer:
    """
    Task Decomposer for breaking down complex tasks

    This class provides intelligent task decomposition capabilities that enable
    AgentDev to handle complex requests by breaking them into manageable pieces.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the Task Decomposer"""
        self.config = config or {}
        self.logger = logger
        self.metrics = metrics
        self.tracer = tracer

        # Decomposition patterns and templates
        self.decomposition_patterns = self._load_decomposition_patterns()
        self.task_templates = self._load_task_templates()
        self.skill_requirements = self._load_skill_requirements()

        # Performance tracking
        self.decomposition_history = []
        self.performance_metrics = {
            "total_decompositions": 0,
            "successful_decompositions": 0,
            "avg_subtasks_per_decomposition": 0.0,
            "avg_decomposition_time": 0.0,
        }

        if self.logger:
            self.logger.info("🔧 Task Decomposer initialized")

    def _load_decomposition_patterns(self) -> dict[str, Any]:
        """Load patterns for task decomposition"""
        return {
            "feature_development": {
                "phases": [
                    "analysis",
                    "design",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                "dependencies": {
                    "analysis": [],
                    "design": ["analysis"],
                    "implementation": ["design"],
                    "testing": ["implementation"],
                    "documentation": ["implementation"],
                },
                "parallel_opportunities": [["testing", "documentation"]],
            },
            "bug_fix": {
                "phases": [
                    "investigation",
                    "analysis",
                    "fix",
                    "testing",
                    "verification",
                ],
                "dependencies": {
                    "investigation": [],
                    "analysis": ["investigation"],
                    "fix": ["analysis"],
                    "testing": ["fix"],
                    "verification": ["testing"],
                },
                "parallel_opportunities": [],
            },
            "code_review": {
                "phases": [
                    "initial_review",
                    "detailed_analysis",
                    "recommendations",
                    "follow_up",
                ],
                "dependencies": {
                    "initial_review": [],
                    "detailed_analysis": ["initial_review"],
                    "recommendations": ["detailed_analysis"],
                    "follow_up": ["recommendations"],
                },
                "parallel_opportunities": [],
            },
            "refactoring": {
                "phases": [
                    "assessment",
                    "planning",
                    "refactoring",
                    "testing",
                    "validation",
                ],
                "dependencies": {
                    "assessment": [],
                    "planning": ["assessment"],
                    "refactoring": ["planning"],
                    "testing": ["refactoring"],
                    "validation": ["testing"],
                },
                "parallel_opportunities": [],
            },
            "deployment": {
                "phases": [
                    "preparation",
                    "testing",
                    "deployment",
                    "verification",
                    "monitoring",
                ],
                "dependencies": {
                    "preparation": [],
                    "testing": ["preparation"],
                    "deployment": ["testing"],
                    "verification": ["deployment"],
                    "monitoring": ["verification"],
                },
                "parallel_opportunities": [["verification", "monitoring"]],
            },
        }

    def _load_task_templates(self) -> dict[TaskType, dict[str, Any]]:
        """Load templates for different task types"""
        return {
            TaskType.FEATURE_DEVELOPMENT: {
                "default_phases": [
                    "analysis",
                    "design",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                "required_skills": ["programming", "architecture", "testing"],
                "estimated_base_time": 1800,  # 30 minutes
                "complexity_multiplier": {
                    TaskComplexity.SIMPLE: 0.5,
                    TaskComplexity.MEDIUM: 1.0,
                    TaskComplexity.COMPLEX: 2.0,
                    TaskComplexity.CRITICAL: 3.0,
                },
            },
            TaskType.BUG_FIX: {
                "default_phases": [
                    "investigation",
                    "analysis",
                    "fix",
                    "testing",
                    "verification",
                ],
                "required_skills": ["debugging", "programming", "testing"],
                "estimated_base_time": 900,  # 15 minutes
                "complexity_multiplier": {
                    TaskComplexity.SIMPLE: 0.3,
                    TaskComplexity.MEDIUM: 0.7,
                    TaskComplexity.COMPLEX: 1.5,
                    TaskComplexity.CRITICAL: 2.5,
                },
            },
            TaskType.CODE_REVIEW: {
                "default_phases": [
                    "initial_review",
                    "detailed_analysis",
                    "recommendations",
                    "follow_up",
                ],
                "required_skills": ["code_analysis", "best_practices"],
                "estimated_base_time": 600,  # 10 minutes
                "complexity_multiplier": {
                    TaskComplexity.SIMPLE: 0.5,
                    TaskComplexity.MEDIUM: 1.0,
                    TaskComplexity.COMPLEX: 1.8,
                    TaskComplexity.CRITICAL: 2.5,
                },
            },
            TaskType.REFACTORING: {
                "default_phases": [
                    "assessment",
                    "planning",
                    "refactoring",
                    "testing",
                    "validation",
                ],
                "required_skills": ["programming", "architecture", "testing"],
                "estimated_base_time": 1200,  # 20 minutes
                "complexity_multiplier": {
                    TaskComplexity.SIMPLE: 0.6,
                    TaskComplexity.MEDIUM: 1.2,
                    TaskComplexity.COMPLEX: 2.2,
                    TaskComplexity.CRITICAL: 3.5,
                },
            },
            TaskType.DEPLOYMENT: {
                "default_phases": [
                    "preparation",
                    "testing",
                    "deployment",
                    "verification",
                    "monitoring",
                ],
                "required_skills": ["devops", "deployment", "monitoring"],
                "estimated_base_time": 900,  # 15 minutes
                "complexity_multiplier": {
                    TaskComplexity.SIMPLE: 0.4,
                    TaskComplexity.MEDIUM: 0.8,
                    TaskComplexity.COMPLEX: 1.6,
                    TaskComplexity.CRITICAL: 2.8,
                },
            },
        }

    def _load_skill_requirements(self) -> dict[str, list[str]]:
        """Load skill requirements for different task types"""
        return {
            "programming": ["code_analysis", "debugging", "architecture"],
            "testing": ["unit_testing", "integration_testing", "validation"],
            "documentation": ["technical_writing", "code_analysis"],
            "deployment": ["devops", "infrastructure", "monitoring"],
            "analysis": ["code_analysis", "problem_solving", "investigation"],
            "architecture": ["system_design", "scalability", "performance"],
        }

    async def decompose_task(
        self,
        request: str,
        task_type: TaskType,
        complexity: TaskComplexity,
        context: dict[str, Any] | None = None,
    ) -> TaskDecomposition:
        """
        Decompose a complex task into manageable subtasks

        Args:
            request: Original user request
            task_type: Type of task to decompose
            complexity: Complexity level of the task
            context: Additional context information

        Returns:
            TaskDecomposition with subtasks and dependencies
        """
        start_time = time.time()
        task_id = f"task_{int(time.time() * 1000)}"

        with self.tracer.start_span("decompose_task") as span:
            span.set_attribute("task_type", task_type.value)
            span.set_attribute("complexity", complexity.value)
            span.set_attribute("task_id", task_id)

            try:
                # Step 1: Analyze the request for decomposition hints
                decomposition_hints = await self._analyze_decomposition_hints(
                    request, context
                )
                span.set_attribute("decomposition_hints", len(decomposition_hints))

                # Step 2: Generate subtasks based on task type and complexity
                subtasks = await self._generate_subtasks(
                    request, task_type, complexity, decomposition_hints
                )
                span.set_attribute("subtasks_count", len(subtasks))

                # Step 3: Calculate dependencies and critical path
                dependencies = self._calculate_dependencies(subtasks, task_type)
                critical_path = self._calculate_critical_path(subtasks, dependencies)
                span.set_attribute("critical_path_length", len(critical_path))

                # Step 4: Identify parallel execution opportunities
                parallel_groups = self._identify_parallel_groups(subtasks, dependencies)
                span.set_attribute("parallel_groups", len(parallel_groups))

                # Step 5: Calculate resource requirements
                resource_requirements = self._calculate_resource_requirements(subtasks)

                # Step 6: Define success criteria
                success_criteria = self._define_success_criteria(
                    request, task_type, complexity
                )

                # Step 7: Calculate total estimated duration
                total_duration = self._calculate_total_duration(
                    subtasks, critical_path, parallel_groups
                )

                # Create decomposition
                decomposition = TaskDecomposition(
                    task_id=task_id,
                    original_request=request,
                    main_task_type=task_type,
                    main_complexity=complexity,
                    subtasks=subtasks,
                    total_estimated_duration=total_duration,
                    critical_path=critical_path,
                    parallel_groups=parallel_groups,
                    resource_requirements=resource_requirements,
                    success_criteria=success_criteria,
                    created_at=start_time,
                    status=SubtaskStatus.PENDING,
                )

                # Record metrics
                processing_time = time.time() - start_time
                self._record_decomposition_metrics(decomposition, processing_time)

                # Log decomposition
                self._log_decomposition(decomposition, processing_time)

                return decomposition

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error decomposing task: {e}")
                span.record_exception(e)
                raise

    async def _analyze_decomposition_hints(
        self, request: str, context: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """Analyze request for hints about how to decompose it"""
        hints = []
        request_lower = request.lower()

        # Look for explicit phase mentions
        phase_keywords = {
            "first": ["first", "initially", "start with"],
            "then": ["then", "next", "after that", "subsequently"],
            "finally": ["finally", "lastly", "at the end"],
            "parallel": ["parallel", "simultaneously", "at the same time"],
            "optional": ["optional", "if needed", "if possible"],
        }

        for phase_type, keywords in phase_keywords.items():
            for keyword in keywords:
                if keyword in request_lower:
                    hints.append(
                        {
                            "type": phase_type,
                            "keyword": keyword,
                            "position": request_lower.find(keyword),
                        }
                    )

        # Look for numbered steps
        import re

        numbered_steps = re.findall(r"(\d+)\.?\s+([^.!?]+)", request)
        for step_num, step_text in numbered_steps:
            hints.append(
                {
                    "type": "numbered_step",
                    "step_number": int(step_num),
                    "step_text": step_text.strip(),
                }
            )

        # Look for conditional statements
        conditional_keywords = ["if", "when", "unless", "provided that"]
        for keyword in conditional_keywords:
            if keyword in request_lower:
                hints.append({"type": "conditional", "keyword": keyword})

        return hints

    async def _generate_subtasks(
        self,
        request: str,
        task_type: TaskType,
        complexity: TaskComplexity,
        hints: list[dict[str, Any]],
    ) -> list[Subtask]:
        """Generate subtasks based on task type, complexity, and hints"""
        subtasks = []

        # Get template for task type
        template = self.task_templates.get(
            task_type, self.task_templates[TaskType.GENERAL]
        )
        phases = template["default_phases"]
        base_time = template["estimated_base_time"]
        complexity_multiplier = template["complexity_multiplier"].get(complexity, 1.0)

        # Adjust phases based on complexity
        if complexity == TaskComplexity.SIMPLE:
            # Simplify phases for simple tasks
            phases = phases[:3]  # Take first 3 phases
        elif complexity == TaskComplexity.CRITICAL:
            # Add additional phases for critical tasks
            phases = phases + ["validation", "monitoring"]

        # Generate subtasks for each phase
        for i, phase in enumerate(phases):
            subtask_id = f"{task_type.value}_{phase}_{i}"

            # Calculate estimated duration for this phase
            phase_duration = (base_time / len(phases)) * complexity_multiplier

            # Adjust duration based on phase complexity
            phase_complexity_multipliers = {
                "analysis": 0.8,
                "design": 1.2,
                "implementation": 1.5,
                "testing": 1.0,
                "documentation": 0.6,
                "investigation": 1.1,
                "fix": 1.3,
                "verification": 0.9,
                "assessment": 0.7,
                "planning": 1.0,
                "refactoring": 1.4,
                "validation": 0.8,
                "preparation": 0.9,
                "deployment": 1.2,
                "monitoring": 0.5,
            }

            phase_multiplier = phase_complexity_multipliers.get(phase, 1.0)
            phase_duration *= phase_multiplier

            # Determine task type for this phase
            phase_task_type = self._map_phase_to_task_type(phase, task_type)

            # Determine complexity for this phase
            phase_complexity = self._map_phase_to_complexity(phase, complexity)

            # Get required skills for this phase
            required_skills = self._get_phase_skills(phase, task_type)

            # Create subtask
            subtask = Subtask(
                id=subtask_id,
                title=self._generate_subtask_title(phase, task_type, request),
                description=self._generate_subtask_description(
                    phase, task_type, request
                ),
                task_type=phase_task_type,
                complexity=phase_complexity,
                estimated_duration=phase_duration,
                required_skills=required_skills,
                assigned_agent=None,  # Will be assigned later
                dependencies=[],  # Will be calculated later
                dependency_type=DependencyType.SEQUENTIAL,
                priority=self._calculate_phase_priority(phase, i, len(phases)),
                status=SubtaskStatus.PENDING,
                created_at=time.time(),
            )

            subtasks.append(subtask)

        # Apply hints to modify subtasks
        subtasks = self._apply_decomposition_hints(subtasks, hints, request)

        return subtasks

    def _map_phase_to_task_type(self, phase: str, main_task_type: TaskType) -> TaskType:
        """Map a phase to its corresponding task type"""
        phase_mapping = {
            "analysis": TaskType.ANALYSIS,
            "design": TaskType.ANALYSIS,
            "implementation": TaskType.FEATURE_DEVELOPMENT,
            "testing": TaskType.TESTING,
            "documentation": TaskType.DOCUMENTATION,
            "investigation": TaskType.ANALYSIS,
            "fix": TaskType.BUG_FIX,
            "verification": TaskType.TESTING,
            "assessment": TaskType.ANALYSIS,
            "planning": TaskType.ANALYSIS,
            "refactoring": TaskType.REFACTORING,
            "validation": TaskType.TESTING,
            "preparation": TaskType.ANALYSIS,
            "deployment": TaskType.DEPLOYMENT,
            "monitoring": TaskType.MONITORING,
        }

        return phase_mapping.get(phase, main_task_type)

    def _map_phase_to_complexity(
        self, phase: str, main_complexity: TaskComplexity
    ) -> TaskComplexity:
        """Map a phase to its complexity level"""
        # Most phases inherit the main complexity
        base_complexity = main_complexity

        # Some phases are inherently more or less complex
        complexity_adjustments = {
            "analysis": -1,  # Usually simpler
            "design": 0,  # Same as main
            "implementation": 0,  # Same as main
            "testing": -1,  # Usually simpler
            "documentation": -2,  # Usually much simpler
            "investigation": 0,  # Same as main
            "fix": 0,  # Same as main
            "verification": -1,  # Usually simpler
            "assessment": -1,  # Usually simpler
            "planning": 0,  # Same as main
            "refactoring": 0,  # Same as main
            "validation": -1,  # Usually simpler
            "preparation": -1,  # Usually simpler
            "deployment": 0,  # Same as main
            "monitoring": -2,  # Usually much simpler
        }

        adjustment = complexity_adjustments.get(phase, 0)
        complexity_values = [
            TaskComplexity.SIMPLE,
            TaskComplexity.MEDIUM,
            TaskComplexity.COMPLEX,
            TaskComplexity.CRITICAL,
        ]
        current_index = complexity_values.index(base_complexity)
        new_index = max(0, min(len(complexity_values) - 1, current_index + adjustment))

        return complexity_values[new_index]

    def _get_phase_skills(self, phase: str, task_type: TaskType) -> list[str]:
        """Get required skills for a specific phase"""
        base_skills = {
            "analysis": ["analysis", "problem_solving"],
            "design": ["architecture", "system_design"],
            "implementation": ["programming", "code_analysis"],
            "testing": ["testing", "validation"],
            "documentation": ["technical_writing", "documentation"],
            "investigation": ["analysis", "debugging"],
            "fix": ["programming", "debugging"],
            "verification": ["testing", "validation"],
            "assessment": ["analysis", "evaluation"],
            "planning": ["planning", "architecture"],
            "refactoring": ["programming", "architecture"],
            "validation": ["testing", "verification"],
            "preparation": ["planning", "analysis"],
            "deployment": ["devops", "deployment"],
            "monitoring": ["monitoring", "analysis"],
        }

        phase_skills = base_skills.get(phase, ["general"])

        # Add task-specific skills
        task_specific_skills = {
            TaskType.FEATURE_DEVELOPMENT: ["programming", "architecture"],
            TaskType.BUG_FIX: ["debugging", "programming"],
            TaskType.CODE_REVIEW: ["code_analysis", "best_practices"],
            TaskType.REFACTORING: ["programming", "architecture"],
            TaskType.DEPLOYMENT: ["devops", "infrastructure"],
        }

        additional_skills = task_specific_skills.get(task_type, [])
        all_skills = list(set(phase_skills + additional_skills))

        return all_skills

    def _generate_subtask_title(
        self, phase: str, task_type: TaskType, request: str
    ) -> str:
        """Generate a descriptive title for a subtask"""
        phase_titles = {
            "analysis": "Analyze Requirements",
            "design": "Design Solution",
            "implementation": "Implement Solution",
            "testing": "Test Implementation",
            "documentation": "Create Documentation",
            "investigation": "Investigate Issue",
            "fix": "Fix Issue",
            "verification": "Verify Fix",
            "assessment": "Assess Current State",
            "planning": "Plan Approach",
            "refactoring": "Refactor Code",
            "validation": "Validate Changes",
            "preparation": "Prepare Environment",
            "deployment": "Deploy Solution",
            "monitoring": "Monitor Results",
        }

        base_title = phase_titles.get(phase, f"Execute {phase.title()}")

        # Add context from request if short enough
        if len(request) < 50:
            return f"{base_title}: {request}"
        else:
            return base_title

    def _generate_subtask_description(
        self, phase: str, task_type: TaskType, request: str
    ) -> str:
        """Generate a detailed description for a subtask"""
        phase_descriptions = {
            "analysis": "Analyze the requirements and constraints for the task",
            "design": "Design the solution architecture and approach",
            "implementation": "Implement the designed solution",
            "testing": "Test the implementation to ensure it works correctly",
            "documentation": "Create or update documentation for the solution",
            "investigation": "Investigate the root cause of the issue",
            "fix": "Implement the fix for the identified issue",
            "verification": "Verify that the fix resolves the issue",
            "assessment": "Assess the current state and identify areas for improvement",
            "planning": "Plan the detailed approach for the task",
            "refactoring": "Refactor the code to improve quality and maintainability",
            "validation": "Validate that the changes meet the requirements",
            "preparation": "Prepare the environment and resources for the task",
            "deployment": "Deploy the solution to the target environment",
            "monitoring": "Monitor the solution to ensure it operates correctly",
        }

        base_description = phase_descriptions.get(
            phase, f"Execute the {phase} phase of the task"
        )

        return f"{base_description}. Original request: {request[:200]}{'...' if len(request) > 200 else ''}"

    def _calculate_phase_priority(
        self, phase: str, phase_index: int, total_phases: int
    ) -> float:
        """Calculate priority for a phase"""
        # Earlier phases generally have higher priority
        base_priority = 1.0 - (phase_index / total_phases)

        # Some phases are more critical
        critical_phases = ["implementation", "fix", "deployment"]
        if phase in critical_phases:
            base_priority += 0.2

        # Some phases are less critical
        low_priority_phases = ["documentation", "monitoring"]
        if phase in low_priority_phases:
            base_priority -= 0.1

        return max(0.0, min(1.0, base_priority))

    def _apply_decomposition_hints(
        self, subtasks: list[Subtask], hints: list[dict[str, Any]], request: str
    ) -> list[Subtask]:
        """Apply decomposition hints to modify subtasks"""
        # This is a simplified implementation
        # In a real system, this would be more sophisticated

        for hint in hints:
            if hint["type"] == "numbered_step":
                # Add explicit step subtask
                step_subtask = Subtask(
                    id=f"explicit_step_{hint['step_number']}",
                    title=f"Step {hint['step_number']}",
                    description=hint["step_text"],
                    task_type=TaskType.GENERAL,
                    complexity=TaskComplexity.MEDIUM,
                    estimated_duration=300,  # 5 minutes default
                    required_skills=["general"],
                    assigned_agent=None,
                    dependencies=[],
                    dependency_type=DependencyType.SEQUENTIAL,
                    priority=0.8,
                    status=SubtaskStatus.PENDING,
                    created_at=time.time(),
                )
                subtasks.append(step_subtask)

        return subtasks

    def _calculate_dependencies(
        self, subtasks: list[Subtask], task_type: TaskType
    ) -> dict[str, list[str]]:
        """Calculate dependencies between subtasks"""
        dependencies = {}

        # Get dependency pattern for task type
        pattern = self.decomposition_patterns.get(task_type.value, {})
        phase_dependencies = pattern.get("dependencies", {})

        # Create mapping from phase names to subtask IDs
        phase_to_id = {}
        for subtask in subtasks:
            # Extract phase from subtask ID
            phase = subtask.id.split("_")[1] if "_" in subtask.id else subtask.id
            phase_to_id[phase] = subtask.id

        # Apply dependencies
        for subtask in subtasks:
            phase = subtask.id.split("_")[1] if "_" in subtask.id else subtask.id
            subtask_dependencies = []

            if phase in phase_dependencies:
                for dep_phase in phase_dependencies[phase]:
                    if dep_phase in phase_to_id:
                        subtask_dependencies.append(phase_to_id[dep_phase])

            dependencies[subtask.id] = subtask_dependencies
            subtask.dependencies = subtask_dependencies

        return dependencies

    def _calculate_critical_path(
        self, subtasks: list[Subtask], dependencies: dict[str, list[str]]
    ) -> list[str]:
        """Calculate the critical path through the subtasks"""
        # Simple critical path calculation
        # In a real system, this would use proper critical path method (CPM)

        # Find subtasks with no dependencies (start nodes)
        start_subtasks = [s for s in subtasks if not s.dependencies]

        if not start_subtasks:
            # If no start subtasks, use first subtask
            return [subtasks[0].id] if subtasks else []

        # Find the longest path (simplified)
        longest_path = []
        max_duration = 0

        def calculate_path_duration(path: list[str]) -> float:
            return sum(s.estimated_duration for s in subtasks if s.id in path)

        def find_longest_path(current_path: list[str], current_subtask: Subtask):
            nonlocal longest_path, max_duration

            current_path = current_path + [current_subtask.id]
            duration = calculate_path_duration(current_path)

            if duration > max_duration:
                max_duration = duration
                longest_path = current_path.copy()

            # Find next subtasks
            next_subtasks = [
                s for s in subtasks if current_subtask.id in s.dependencies
            ]

            for next_subtask in next_subtasks:
                find_longest_path(current_path, next_subtask)

        # Start from each start subtask
        for start_subtask in start_subtasks:
            find_longest_path([], start_subtask)

        return longest_path

    def _identify_parallel_groups(
        self, subtasks: list[Subtask], dependencies: dict[str, list[str]]
    ) -> list[list[str]]:
        """Identify groups of subtasks that can run in parallel"""
        parallel_groups = []

        # Get parallel opportunities from patterns
        task_type = subtasks[0].task_type if subtasks else TaskType.GENERAL
        pattern = self.decomposition_patterns.get(task_type.value, {})
        parallel_opportunities = pattern.get("parallel_opportunities", [])

        # Convert phase names to subtask IDs
        phase_to_id = {}
        for subtask in subtasks:
            phase = subtask.id.split("_")[1] if "_" in subtask.id else subtask.id
            phase_to_id[phase] = subtask.id

        # Create parallel groups
        for opportunity in parallel_opportunities:
            group = []
            for phase in opportunity:
                if phase in phase_to_id:
                    group.append(phase_to_id[phase])

            if len(group) > 1:
                parallel_groups.append(group)

        return parallel_groups

    def _calculate_resource_requirements(
        self, subtasks: list[Subtask]
    ) -> dict[str, Any]:
        """Calculate resource requirements for all subtasks"""
        requirements = {
            "cpu_intensive": False,
            "memory_intensive": False,
            "network_required": False,
            "storage_required": False,
            "specialized_tools": set(),
            "estimated_total_time": sum(s.estimated_duration for s in subtasks),
        }

        for subtask in subtasks:
            # Check if any subtask requires specific resources
            if "programming" in subtask.required_skills:
                requirements["cpu_intensive"] = True

            if "testing" in subtask.required_skills:
                requirements["memory_intensive"] = True

            if "deployment" in subtask.required_skills:
                requirements["network_required"] = True

            if "documentation" in subtask.required_skills:
                requirements["storage_required"] = True

            # Collect specialized tools
            for skill in subtask.required_skills:
                if skill in ["devops", "deployment"]:
                    requirements["specialized_tools"].add("deployment_tools")
                elif skill in ["testing"]:
                    requirements["specialized_tools"].add("testing_framework")
                elif skill in ["monitoring"]:
                    requirements["specialized_tools"].add("monitoring_tools")

        # Convert set to list for JSON serialization
        requirements["specialized_tools"] = list(requirements["specialized_tools"])

        return requirements

    def _define_success_criteria(
        self, request: str, task_type: TaskType, complexity: TaskComplexity
    ) -> list[str]:
        """Define success criteria for the task"""
        criteria = []

        # Base criteria for all tasks
        criteria.append("All subtasks completed successfully")
        criteria.append("No critical errors or failures")

        # Task-specific criteria
        if task_type == TaskType.FEATURE_DEVELOPMENT:
            criteria.append("Feature implemented according to requirements")
            criteria.append("Code passes all tests")
            criteria.append("Documentation updated")

        elif task_type == TaskType.BUG_FIX:
            criteria.append("Bug is fixed and verified")
            criteria.append("No regression introduced")
            criteria.append("Fix is properly tested")

        elif task_type == TaskType.CODE_REVIEW:
            criteria.append("Code review completed")
            criteria.append("Issues identified and documented")
            criteria.append("Recommendations provided")

        elif task_type == TaskType.REFACTORING:
            criteria.append("Code refactored successfully")
            criteria.append("Functionality preserved")
            criteria.append("Code quality improved")

        elif task_type == TaskType.DEPLOYMENT:
            criteria.append("Deployment completed successfully")
            criteria.append("System is operational")
            criteria.append("Monitoring is active")

        # Complexity-based criteria
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]:
            criteria.append("Performance requirements met")
            criteria.append("Security considerations addressed")

        return criteria

    def _calculate_total_duration(
        self,
        subtasks: list[Subtask],
        critical_path: list[str],
        parallel_groups: list[list[str]],
    ) -> float:
        """Calculate total estimated duration considering parallelization"""
        if not subtasks:
            return 0.0

        # Calculate critical path duration
        critical_path_duration = sum(
            s.estimated_duration for s in subtasks if s.id in critical_path
        )

        # Calculate parallel savings
        parallel_savings = 0.0
        for group in parallel_groups:
            if len(group) > 1:
                group_duration = max(
                    s.estimated_duration for s in subtasks if s.id in group
                )
                sequential_duration = sum(
                    s.estimated_duration for s in subtasks if s.id in group
                )
                parallel_savings += sequential_duration - group_duration

        # Total duration is critical path minus parallel savings
        total_duration = critical_path_duration - parallel_savings

        return max(0.0, total_duration)

    def _record_decomposition_metrics(
        self, decomposition: TaskDecomposition, processing_time: float
    ):
        """Record decomposition performance metrics"""
        if self.metrics:
            self.metrics.increment_counter("task_decompositions_total")
            self.metrics.increment_counter(
                f"task_decompositions_by_type_{decomposition.main_task_type.value}"
            )
            self.metrics.increment_counter(
                f"task_decompositions_by_complexity_{decomposition.main_complexity.value}"
            )
            self.metrics.record_histogram(
                "task_decomposition_time_seconds", processing_time
            )
            self.metrics.record_histogram(
                "subtasks_per_decomposition", len(decomposition.subtasks)
            )
            # Note: record_gauge might not exist, using record_histogram instead
            self.metrics.record_histogram("decomposition_confidence", 0.8)

        # Update performance metrics
        self.performance_metrics["total_decompositions"] += 1
        self.performance_metrics["successful_decompositions"] += 1

        # Update average subtasks per decomposition
        total_decompositions = self.performance_metrics["total_decompositions"]
        current_avg = self.performance_metrics["avg_subtasks_per_decomposition"]
        self.performance_metrics["avg_subtasks_per_decomposition"] = (
            current_avg * (total_decompositions - 1) + len(decomposition.subtasks)
        ) / total_decompositions

        # Update average decomposition time
        current_avg_time = self.performance_metrics["avg_decomposition_time"]
        self.performance_metrics["avg_decomposition_time"] = (
            current_avg_time * (total_decompositions - 1) + processing_time
        ) / total_decompositions

    def _log_decomposition(
        self, decomposition: TaskDecomposition, processing_time: float
    ):
        """Log decomposition for debugging and analysis"""
        if self.logger:
            self.logger.info(
                "Task decomposed successfully",
                extra={
                    "task_id": decomposition.task_id,
                    "task_type": decomposition.main_task_type.value,
                    "complexity": decomposition.main_complexity.value,
                    "subtasks_count": len(decomposition.subtasks),
                    "total_duration": decomposition.total_estimated_duration,
                    "critical_path_length": len(decomposition.critical_path),
                    "parallel_groups": len(decomposition.parallel_groups),
                    "processing_time": processing_time,
                },
            )

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def get_decomposition_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent decomposition history"""
        return self.decomposition_history[-limit:]

    async def update_subtask_status(
        self,
        task_id: str,
        subtask_id: str,
        status: SubtaskStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ):
        """Update the status of a subtask"""
        # This would typically update a database or storage system
        # For now, we'll just log the update
        if self.logger:
            self.logger.info(
                "Subtask status updated",
                extra={
                    "task_id": task_id,
                    "subtask_id": subtask_id,
                    "status": status.value,
                    "has_result": result is not None,
                    "has_error": error_message is not None,
                },
            )

    def export_decomposition_data(self) -> dict[str, Any]:
        """Export decomposition data for analysis"""
        return {
            "decomposition_patterns": self.decomposition_patterns,
            "task_templates": {k.value: v for k, v in self.task_templates.items()},
            "performance_metrics": self.performance_metrics,
            "recent_history": self.decomposition_history[
                -50:
            ],  # Last 50 decompositions
        }


# Global decomposer instance
_decomposer_instance: TaskDecomposer | None = None


def get_task_decomposer(config: dict[str, Any] | None = None) -> TaskDecomposer:
    """Get or create global TaskDecomposer instance"""
    global _decomposer_instance

    if _decomposer_instance is None:
        _decomposer_instance = TaskDecomposer(config)

    return _decomposer_instance


# Convenience functions for common operations
async def decompose_task(
    request: str,
    task_type: TaskType,
    complexity: TaskComplexity,
    context: dict[str, Any] | None = None,
) -> TaskDecomposition:
    """Convenience function to decompose a task"""
    decomposer = get_task_decomposer()
    return await decomposer.decompose_task(request, task_type, complexity, context)
