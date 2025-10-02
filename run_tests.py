#!/usr/bin/env python3
"""
AgentDev Foundation Test Suite Runner
Run all tests and generate comprehensive reports
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return -1, "", str(e)

def main():
    """Main test runner"""
    print("🧪 AgentDev Foundation Test Suite Runner")
    print("=" * 50)

    # Get project root
    project_root = Path(__file__).parent.parent
    test_dir = Path(__file__).parent

    print(f"📁 Project Root: {project_root}")
    print(f"📁 Test Directory: {test_dir}")

    # Install test dependencies
    print("\n📦 Installing test dependencies...")
    returncode, stdout, stderr = run_command(
        f"pip install -r {test_dir}/requirements-test.txt",
        cwd=project_root
    )

    if returncode != 0:
        print(f"❌ Failed to install dependencies: {stderr}")
        return 1

    print("✅ Dependencies installed successfully")

    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    start_time = time.time()

    returncode, stdout, stderr = run_command(
        f"python -m pytest {test_dir}/unit/ -v --tb=short --junitxml={test_dir}/reports/unit_results.xml --cov=agent_dev/core --cov-report=xml:{test_dir}/reports/unit_coverage.xml",
        cwd=project_root
    )

    unit_time = time.time() - start_time
    unit_passed = returncode == 0

    print(f"Unit Tests: {'✅ PASSED' if unit_passed else '❌ FAILED'} ({unit_time:.2f}s)")
    if not unit_passed:
        print(f"Error: {stderr}")

    # Run integration tests
    print("\n🔗 Running Integration Tests...")
    start_time = time.time()

    returncode, stdout, stderr = run_command(
        f"python -m pytest {test_dir}/integration/ -v --tb=short --junitxml={test_dir}/reports/integration_results.xml",
        cwd=project_root
    )

    integration_time = time.time() - start_time
    integration_passed = returncode == 0

    print(f"Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'} ({integration_time:.2f}s)")
    if not integration_passed:
        print(f"Error: {stderr}")

    # Run E2E tests
    print("\n🎯 Running E2E Tests...")
    start_time = time.time()

    returncode, stdout, stderr = run_command(
        f"python -m pytest {test_dir}/e2e_scenarios/ -v --tb=short --junitxml={test_dir}/reports/e2e_results.xml",
        cwd=project_root
    )

    e2e_time = time.time() - start_time
    e2e_passed = returncode == 0

    print(f"E2E Tests: {'✅ PASSED' if e2e_passed else '❌ FAILED'} ({e2e_time:.2f}s)")
    if not e2e_passed:
        print(f"Error: {stderr}")

    # Run security tests
    print("\n🔒 Running Security Tests...")
    start_time = time.time()

    returncode, stdout, stderr = run_command(
        f"python -m pytest {test_dir}/security_basics/ -v --tb=short --junitxml={test_dir}/reports/security_results.xml",
        cwd=project_root
    )

    security_time = time.time() - start_time
    security_passed = returncode == 0

    print(f"Security Tests: {'✅ PASSED' if security_passed else '❌ FAILED'} ({security_time:.2f}s)")
    if not security_passed:
        print(f"Error: {stderr}")

    # Generate coverage report
    print("\n📊 Generating Coverage Report...")
    returncode, stdout, stderr = run_command(
        f"python -m pytest {test_dir}/ --cov=agent_dev/core --cov-report=html:{test_dir}/reports/coverage_html --cov-report=term-missing",
        cwd=project_root
    )

    # Generate summary report
    generate_summary_report(test_dir, {
        'unit': {'passed': unit_passed, 'time': unit_time},
        'integration': {'passed': integration_passed, 'time': integration_time},
        'e2e': {'passed': e2e_passed, 'time': e2e_time},
        'security': {'passed': security_passed, 'time': security_time}
    })

    # Overall result
    all_passed = unit_passed and integration_passed and e2e_passed and security_passed
    total_time = unit_time + integration_time + e2e_time + security_time

    print("\n" + "=" * 50)
    print("📋 FOUNDATION TEST SUITE - COMPLETION REPORT")
    print("=" * 50)
    print(f"Unit Tests: {'✅ PASSED' if unit_passed else '❌ FAILED'} ({unit_time:.2f}s)")
    print(f"Integration: {'✅ PASSED' if integration_passed else '❌ FAILED'} ({integration_time:.2f}s)")
    print(f"E2E: {'✅ PASSED' if e2e_passed else '❌ FAILED'} ({e2e_time:.2f}s)")
    print(f"Security: {'✅ PASSED' if security_passed else '❌ FAILED'} ({security_time:.2f}s)")
    print(f"Total Time: {total_time:.2f}s")
    print(f"STATUS: {'✅ READY FOR PRODUCTION USE' if all_passed else '❌ NEEDS IMPROVEMENT'}")

    if all_passed:
        print("NEXT: Begin performance optimization phase")
    else:
        print("NEXT: Fix failing tests before proceeding")

    return 0 if all_passed else 1

def generate_summary_report(test_dir, results):
    """Generate summary report"""
    report_path = test_dir / "reports" / "test_summary.md"

    with open(report_path, 'w') as f:
        f.write("# AgentDev Foundation Test Suite Results\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Test Results\n\n")
        for test_type, result in results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            f.write(f"- **{test_type.title()} Tests**: {status} ({result['time']:.2f}s)\n")

        f.write("\n## Coverage Report\n\n")
        f.write("Coverage reports are available in:\n")
        f.write("- HTML: `reports/coverage_html/index.html`\n")
        f.write("- XML: `reports/coverage.xml`\n")

        f.write("\n## Quality Gates\n\n")
        all_passed = all(r['passed'] for r in results.values())
        if all_passed:
            f.write("✅ All quality gates passed\n")
            f.write("✅ Ready for production use\n")
        else:
            f.write("❌ Some quality gates failed\n")
            f.write("❌ Needs improvement before production\n")

        f.write("\n## Next Steps\n\n")
        if all_passed:
            f.write("1. Begin performance optimization phase\n")
            f.write("2. Implement advanced testing features\n")
            f.write("3. Add mutation testing\n")
        else:
            f.write("1. Fix failing tests\n")
            f.write("2. Improve test coverage\n")
            f.write("3. Re-run test suite\n")

if __name__ == "__main__":
    sys.exit(main())
