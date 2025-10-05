# StillMe CLI Usage Guide

## Overview

The StillMe CLI is a powerful command-line interface for the StillMe AI Framework, providing automation, quality management, and system monitoring capabilities.

## Installation

The CLI is automatically available when you install StillMe:

```bash
pip install -e .
```

## Basic Usage

### Getting Help

```bash
# Show main help
stillme --help

# Show version
stillme --version

# Show information about StillMe
stillme info
```

### System Diagnostics

```bash
# Run comprehensive system diagnostics
stillme doctor

# Check system status
stillme status
```

## Quality Management Commands

### Code Quality Analysis

```bash
# Basic quality check
stillme quality-check .

# Check specific directory
stillme quality-check src/

# Use specific tools only
stillme quality-check . --tool ruff --tool pylint

# Apply automatic fixes
stillme quality-check . --fix

# Save detailed report
stillme quality-check . --output quality_report.json
```

### Quality Workflow

```bash
# Run quick quality workflow
stillme quality-check . --tool ruff --fix

# Run comprehensive analysis
stillme quality-check . --tool ruff --tool pylint --tool mypy --fix
```

## AgentDev Commands

### Running Automated Tasks

```bash
# Run a simple task
stillme agent-run "fix code style issues"

# Run with custom parameters
stillme agent-run "improve code quality" --max-steps 10

# Save task results
stillme agent-run "analyze project" --output task_results.json
```

## Configuration

### Viewing Configuration

```bash
# Show current configuration
stillme config show

# Get specific config value
stillme config get quality.min_quality_score

# List all configuration sections
stillme config list-sections
```

### Managing Configuration

```bash
# Set configuration value
stillme config set quality.min_quality_score 85.0

# Reset to defaults
stillme config reset

# Validate configuration
stillme config validate

# Export configuration
stillme config export --output my_config.json

# Import configuration
stillme config import my_config.json
```

## Examples

### Daily Development Workflow

```bash
# 1. Check system health
stillme doctor

# 2. Run quality analysis with auto-fix
stillme quality-check . --fix

# 3. Check status
stillme status
```

### Pre-commit Quality Check

```bash
# Run pre-commit quality check
stillme quality-check . --tool ruff --tool pylint --fix

# Save report for review
stillme quality-check . --output pre_commit_report.json
```

### Project Setup

```bash
# 1. Check system requirements
stillme doctor

# 2. Configure quality settings
stillme config set quality.min_quality_score 80.0
stillme config set quality.auto_fix true

# 3. Run initial quality analysis
stillme quality-check . --fix

# 4. Export configuration
stillme config export --output project_config.json
```

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   ```bash
   # Run diagnostics to identify issues
   stillme doctor
   ```

2. **Quality Analysis Failures**
   ```bash
   # Check system status
   stillme status
   
   # Try with specific tools only
   stillme quality-check . --tool ruff
   ```

3. **Configuration Issues**
   ```bash
   # Validate configuration
   stillme config validate
   
   # Reset to defaults
   stillme config reset
   ```

### Getting Support

- Run `stillme doctor` for system diagnostics
- Check `stillme status` for component health
- Use `--verbose` flag for detailed output
- Export reports for debugging: `--output debug_report.json`

## Advanced Usage

### Custom Quality Workflows

```bash
# Create custom quality workflow
stillme quality-check . --tool ruff --fix --output custom_report.json

# Analyze specific file types
stillme quality-check src/ --tool mypy --tool pylint
```

### Integration with CI/CD

```bash
# Pre-commit hook
stillme quality-check . --tool ruff --fix

# CI pipeline check
stillme quality-check . --tool ruff --tool pylint --tool mypy

# Generate reports for CI
stillme quality-check . --output ci_quality_report.json
```

## Configuration Reference

### Quality Settings

- `quality.min_quality_score`: Minimum acceptable quality score (default: 80.0)
- `quality.auto_fix`: Enable automatic fixes (default: true)
- `quality.enabled_tools`: List of enabled quality tools
- `quality.max_issues_per_file`: Maximum issues per file threshold

### Agent Settings

- `agent.max_steps`: Maximum execution steps (default: 5)
- `agent.timeout`: Task timeout in seconds (default: 300)
- `agent.auto_commit`: Auto-commit changes (default: false)
- `agent.create_backups`: Create backups before changes (default: true)

### CLI Settings

- `cli.theme`: CLI theme (default: "default")
- `cli.show_progress`: Show progress indicators (default: true)
- `cli.verbose_output`: Enable verbose output (default: false)
- `cli.color_output`: Enable colored output (default: true)
