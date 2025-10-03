#!/usr/bin/env python3
"""
Script to validate all modules in the project.
This script runs ruff, mypy, and tests for each module.
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


def validate_module(module: str) -> Dict[str, Any]:
    """Validate a single module."""
    print(f"\n🔍 Validating module: {module}")
    
    results = {
        "module": module,
        "ruff": {"success": False, "output": ""},
        "mypy": {"success": False, "output": ""},
        "tests": {"success": False, "output": ""},
        "type_ignore": {"success": False, "output": ""}
    }
    
    # Check if module exists
    module_path = Path(module)
    if not module_path.exists():
        print(f"❌ Module {module} does not exist")
        return results
    
    # Run Ruff linting
    print(f"  🔍 Running Ruff linting...")
    ruff_result = run_command(["ruff", "check", module, "--statistics"], module)
    results["ruff"] = {
        "success": ruff_result["success"],
        "output": ruff_result["stdout"] + ruff_result["stderr"]
    }
    
    if ruff_result["success"]:
        print(f"  ✅ Ruff linting passed")
    else:
        print(f"  ❌ Ruff linting failed")
        print(f"     {ruff_result['stderr']}")
    
    # Run Mypy type checking
    print(f"  🔍 Running Mypy type checking...")
    mypy_result = run_command(["mypy", module, "--ignore-missing-imports"], module)
    results["mypy"] = {
        "success": mypy_result["success"],
        "output": mypy_result["stdout"] + mypy_result["stderr"]
    }
    
    if mypy_result["success"]:
        print(f"  ✅ Mypy type checking passed")
    else:
        print(f"  ❌ Mypy type checking failed")
        print(f"     {mypy_result['stderr']}")
    
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
        results["tests"] = {
            "success": test_result["success"],
            "output": test_result["stdout"] + test_result["stderr"]
        }
        
        if test_result["success"]:
            print(f"  ✅ Tests passed")
        else:
            print(f"  ❌ Tests failed")
            print(f"     {test_result['stderr']}")
    else:
        print(f"  ℹ️ No tests found")
        results["tests"] = {"success": True, "output": "No tests found"}
    
    # Check for forbidden type: ignore comments
    print(f"  🔍 Checking for forbidden type: ignore comments...")
    type_ignore_result = run_command(["python", "scripts/deny_type_ignore.py", module], module)
    results["type_ignore"] = {
        "success": type_ignore_result["success"],
        "output": type_ignore_result["stdout"] + type_ignore_result["stderr"]
    }
    
    if type_ignore_result["success"]:
        print(f"  ✅ No forbidden type: ignore comments found")
    else:
        print(f"  ❌ Found forbidden type: ignore comments")
        print(f"     {type_ignore_result['stderr']}")
    
    return results


def main():
    """Main function."""
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
    
    print("🚀 Starting module validation...")
    
    all_results = []
    failed_modules = []
    
    for module in modules:
        result = validate_module(module)
        all_results.append(result)
        
        # Check if module passed all validations
        all_passed = all([
            result["ruff"]["success"],
            result["mypy"]["success"],
            result["tests"]["success"],
            result["type_ignore"]["success"]
        ])
        
        if not all_passed:
            failed_modules.append(module)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    for result in all_results:
        module = result["module"]
        status = "✅ PASSED" if all([
            result["ruff"]["success"],
            result["mypy"]["success"],
            result["tests"]["success"],
            result["type_ignore"]["success"]
        ]) else "❌ FAILED"
        
        print(f"{module:<25} {status}")
    
    print("\n" + "="*60)
    
    if failed_modules:
        print(f"❌ {len(failed_modules)} modules failed validation:")
        for module in failed_modules:
            print(f"   - {module}")
        sys.exit(1)
    else:
        print("🎉 All modules passed validation!")
        sys.exit(0)


if __name__ == "__main__":
    main()
