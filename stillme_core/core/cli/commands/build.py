"""
Build Commands
==============

CLI commands for building, testing, and packaging applications.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from stillme_core.build import LocalBuilder, LocalPackager, LocalTester

console = Console()
app = typer.Typer(name="build", help="Build and package applications")


@app.command()
def python_app(
    source_path: str = typer.Argument(..., help="Path to Python source code"),
    app_name: str = typer.Argument(..., help="Name of the application"),
    entry_point: str = typer.Option(
        "main.py", "--entry", "-e", help="Main entry point file"
    ),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Application version"),
    output_dir: str = typer.Option(
        "build_output", "--output", "-o", help="Output directory"
    ),
):
    """Build a Python application into executable"""
    console.print(f"[bold blue]🔨 Building Python app: {app_name}[/bold blue]")

    builder = LocalBuilder(output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building application...", total=None)

        result = builder.build_python_app(
            source_path=source_path,
            app_name=app_name,
            entry_point=entry_point,
            version=version,
        )

        progress.update(task, description="✅ Build completed")

    if result.success:
        console.print("[bold green]✅ Build successful![/bold green]")
        console.print(f"📦 Output: {result.output_path}")
        console.print(f"⏱️  Build time: {result.build_time:.2f}s")
        console.print(f"📊 File size: {result.file_size / 1024 / 1024:.2f} MB")
        console.print(f"🏷️  Version: {result.version}")
    else:
        console.print("[bold red]❌ Build failed![/bold red]")
        console.print(f"Error: {result.error_message}")


@app.command()
def web_app(
    source_path: str = typer.Argument(..., help="Path to web app source code"),
    app_name: str = typer.Argument(..., help="Name of the web application"),
    framework: str = typer.Option(
        "flask", "--framework", "-f", help="Web framework (flask, fastapi, django)"
    ),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Application version"),
    output_dir: str = typer.Option(
        "build_output", "--output", "-o", help="Output directory"
    ),
):
    """Build a web application"""
    console.print(f"[bold blue]🌐 Building web app: {app_name}[/bold blue]")

    builder = LocalBuilder(output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building web application...", total=None)

        result = builder.build_web_app(
            source_path=source_path,
            app_name=app_name,
            framework=framework,
            version=version,
        )

        progress.update(task, description="✅ Build completed")

    if result.success:
        console.print("[bold green]✅ Web app built successfully![/bold green]")
        console.print(f"📦 Output: {result.output_path}")
        console.print(f"⏱️  Build time: {result.build_time:.2f}s")
        console.print(f"📊 Directory size: {result.file_size / 1024 / 1024:.2f} MB")
        console.print(f"🏷️  Version: {result.version}")
        console.print(f"🔧 Framework: {framework}")
    else:
        console.print("[bold red]❌ Build failed![/bold red]")
        console.print(f"Error: {result.error_message}")


@app.command()
def cli_tool(
    source_path: str = typer.Argument(..., help="Path to CLI tool source code"),
    tool_name: str = typer.Argument(..., help="Name of the CLI tool"),
    entry_point: str = typer.Option(
        "main.py", "--entry", "-e", help="Main entry point file"
    ),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Tool version"),
    output_dir: str = typer.Option(
        "build_output", "--output", "-o", help="Output directory"
    ),
):
    """Build a CLI tool"""
    console.print(f"[bold blue]🛠️  Building CLI tool: {tool_name}[/bold blue]")

    builder = LocalBuilder(output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building CLI tool...", total=None)

        result = builder.build_cli_tool(
            source_path=source_path,
            tool_name=tool_name,
            entry_point=entry_point,
            version=version,
        )

        progress.update(task, description="✅ Build completed")

    if result.success:
        console.print("[bold green]✅ CLI tool built successfully![/bold green]")
        console.print(f"📦 Output: {result.output_path}")
        console.print(f"⏱️  Build time: {result.build_time:.2f}s")
        console.print(f"📊 Directory size: {result.file_size / 1024 / 1024:.2f} MB")
        console.print(f"🏷️  Version: {result.version}")
    else:
        console.print("[bold red]❌ Build failed![/bold red]")
        console.print(f"Error: {result.error_message}")


@app.command()
def test(
    target_path: str = typer.Argument(..., help="Path to the built application"),
    test_type: str = typer.Option(
        "auto", "--type", "-t", help="Test type (python, web, cli, auto)"
    ),
    test_cases: list[str] | None = typer.Option(
        None, "--test-case", help="Custom test cases"
    ),
):
    """Test a built application"""
    console.print(f"[bold blue]🧪 Testing application: {target_path}[/bold blue]")

    tester = LocalTester()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running tests...", total=None)

        if test_type == "auto":
            # Auto-detect test type based on file extension or content
            if target_path.endswith(".exe") or Path(target_path).is_file():
                test_type = "python"
            elif (
                Path(target_path).is_dir() and (Path(target_path) / "start.py").exists()
            ):
                test_type = "web"
            else:
                test_type = "cli"

        if test_type == "python":
            # Convert test cases to proper format
            test_cases_formatted = []
            if test_cases:
                for case in test_cases:
                    test_cases_formatted.append(
                        {
                            "command": case.split(),
                            "expected_output": "",
                            "expected_exit_code": 0,
                        }
                    )

            result = tester.test_python_executable(target_path, test_cases_formatted)
        elif test_type == "web":
            result = tester.test_web_app(target_path)
        elif test_type == "cli":
            result = tester.test_cli_tool(target_path, test_cases or [])
        else:
            console.print(f"[bold red]❌ Unknown test type: {test_type}[/bold red]")
            return

        progress.update(task, description="✅ Tests completed")

    # Display test results
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Details", style="white")

    for test_result in result.results:
        status = "✅ PASS" if test_result.success else "❌ FAIL"
        table.add_row(
            test_result.test_name,
            status,
            f"{test_result.execution_time:.2f}s",
            (
                test_result.output[:50] + "..."
                if len(test_result.output) > 50
                else test_result.output
            ),
        )

    console.print(table)

    # Summary
    console.print("\n[bold]Test Summary:[/bold]")
    console.print(f"Total tests: {result.total_tests}")
    console.print(f"Passed: {result.passed_tests}")
    console.print(f"Failed: {result.failed_tests}")
    console.print(
        f"Success rate: {result.passed_tests/result.total_tests*100:.1f}%"
        if result.total_tests > 0
        else "N/A"
    )
    console.print(f"Execution time: {result.execution_time:.2f}s")


@app.command()
def package(
    source_path: str = typer.Argument(..., help="Path to source code"),
    package_name: str = typer.Argument(..., help="Name of the package"),
    package_type: str = typer.Option(
        "zip", "--type", "-t", help="Package type (zip, tar, installer, docker)"
    ),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Package version"),
    output_dir: str = typer.Option(
        "packages", "--output", "-o", help="Output directory"
    ),
):
    """Package an application"""
    console.print(f"[bold blue]📦 Packaging: {package_name}[/bold blue]")

    packager = LocalPackager(output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating package...", total=None)

        if package_type == "zip":
            result = packager.create_zip_package(source_path, package_name, version)
        elif package_type == "tar":
            result = packager.create_tar_package(source_path, package_name, version)
        elif package_type == "installer":
            result = packager.create_installer_package(
                source_path, package_name, version
            )
        elif package_type == "docker":
            result = packager.create_docker_package(source_path, package_name, version)
        else:
            console.print(
                f"[bold red]❌ Unknown package type: {package_type}[/bold red]"
            )
            return

        progress.update(task, description="✅ Package created")

    if result.success:
        console.print("[bold green]✅ Package created successfully![/bold green]")
        console.print(f"📦 Output: {result.package_path}")
        console.print(f"📊 File size: {result.file_size / 1024 / 1024:.2f} MB")
        console.print(f"🏷️  Version: {result.version}")
        console.print(f"🔧 Type: {result.package_type}")
    else:
        console.print("[bold red]❌ Packaging failed![/bold red]")
        console.print(f"Error: {result.error_message}")


@app.command()
def status():
    """Show build system status"""
    console.print("[bold blue]📊 Build System Status[/bold blue]")

    # Check build output directory
    build_dir = Path("build_output")
    if build_dir.exists():
        builds = list(build_dir.glob("*"))
        console.print(f"📁 Build output directory: {build_dir} ({len(builds)} builds)")
    else:
        console.print(f"📁 Build output directory: {build_dir} (not found)")

    # Check packages directory
    packages_dir = Path("packages")
    if packages_dir.exists():
        packages = list(packages_dir.glob("*"))
        console.print(
            f"📦 Packages directory: {packages_dir} ({len(packages)} packages)"
        )
    else:
        console.print(f"📦 Packages directory: {packages_dir} (not found)")

    # Check test output directory
    test_dir = Path("test_output")
    if test_dir.exists():
        tests = list(test_dir.glob("*.json"))
        console.print(
            f"🧪 Test output directory: {test_dir} ({len(tests)} test results)"
        )
    else:
        console.print(f"🧪 Test output directory: {test_dir} (not found)")


@app.command()
def history():
    """Show build and test history"""
    console.print("[bold blue]📜 Build & Test History[/bold blue]")

    # Build history
    builder = LocalBuilder()
    build_summary = builder.get_build_summary()

    console.print("\n[bold]Build History:[/bold]")
    console.print(f"Total builds: {build_summary['total_builds']}")
    console.print(f"Successful builds: {build_summary['successful_builds']}")
    console.print(f"Success rate: {build_summary['success_rate']*100:.1f}%")

    if build_summary["latest_build"]:
        latest = build_summary["latest_build"]
        console.print(f"Latest build: {latest.output_path} ({latest.build_type})")

    # Test history
    tester = LocalTester()
    test_summary = tester.get_test_summary()

    console.print("\n[bold]Test History:[/bold]")
    console.print(f"Total test suites: {test_summary['total_test_suites']}")
    console.print(f"Total tests: {test_summary['total_tests']}")
    console.print(f"Total passed: {test_summary['total_passed']}")
    console.print(f"Success rate: {test_summary['success_rate']*100:.1f}%")

    # Package history
    packager = LocalPackager()
    package_summary = packager.get_package_summary()

    console.print("\n[bold]Package History:[/bold]")
    console.print(f"Total packages: {package_summary['total_packages']}")
    console.print(f"Successful packages: {package_summary['successful_packages']}")
    console.print(f"Success rate: {package_summary['success_rate']*100:.1f}%")


if __name__ == "__main__":
    app()