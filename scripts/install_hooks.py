import secrets

#!/usr/bin/env python3
"""
Install pre-commit hooks for NicheRadar v1.5
Sets up development environment with quality gates
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"🚀 {description}")
    print(f"Command: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(command, shell=False, check=True, capture_output=True, text=True)
        print("✅ Success")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed")
        print("Error:", e.stderr)
        return False

def install_pre_commit():
    """Install pre-commit"""
    if not run_command("pip install pre-commit", "Installing pre-commit"):
        return False

    if not run_command("pre-commit --version", "Verifying pre-commit installation"):
        return False

    return True

def install_hooks():
    """Install pre-commit hooks"""
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        return False

    if not run_command("pre-commit install --hook-type pre-push", "Installing pre-push hooks"):
        return False

    return True

def install_hook_dependencies():
    """Install dependencies for hooks"""
    dependencies = [
        "black",
        "isort",
        "flake8",
        "mypy",
        "bandit",
        "safety",
        "detect-secrets"
    ]

    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False

    return True

def create_secrets_baseline():
    """Create secrets baseline for detect-secrets"""
    if not Path(".secrets.baseline").exists():
        if not run_command("detect-secrets scan --baseline .secrets.baseline", "Creating secrets baseline"):
            return False

    return True

def test_hooks():
    """Test pre-commit hooks"""
    if not run_command("pre-commit run --all-files", "Testing pre-commit hooks"):
        return False

    return True

def setup_git_attributes():
    """Setup .gitattributes for better diff handling"""
    gitattributes_content = """# Python
*.py diff=python

# YAML
*.yaml diff=yaml
*.yml diff=yaml

# JSON
*.json diff=json

# Markdown
*.md diff=markdown

# Test files
tests/** diff=python
e2e/** diff=typescript
"""

    with open(".gitattributes", "w") as f:
        f.write(gitattributes_content)

    print("✅ Created .gitattributes")
    return True

def setup_gitignore():
    """Setup .gitignore for test artifacts"""
    gitignore_additions = """
# Test artifacts
reports/
logs/
tests/cassettes/
*.log

# Playwright
test-results/
playwright-report/
playwright/.cache/

# Coverage reports
coverage/
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
*.py,cover

# Pytest
.pytest_cache/
.tox/
.nox/

# VCR cassettes
tests/cassettes/

# Test reports
reports/test_report.html
reports/coverage/
reports/junit.xml
reports/coverage.xml
reports/playwright-report/
reports/playwright-results.json
reports/playwright-junit.xml
reports/test_summary.json

# Log files
logs/*.log
logs/web_metrics.log
logs/tool_gate.log
logs/staging.log

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db

# IDE files
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# StillMe specific
.env.local
.env.production
.env.staging
config/local.yaml
config/production.yaml
"""

    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            existing_content = f.read()

        if "Test artifacts" not in existing_content:
            with open(gitignore_path, "a") as f:
                f.write(gitignore_additions)
            print("✅ Updated .gitignore with test artifacts")
    else:
        with open(gitignore_path, "w") as f:
            f.write(gitignore_additions)
        print("✅ Created .gitignore")

    return True

def create_hooks_readme():
    """Create README for hooks setup"""
    readme_content = """# Pre-commit Hooks Setup

This project uses pre-commit hooks to ensure code quality and security.

## Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Install pre-push hooks
pre-commit install --hook-type pre-push

# Install hook dependencies
pip install black isort flake8 mypy bandit safety detect-secrets
```

## Hooks

- **Black**: Python code formatting
- **isort**: Python import sorting
- **flake8**: Python linting
- **mypy**: Python type checking
- **bandit**: Security vulnerability scanning
- **safety**: Dependency security check
- **detect-secrets**: Secret detection
- **prettier**: YAML formatting
- **Policy Compliance**: Custom policy checks
- **Test Data Validation**: Test fixture validation
- **Coverage Check**: Test coverage validation

## Usage

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black

# Update hooks
pre-commit autoupdate
```

## Configuration

Hooks are configured in `.pre-commit-config.yaml`.

## Troubleshooting

If hooks fail:

1. Check the error message
2. Fix the issue
3. Re-run the hook
4. Commit your changes

For persistent issues, check the hook documentation or project maintainers.
"""

    with open("HOOKS.md", "w") as f:
        f.write(readme_content)

    print("✅ Created HOOKS.md")
    return True

def main():
    """Main installation function"""
    print("🔧 Installing pre-commit hooks for NicheRadar v1.5")
    print("=" * 60)

    steps = [
        ("Install pre-commit", install_pre_commit),
        ("Install hook dependencies", install_hook_dependencies),
        ("Create secrets baseline", create_secrets_baseline),
        ("Install hooks", install_hooks),
        ("Setup .gitattributes", setup_git_attributes),
        ("Setup .gitignore", setup_gitignore),
        ("Create hooks README", create_hooks_readme),
        ("Test hooks", test_hooks)
    ]

    all_passed = True
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}:")
        if not step_func():
            all_passed = False

    if all_passed:
        print("\n✅ All hooks installed successfully!")
        print("📋 Hooks are now active for commits and pushes")
        print("📖 See HOOKS.md for usage instructions")
        return 0
    else:
        print("\n❌ Some hook installation steps failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
