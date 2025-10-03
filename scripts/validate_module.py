#!/usr/bin/env python3
"""
Script to validate a specific module.
Usage: python scripts/validate_module.py <module_name>
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


def run_command(cmd: List[str], module: str) -> Dict[str, Any]:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path.cwd()
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def validate_module(module: str) -> bool:
    """Validate a single module and return True if all checks pass."""
    print(f"🔍 Validating module: {module}")
    
    # Check if module exists
    module_path = Path(module)
    if not module_path.exists():
        print(f"❌ Module {module} does not exist")
        return False
    
    all_passed = True
    
    # Run Ruff linting
    print(f"  🔍 Running Ruff linting...")
    ruff_result = run_command(["ruff", "check", module, "--statistics"], module)
    
    if ruff_result["success"]:
        print(f"  ✅ Ruff linting passed")
    else:
        print(f"  ❌ Ruff linting failed")
        print(f"     {ruff_result['stderr']}")
        all_passed = False
    
    # Run Mypy type checking
    print(f"  🔍 Running Mypy type checking...")
    mypy_result = run_command(["mypy", module, "--ignore-missing-imports"], module)
    
    if mypy_result["success"]:
        print(f"  ✅ Mypy type checking passed")
    else:
        print(f"  ❌ Mypy type checking failed")
        print(f"     {mypy_result['stderr']}")
        all_passed = False
    
    # Run tests (if available)
    print(f"  🔍 Running tests...")
    test_paths = [
        module_path / "tests",
        module_path / "test_*.py",
        Path(f"{module}/test_*.py")
    ]
    
    has_tests = any(
        path.exists() if isinstance(path, Path) else list(Path(".").glob(str(path)))
        for path in test_paths
    )
    
    if has_tests:
        test_result = run_command(["pytest", module, "-v"], module)
        
        if test_result["success"]:
            print(f"  ✅ Tests passed")
        else:
            print(f"  ❌ Tests failed")
            print(f"     {test_result['stderr']}")
            all_passed = False
    else:
        print(f"  ℹ️ No tests found")
    
    # Check for forbidden type: ignore comments
    print(f"  🔍 Checking for forbidden type: ignore comments...")
    type_ignore_result = run_command(["python", "scripts/deny_type_ignore.py", module], module)
    
    if type_ignore_result["success"]:
        print(f"  ✅ No forbidden type: ignore comments found")
    else:
        print(f"  ❌ Found forbidden type: ignore comments")
        print(f"     {type_ignore_result['stderr']}")
        all_passed = False
    
    return all_passed


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_module.py <module_name>")
        print("Available modules:")
        modules = [
            "stillme_core/common",
            "gateway_poc", 
            "stillme_core",
            "agent_dev",
            "clients",
            "desktop_app",
            "dashboards",
            "niche_radar",
            "plugins",
            "runtime",
            "scripts",
            "tests",
            "tools"
        ]
        for module in modules:
            print(f"   - {module}")
        sys.exit(1)
    
    module = sys.argv[1]
    
    print("🚀 Starting module validation...")
    
    success = validate_module(module)
    
    print("\n" + "="*60)
    if success:
        print(f"🎉 Module {module} passed all validations!")
        sys.exit(0)
    else:
        print(f"❌ Module {module} failed validation!")
        sys.exit(1)


if __name__ == "__main__":
    main()
