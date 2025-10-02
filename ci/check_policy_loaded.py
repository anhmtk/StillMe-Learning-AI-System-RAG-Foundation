#!/usr/bin/env python3
"""
Policy Loading Compliance Check
Ensures all entrypoints load required policies
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Set


def find_entrypoints() -> List[Path]:
    """Find all Python entrypoints in the project"""
    entrypoints = []

    # Main entrypoints
    main_files = [
        "app.py",
        "main.py",
        "run.py",
        "server.py",
        "gateway.py"
    ]

    for file_name in main_files:
        if Path(file_name).exists():
            entrypoints.append(Path(file_name))

    # AgentDev entrypoints
    agentdev_dir = Path("agentdev")
    if agentdev_dir.exists():
        for py_file in agentdev_dir.rglob("*.py"):
            if py_file.name in ["__init__.py", "main.py", "cli.py", "server.py"]:
                entrypoints.append(py_file)

    # API entrypoints
    api_dir = Path("api")
    if api_dir.exists():
        for py_file in api_dir.rglob("*.py"):
            if py_file.name in ["__init__.py", "main.py", "app.py", "server.py"]:
                entrypoints.append(py_file)

    return entrypoints

def check_policy_imports(file_path: Path) -> Set[str]:
    """Check if file imports required policies"""
    required_imports = {
        "load_interaction_policy",
        "get_interaction_policy",
        "load_file_policy",
        "assert_protected_files",
        "diagnose_on_skip"
    }

    found_imports = set()

    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('runtime.'):
                        found_imports.add(alias.name.split('.')[-1])
            elif isinstance(node, ast.ImportFrom):
                if node.module and 'runtime' in node.module:
                    for alias in node.names:
                        found_imports.add(alias.name)

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return set()

    return found_imports

def check_policy_usage(file_path: Path) -> bool:
    """Check if file actually uses policy functions"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Check for policy function calls
        policy_calls = [
            "load_interaction_policy()",
            "get_interaction_policy()",
            "load_file_policy()",
            "assert_protected_files()",
            "diagnose_on_skip()"
        ]

        for call in policy_calls:
            if call in content:
                return True

        return False

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

def main():
    """Main compliance check"""
    print("🔍 Checking policy loading compliance...")

    entrypoints = find_entrypoints()
    if not entrypoints:
        print("❌ No entrypoints found")
        sys.exit(1)

    violations = []

    for entrypoint in entrypoints:
        print(f"Checking {entrypoint}...")

        imports = check_policy_imports(entrypoint)
        uses_policies = check_policy_usage(entrypoint)

        if not imports:
            violations.append(f"{entrypoint}: No policy imports found")
        elif not uses_policies:
            violations.append(f"{entrypoint}: Imports policies but doesn't use them")

    if violations:
        print("\n❌ Policy compliance violations found:")
        for violation in violations:
            print(f"  - {violation}")
        print("\nRequired imports:")
        print("  from runtime.interaction_policy import load_interaction_policy, get_interaction_policy")
        print("  from runtime.file_policy import load_file_policy, assert_protected_files")
        print("  from runtime.skip_diagnose import diagnose_on_skip")
        sys.exit(1)
    else:
        print("✅ All entrypoints comply with policy loading requirements")
        sys.exit(0)

if __name__ == "__main__":
    main()
