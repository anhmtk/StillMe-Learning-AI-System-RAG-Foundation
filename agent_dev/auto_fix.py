#!/usr/bin/env python3
"""
AgentDev Auto-Fix System
========================

Self-improvement loop for automatic error detection and fixing.
"""

import argparse
import hashlib
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from agent_dev.anomaly import AnomalyDetector
from agent_dev.self_monitoring import MonitoringSystem
from agent_dev.persistence.models import create_database_engine
from agent_dev.persistence.repo import AgentDevRepo
from agent_dev.rules.actions import apply_fixer
from agent_dev.rules.engine import RuleEngine


class AutoFixSystem:
    """Auto-fix system for self-improvement"""

    def __init__(self, db_path: str = "agentdev.db"):
        self.engine = create_database_engine(f"sqlite:///{db_path}")

        # Create tables
        from agent_dev.persistence.models import Base

        Base.metadata.create_all(self.engine)

        self.repo = AgentDevRepo(self.engine)
        self.rule_engine = RuleEngine()
        self.monitoring = MonitoringSystem(self.repo)
        self.anomaly_detector = AnomalyDetector()

        # Load YAML rules
        self.rule_engine.load_yaml_rules()

    def run_tests(self) -> Tuple[int, str, str]:
        """Run tests and return (return_code, stdout, stderr)"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", "--maxfail=1"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Test timeout after 5 minutes"
        except Exception as e:
            return -1, "", f"Test error: {e}"

    def parse_errors(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse errors from test output"""
        errors = []
        output = stdout + stderr

        # Parse pytest errors
        pytest_pattern = r"FAILED\s+([^\s]+)\s+-\s+(.+)"
        for match in re.finditer(pytest_pattern, output):
            test_name = match.group(1)
            error_msg = match.group(2)
            errors.append(
                {
                    "source": "pytest",
                    "test_name": test_name,
                    "error_sig": error_msg,
                    "file_path": self._extract_file_path(error_msg),
                    "line_number": self._extract_line_number(error_msg),
                }
            )

        # Parse import errors
        import_pattern = r"(ImportError|ModuleNotFoundError):\s+(.+)"
        for match in re.finditer(import_pattern, output):
            error_msg = match.group(2)
            errors.append(
                {
                    "source": "import",
                    "test_name": None,
                    "error_sig": error_msg,
                    "file_path": self._extract_file_path(error_msg),
                    "line_number": self._extract_line_number(error_msg),
                }
            )

        # Parse name errors
        name_pattern = r"NameError:\s+name\s+'([^']+)'\s+is not defined"
        for match in re.finditer(name_pattern, output):
            name = match.group(1)
            errors.append(
                {
                    "source": "name_error",
                    "test_name": None,
                    "error_sig": f"NameError: name '{name}' is not defined",
                    "file_path": None,
                    "line_number": None,
                }
            )

        return errors

    def _extract_file_path(self, error_msg: str) -> Optional[str]:
        """Extract file path from error message"""
        # Look for file paths in error messages
        path_pattern = r"([^\s]+\.py)"
        match = re.search(path_pattern, error_msg)
        return match.group(1) if match else None

    def _extract_line_number(self, error_msg: str) -> Optional[int]:
        """Extract line number from error message"""
        # Look for line numbers in error messages
        line_pattern = r"line (\d+)"
        match = re.search(line_pattern, error_msg)
        return int(match.group(1)) if match else None

    def select_rules(
        self, errors: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Select rules for errors"""
        rule_error_pairs = []

        for error in errors:
            matching_rules = self.rule_engine.find_matching_rules(error["error_sig"])
            for rule in matching_rules:
                rule_error_pairs.append((rule, error))

        return rule_error_pairs

    def apply_fixes(
        self, rule_error_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Apply fixes using selected rules"""
        results = []

        for rule, error in rule_error_pairs:
            print(f"🔧 Applying fix: {rule['name']} for {error['error_sig'][:50]}...")

            if not error.get("file_path"):
                print("   ⚠️ No file path found, skipping")
                results.append(
                    {
                        "rule": rule,
                        "error": error,
                        "success": False,
                        "reason": "No file path found",
                    }
                )
                continue

            # Apply fixer
            success = apply_fixer(
                rule["fix_action"],
                error["file_path"],
                error.get("line_number", 0),
                error["error_sig"],
            )

            results.append(
                {
                    "rule": rule,
                    "error": error,
                    "success": success,
                    "reason": "Fix applied" if success else "Fix failed",
                }
            )

            if success:
                print("   ✅ Fix applied successfully")
                # Update rule hits
                self.repo.update_rule_hits(rule["name"], success)
            else:
                print("   ❌ Fix failed")

        return results

    def record_feedback(self, results: List[Dict[str, Any]]) -> None:
        """Record feedback for learning"""
        for result in results:
            self.repo.record_feedback(
                source=result["error"]["source"],
                test_name=result["error"]["test_name"],
                error_sig=result["error"]["error_sig"],
                rule_applied=result["rule"]["name"],
                outcome="success" if result["success"] else "failure",
                notes=result["reason"],
            )

    def calculate_diff_hash(self, files_changed: List[str]) -> str:
        """Calculate hash of changed files"""
        content = ""
        for file_path in files_changed:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content += f.read()
            except Exception:
                continue

        return hashlib.sha256(content.encode()).hexdigest()

    def run_autofix_cycle(self, max_tries: int = 2) -> Dict[str, Any]:
        """Run one autofix cycle"""
        print("🚀 Starting autofix cycle...")

        # Get initial test results
        return_code, stdout, stderr = self.run_tests()
        initial_failures = return_code != 0

        if not initial_failures:
            print("✅ All tests passing, no fixes needed")
            return {
                "success": True,
                "fixes_applied": 0,
                "tests_passing": True,
                "message": "All tests already passing",
            }

        print(f"❌ Tests failing (return code: {return_code})")

        # Parse errors
        errors = self.parse_errors(stdout, stderr)
        print(f"🔍 Found {len(errors)} errors")

        if not errors:
            print("⚠️ No parseable errors found")
            return {
                "success": False,
                "fixes_applied": 0,
                "tests_passing": False,
                "message": "No parseable errors found",
            }

        # Select rules
        rule_error_pairs = self.select_rules(errors)
        print(f"🎯 Selected {len(rule_error_pairs)} rule-error pairs")

        if not rule_error_pairs:
            print("⚠️ No matching rules found")
            return {
                "success": False,
                "fixes_applied": 0,
                "tests_passing": False,
                "message": "No matching rules found",
            }

        # Apply fixes
        results = self.apply_fixes(rule_error_pairs)
        successful_fixes = [r for r in results if r["success"]]

        print(f"🔧 Applied {len(successful_fixes)} fixes")

        # Record feedback
        self.record_feedback(results)

        # Test again
        print("🧪 Testing after fixes...")
        return_code, stdout, stderr = self.run_tests()
        tests_passing = return_code == 0

        if tests_passing:
            print("✅ All tests now passing!")
        else:
            print("❌ Tests still failing")

        return {
            "success": tests_passing,
            "fixes_applied": len(successful_fixes),
            "tests_passing": tests_passing,
            "message": "Tests passing after fixes"
            if tests_passing
            else "Tests still failing",
        }

    def run_multiple_cycles(self, max_tries: int = 2) -> Dict[str, Any]:
        """Run multiple autofix cycles"""
        print(f"🔄 Running up to {max_tries} autofix cycles...")

        total_fixes = 0
        cycles_run = 0

        for cycle in range(max_tries):
            print(f"\n--- Cycle {cycle + 1}/{max_tries} ---")
            result = self.run_autofix_cycle()
            cycles_run += 1
            total_fixes += result["fixes_applied"]

            if result["tests_passing"]:
                print(
                    f"🎉 Success after {cycles_run} cycles with {total_fixes} total fixes"
                )
                break

            if result["fixes_applied"] == 0:
                print("⚠️ No fixes applied, stopping")
                break

        return {
            "success": result["tests_passing"],
            "cycles_run": cycles_run,
            "total_fixes": total_fixes,
            "final_result": result,
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AgentDev Auto-Fix System")
    parser.add_argument(
        "--max-tries", type=int, default=2, help="Maximum number of fix cycles"
    )
    parser.add_argument(
        "--db-path", type=str, default="agentdev.db", help="Database path"
    )

    args = parser.parse_args()

    # Initialize system
    autofix = AutoFixSystem(args.db_path)

    # Run autofix
    result = autofix.run_multiple_cycles(args.max_tries)

    # Print discipline line
    print("\n" + "=" * 60)
    print("ko dùng # type: ignore và ko dùng comment out để che giấu lỗi")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
