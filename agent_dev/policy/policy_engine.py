#!/usr/bin/env python3
"""
StillMe AgentDev Policy Engine
Enterprise-grade policy enforcement and compliance validation
"""

import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml


class PolicySeverity(Enum):
    BLOCK = "BLOCK"  # Must fix before proceeding
    WARN = "WARN"  # Should fix but can proceed
    INFO = "INFO"  # Informational only


@dataclass
class PolicyViolation:
    """Represents a policy violation"""

    rule_id: str
    severity: PolicySeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class PolicyEngine:
    """Main policy engine for AgentDev"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.policies = {}
        self.violations = []

    def load_policies(self, policy_file: Optional[str] = None):
        """Load policies from YAML file"""
        if policy_file:
            policy_path = Path(policy_file)
        else:
            policy_path = self.repo_root / "policies" / "agentdev_policies.yaml"

        if not policy_path.exists():
            print(f"⚠️  Policy file not found: {policy_path}")
            return

        with open(policy_path) as f:
            self.policies = yaml.safe_load(f)

    def validate_project_spec(
        self, spec_path: Optional[str] = None
    ) -> list[PolicyViolation]:
        """Validate project specification compliance"""
        if spec_path:
            spec_file = Path(spec_path)
        else:
            spec_file = self.repo_root / "project.spec.yaml"

        if not spec_file.exists():
            return [
                PolicyViolation(
                    rule_id="PROJECT_SPEC_MISSING",
                    severity=PolicySeverity.WARN,
                    message="project.spec.yaml not found - using defaults",
                )
            ]

        with open(spec_file) as f:
            spec = yaml.safe_load(f)

        violations = []

        # Check edge stateless policy
        if spec.get("edge_stateless", True):
            violations.extend(self._check_edge_stateless_compliance())

        # Check inference location policy
        if "inference_location" in spec:
            violations.extend(self._check_inference_location_compliance(spec))

        return violations

    def validate_task_config(self, config_path: str) -> list[PolicyViolation]:
        """Validate task configuration against policies"""
        config_file = Path(config_path)
        if not config_file.exists():
            return [
                PolicyViolation(
                    rule_id="TASK_CONFIG_MISSING",
                    severity=PolicySeverity.BLOCK,
                    message=f"Task config not found: {config_path}",
                )
            ]

        with open(config_file) as f:
            config = json.load(f)

        violations = []

        # Check inference location
        if config.get("inference_location") == "EDGE_STATELESS":
            violations.extend(self._check_edge_stateless_compliance())

        # Check budget constraints
        if config.get("inference_location") == "CORE_CLOUD":
            budget = config.get("cloud_budget_usd", 0)
            if budget > 1000:
                violations.append(
                    PolicyViolation(
                        rule_id="BUDGET_EXCESSIVE",
                        severity=PolicySeverity.WARN,
                        message=f"Cloud budget ${budget} exceeds recommended limit of $1000",
                        suggestion="Consider optimizing for cost or getting approval",
                    )
                )

        return violations

    def scan_codebase(self) -> list[PolicyViolation]:
        """Scan codebase for policy violations"""
        violations = []

        # Check for forbidden patterns
        violations.extend(self._scan_forbidden_patterns())

        # Check for security issues
        violations.extend(self._scan_security_issues())

        # Check for architecture violations
        violations.extend(self._scan_architecture_violations())

        return violations

    def _check_edge_stateless_compliance(self) -> list[PolicyViolation]:
        """Check edge stateless compliance"""
        violations = []

        # Check for model runtime in edge/
        edge_dir = self.repo_root / "edge"
        if edge_dir.exists():
            for file_path in edge_dir.rglob("*.yml"):
                if "docker-compose" in file_path.name:
                    violations.extend(self._check_docker_compose_for_models(file_path))

            for file_path in edge_dir.rglob("*.py"):
                violations.extend(self._check_python_for_model_runtime(file_path))

        return violations

    def _check_docker_compose_for_models(
        self, file_path: Path
    ) -> list[PolicyViolation]:
        """Check docker-compose file for forbidden model containers"""
        violations = []

        try:
            with open(file_path) as f:
                content = f.read()

            # Check for forbidden model services
            forbidden_services = [
                "ollama",
                "vllm",
                "text-generation-inference",
                "transformers",
                "torchserve",
            ]

            for service in forbidden_services:
                if service in content.lower():
                    violations.append(
                        PolicyViolation(
                            rule_id="EDGE_MODEL_RUNTIME",
                            severity=PolicySeverity.BLOCK,
                            message=f"Detected forbidden '{service}' in edge docker-compose",
                            file_path=str(file_path),
                            suggestion="Move model runtime to CORE or remove from edge",
                        )
                    )

        except Exception as e:
            violations.append(
                PolicyViolation(
                    rule_id="FILE_READ_ERROR",
                    severity=PolicySeverity.WARN,
                    message=f"Could not read {file_path}: {e}",
                )
            )

        return violations

    def _check_python_for_model_runtime(self, file_path: Path) -> list[PolicyViolation]:
        """Check Python file for forbidden model runtime code"""
        violations = []

        try:
            with open(file_path) as f:
                content = f.read()

            # Check for forbidden patterns
            forbidden_patterns = [
                (r"ollama\s+serve", "ollama serve command"),
                (r"ollama\s+pull", "ollama pull command"),
                (r"vllm\s+serve", "vllm serve command"),
                (r"text-generation-inference", "text-generation-inference"),
                (r"transformers\s+pipeline", "transformers pipeline"),
            ]

            for pattern, description in forbidden_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(
                        PolicyViolation(
                            rule_id="EDGE_MODEL_RUNTIME",
                            severity=PolicySeverity.BLOCK,
                            message=f"Detected {description} in edge code",
                            file_path=str(file_path),
                            suggestion="Move model runtime to CORE or remove from edge",
                        )
                    )

        except Exception as e:
            violations.append(
                PolicyViolation(
                    rule_id="FILE_READ_ERROR",
                    severity=PolicySeverity.WARN,
                    message=f"Could not read {file_path}: {e}",
                )
            )

        return violations

    def _check_inference_location_compliance(
        self, spec: dict[str, Any]
    ) -> list[PolicyViolation]:
        """Check inference location compliance"""
        violations = []

        allowed_locations = spec.get(
            "allowed_inference_locations", ["CORE_LOCAL", "CORE_CLOUD"]
        )
        inference_location = spec.get("inference_location", "CORE_LOCAL")

        if inference_location not in allowed_locations:
            violations.append(
                PolicyViolation(
                    rule_id="INFERENCE_LOCATION_VIOLATION",
                    severity=PolicySeverity.BLOCK,
                    message=f"Inference location '{inference_location}' not allowed",
                    suggestion=f"Use one of: {', '.join(allowed_locations)}",
                )
            )

        return violations

    def _scan_forbidden_patterns(self) -> list[PolicyViolation]:
        """Scan for forbidden patterns in codebase"""
        violations = []

        # Define forbidden patterns
        forbidden_patterns = [
            (r"TODO.*FIXME.*HACK", "TODO/FIXME/HACK comments in production code"),
            (r"console\.log\s*\(", "console.log in production code"),
            (r"print\s*\(", "print statements in production code"),
            (r"debugger\s*;", "debugger statements"),
        ]

        # Scan relevant directories
        scan_dirs = ["src", "lib", "core", "api"]

        for dir_name in scan_dirs:
            scan_dir = self.repo_root / dir_name
            if scan_dir.exists():
                for file_path in scan_dir.rglob("*.py"):
                    violations.extend(
                        self._check_file_patterns(file_path, forbidden_patterns)
                    )

        return violations

    def _check_file_patterns(
        self, file_path: Path, patterns: list[tuple[str, str]]
    ) -> list[PolicyViolation]:
        """Check file for forbidden patterns"""
        violations = []

        try:
            with open(file_path) as f:
                content = f.read()
                lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern, description in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(
                            PolicyViolation(
                                rule_id="FORBIDDEN_PATTERN",
                                severity=PolicySeverity.WARN,
                                message=f"Found {description}",
                                file_path=str(file_path),
                                line_number=line_num,
                                suggestion="Remove or replace with proper logging",
                            )
                        )

        except Exception as e:
            violations.append(
                PolicyViolation(
                    rule_id="FILE_READ_ERROR",
                    severity=PolicySeverity.WARN,
                    message=f"Could not read {file_path}: {e}",
                )
            )

        return violations

    def _scan_security_issues(self) -> list[PolicyViolation]:
        """Scan for security issues"""
        violations = []

        # Check for hardcoded secrets
        secret_patterns = [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token"),
        ]

        # Scan all Python files
        for file_path in self.repo_root.rglob("*.py"):
            if "test" not in str(file_path):  # Skip test files
                violations.extend(self._check_file_patterns(file_path, secret_patterns))

        return violations

    def _scan_architecture_violations(self) -> list[PolicyViolation]:
        """Scan for architecture violations"""
        violations = []

        # Check for circular imports
        violations.extend(self._check_circular_imports())

        # Check for dependency violations
        violations.extend(self._check_dependency_violations())

        return violations

    def _check_circular_imports(self) -> list[PolicyViolation]:
        """Check for circular imports"""
        # This would implement actual circular import detection
        return []

    def _check_dependency_violations(self) -> list[PolicyViolation]:
        """Check for dependency violations"""
        # This would implement actual dependency violation detection
        return []

    def generate_report(self, violations: list[PolicyViolation]) -> str:
        """Generate policy violation report"""
        if not violations:
            return "✅ No policy violations found"

        report = "🚨 POLICY VIOLATION REPORT\n"
        report += "=" * 50 + "\n\n"

        # Group by severity
        by_severity = {}
        for violation in violations:
            severity = violation.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(violation)

        # Report by severity
        for severity in ["BLOCK", "WARN", "INFO"]:
            if severity in by_severity:
                report += f"\n{severity} VIOLATIONS ({len(by_severity[severity])}):\n"
                report += "-" * 30 + "\n"

                for violation in by_severity[severity]:
                    report += f"• {violation.rule_id}: {violation.message}\n"
                    if violation.file_path:
                        report += f"  File: {violation.file_path}"
                        if violation.line_number:
                            report += f":{violation.line_number}"
                        report += "\n"
                    if violation.suggestion:
                        report += f"  Suggestion: {violation.suggestion}\n"
                    report += "\n"

        return report

    def validate_all(self, config_path: Optional[str] = None) -> bool:
        """Run all validations and return True if all pass"""
        self.load_policies()

        all_violations = []

        # Validate project spec
        all_violations.extend(self.validate_project_spec())

        # Validate task config if provided
        if config_path:
            all_violations.extend(self.validate_task_config(config_path))

        # Scan codebase
        all_violations.extend(self.scan_codebase())

        # Generate report
        report = self.generate_report(all_violations)
        print(report)

        # Check if any BLOCK violations
        block_violations = [
            v for v in all_violations if v.severity == PolicySeverity.BLOCK
        ]

        if block_violations:
            print(
                f"\n❌ Policy validation FAILED - {len(block_violations)} blocking violations"
            )
            return False
        else:
            print("\n✅ Policy validation PASSED")
            return True


def main():
    """CLI entry point for policy engine"""
    import argparse

    parser = argparse.ArgumentParser(description="StillMe AgentDev Policy Engine")
    parser.add_argument("--config", help="Path to task config file")
    parser.add_argument("--spec", help="Path to project spec file")
    parser.add_argument("--policies", help="Path to policies file")
    parser.add_argument("--repo-root", default=".", help="Repository root path")

    args = parser.parse_args()

    engine = PolicyEngine(args.repo_root)
    success = engine.validate_all(args.config)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
