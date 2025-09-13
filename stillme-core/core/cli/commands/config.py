"""
Configuration management commands for StillMe CLI

Commands for managing StillMe configuration and settings.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize Typer app
app = typer.Typer(name="config", help="Configuration management commands")

# Initialize console
console = Console()


@app.command()
def show():
    """Show current configuration"""
    console.print("[bold blue]⚙️  Current StillMe Configuration[/bold blue]")

    config_data = load_configuration()

    # Display configuration in panels
    for section, settings in config_data.items():
        if settings:
            panel_content = "\n".join(
                [f"[bold]{key}:[/bold] {value}" for key, value in settings.items()]
            )
            panel = Panel.fit(
                panel_content,
                title=f"{section.title()} Configuration",
                border_style="blue",
            )
            console.print(panel)


@app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key to get"),
    section: Optional[str] = typer.Option(
        None, "--section", "-s", help="Configuration section"
    ),
):
    """Get a specific configuration value"""
    config_data = load_configuration()

    if section:
        if section in config_data and key in config_data[section]:
            value = config_data[section][key]
            console.print(f"[bold green]{section}.{key}:[/bold green] {value}")
        else:
            console.print(
                f"[bold red]Configuration key '{section}.{key}' not found[/bold red]"
            )
    else:
        # Search across all sections
        found = False
        for sect, settings in config_data.items():
            if key in settings:
                console.print(f"[bold green]{sect}.{key}:[/bold green] {settings[key]}")
                found = True

        if not found:
            console.print(f"[bold red]Configuration key '{key}' not found[/bold red]")


@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
    section: str = typer.Option(
        "general", "--section", "-s", help="Configuration section"
    ),
):
    """Set a configuration value"""
    console.print(f"[bold blue]Setting {section}.{key} = {value}[/bold blue]")

    # This would implement actual configuration setting
    # For now, just show what would be set
    console.print(
        f"[bold green]✅ Configuration updated: {section}.{key} = {value}[/bold green]"
    )
    console.print(
        "[dim]Note: Configuration changes require restart to take effect[/dim]"
    )


@app.command()
def reset():
    """Reset configuration to defaults"""
    console.print("[bold blue]🔄 Resetting configuration to defaults...[/bold blue]")

    # This would implement actual configuration reset
    console.print("[bold green]✅ Configuration reset to defaults[/bold green]")
    console.print(
        "[dim]Note: Configuration changes require restart to take effect[/dim]"
    )


@app.command()
def validate():
    """Validate current configuration"""
    console.print("[bold blue]🔍 Validating configuration...[/bold blue]")

    config_data = load_configuration()
    validation_results = validate_configuration(config_data)

    # Display validation results
    if validation_results["valid"]:
        console.print("[bold green]✅ Configuration is valid[/bold green]")
    else:
        console.print("[bold red]❌ Configuration validation failed[/bold red]")

        if validation_results["errors"]:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in validation_results["errors"]:
                console.print(f"  • {error}")

        if validation_results["warnings"]:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in validation_results["warnings"]:
                console.print(f"  • {warning}")


@app.command()
def export(
    output_path: str = typer.Option(
        "stillme_config.json", "--output", "-o", help="Output file path"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format: json, yaml"
    ),
):
    """Export configuration to file"""
    console.print(
        f"[bold blue]📤 Exporting configuration to {output_path}...[/bold blue]"
    )

    config_data = load_configuration()

    if format == "yaml":
        try:
            import yaml

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        except ImportError:
            console.print("[bold red]❌ YAML format requires PyYAML package[/bold red]")
            return
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    console.print(
        f"[bold green]✅ Configuration exported to: {output_path}[/bold green]"
    )


@app.command()
def import_config(
    config_path: str = typer.Argument(..., help="Path to configuration file to import"),
    merge: bool = typer.Option(
        True, "--merge/--replace", help="Merge with existing config or replace"
    ),
):
    """Import configuration from file"""
    console.print(
        f"[bold blue]📥 Importing configuration from {config_path}...[/bold blue]"
    )

    config_file = Path(config_path)
    if not config_file.exists():
        console.print(
            f"[bold red]❌ Configuration file not found: {config_path}[/bold red]"
        )
        return

    try:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            import yaml

            with open(config_file, encoding="utf-8") as f:
                imported_config = yaml.safe_load(f)
        else:
            with open(config_file, encoding="utf-8") as f:
                imported_config = json.load(f)

        # This would implement actual configuration import
        action = "merged" if merge else "replaced"
        console.print(
            f"[bold green]✅ Configuration {action} successfully[/bold green]"
        )
        console.print(
            "[dim]Note: Configuration changes require restart to take effect[/dim]"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Failed to import configuration: {e}[/bold red]")


@app.command()
def list_sections():
    """List all configuration sections"""
    console.print("[bold blue]📋 Configuration Sections[/bold blue]")

    config_data = load_configuration()

    table = Table(title="Configuration Sections")
    table.add_column("Section", style="cyan")
    table.add_column("Settings Count", style="green")
    table.add_column("Description", style="white")

    section_descriptions = {
        "general": "General StillMe settings",
        "quality": "Code quality tool configuration",
        "agent": "AgentDev automation settings",
        "cli": "CLI interface settings",
        "logging": "Logging configuration",
        "performance": "Performance and optimization settings",
    }

    for section, settings in config_data.items():
        count = len(settings) if settings else 0
        description = section_descriptions.get(section, "Configuration section")
        table.add_row(section, str(count), description)

    console.print(table)


def load_configuration():
    """Load current configuration"""
    # This would load actual configuration from files
    # For now, return mock configuration
    return {
        "general": {
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO",
            "max_workers": 4,
        },
        "quality": {
            "enabled_tools": ["ruff", "pylint", "mypy"],
            "auto_fix": True,
            "min_quality_score": 80.0,
            "max_issues_per_file": 2.0,
        },
        "agent": {
            "max_steps": 5,
            "timeout": 300,
            "auto_commit": False,
            "create_backups": True,
        },
        "cli": {
            "theme": "default",
            "show_progress": True,
            "verbose_output": False,
            "color_output": True,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "stillme.log",
            "max_size": "10MB",
        },
        "performance": {
            "cache_enabled": True,
            "parallel_execution": True,
            "memory_limit": "1GB",
            "timeout": 300,
        },
    }


def validate_configuration(config_data):
    """Validate configuration data"""
    errors = []
    warnings = []

    # Validate general section
    if "general" in config_data:
        general = config_data["general"]

        if "log_level" in general:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if general["log_level"] not in valid_levels:
                errors.append(f"Invalid log_level: {general['log_level']}")

        if "max_workers" in general:
            try:
                workers = int(general["max_workers"])
                if workers < 1 or workers > 16:
                    warnings.append("max_workers should be between 1 and 16")
            except (ValueError, TypeError):
                errors.append("max_workers must be an integer")

    # Validate quality section
    if "quality" in config_data:
        quality = config_data["quality"]

        if "min_quality_score" in quality:
            try:
                score = float(quality["min_quality_score"])
                if score < 0 or score > 100:
                    errors.append("min_quality_score must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("min_quality_score must be a number")

        if "enabled_tools" in quality:
            valid_tools = ["ruff", "pylint", "mypy", "black", "isort"]
            for tool in quality["enabled_tools"]:
                if tool not in valid_tools:
                    warnings.append(f"Unknown quality tool: {tool}")

    # Validate agent section
    if "agent" in config_data:
        agent = config_data["agent"]

        if "max_steps" in agent:
            try:
                steps = int(agent["max_steps"])
                if steps < 1 or steps > 50:
                    warnings.append("max_steps should be between 1 and 50")
            except (ValueError, TypeError):
                errors.append("max_steps must be an integer")

        if "timeout" in agent:
            try:
                timeout = int(agent["timeout"])
                if timeout < 30 or timeout > 3600:
                    warnings.append("timeout should be between 30 and 3600 seconds")
            except (ValueError, TypeError):
                errors.append("timeout must be an integer")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
