"""
Router CLI Commands - Intelligent Routing and Coordination
=========================================================

This module provides CLI commands for the intelligent router system,
enabling users to interact with routing, coordination, and learning features.

Author: StillMe AI Framework
Version: 1.0.0
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

# Import StillMe core components
try:
    from ...router import (
        IntelligentRouter,
        TaskDecomposer,
        AgentCoordinator,
        LearningEngine,
        RouterMemoryManager,
    )
    from ...router.intelligent_router import TaskComplexity, TaskType, AgentType
    from ...router.task_decomposer import TaskDecomposition
    from ...router.agent_coordinator import CoordinationResult
except ImportError:
    # Fallback for standalone execution
    import sys

    sys.path.append(str(Path(__file__).parent.parent.parent / "router"))
try:
try:
try:
try:
try:
                        from intelligent_router import (
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
        IntelligentRouter,
        TaskComplexity,
        TaskType,
        AgentType,
    )
try:
try:
try:
try:
try:
                        from task_decomposer import TaskDecomposer, TaskDecomposition
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
try:
try:
try:
try:
try:
                        from agent_coordinator import AgentCoordinator, CoordinationResult
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
try:
try:
try:
try:
try:
                        from learning_engine import LearningEngine
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
try:
try:
try:
try:
try:
                        from memory_manager import RouterMemoryManager
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass
except ImportError:
    pass

console = Console()
app = typer.Typer(
    name="router",
    help="Intelligent routing and coordination commands",
    rich_markup_mode="rich",
)


@app.command()
def route_request(
    request: str = typer.Argument(..., help="User request to route"),
    complexity: str = typer.Option(
        "medium",
        "--complexity",
        "-c",
        help="Task complexity (simple/medium/complex/critical)",
    ),
    urgency: str = typer.Option(
        "normal", "--urgency", "-u", help="Request urgency (low/normal/high/critical)"
    ),
    user_id: str = typer.Option("default_user", "--user", help="User ID for context"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
):
    """Route a user request to the most appropriate agent"""
    console.print(f"[bold blue]🧠 Routing Request...[/bold blue]")
    console.print(f"📝 Request: {request}")
    console.print(f"⚡ Complexity: {complexity}")
    console.print(f"🚨 Urgency: {urgency}")

    async def _route_request():
        try:
            # Initialize router
            router = IntelligentRouter()

            # Create request context
            from ...router.intelligent_router import RequestContext

            context = RequestContext(
                user_id=user_id,
                session_id=f"session_{int(time.time())}",
                timestamp=time.time(),
                urgency=urgency,
            )

            # Route the request
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Analyzing request...", total=None)

                decision = await router.route_request(request, context)

                progress.update(task, description="✅ Routing completed")

            # Display results
            console.print(f"\n[bold green]🎯 Routing Decision:[/bold green]")

            # Create results table
            table = Table(title="Routing Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Primary Agent", decision.primary_agent.value)
            table.add_row("Strategy", decision.coordination_strategy)
            table.add_row("Estimated Time", f"{decision.estimated_time:.1f} seconds")
            table.add_row("Confidence", f"{decision.confidence:.1%}")
            table.add_row("Reasoning", decision.reasoning)

            if decision.secondary_agents:
                table.add_row(
                    "Secondary Agents",
                    ", ".join([a.value for a in decision.secondary_agents]),
                )

            console.print(table)

            if verbose:
                console.print(f"\n[bold blue]📊 Resource Requirements:[/bold blue]")
                for key, value in decision.resource_requirements.items():
                    console.print(f"  • {key}: {value}")

                console.print(f"\n[bold blue]🔄 Fallback Plan:[/bold blue]")
                console.print(f"  {decision.fallback_plan}")

            # Store the routing decision in memory
            memory_manager = RouterMemoryManager()
            await memory_manager.store_memory(
                request_hash=hash(request),  # type: ignore
                task_type=TaskType.GENERAL,  # Would be determined by analysis  # type: ignore
                complexity=TaskComplexity(complexity),  # type: ignore
                selected_agent=decision.primary_agent,  # type: ignore
                confidence=decision.confidence,
                success=True,  # Assume success for now
                duration=decision.estimated_time,
                context={"user_id": user_id, "urgency": urgency},
                outcome={"strategy": decision.coordination_strategy},
            )

        except Exception as e:
            console.print(f"[bold red]❌ Error routing request: {e}[/bold red]")

    asyncio.run(_route_request())


@app.command()
def decompose_task(
    request: str = typer.Argument(..., help="Complex task to decompose"),
    task_type: str = typer.Option("general", "--type", "-t", help="Task type"),
    complexity: str = typer.Option(
        "medium", "--complexity", "-c", help="Task complexity"
    ),
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed subtask information"
    ),
):
    """Decompose a complex task into manageable subtasks"""
    console.print(f"[bold blue]🔧 Decomposing Task...[/bold blue]")
    console.print(f"📝 Request: {request}")
    console.print(f"🏷️  Type: {task_type}")
    console.print(f"⚡ Complexity: {complexity}")

    async def _decompose_task():
        try:
            # Initialize decomposer
            decomposer = TaskDecomposer()

            # Decompose the task
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Analyzing and decomposing task...", total=None
                )

                decomposition = await decomposer.decompose_task(
                    request=request,
                    task_type=TaskType(task_type),  # type: ignore
                    complexity=TaskComplexity(complexity),  # type: ignore
                )

                progress.update(task, description="✅ Task decomposed")

            # Display results
            console.print(f"\n[bold green]📋 Task Decomposition:[/bold green]")
            console.print(f"🆔 Task ID: {decomposition.task_id}")
            console.print(
                f"⏱️  Estimated Duration: {decomposition.total_estimated_duration:.1f} seconds"
            )
            console.print(f"📊 Subtasks: {len(decomposition.subtasks)}")
            console.print(f"🔄 Parallel Groups: {len(decomposition.parallel_groups)}")

            # Create subtasks table
            table = Table(title="Subtasks")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Type", style="green")
            table.add_column("Complexity", style="yellow")
            table.add_column("Duration", style="blue")
            table.add_column("Priority", style="magenta")

            for subtask in decomposition.subtasks:
                table.add_row(
                    subtask.id,
                    subtask.title,
                    subtask.task_type.value,
                    subtask.complexity.value,
                    f"{subtask.estimated_duration:.1f}s",
                    f"{subtask.priority:.2f}",
                )

            console.print(table)

            if show_details:
                console.print(f"\n[bold blue]🔗 Dependencies:[/bold blue]")
                for subtask in decomposition.subtasks:
                    if subtask.dependencies:
                        console.print(
                            f"  • {subtask.id} depends on: {', '.join(subtask.dependencies)}"
                        )

                console.print(f"\n[bold blue]⚡ Critical Path:[/bold blue]")
                console.print(f"  {' → '.join(decomposition.critical_path)}")

                console.print(f"\n[bold blue]🔄 Parallel Groups:[/bold blue]")
                for i, group in enumerate(decomposition.parallel_groups):
                    console.print(f"  Group {i+1}: {', '.join(group)}")

                console.print(f"\n[bold blue]✅ Success Criteria:[/bold blue]")
                for criterion in decomposition.success_criteria:
                    console.print(f"  • {criterion}")

        except Exception as e:
            console.print(f"[bold red]❌ Error decomposing task: {e}[/bold red]")

    asyncio.run(_decompose_task())


@app.command()
def coordinate_agents(
    task_id: str = typer.Argument(..., help="Task ID to coordinate"),
    strategy: str = typer.Option(
        "auto",
        "--strategy",
        "-s",
        help="Coordination strategy (auto/sequential/parallel/hierarchical/collaborative)",
    ),
    monitor: bool = typer.Option(
        False, "--monitor", "-m", help="Monitor execution in real-time"
    ),
):
    """Coordinate multiple agents to execute a task"""
    console.print(f"[bold blue]🤝 Coordinating Agents...[/bold blue]")
    console.print(f"🆔 Task ID: {task_id}")
    console.print(f"📋 Strategy: {strategy}")

    async def _coordinate_agents():
        try:
            # Initialize coordinator
            coordinator = AgentCoordinator()

            # For demo purposes, create a sample decomposition
            # In real usage, this would be retrieved from storage
            from ...router.task_decomposer import Subtask, SubtaskStatus, DependencyType

            sample_subtasks = [
                Subtask(
                    id="analysis_1",
                    title="Analyze Requirements",
                    description="Analyze the task requirements",
                    task_type=TaskType.ANALYSIS,  # type: ignore
                    complexity=TaskComplexity.MEDIUM,  # type: ignore
                    estimated_duration=300,
                    required_skills=["analysis"],
                    assigned_agent=None,
                    dependencies=[],
                    dependency_type=DependencyType.SEQUENTIAL,
                    priority=0.9,
                    status=SubtaskStatus.PENDING,
                    created_at=time.time(),
                ),
                Subtask(
                    id="implementation_1",
                    title="Implement Solution",
                    description="Implement the solution",
                    task_type=TaskType.FEATURE_DEVELOPMENT,  # type: ignore
                    complexity=TaskComplexity.COMPLEX,  # type: ignore
                    estimated_duration=600,
                    required_skills=["programming"],
                    assigned_agent=None,
                    dependencies=["analysis_1"],
                    dependency_type=DependencyType.SEQUENTIAL,
                    priority=0.8,
                    status=SubtaskStatus.PENDING,
                    created_at=time.time(),
                ),
            ]

            from ...router.task_decomposer import TaskDecomposition

            decomposition = TaskDecomposition(
                task_id=task_id,
                original_request="Sample coordination task",
                main_task_type=TaskType.FEATURE_DEVELOPMENT,  # type: ignore
                main_complexity=TaskComplexity.COMPLEX,  # type: ignore
                subtasks=sample_subtasks,
                total_estimated_duration=900,
                critical_path=["analysis_1", "implementation_1"],
                parallel_groups=[],
                resource_requirements={},
                success_criteria=["All subtasks completed successfully"],
                created_at=time.time(),
                status=SubtaskStatus.PENDING,
            )

            # Coordinate execution
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Coordinating agent execution...", total=None)

                result = await coordinator.coordinate_task_execution(decomposition)  # type: ignore

                progress.update(task, description="✅ Coordination completed")

            # Display results
            console.print(f"\n[bold green]🎯 Coordination Results:[/bold green]")
            console.print(f"✅ Success: {result.success}")
            console.print(f"⏱️  Duration: {result.total_duration:.1f} seconds")
            console.print(f"✅ Completed: {len(result.completed_subtasks)} subtasks")
            console.print(f"❌ Failed: {len(result.failed_subtasks)} subtasks")

            if result.completed_subtasks:
                console.print(f"\n[bold green]✅ Completed Subtasks:[/bold green]")
                for subtask_id in result.completed_subtasks:
                    console.print(f"  • {subtask_id}")

            if result.failed_subtasks:
                console.print(f"\n[bold red]❌ Failed Subtasks:[/bold red]")
                for subtask_id in result.failed_subtasks:
                    console.print(f"  • {subtask_id}")

            if result.agent_performance:
                console.print(f"\n[bold blue]📊 Agent Performance:[/bold blue]")
                perf_table = Table()
                perf_table.add_column("Agent", style="cyan")
                perf_table.add_column("Completed", style="green")
                perf_table.add_column("Failed", style="red")

                for agent_id, perf in result.agent_performance.items():
                    perf_table.add_row(
                        agent_id,
                        str(perf.get("completed", 0)),
                        str(perf.get("failed", 0)),
                    )

                console.print(perf_table)

            if result.error_messages:
                console.print(f"\n[bold red]⚠️  Errors:[/bold red]")
                for error in result.error_messages:
                    console.print(f"  • {error}")

        except Exception as e:
            console.print(f"[bold red]❌ Error coordinating agents: {e}[/bold red]")

    asyncio.run(_coordinate_agents())


@app.command()
def show_learning_insights(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    export: bool = typer.Option(
        False, "--export", "-e", help="Export insights to file"
    ),
):
    """Show learning insights and performance analytics"""
    console.print(f"[bold blue]🧠 Learning Insights...[/bold blue]")
    console.print(f"📅 Analyzing last {days} days")

    async def _show_insights():
        try:
            # Initialize components
            memory_manager = RouterMemoryManager()
            learning_engine = LearningEngine()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Analyzing learning data...", total=None)

                # Get insights
                insights = await memory_manager.get_learning_insights()
                learning_metrics = learning_engine.get_learning_metrics()

                progress.update(task, description="✅ Analysis completed")

            # Display insights
            console.print(f"\n[bold green]📊 Learning Insights:[/bold green]")

            # Best performing agents
            if insights.get("best_performing_agents"):
                console.print(f"\n[bold green]🏆 Best Performing Agents:[/bold green]")
                for agent, perf in insights["best_performing_agents"]:
                    console.print(
                        f"  • {agent}: {perf['success_rate']:.1%} success rate"
                    )

            # Worst performing agents
            if insights.get("worst_performing_agents"):
                console.print(f"\n[bold red]⚠️  Agents Needing Improvement:[/bold red]")
                for agent, perf in insights["worst_performing_agents"]:
                    console.print(
                        f"  • {agent}: {perf['success_rate']:.1%} success rate"
                    )

            # Most common task types
            if insights.get("most_common_task_types"):
                console.print(f"\n[bold blue]📈 Most Common Task Types:[/bold blue]")
                for task_type, stats in insights["most_common_task_types"]:
                    console.print(
                        f"  • {task_type}: {stats['total_tasks']} tasks, {stats['success_rate']:.1%} success"
                    )

            # Recommendations
            if insights.get("recommendations"):
                console.print(f"\n[bold yellow]💡 Recommendations:[/bold yellow]")
                for recommendation in insights["recommendations"]:
                    console.print(f"  • {recommendation}")

            # Learning metrics
            console.print(f"\n[bold blue]📊 Learning Metrics:[/bold blue]")
            metrics_table = Table()
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")

            for key, value in learning_metrics.items():
                metrics_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(metrics_table)

            # Export if requested
            if export:
                export_data = {
                    "insights": insights,
                    "learning_metrics": learning_metrics,
                    "export_timestamp": time.time(),
                    "days_analyzed": days,
                }

                export_file = f"learning_insights_{int(time.time())}.json"
                with open(export_file, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)

                console.print(
                    f"\n[bold green]📁 Insights exported to: {export_file}[/bold green]"
                )

        except Exception as e:
            console.print(
                f"[bold red]❌ Error getting learning insights: {e}[/bold red]"
            )

    asyncio.run(_show_insights())


@app.command()
def show_agent_status():
    """Show status of all registered agents"""
    console.print(f"[bold blue]🤖 Agent Status...[/bold blue]")

    async def _show_agent_status():
        try:
            # Initialize coordinator
            coordinator = AgentCoordinator()

            # Get all agents
            agents = coordinator.get_all_agents()

            if not agents:
                console.print("[yellow]No agents registered[/yellow]")
                return

            # Create agents table
            table = Table(title="Registered Agents")
            table.add_column("Agent ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Load", style="blue")
            table.add_column("Performance", style="magenta")
            table.add_column("Success Rate", style="white")

            for agent_id, agent_info in agents.items():
                # Calculate success rate
                total_tasks = agent_info.success_count + agent_info.error_count
                success_rate = (
                    agent_info.success_count / total_tasks if total_tasks > 0 else 0.0
                )

                table.add_row(
                    agent_id,
                    agent_info.agent_type.value,
                    agent_info.status.value,
                    f"{agent_info.current_load:.1%}",
                    f"{agent_info.performance_score:.2f}",
                    f"{success_rate:.1%}",
                )

            console.print(table)

            # Show capabilities
            console.print(f"\n[bold blue]🔧 Agent Capabilities:[/bold blue]")
            for agent_id, agent_info in agents.items():
                console.print(f"  • {agent_id}: {', '.join(agent_info.capabilities)}")

        except Exception as e:
            console.print(f"[bold red]❌ Error getting agent status: {e}[/bold red]")

    asyncio.run(_show_agent_status())


@app.command()
def test_routing_system():
    """Test the routing system with sample requests"""
    console.print(f"[bold blue]🧪 Testing Routing System...[/bold blue]")

    # Sample test requests
    test_requests = [
        {
            "request": "Review this Python code for best practices",
            "expected_type": "code_review",
            "expected_complexity": "medium",
        },
        {
            "request": "Fix the bug in the login function",
            "expected_type": "bug_fix",
            "expected_complexity": "medium",
        },
        {
            "request": "Create a simple calculator app",
            "expected_type": "feature_development",
            "expected_complexity": "complex",
        },
        {
            "request": "Write documentation for the API",
            "expected_type": "documentation",
            "expected_complexity": "simple",
        },
    ]

    async def _test_routing():
        try:
            router = IntelligentRouter()

            results_table = Table(title="Routing Test Results")
            results_table.add_column("Request", style="cyan", max_width=40)
            results_table.add_column("Expected Type", style="green")
            results_table.add_column("Expected Complexity", style="yellow")
            results_table.add_column("Actual Agent", style="blue")
            results_table.add_column("Confidence", style="magenta")
            results_table.add_column("Status", style="white")

            for test in test_requests:
                try:
                    # Create context
                    from ...router.intelligent_router import RequestContext

                    context = RequestContext(
                        user_id="test_user",
                        session_id=f"test_session_{int(time.time())}",
                        timestamp=time.time(),
                        urgency="normal",
                    )

                    # Route request
                    decision = await router.route_request(test["request"], context)

                    # Determine status
                    status = "✅ PASS" if decision.confidence > 0.7 else "⚠️ LOW_CONF"

                    results_table.add_row(
                        (
                            test["request"][:40] + "..."
                            if len(test["request"]) > 40
                            else test["request"]
                        ),
                        test["expected_type"],
                        test["expected_complexity"],
                        decision.primary_agent.value,
                        f"{decision.confidence:.1%}",
                        status,
                    )

                except Exception as e:
                    results_table.add_row(
                        (
                            test["request"][:40] + "..."
                            if len(test["request"]) > 40
                            else test["request"]
                        ),
                        test["expected_type"],
                        test["expected_complexity"],
                        "ERROR",
                        "0%",
                        f"❌ {str(e)[:20]}",
                    )

            console.print(results_table)

            # Show performance metrics
            metrics = router.get_performance_metrics()
            console.print(f"\n[bold blue]📊 Router Performance:[/bold blue]")
            console.print(f"  • Total Requests: {metrics['total_requests']}")
            console.print(f"  • Successful Routes: {metrics['successful_routes']}")
            console.print(
                f"  • Avg Processing Time: {metrics['avg_processing_time']:.3f}s"
            )
            console.print(f"  • User Satisfaction: {metrics['user_satisfaction']:.1%}")

        except Exception as e:
            console.print(f"[bold red]❌ Error testing routing system: {e}[/bold red]")

    asyncio.run(_test_routing())


if __name__ == "__main__":
    app()
