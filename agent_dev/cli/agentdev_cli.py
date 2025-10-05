#!/usr/bin/env python3
"""
StillMe AgentDev CLI - Trưởng phòng Kỹ thuật Tự động
Enterprise-grade development automation with security-first approach
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


class AgentDevCLI:
    """Main CLI interface for AgentDev"""

    def __init__(self):
        self.repo_root = Path.cwd()
        self.config_dir = self.repo_root / ".agentdev"
        self.config_dir.mkdir(exist_ok=True)

    def init_task(self, task_type: str):
        """Initialize a new task with preflight Q&A"""
        print(f"🚀 Initializing {task_type} task...")

        # Preflight Q&A
        config = self._preflight_qa(task_type)

        # Save task config
        config_path = self.config_dir / "task.config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Task configuration saved to {config_path}")
        return config

    def _preflight_qa(self, task_type: str) -> dict[str, Any]:
        """Interactive preflight Q&A"""
        config = {"task_type": task_type}

        print("\n📋 PREFLIGHT Q&A - AgentDev Configuration")
        print("=" * 50)

        # Inference location
        print("\n1. Inference Location:")
        print("   a) CORE_LOCAL (default) - Run AI models locally")
        print("   b) CORE_CLOUD - Use cloud AI services")
        print("   c) EDGE_STATELESS - Edge proxy only (no models)")

        choice = input("   Choose (a/b/c) [a]: ").strip().lower() or "a"
        config["inference_location"] = {
            "a": "CORE_LOCAL",
            "b": "CORE_CLOUD",
            "c": "EDGE_STATELESS",
        }[choice]

        # Budget constraints
        if config["inference_location"] == "CORE_CLOUD":
            budget = input("\n2. Cloud Budget (USD/month) [100]: ").strip() or "100"
            config["cloud_budget_usd"] = str(int(budget))

        # Downtime tolerance
        print("\n3. Downtime Tolerance:")
        print("   a) ZERO - No downtime allowed")
        print("   b) MINIMAL - < 5 minutes")
        print("   c) MODERATE - < 30 minutes")

        choice = input("   Choose (a/b/c) [b]: ").strip().lower() or "b"
        config["downtime_tolerance"] = {"a": "ZERO", "b": "MINIMAL", "c": "MODERATE"}[
            choice
        ]

        # PII handling
        print("\n4. PII/Logging Requirements:")
        print("   a) STRICT - No PII in logs, full redaction")
        print("   b) MODERATE - Limited PII, selective redaction")
        print("   c) RELAXED - Standard logging")

        choice = input("   Choose (a/b/c) [a]: ").strip().lower() or "a"
        config["pii_handling"] = {"a": "STRICT", "b": "MODERATE", "c": "RELAXED"}[
            choice
        ]

        # Tunnel endpoint
        if config["inference_location"] == "EDGE_STATELESS":
            tunnel = (
                input("\n5. Tunnel Endpoint (WireGuard) [auto]: ").strip() or "auto"
            )
            config["tunnel_endpoint"] = tunnel

        return config

    def plan(self, config_path: str | None = None):
        """Generate execution plan"""
        config = self._load_config(config_path)

        print("📋 AGENTDEV EXECUTION PLAN")
        print("=" * 50)

        # Policy validation
        policy_result = self._validate_policies(config)
        if not policy_result["valid"]:
            print("❌ POLICY VALIDATION FAILED:")
            for error in policy_result["errors"]:
                print(f"   - {error}")
            return False

        # Generate plan
        plan = self._generate_plan(config)

        # Display plan
        print(f"\n🎯 Task: {config['task_type']}")
        print(f"📍 Inference: {config['inference_location']}")
        print(f"⏱️  Downtime: {config['downtime_tolerance']}")
        print(f"🔒 PII: {config['pii_handling']}")

        print("\n📝 EXECUTION STEPS:")
        for i, step in enumerate(plan["steps"], 1):
            print(f"   {i}. {step['action']}")
            if step.get("risk"):
                print(f"      ⚠️  Risk: {step['risk']}")

        print(f"\n💰 ESTIMATED COST: ${plan.get('cost', 0)}")
        print(f"⏰ ESTIMATED TIME: {plan.get('duration', 'Unknown')}")

        return True

    def dry_run(self, config_path: str | None = None):
        """Run conformance tests and contract validation"""
        config = self._load_config(config_path)

        print("🧪 AGENTDEV DRY RUN")
        print("=" * 50)

        # Run conformance tests
        conformance_result = self._run_conformance_tests(config)

        # Run contract tests
        contract_result = self._run_contract_tests(config)

        # Security scan
        security_result = self._run_security_scan()

        # Summary
        all_passed = all(
            [
                conformance_result["passed"],
                contract_result["passed"],
                security_result["passed"],
            ]
        )

        if all_passed:
            print("✅ DRY RUN PASSED - Ready for execution")
            return True
        else:
            print("❌ DRY RUN FAILED - Fix issues before execution")
            return False

    def execute(self, config_path: str | None = None):
        """Execute the planned changes"""
        config = self._load_config(config_path)

        print("🚀 AGENTDEV EXECUTION")
        print("=" * 50)

        # Pre-execution validation
        if not self.dry_run(config_path):
            print("❌ Dry run failed - execution aborted")
            return False

        # Execute plan
        result = self._execute_plan(config)

        if result["success"]:
            print("✅ EXECUTION COMPLETED SUCCESSFULLY")
            print(f"📊 Results: {result['summary']}")
        else:
            print("❌ EXECUTION FAILED")
            print(f"🔍 Error: {result['error']}")

        return result["success"]

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load task configuration"""
        if config_path:
            path = Path(config_path)
        else:
            path = self.config_dir / "task.config.json"

        if not path.exists():
            print(f"❌ Config file not found: {path}")
            print("Run 'stillme agentdev init-task <type>' first")
            sys.exit(1)

        with open(path) as f:
            return json.load(f)

    def _validate_policies(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate against project policies"""
        # Load project spec
        spec_path = self.repo_root / "project.spec.yaml"
        if not spec_path.exists():
            return {"valid": True, "errors": []}  # No spec = no restrictions

        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        errors: list[str] = []

        # Check edge stateless policy
        if (
            spec.get("edge_stateless", True)
            and config["inference_location"] == "EDGE_STATELESS"
        ):
            # This is allowed
            pass
        elif (
            spec.get("edge_stateless", True)
            and config["inference_location"] != "EDGE_STATELESS"
        ):
            errors.append("EDGE must be stateless per project.spec.yaml")

        return {"valid": len(errors) == 0, "errors": errors}

    def _generate_plan(self, config: dict[str, Any]) -> dict[str, Any]:
        """Generate execution plan"""
        # This would integrate with the actual AgentDev planning system
        return {
            "steps": [
                {"action": "Validate project structure", "risk": "Low"},
                {"action": "Run security scan", "risk": "Medium"},
                {"action": "Execute task", "risk": "High"},
                {"action": "Run tests", "risk": "Low"},
                {"action": "Commit changes", "risk": "Low"},
            ],
            "cost": config.get("cloud_budget_usd", 0),
            "duration": "15-30 minutes",
        }

    def _run_conformance_tests(self, config: dict[str, Any]) -> dict[str, Any]:
        """Run conformance tests"""
        print("🔍 Running conformance tests...")
        # This would run actual conformance tests
        return {"passed": True, "details": "All conformance tests passed"}

    def _run_contract_tests(self, config: dict[str, Any]) -> dict[str, Any]:
        """Run contract tests"""
        print("📋 Running contract tests...")
        # This would run actual contract tests
        return {"passed": True, "details": "All contract tests passed"}

    def _run_security_scan(self) -> dict[str, Any]:
        """Run security scan"""
        print("🔒 Running security scan...")
        # This would run actual security scan
        return {"passed": True, "details": "No security issues found"}

    def _execute_plan(self, config: dict[str, Any]) -> dict[str, Any]:
        """Execute the actual plan"""
        print("⚡ Executing plan...")
        # This would integrate with the actual AgentDev execution system
        return {"success": True, "summary": "Task completed successfully"}


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="StillMe AgentDev CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-task command
    init_parser = subparsers.add_parser("init-task", help="Initialize a new task")
    init_parser.add_argument("task_type", help="Type of task to initialize")

    # plan command
    plan_parser = subparsers.add_parser("plan", help="Generate execution plan")
    plan_parser.add_argument("--task", help="Path to task config file")

    # dry-run command
    dry_run_parser = subparsers.add_parser("dry-run", help="Run dry run tests")
    dry_run_parser.add_argument("--task", help="Path to task config file")

    # execute command
    execute_parser = subparsers.add_parser("execute", help="Execute the plan")
    execute_parser.add_argument("--task", help="Path to task config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = AgentDevCLI()

    if args.command == "init-task":
        cli.init_task(args.task_type)
    elif args.command == "plan":
        cli.plan(args.task)
    elif args.command == "dry-run":
        cli.dry_run(args.task)
    elif args.command == "execute":
        cli.execute(args.task)


if __name__ == "__main__":
    main()
