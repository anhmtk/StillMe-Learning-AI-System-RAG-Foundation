#!/usr/bin/env python3
"""
Setup QA environment for NicheRadar v1.5
Installs all necessary tools and configurations for quality assurance
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🚀 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed")
        print("Error:", e.stderr)
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    if not run_command("pip install -r requirements-test.txt", "Installing Python test dependencies"):
        return False
    
    return True

def install_node_dependencies():
    """Install Node.js dependencies"""
    if not run_command("npm install", "Installing Node.js dependencies"):
        return False
    
    return True

def install_playwright():
    """Install Playwright browsers"""
    if not run_command("npx playwright install", "Installing Playwright browsers"):
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "reports",
        "logs",
        "tests/cassettes",
        "reports/coverage",
        "reports/playbooks"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    return True

def setup_git_hooks():
    """Setup Git hooks"""
    if not run_command("pip install pre-commit", "Installing pre-commit"):
        return False
    
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        return False
    
    if not run_command("pre-commit install --hook-type pre-push", "Installing pre-push hooks"):
        return False
    
    return True

def setup_environment_variables():
    """Setup environment variables"""
    env_content = """# QA Environment Variables
TESTING=true
LOG_LEVEL=DEBUG
COVERAGE=true
PLAYWRIGHT_BROWSERS_PATH=0
"""
    
    with open(".env.qa", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env.qa file")
    return True

def setup_test_configuration():
    """Setup test configuration"""
    test_config_content = """# Test Configuration
[test]
timeout = 30
retries = 2
parallel = true
coverage = true
html_report = true
xml_report = true

[coverage]
minimum = 65
exclude = [
    "tests/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*"
]

[playwright]
browsers = ["chromium", "firefox", "webkit"]
headless = false
timeout = 30000
"""
    
    with open("test.ini", "w") as f:
        f.write(test_config_content)
    
    print("✅ Created test.ini file")
    return True

def setup_ci_configuration():
    """Setup CI configuration"""
    ci_dir = Path(".github/workflows")
    ci_dir.mkdir(parents=True, exist_ok=True)
    
    ci_content = """name: NicheRadar v1.5 QA

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        npm install
        npx playwright install
    - name: Run QA suite
      run: python scripts/run_qa_suite.py --full
    - name: Upload reports
      uses: actions/upload-artifact@v3
      with:
        name: qa-reports
        path: reports/
"""
    
    with open(ci_dir / "qa.yml", "w") as f:
        f.write(ci_content)
    
    print("✅ Created CI configuration")
    return True

def setup_documentation():
    """Setup documentation"""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # QA documentation
    qa_docs_content = """# QA Documentation

## Overview
This document describes the quality assurance process for NicheRadar v1.5.

## Setup
1. Install dependencies: `python scripts/setup_qa_environment.py`
2. Run QA suite: `python scripts/run_qa_suite.py --full`

## Tests
- Unit tests: `pytest tests/test_niche_units.py`
- Integration tests: `pytest tests/test_niche_integration.py`
- E2E tests: `npx playwright test e2e/test_niche_ui.spec.ts`

## Reports
- Test reports: `reports/test_report.html`
- Coverage reports: `reports/coverage/index.html`
- Security reports: `reports/bandit-report.json`

## Troubleshooting
See individual test files for specific troubleshooting information.
"""
    
    with open(docs_dir / "qa.md", "w") as f:
        f.write(qa_docs_content)
    
    print("✅ Created QA documentation")
    return True

def verify_installation():
    """Verify installation"""
    print("\n🔍 Verifying installation...")
    
    # Check Python tools
    python_tools = ["pytest", "black", "isort", "flake8", "mypy", "bandit", "safety"]
    for tool in python_tools:
        if not run_command(f"{tool} --version", f"Checking {tool}"):
            return False
    
    # Check Node.js tools
    node_tools = ["npx", "playwright"]
    for tool in node_tools:
        if not run_command(f"{tool} --version", f"Checking {tool}"):
            return False
    
    # Check directories
    required_dirs = ["reports", "logs", "tests/cassettes"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Directory not found: {dir_path}")
            return False
    
    print("✅ Installation verification passed")
    return True

def main():
    """Main setup function"""
    print("🔧 Setting up QA environment for NicheRadar v1.5")
    print("=" * 60)
    
    steps = [
        ("Install Python Dependencies", install_python_dependencies),
        ("Install Node.js Dependencies", install_node_dependencies),
        ("Install Playwright", install_playwright),
        ("Create Directories", create_directories),
        ("Setup Git Hooks", setup_git_hooks),
        ("Setup Environment Variables", setup_environment_variables),
        ("Setup Test Configuration", setup_test_configuration),
        ("Setup CI Configuration", setup_ci_configuration),
        ("Setup Documentation", setup_documentation),
        ("Verify Installation", verify_installation)
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}:")
        if not step_func():
            all_passed = False
    
    if all_passed:
        print("\n✅ QA environment setup completed successfully!")
        print("📋 You can now run: python scripts/run_qa_suite.py --full")
        return 0
    else:
        print("\n❌ Some setup steps failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
