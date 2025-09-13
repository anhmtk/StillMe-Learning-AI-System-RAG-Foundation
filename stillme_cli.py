#!/usr/bin/env python3
"""
StillMe CLI Entry Point

Main entry point for the StillMe AI Framework command-line interface.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import CLI modules directly to avoid stillme_core.__init__.py issues
from stillme_core.cli.commands import agent, config, quality, status

# Initialize Typer app
app = typer.Typer(
    name="stillme",
    help="StillMe AI Framework - AgentDev CLI",
    add_completion=False,
    rich_markup_mode="rich",
)

# Add command groups
app.add_typer(quality.app, name="quality", help="Code quality management commands")
app.add_typer(agent.app, name="agent", help="AgentDev automation commands")
app.add_typer(status.app, name="status", help="System status and health checks")
app.add_typer(config.app, name="config", help="Configuration management")

# Initialize console
console = Console()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version information"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
):
    """
    StillMe AI Framework - AgentDev CLI

    A powerful command-line interface for the StillMe AI Framework,
    providing automation, quality management, and system monitoring capabilities.
    """
    if version:
        console.print("[bold blue]StillMe AI Framework[/bold blue]")
        console.print("Version: 1.0.0")
        console.print("AgentDev CLI: 1.0.0")
        raise typer.Exit()

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


@app.command()
def info():
    """Show information about StillMe AI Framework"""
    info_panel = Panel.fit(
        """
[bold blue]StillMe AI Framework[/bold blue]

[bold]AgentDev System:[/bold] AI-powered development assistant
[bold]Quality Management:[/bold] Automated code quality enforcement
[bold]CLI Interface:[/bold] Command-line automation tools

[bold]Key Features:[/bold]
• Automated code quality analysis and fixing
• Intelligent development task planning and execution
• Real-time system monitoring and health checks
• Comprehensive reporting and metrics tracking

[bold]Quick Start:[/bold]
• [cyan]stillme quality check .[/cyan] - Check code quality
• [cyan]stillme agent run "fix bugs"[/cyan] - Run automated task
• [cyan]stillme status[/cyan] - Check system status
        """,
        title="StillMe AI Framework Information",
        border_style="blue",
    )
    console.print(info_panel)


@app.command()
def doctor():
    """Run system diagnostics and health checks"""
    console.print("[bold blue]🔍 Running StillMe System Diagnostics...[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Check Python version
        task1 = progress.add_task("Checking Python version...", total=None)
        python_version = sys.version_info
        progress.update(
            task1,
            description=f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}",
        )

        # Check required packages
        task2 = progress.add_task("Checking required packages...", total=None)
        required_packages = ["typer", "rich", "ruff", "pylint", "mypy"]
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            progress.update(
                task2, description=f"❌ Missing packages: {', '.join(missing_packages)}"
            )
        else:
            progress.update(task2, description="✅ All required packages installed")

        # Check StillMe modules
        task3 = progress.add_task("Checking StillMe modules...", total=None)
        try:
            from stillme_core.cli import main
            from stillme_core.quality import CodeQualityEnforcer

            progress.update(task3, description="✅ StillMe modules loaded successfully")
        except ImportError as e:
            progress.update(task3, description=f"❌ Module import error: {e}")

        # Check configuration
        task4 = progress.add_task("Checking configuration...", total=None)
        config_files = ["pyproject.toml", ".pylintrc"]
        missing_config = []

        for config_file in config_files:
            if not Path(config_file).exists():
                missing_config.append(config_file)

        if missing_config:
            progress.update(
                task4,
                description=f"⚠️  Missing config files: {', '.join(missing_config)}",
            )
        else:
            progress.update(task4, description="✅ Configuration files present")

    # Summary
    console.print("\n[bold green]🎉 System diagnostics completed![/bold green]")

    if missing_packages or missing_config:
        console.print("\n[bold yellow]⚠️  Issues found:[/bold yellow]")
        if missing_packages:
            console.print(f"• Missing packages: {', '.join(missing_packages)}")
        if missing_config:
            console.print(f"• Missing config files: {', '.join(missing_config)}")
        console.print(
            "\nRun [cyan]pip install {' '.join(missing_packages)}[/cyan] to install missing packages."
        )
    else:
        console.print("\n[bold green]✅ All systems operational![/bold green]")


if __name__ == "__main__":
    app()
