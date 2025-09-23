#!/usr/bin/env python3
"""
Test runner script for NicheRadar v1.5
Runs unit, integration, and E2E tests with comprehensive reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🚀 {description}")
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

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if Python is available
    if not run_command("python --version", "Checking Python version"):
        return False
    
    # Check if pytest is installed
    if not run_command("pytest --version", "Checking pytest installation"):
        return False
    
    # Check if required directories exist
    required_dirs = ["tests", "reports", "logs", "config", "policies"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Required directory not found: {dir_path}")
            return False
    
    # Check if required files exist
    required_files = [
        "config/staging.yaml",
        "policies/network_allowlist.yaml",
        "policies/niche_weights.yaml",
        "pytest.ini"
    ]
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return False
    
    print("✅ All prerequisites met")
    return True

def run_unit_tests():
    """Run unit tests"""
    return run_command(
        "pytest -q tests/test_niche_units.py -m unit",
        "Running unit tests"
    )

def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "pytest -q tests/test_niche_integration.py -m integration",
        "Running integration tests"
    )

def run_all_tests_with_reports():
    """Run all tests with HTML report and coverage"""
    return run_command(
        "pytest -q --maxfail=1 --disable-warnings --cov=stillme --cov=niche_radar --cov=policy --cov=security --cov=cache --cov=metrics --cov-report=html:reports/coverage --cov-report=term-missing --cov-report=xml:reports/coverage.xml --html=reports/test_report.html --self-contained-html --junitxml=reports/junit.xml",
        "Running all tests with comprehensive reporting"
    )

def run_e2e_tests():
    """Run E2E UI tests with Playwright"""
    return run_command(
        "npx playwright test e2e/test_niche_ui.spec.ts --headed",
        "Running E2E UI tests with Playwright"
    )

def generate_test_summary():
    """Generate test summary report"""
    print("\n📊 Generating test summary...")
    
    # Check if reports were generated
    report_files = [
        "reports/test_report.html",
        "reports/coverage/index.html",
        "reports/junit.xml",
        "reports/coverage.xml"
    ]
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "reports_generated": [],
        "reports_missing": []
    }
    
    for report_file in report_files:
        if Path(report_file).exists():
            summary["reports_generated"].append(report_file)
            print(f"✅ {report_file}")
        else:
            summary["reports_missing"].append(report_file)
            print(f"❌ {report_file}")
    
    # Save summary
    summary_path = "reports/test_summary.json"
    with open(summary_path, 'w') as f:
        import json
        json.dump(summary, f, indent=2)
    
    print(f"📋 Test summary saved to {summary_path}")
    return summary

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run NicheRadar v1.5 tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run E2E tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests with reports")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (unit + integration)")
    parser.add_argument("--skip-prereq", action="store_true", help="Skip prerequisite checks")
    
    args = parser.parse_args()
    
    print("🧪 NicheRadar v1.5 Test Runner")
    print("=" * 50)
    
    # Check prerequisites unless skipped
    if not args.skip_prereq:
        if not check_prerequisites():
            print("❌ Prerequisites not met. Exiting.")
            sys.exit(1)
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    
    success = True
    
    if args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.e2e:
        success &= run_e2e_tests()
    elif args.all:
        success &= run_all_tests_with_reports()
    elif args.quick:
        success &= run_unit_tests()
        success &= run_integration_tests()
    else:
        # Default: run all tests with reports
        success &= run_all_tests_with_reports()
    
    # Generate summary
    summary = generate_test_summary()
    
    # Print final results
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
        print("📊 Reports available in reports/ directory")
        print("📋 Test summary: reports/test_summary.json")
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
