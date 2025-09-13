"""
Quality management commands for StillMe CLI

Commands for code quality analysis, fixing, and monitoring.
"""

import asyncio
import json
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from stillme_core.quality.agentdev_integration import AgentDevQualityIntegration

# Initialize Typer app
app = typer.Typer(name="quality", help="Code quality management commands")

# Initialize console
console = Console()


@app.command()
def check(
    target_path: str = typer.Argument(".", help="Path to analyze"),
    tools: Optional[List[str]] = typer.Option(
        None,
        "--tool",
        "-t",
        help="Specific tools to run (ruff, pylint, mypy, black, isort)",
    ),
    auto_fix: bool = typer.Option(False, "--fix", "-f", help="Apply automatic fixes"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for detailed report"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Run code quality analysis on target path"""
    console.print(
        f"[bold blue]🔍 Analyzing code quality for: {target_path}[/bold blue]"
    )

    async def run_analysis():
        integration = AgentDevQualityIntegration()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running quality analysis...", total=None)

            result = await integration.analyze_and_fix(
                target_path=target_path,
                auto_fix=auto_fix,
                tools=tools,
                save_metrics=True,
            )

            progress.update(task, description="✅ Analysis completed")

        # Display results
        display_quality_results(result, verbose)

        # Save detailed report if requested
        if output:
            save_detailed_report(result, output)

    asyncio.run(run_analysis())


@app.command()
def pre_commit(
    target_path: str = typer.Argument(".", help="Path to check"),
    min_score: float = typer.Option(
        80.0, "--min-score", "-s", help="Minimum quality score threshold"
    ),
    max_issues: float = typer.Option(
        2.0, "--max-issues", "-i", help="Maximum issues per file"
    ),
    fail_fast: bool = typer.Option(
        True, "--fail-fast/--no-fail-fast", help="Exit with error code if check fails"
    ),
):
    """Run pre-commit quality check with configurable thresholds"""
    console.print(
        f"[bold blue]🚦 Running pre-commit quality check for: {target_path}[/bold blue]"
    )

    async def run_pre_commit():
        integration = AgentDevQualityIntegration()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running pre-commit check...", total=None)

            result = await integration.pre_commit_quality_check(
                target_path=target_path,
                min_quality_score=min_score,
                max_issues_per_file=max_issues,
            )

            progress.update(task, description="✅ Pre-commit check completed")

        # Display results
        display_pre_commit_results(result)

        # Exit with error code if check failed
        if fail_fast and not result.get("passed", False):
            console.print("\n[bold red]❌ Pre-commit check failed![/bold red]")
            raise typer.Exit(1)
        elif result.get("passed", False):
            console.print("\n[bold green]✅ Pre-commit check passed![/bold green]")

    asyncio.run(run_pre_commit())


@app.command()
def workflow(
    target_path: str = typer.Argument(".", help="Path to analyze"),
    workflow_type: str = typer.Option(
        "full", "--type", "-t", help="Workflow type: quick, full, pre-commit"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for workflow report"
    ),
):
    """Run complete quality workflow"""
    console.print(
        f"[bold blue]🔄 Running {workflow_type} quality workflow for: {target_path}[/bold blue]"
    )

    async def run_workflow():
        integration = AgentDevQualityIntegration()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {workflow_type} workflow...", total=None)

            result = await integration.run_quality_workflow(
                target_path=target_path, workflow_type=workflow_type
            )

            progress.update(task, description="✅ Workflow completed")

        # Display results
        display_workflow_results(result)

        # Save report if requested
        if output:
            save_workflow_report(result, output)

    asyncio.run(run_workflow())


@app.command()
def dashboard(
    target_path: str = typer.Argument(".", help="Path to get dashboard for"),
    days: int = typer.Option(
        30, "--days", "-d", help="Number of days to include in dashboard"
    ),
):
    """Show quality dashboard with trends and metrics"""
    console.print(f"[bold blue]📊 Quality Dashboard for: {target_path}[/bold blue]")

    integration = AgentDevQualityIntegration()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading dashboard data...", total=None)

        dashboard_data = integration.get_quality_dashboard(target_path)

        progress.update(task, description="✅ Dashboard loaded")

    # Display dashboard
    display_quality_dashboard(dashboard_data, days)


@app.command()
def export(
    target_path: str = typer.Argument(".", help="Path to export data for"),
    output_path: str = typer.Option(
        "quality_report.json", "--output", "-o", help="Output file path"
    ),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to include"),
):
    """Export quality report to file"""
    console.print(
        f"[bold blue]📤 Exporting quality report for: {target_path}[/bold blue]"
    )

    integration = AgentDevQualityIntegration()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting quality data...", total=None)

        result = integration.export_quality_report(
            target_path=target_path, output_path=output_path, days=days
        )

        progress.update(task, description="✅ Export completed")

    if result["status"] == "success":
        console.print(
            f"\n[bold green]✅ Report exported to: {result['output_path']}[/bold green]"
        )
        console.print(f"📊 Reports exported: {result['reports_exported']}")
    else:
        console.print(f"\n[bold red]❌ Export failed: {result['error']}[/bold red]")


def display_quality_results(result: dict, verbose: bool = False):
    """Display quality analysis results"""
    if result["status"] != "success":
        console.print(f"[bold red]❌ Analysis failed: {result['error']}[/bold red]")
        return

    analysis = result["analysis"]

    # Create results table
    table = Table(title="Quality Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Quality Score", f"{analysis['quality_score']:.1f}/100")
    table.add_row("Total Files", str(analysis["total_files"]))
    table.add_row("Total Issues", str(analysis["total_issues"]))
    table.add_row("Auto-fixes Applied", str(analysis["auto_fixes_applied"]))
    table.add_row("Execution Time", f"{analysis['execution_time']:.2f}s")

    console.print(table)

    # Quality level indicator
    quality_level = result["quality_level"]
    level_colors = {
        "excellent": "green",
        "good": "blue",
        "fair": "yellow",
        "poor": "orange",
        "critical": "red",
    }
    color = level_colors.get(quality_level, "white")
    console.print(
        f"\n[bold {color}]Quality Level: {quality_level.upper()}[/bold {color}]"
    )

    # Issues by tool
    if analysis["issues_by_tool"]:
        console.print("\n[bold]Issues by Tool:[/bold]")
        for tool, count in analysis["issues_by_tool"].items():
            console.print(f"  • {tool}: {count}")

    # Recommendations
    if result["recommendations"]:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in result["recommendations"]:
            console.print(f"  • {rec}")

    if verbose:
        # Show detailed issues by severity
        if analysis["issues_by_severity"]:
            console.print("\n[bold]Issues by Severity:[/bold]")
            for severity, count in analysis["issues_by_severity"].items():
                console.print(f"  • {severity}: {count}")


def display_pre_commit_results(result: dict):
    """Display pre-commit check results"""
    if result["status"] != "success":
        console.print(
            f"[bold red]❌ Pre-commit check failed: {result['error']}[/bold red]"
        )
        return

    passed = result["passed"]
    status_color = "green" if passed else "red"
    status_icon = "✅" if passed else "❌"

    console.print(
        f"\n{status_icon} [bold {status_color}]Pre-commit Check: {'PASSED' if passed else 'FAILED'}[/bold {status_color}]"
    )

    # Create results table
    table = Table(title="Pre-commit Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="white")

    table.add_row(
        "Quality Score",
        "✅" if result["checks"]["quality_score_pass"] else "❌",
        f"{result['quality_score']:.1f}",
    )
    table.add_row(
        "Issues per File",
        "✅" if result["checks"]["issues_per_file_pass"] else "❌",
        f"{result['issues_per_file']:.1f}",
    )

    console.print(table)

    # Show thresholds
    thresholds = result["thresholds"]
    console.print("\n[bold]Thresholds:[/bold]")
    console.print(f"  • Min Quality Score: {thresholds['min_quality_score']}")
    console.print(f"  • Max Issues per File: {thresholds['max_issues_per_file']}")


def display_workflow_results(result: dict):
    """Display workflow results"""
    if result["status"] != "success":
        console.print(f"[bold red]❌ Workflow failed: {result['error']}[/bold red]")
        return

    workflow_type = result["workflow_type"]
    completed = result["workflow_completed"]

    status_color = "green" if completed else "red"
    status_icon = "✅" if completed else "❌"

    console.print(
        f"\n{status_icon} [bold {status_color}]{workflow_type.title()} Workflow: {'COMPLETED' if completed else 'FAILED'}[/bold {status_color}]"
    )

    # Display analysis results if available
    if "analysis" in result:
        display_quality_results(result, verbose=False)


def display_quality_dashboard(dashboard_data: dict, days: int):
    """Display quality dashboard"""
    if dashboard_data["status"] != "success":
        console.print(
            f"[bold red]❌ Dashboard failed: {dashboard_data['error']}[/bold red]"
        )
        return

    # Summary panel
    summary = dashboard_data["summary"]
    if summary["status"] == "success":
        summary_panel = Panel.fit(
            f"""
[bold]Quality Score:[/bold] {summary['quality_score']:.1f}/100
[bold]Total Issues:[/bold] {summary['total_issues']}
[bold]Total Files:[/bold] {summary['total_files']}
[bold]Auto-fixes:[/bold] {summary['auto_fixes']}
[bold]Trend:[/bold] {summary['recent_trend']}
            """,
            title="Quality Summary (Last 7 Days)",
            border_style="blue",
        )
        console.print(summary_panel)

    # Trends table
    trends = dashboard_data["trends"]
    if trends:
        console.print("\n[bold]Quality Trends (Last 30 Days):[/bold]")
        trends_table = Table()
        trends_table.add_column("Period", style="cyan")
        trends_table.add_column("Quality Score", style="green")
        trends_table.add_column("Issues", style="yellow")
        trends_table.add_column("Files", style="blue")

        for trend in trends[-10:]:  # Show last 10 trends
            trends_table.add_row(
                trend["period_start"][:10],
                f"{trend['quality_score']:.1f}",
                str(trend["total_issues"]),
                str(trend["total_files"]),
            )

        console.print(trends_table)


def save_detailed_report(result: dict, output_path: str):
    """Save detailed quality report to file"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    console.print(
        f"\n[bold green]📄 Detailed report saved to: {output_path}[/bold green]"
    )


def save_workflow_report(result: dict, output_path: str):
    """Save workflow report to file"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    console.print(
        f"\n[bold green]📄 Workflow report saved to: {output_path}[/bold green]"
    )
