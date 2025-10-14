"""
Observability Commands
======================

CLI commands for monitoring, logging, metrics, and health checks.
"""

import json
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from stillme_core.observability import (
    HealthMonitor,
    HealthStatus,
    LogContext,
    MetricsCollector,
    MetricType,
    ObservabilityDashboard,
    RequestTracer,
    StructuredLogger,
)

console = Console()
app = typer.Typer(name="observability", help="Observability and monitoring commands")


@app.command()
def dashboard(
    port: int = typer.Option(8080, "--port", "-p", help="Port to run dashboard on"),
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    open_browser: bool = typer.Option(
        True, "--no-browser", help="Don't open browser automatically"
    ),
):
    """Start the observability dashboard"""
    console.print("[bold blue]🚀 Starting Observability Dashboard...[/bold blue]")
    console.print(f"📍 URL: http://{host}:{port}")

    try:
        dashboard = ObservabilityDashboard(port, host)
        dashboard.start(open_browser=open_browser)

        console.print("[bold green]✅ Dashboard started successfully![/bold green]")
        console.print(
            f"🌐 Open your browser and go to: [cyan]http://{host}:{port}[/cyan]"
        )
        console.print("⏹️  Press Ctrl+C to stop the dashboard")

        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]🛑 Stopping dashboard...[/bold yellow]")
            dashboard.stop()
            console.print("[bold green]✅ Dashboard stopped[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Failed to start dashboard: {e}[/bold red]")


@app.command()
def health(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed health information"
    ),
    history: int = typer.Option(0, "--history", help="Show health history (hours)"),
):
    """Check system health status"""
    console.print("[bold blue]🏥 Checking System Health...[/bold blue]")

    try:
        health_monitor = HealthMonitor()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running health checks...", total=None)

            health_status = health_monitor.get_health_status()

            progress.update(task, description="✅ Health checks completed")

        # Display overall status
        status_color = {
            HealthStatus.HEALTHY: "green",
            HealthStatus.DEGRADED: "yellow",
            HealthStatus.UNHEALTHY: "red",
            HealthStatus.UNKNOWN: "blue",
        }

        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓",
        }

        console.print(
            f"\n[bold {status_color[health_status.status]}]{status_emoji[health_status.status]} Overall Status: {health_status.status.value.upper()}[/bold {status_color[health_status.status]}]"
        )

        # Display summary
        summary = health_status.summary
        console.print(f"📊 Health Percentage: {summary['health_percentage']:.1f}%")
        console.print(f"🔢 Total Checks: {summary['total_checks']}")
        console.print(f"✅ Healthy: {summary['healthy_checks']}")
        console.print(f"⚠️  Degraded: {summary['degraded_checks']}")
        console.print(f"❌ Unhealthy: {summary['unhealthy_checks']}")

        if summary.get("avg_response_time_ms"):
            console.print(
                f"⏱️  Avg Response Time: {summary['avg_response_time_ms']:.1f}ms"
            )

        # Display detailed checks
        if detailed or health_status.status != HealthStatus.HEALTHY:
            console.print("\n[bold]Health Checks:[/bold]")

            table = Table()
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Message", style="white")
            table.add_column("Response Time", style="yellow")

            for check in health_status.checks:
                status_style = status_color[check.status]
                response_time = (
                    f"{check.response_time_ms:.1f}ms"
                    if check.response_time_ms
                    else "N/A"
                )

                table.add_row(
                    check.name,
                    f"[{status_style}]{check.status.value.upper()}[/{status_style}]",
                    check.message,
                    response_time,
                )

            console.print(table)

        # Show history if requested
        if history > 0:
            console.print(f"\n[bold]Health History (Last {history} hours):[/bold]")
            health_history = health_monitor.get_health_history(hours=history)

            if health_history:
                # Group by check name
                check_groups = {}
                for check in health_history:
                    if check.name not in check_groups:
                        check_groups[check.name] = []
                    check_groups[check.name].append(check)

                for name, checks in check_groups.items():
                    console.print(f"\n[bold cyan]{name}:[/bold cyan]")
                    for check in checks[:5]:  # Show last 5 checks
                        timestamp = (
                            check.last_checked.split("T")[1][:8]
                            if check.last_checked
                            else "Unknown"
                        )
                        status_style = status_color[check.status]
                        console.print(
                            f"  [{timestamp}] [{status_style}]{check.status.value.upper()}[/{status_style}] {check.message}"
                        )
            else:
                console.print("No health history available")

    except Exception as e:
        console.print(f"[bold red]❌ Health check failed: {e}[/bold red]")


@app.command()
def metrics(
    metric_name: str | None = typer.Argument(None, help="Specific metric name to show"),
    summary: bool = typer.Option(False, "--summary", "-s", help="Show metrics summary"),
    export: str | None = typer.Option(
        None, "--export", "-e", help="Export metrics to file"
    ),
):
    """Show metrics information"""
    console.print("[bold blue]📊 Metrics Information[/bold blue]")

    try:
        metrics_collector = MetricsCollector()

        if summary:
            # Show overview
            overview = metrics_collector.get_metrics_overview()

            console.print("\n[bold]Metrics Overview:[/bold]")
            console.print(f"📈 Total Metrics: {overview['total_metrics']:,}")
            console.print(f"🔢 Unique Metrics: {overview['unique_metrics']}")
            console.print(
                f"💾 Database Size: {overview['database_size'] / 1024 / 1024:.2f} MB"
            )

            if overview.get("time_range"):
                console.print(
                    f"⏰ Time Range: {overview['time_range']['start']} to {overview['time_range']['end']}"
                )

            if overview.get("metrics_by_type"):
                console.print("\n[bold]Metrics by Type:[/bold]")
                for metric_type, count in overview["metrics_by_type"].items():
                    console.print(f"  {metric_type}: {count}")

        elif metric_name:
            # Show specific metric
            summary_data = metrics_collector.get_metric_summary(metric_name)

            if summary_data:
                console.print(f"\n[bold]Metric: {metric_name}[/bold]")
                console.print(f"📊 Type: {summary_data.metric_type}")
                console.print(f"🔢 Count: {summary_data.count}")
                console.print(f"📈 Min: {summary_data.min_value:.2f}")
                console.print(f"📈 Max: {summary_data.max_value:.2f}")
                console.print(f"📈 Mean: {summary_data.mean_value:.2f}")
                console.print(f"📈 Median: {summary_data.median_value:.2f}")
                console.print(f"📈 P95: {summary_data.p95_value:.2f}")
                console.print(f"📈 P99: {summary_data.p99_value:.2f}")
                console.print(f"📈 Total: {summary_data.total_value:.2f}")
                console.print(f"⏰ Time Range: {summary_data.time_range}")
            else:
                console.print(
                    f"[bold red]❌ Metric '{metric_name}' not found[/bold red]"
                )

        else:
            # Show all metrics
            console.print("\n[bold]Available Metrics:[/bold]")

            for metric_type in MetricType:
                metrics_of_type = metrics_collector.get_metrics_by_type(metric_type)
                if metrics_of_type:
                    console.print(
                        f"\n[bold cyan]{metric_type.value.upper()}:[/bold cyan]"
                    )
                    for metric in metrics_of_type[:10]:  # Show first 10
                        console.print(f"  • {metric}")
                    if len(metrics_of_type) > 10:
                        console.print(f"  ... and {len(metrics_of_type) - 10} more")

        # Export if requested
        if export:
            console.print(
                f"\n[bold blue]📤 Exporting metrics to {export}...[/bold blue]"
            )
            success = metrics_collector.export_metrics(export)
            if success:
                console.print(
                    "[bold green]✅ Metrics exported successfully[/bold green]"
                )
            else:
                console.print("[bold red]❌ Failed to export metrics[/bold red]")

    except Exception as e:
        console.print(f"[bold red]❌ Metrics operation failed: {e}[/bold red]")


@app.command()
def traces(
    trace_id: str | None = typer.Argument(None, help="Specific trace ID to show"),
    recent: int = typer.Option(
        10, "--recent", "-r", help="Number of recent traces to show"
    ),
    performance: bool = typer.Option(
        False, "--performance", "-p", help="Show performance statistics"
    ),
):
    """Show tracing information"""
    console.print("[bold blue]🔍 Tracing Information[/bold blue]")

    try:
        tracer = RequestTracer()

        if trace_id:
            # Show specific trace
            spans = tracer.get_trace(trace_id)

            if spans:
                console.print(f"\n[bold]Trace: {trace_id}[/bold]")
                console.print(f"🔢 Total Spans: {len(spans)}")

                table = Table()
                table.add_column("Span ID", style="cyan")
                table.add_column("Operation", style="white")
                table.add_column("Duration", style="green")
                table.add_column("Status", style="yellow")

                for span in spans:
                    duration = (
                        f"{span.duration_ms:.1f}ms" if span.duration_ms else "N/A"
                    )
                    status_style = "red" if span.status == "error" else "green"

                    table.add_row(
                        span.span_id[:8] + "...",
                        span.operation_name,
                        duration,
                        f"[{status_style}]{span.status}[/{status_style}]",
                    )

                console.print(table)
            else:
                console.print(f"[bold red]❌ Trace '{trace_id}' not found[/bold red]")

        elif performance:
            # Show performance statistics
            stats = tracer.get_performance_stats()

            if "error" not in stats:
                console.print("\n[bold]Performance Statistics:[/bold]")
                console.print(f"🔧 Operation: {stats['operation_name']}")
                console.print(f"🔢 Total Operations: {stats['total_operations']}")
                console.print(f"❌ Error Count: {stats['error_count']}")
                console.print(f"📊 Error Rate: {stats['error_rate']:.1f}%")
                console.print(f"⏱️  Min Duration: {stats['min_duration_ms']:.1f}ms")
                console.print(f"⏱️  Max Duration: {stats['max_duration_ms']:.1f}ms")
                console.print(f"⏱️  Mean Duration: {stats['mean_duration_ms']:.1f}ms")
                console.print(
                    f"⏱️  Median Duration: {stats['median_duration_ms']:.1f}ms"
                )
                console.print(f"⏱️  P95 Duration: {stats['p95_duration_ms']:.1f}ms")
                console.print(f"⏱️  P99 Duration: {stats['p99_duration_ms']:.1f}ms")
            else:
                console.print(f"[bold red]❌ {stats['error']}[/bold red]")

        else:
            # Show recent traces
            traces = tracer.get_traces_overview(limit=recent)

            if traces:
                console.print("\n[bold]Recent Traces:[/bold]")

                table = Table()
                table.add_column("Trace ID", style="cyan")
                table.add_column("Spans", style="white")
                table.add_column("Duration", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Start Time", style="blue")

                for trace in traces:
                    duration = (
                        f"{trace['total_duration']:.1f}ms"
                        if trace["total_duration"]
                        else "N/A"
                    )
                    status = "❌ ERROR" if trace["has_error"] else "✅ OK"
                    start_time = (
                        trace["start_time"].split("T")[1][:8]
                        if trace["start_time"]
                        else "Unknown"
                    )

                    table.add_row(
                        trace["trace_id"][:8] + "...",
                        str(trace["span_count"]),
                        duration,
                        status,
                        start_time,
                    )

                console.print(table)
            else:
                console.print("[bold yellow]⚠️  No traces found[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]❌ Traces operation failed: {e}[/bold red]")


@app.command()
def logs(
    level: str | None = typer.Option(None, "--level", "-l", help="Filter by log level"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
):
    """Show log information"""
    console.print("[bold blue]📝 Log Information[/bold blue]")

    try:
        logger = StructuredLogger()

        # Get log statistics
        stats = logger.get_log_stats()

        console.print("\n[bold]Log Statistics:[/bold]")
        console.print(f"📊 Total Logs: {stats.get('total_logs', 0):,}")
        console.print(f"💾 File Size: {stats.get('file_size_mb', 0):.2f} MB")
        console.print(f"📁 Log File: {stats.get('log_file', 'N/A')}")

        if stats.get("level_counts"):
            console.print("\n[bold]Logs by Level:[/bold]")
            for level_name, count in stats["level_counts"].items():
                console.print(f"  {level_name}: {count}")

        # Show recent logs if log file exists
        log_file = Path(stats.get("log_file", ""))
        if log_file.exists():
            console.print("\n[bold]Recent Logs:[/bold]")

            try:
                with open(log_file, encoding="utf-8") as f:
                    all_lines = f.readlines()

                # Filter by level if specified
                if level:
                    filtered_lines = []
                    for line in all_lines:
                        try:
                            log_data = json.loads(line.strip())
                            if log_data.get("level", "").lower() == level.lower():
                                filtered_lines.append(line)
                        except json.JSONDecodeError:
                            continue
                    lines_to_show = (
                        filtered_lines[-lines:]
                        if len(filtered_lines) > lines
                        else filtered_lines
                    )
                else:
                    lines_to_show = (
                        all_lines[-lines:] if len(all_lines) > lines else all_lines
                    )

                # Display logs
                for line in lines_to_show:
                    try:
                        log_data = json.loads(line.strip())
                        timestamp = log_data.get("timestamp", "")[
                            :19
                        ]  # Remove microseconds
                        log_level = log_data.get("level", "UNKNOWN")
                        message = log_data.get("message", "")
                        module = log_data.get("module", "")
                        function = log_data.get("function", "")

                        # Color coding for levels
                        level_colors = {
                            "DEBUG": "blue",
                            "INFO": "green",
                            "WARNING": "yellow",
                            "ERROR": "red",
                            "CRITICAL": "magenta",
                        }

                        color = level_colors.get(log_level, "white")

                        console.print(
                            f"[{color}][{timestamp}] {log_level:8} {module}:{function} - {message}[/{color}]"
                        )

                    except json.JSONDecodeError:
                        console.print(f"[dim]{line.strip()}[/dim]")

                if follow:
                    console.print(
                        "\n[bold yellow]⚠️  Follow mode not implemented yet[/bold yellow]"
                    )

            except Exception as e:
                console.print(f"[bold red]❌ Failed to read log file: {e}[/bold red]")
        else:
            console.print("[bold yellow]⚠️  No log file found[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]❌ Logs operation failed: {e}[/bold red]")


@app.command()
def test():
    """Test observability system"""
    console.print("[bold blue]🧪 Testing Observability System...[/bold blue]")

    try:
        # Test logger
        console.print("\n[bold]Testing Logger...[/bold]")
        logger = StructuredLogger("test")

        with LogContext("test-request", "test-user", "test-session"):
            logger.info("Test info message", test_data="hello")
            logger.warning("Test warning message", test_data="world")
            logger.error("Test error message", test_data="error")

        console.print("✅ Logger test completed")

        # Test metrics
        console.print("\n[bold]Testing Metrics...[/bold]")
        metrics_collector = MetricsCollector()

        metrics_collector.increment_counter("test_counter")
        metrics_collector.set_gauge("test_gauge", 42.5)
        metrics_collector.record_histogram("test_histogram", 100)

        with metrics_collector.time_operation("test_operation"):
            time.sleep(0.1)  # Simulate work

        console.print("✅ Metrics test completed")

        # Test tracer
        console.print("\n[bold]Testing Tracer...[/bold]")
        tracer = RequestTracer()

        span = tracer.start_span("test_operation")
        tracer.add_span_tag(span.span_id, "test_tag", "test_value")
        tracer.add_span_log(span.span_id, "Test log message", "info")
        time.sleep(0.05)  # Simulate work
        tracer.finish_span(span.span_id)

        console.print("✅ Tracer test completed")

        # Test health monitor
        console.print("\n[bold]Testing Health Monitor...[/bold]")
        health_monitor = HealthMonitor()
        health_status = health_monitor.get_health_status()

        console.print("✅ Health monitor test completed")
        console.print(f"🏥 Health Status: {health_status.status.value}")

        console.print("\n[bold green]🎉 All observability tests passed![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Observability test failed: {e}[/bold red]")


if __name__ == "__main__":
    app()