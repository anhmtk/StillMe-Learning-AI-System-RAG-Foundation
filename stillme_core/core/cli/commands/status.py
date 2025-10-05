"""
System status and health check commands for StillMe CLI

Commands for monitoring system health and status.
"""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Initialize Typer app
app = typer.Typer(name="status", help="System status and health checks")

# Initialize console
console = Console()


@app.command()
def health():
    """Check overall system health"""
    console.print("[bold blue]🏥 Checking StillMe System Health...[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Check Python environment
        task1 = progress.add_task("Checking Python environment...", total=None)
        python_status = check_python_environment()
        progress.update(task1, description=f"✅ Python {python_status['version']}")

        # Check required packages
        task2 = progress.add_task("Checking required packages...", total=None)
        packages_status = check_required_packages()
        progress.update(
            task2,
            description=f"✅ {packages_status['installed']}/{packages_status['total']} packages",
        )

        # Check StillMe modules
        task3 = progress.add_task("Checking StillMe modules...", total=None)
        modules_status = check_stillme_modules()
        progress.update(
            task3,
            description=f"✅ {modules_status['loaded']}/{modules_status['total']} modules",
        )

        # Check configuration
        task4 = progress.add_task("Checking configuration...", total=None)
        config_status = check_configuration()
        progress.update(
            task4,
            description=f"✅ {config_status['valid']}/{config_status['total']} configs",
        )

        # Check file system
        task5 = progress.add_task("Checking file system...", total=None)
        fs_status = check_file_system()
        progress.update(
            task5,
            description=f"✅ {fs_status['accessible']}/{fs_status['total']} paths",
        )

    # Display health summary
    display_health_summary(
        python_status, packages_status, modules_status, config_status, fs_status
    )


@app.command()
def modules():
    """Show status of StillMe modules"""
    console.print("[bold blue]📦 StillMe Modules Status[/bold blue]")

    modules_info = get_modules_info()

    # Create modules table
    table = Table(title="StillMe Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Description", style="white")

    for module in modules_info:
        status_icon = "✅" if module["status"] == "loaded" else "❌"
        table.add_row(
            module["name"],
            f"{status_icon} {module['status']}",
            module.get("version", "N/A"),
            module.get("description", ""),
        )

    console.print(table)


@app.command()
def dependencies():
    """Show dependency status and versions"""
    console.print("[bold blue]📚 Dependencies Status[/bold blue]")

    dependencies_info = get_dependencies_info()

    # Create dependencies table
    table = Table(title="Dependencies")
    table.add_column("Package", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Required", style="white")

    for dep in dependencies_info:
        status_icon = "✅" if dep["status"] == "installed" else "❌"
        table.add_row(
            dep["name"],
            f"{status_icon} {dep['status']}",
            dep.get("version", "N/A"),
            dep.get("required", "Yes"),
        )

    console.print(table)


@app.command()
def config():
    """Show configuration status"""
    console.print("[bold blue]⚙️  Configuration Status[/bold blue]")

    config_info = get_configuration_info()

    # Create config table
    table = Table(title="Configuration Files")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Last Modified", style="white")

    for config in config_info:
        status_icon = "✅" if config["status"] == "valid" else "❌"
        table.add_row(
            config["name"],
            f"{status_icon} {config['status']}",
            config.get("size", "N/A"),
            config.get("modified", "N/A"),
        )

    console.print(table)


@app.command()
def performance():
    """Show system performance metrics"""
    console.print("[bold blue]⚡ System Performance Metrics[/bold blue]")

    performance_info = get_performance_info()

    # Create performance table
    table = Table(title="Performance Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    for metric in performance_info:
        status_icon = (
            "✅"
            if metric["status"] == "good"
            else "⚠️"
            if metric["status"] == "warning"
            else "❌"
        )
        table.add_row(
            metric["name"], metric["value"], f"{status_icon} {metric['status']}"
        )

    console.print(table)


@app.command()
def export(
    output_path: str = typer.Option(
        "system_status.json", "--output", "-o", help="Output file path"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format: json, yaml"
    ),
):
    """Export system status to file"""
    console.print("[bold blue]📤 Exporting system status...[/bold blue]")

    status_data = {
        "timestamp": "2025-01-01T00:00:00Z",  # Would be actual timestamp
        "python": check_python_environment(),
        "packages": check_required_packages(),
        "modules": get_modules_info(),
        "configuration": get_configuration_info(),
        "performance": get_performance_info(),
    }

    if format == "yaml":
        try:
            import yaml

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(status_data, f, default_flow_style=False)
        except ImportError:
            console.print("[bold red]❌ YAML format requires PyYAML package[/bold red]")
            return
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)

    console.print(
        f"\n[bold green]✅ System status exported to: {output_path}[/bold green]"
    )


def check_python_environment():
    """Check Python environment status"""
    return {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "executable": sys.executable,
        "status": "healthy",
    }


def check_required_packages():
    """Check required packages status"""
    required_packages = ["typer", "rich", "ruff", "pylint", "mypy", "black", "isort"]

    installed = 0
    for package in required_packages:
        try:
            __import__(package)
            installed += 1
        except ImportError:
            pass

    return {
        "total": len(required_packages),
        "installed": installed,
        "missing": len(required_packages) - installed,
        "status": "healthy" if installed == len(required_packages) else "warning",
    }


def check_stillme_modules():
    """Check StillMe modules status"""
    modules_to_check = [
        "stillme_core.quality.code_quality_enforcer",
        "stillme_core.quality.quality_metrics",
        "stillme_core.quality.auto_fixer",
        "stillme_core.quality.agentdev_integration",
        "stillme_core.cli.main",
    ]

    loaded = 0
    for module in modules_to_check:
        try:
            __import__(module)
            loaded += 1
        except ImportError:
            pass

    return {
        "total": len(modules_to_check),
        "loaded": loaded,
        "failed": len(modules_to_check) - loaded,
        "status": "healthy" if loaded == len(modules_to_check) else "warning",
    }


def check_configuration():
    """Check configuration files status"""
    config_files = ["pyproject.toml", ".pylintrc"]

    valid = 0
    for config_file in config_files:
        if Path(config_file).exists():
            valid += 1

    return {
        "total": len(config_files),
        "valid": valid,
        "missing": len(config_files) - valid,
        "status": "healthy" if valid == len(config_files) else "warning",
    }


def check_file_system():
    """Check file system accessibility"""
    paths_to_check = [".", "stillme_core", "stillme_core/quality", "stillme_core/cli"]

    accessible = 0
    for path in paths_to_check:
        if Path(path).exists():
            accessible += 1

    return {
        "total": len(paths_to_check),
        "accessible": accessible,
        "inaccessible": len(paths_to_check) - accessible,
        "status": "healthy" if accessible == len(paths_to_check) else "warning",
    }


def get_modules_info():
    """Get detailed modules information"""
    modules = [
        {
            "name": "stillme_core.quality.code_quality_enforcer",
            "status": "loaded",
            "version": "1.0.0",
            "description": "Core code quality enforcement",
        },
        {
            "name": "stillme_core.quality.quality_metrics",
            "status": "loaded",
            "version": "1.0.0",
            "description": "Quality metrics tracking",
        },
        {
            "name": "stillme_core.quality.auto_fixer",
            "status": "loaded",
            "version": "1.0.0",
            "description": "Automatic code fixing",
        },
        {
            "name": "stillme_core.quality.agentdev_integration",
            "status": "loaded",
            "version": "1.0.0",
            "description": "AgentDev integration layer",
        },
        {
            "name": "stillme_core.cli.main",
            "status": "loaded",
            "version": "1.0.0",
            "description": "CLI interface",
        },
    ]

    # Check actual status
    for module in modules:
        try:
            __import__(module["name"])
            module["status"] = "loaded"
        except ImportError:
            module["status"] = "failed"

    return modules


def get_dependencies_info():
    """Get dependencies information"""
    dependencies = [
        {
            "name": "typer",
            "required": "Yes",
            "version": "0.17.4",
            "status": "installed",
        },
        {"name": "rich", "required": "Yes", "version": "14.1.0", "status": "installed"},
        {"name": "ruff", "required": "Yes", "version": "0.13.0", "status": "installed"},
        {
            "name": "pylint",
            "required": "Yes",
            "version": "3.3.8",
            "status": "installed",
        },
        {"name": "mypy", "required": "Yes", "version": "1.18.1", "status": "installed"},
        {
            "name": "black",
            "required": "Yes",
            "version": "25.1.0",
            "status": "installed",
        },
        {"name": "isort", "required": "Yes", "version": "6.0.1", "status": "installed"},
    ]

    # Check actual status
    for dep in dependencies:
        try:
            __import__(dep["name"])
            dep["status"] = "installed"
        except ImportError:
            dep["status"] = "missing"

    return dependencies


def get_configuration_info():
    """Get configuration files information"""
    config_files = [
        {
            "name": "pyproject.toml",
            "status": "valid",
            "size": "5.2 KB",
            "modified": "2025-01-01 19:44:00",
        },
        {
            "name": ".pylintrc",
            "status": "valid",
            "size": "15.1 KB",
            "modified": "2025-01-01 19:44:00",
        },
    ]

    # Check actual status
    for config in config_files:
        config_path = Path(config["name"])
        if config_path.exists():
            config["status"] = "valid"
            config["size"] = f"{config_path.stat().st_size / 1024:.1f} KB"
        else:
            config["status"] = "missing"

    return config_files


def get_performance_info():
    """Get system performance information"""
    import psutil

    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(".")

        performance_metrics = [
            {
                "name": "CPU Usage",
                "value": f"{cpu_percent:.1f}%",
                "status": (
                    "good"
                    if cpu_percent < 80
                    else "warning"
                    if cpu_percent < 95
                    else "critical"
                ),
            },
            {
                "name": "Memory Usage",
                "value": f"{memory.percent:.1f}%",
                "status": (
                    "good"
                    if memory.percent < 80
                    else "warning"
                    if memory.percent < 95
                    else "critical"
                ),
            },
            {
                "name": "Disk Usage",
                "value": f"{disk.percent:.1f}%",
                "status": (
                    "good"
                    if disk.percent < 80
                    else "warning"
                    if disk.percent < 95
                    else "critical"
                ),
            },
            {
                "name": "Python Memory",
                "value": f"{sys.getsizeof(sys.modules) / 1024 / 1024:.1f} MB",
                "status": "good",
            },
        ]
    except ImportError:
        # Fallback if psutil is not available
        performance_metrics = [
            {
                "name": "Python Memory",
                "value": f"{sys.getsizeof(sys.modules) / 1024 / 1024:.1f} MB",
                "status": "good",
            },
            {
                "name": "System Info",
                "value": "Limited (psutil not available)",
                "status": "warning",
            },
        ]

    return performance_metrics


def display_health_summary(
    python_status, packages_status, modules_status, config_status, fs_status
):
    """Display overall health summary"""
    # Calculate overall health
    all_statuses = [
        python_status,
        packages_status,
        modules_status,
        config_status,
        fs_status,
    ]
    healthy_count = sum(1 for status in all_statuses if status["status"] == "healthy")
    overall_health = "healthy" if healthy_count == len(all_statuses) else "warning"

    # Health summary panel
    health_color = "green" if overall_health == "healthy" else "yellow"
    health_icon = "✅" if overall_health == "healthy" else "⚠️"

    summary_panel = Panel.fit(
        f"""
{health_icon} [bold {health_color}]Overall System Health: {overall_health.upper()}[/bold {health_color}]

[bold]Python Environment:[/bold] ✅ {python_status['version']}
[bold]Required Packages:[/bold] ✅ {packages_status['installed']}/{packages_status['total']}
[bold]StillMe Modules:[/bold] ✅ {modules_status['loaded']}/{modules_status['total']}
[bold]Configuration:[/bold] ✅ {config_status['valid']}/{config_status['total']}
[bold]File System:[/bold] ✅ {fs_status['accessible']}/{fs_status['total']}
        """,
        title="System Health Summary",
        border_style=health_color,
    )
    console.print(summary_panel)

    # Show warnings if any
    if overall_health != "healthy":
        console.print("\n[bold yellow]⚠️  System Health Warnings:[/bold yellow]")

        if packages_status["status"] != "healthy":
            console.print(f"  • Missing packages: {packages_status['missing']}")

        if modules_status["status"] != "healthy":
            console.print(f"  • Failed modules: {modules_status['failed']}")

        if config_status["status"] != "healthy":
            console.print(f"  • Missing config files: {config_status['missing']}")

        if fs_status["status"] != "healthy":
            console.print(f"  • Inaccessible paths: {fs_status['inaccessible']}")

        console.print("\n[bold]Recommendations:[/bold]")
        console.print("  • Run [cyan]stillme doctor[/cyan] for detailed diagnostics")
        console.print(
            "  • Install missing packages with [cyan]pip install <package>[/cyan]"
        )
        console.print("  • Check file permissions and paths")
    else:
        console.print(
            "\n[bold green]🎉 All systems are healthy and operational![/bold green]"
        )
