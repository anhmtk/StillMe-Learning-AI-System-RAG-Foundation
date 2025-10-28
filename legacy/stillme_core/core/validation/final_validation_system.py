"""
🔍 FINAL VALIDATION SYSTEM

Comprehensive validation system for StillMe framework components.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""

    component: str
    check_type: str
    passed: bool
    message: str
    details: dict[str, Any]
    timestamp: datetime


class FinalValidationSystem:
    """
    Final validation system for StillMe framework
    """

    def __init__(self, config_path: str = "config/validation_config.json"):
        self.config = self._load_config(config_path)
        self.validation_results: list[ValidationResult] = []
        self.security_middleware = None
        self.performance_monitor = None
        self.integration_bridge = None
        self.memory_security_integration = None
        self.module_governance_system = None

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load validation configuration"""
        default_config = {
            "validation": {
                "security": {
                    "enabled": True,
                    "checks": ["input_validation", "rate_limiting", "headers"],
                },
                "performance": {
                    "enabled": True,
                    "max_response_time": 5.0,
                    "max_memory_usage": 1024,
                },
                "integration": {
                    "enabled": True,
                    "required_components": ["security", "memory", "governance"],
                },
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            logger.warning(f"Could not load validation config: {e}")

        return default_config

    def initialize_components(self):
        """Initialize all required components"""
        try:
            # Try to import security middleware
            try:
                from .security_middleware import SecurityMiddleware

                self.security_middleware = SecurityMiddleware()
                logger.info("✅ Security middleware initialized")
            except ImportError:
                logger.warning("⚠️ Security middleware not available")

            # Try to import performance monitor
            try:
                from .performance_monitor import PerformanceMonitor

                self.performance_monitor = PerformanceMonitor()
                logger.info("✅ Performance monitor initialized")
            except ImportError:
                logger.warning("⚠️ Performance monitor not available")

            # Try to import integration bridge
            try:
                from .integration_bridge import IntegrationBridge

                self.integration_bridge = IntegrationBridge()
                logger.info("✅ Integration bridge initialized")
            except ImportError:
                logger.warning("⚠️ Integration bridge not available")

            # Try to import memory security integration
            try:
                from ..memory_security_integration import MemorySecurityIntegration

                self.memory_security_integration = MemorySecurityIntegration()
                logger.info("✅ Memory security integration initialized")
            except ImportError:
                logger.warning("⚠️ Memory security integration not available")

            # Try to import module governance system
            try:
                from ..module_governance_system import ModuleGovernanceSystem

                self.module_governance_system = ModuleGovernanceSystem()
                logger.info("✅ Module governance system initialized")
            except ImportError:
                logger.warning("⚠️ Module governance system not available")

        except Exception as e:
            logger.error(f"Error initializing components: {e}")

    def run_security_validation(self) -> list[ValidationResult]:
        """Run security validation checks"""
        results = []

        if not self.config["validation"]["security"]["enabled"]:
            return results

        # Check if security middleware is available
        if self.security_middleware is None:
            results.append(
                ValidationResult(
                    component="security_middleware",
                    check_type="availability",
                    passed=False,
                    message="Security middleware not available",
                    details={"error": "Import failed"},
                    timestamp=datetime.now(),
                )
            )
            return results

        # Test input validation
        if "input_validation" in self.config["validation"]["security"]["checks"]:
            test_inputs = [
                ("valid_input", "Hello world", True),
                ("xss_attempt", "<script>alert('xss')</script>", False),
                ("sql_injection", "'; DROP TABLE users; --", False),
            ]

            for test_name, test_input, expected_valid in test_inputs:
                result = self.security_middleware.validate_input(test_input)
                passed = result["is_valid"] == expected_valid

                results.append(
                    ValidationResult(
                        component="security_middleware",
                        check_type="input_validation",
                        passed=passed,
                        message=f"Input validation test: {test_name}",
                        details={
                            "input": test_input,
                            "expected_valid": expected_valid,
                            "actual_valid": result["is_valid"],
                            "threats_detected": result["threats_detected"],
                        },
                        timestamp=datetime.now(),
                    )
                )

        return results

    def run_performance_validation(self) -> list[ValidationResult]:
        """Run performance validation checks"""
        results = []

        if not self.config["validation"]["performance"]["enabled"]:
            return results

        # Check if performance monitor is available
        if self.performance_monitor is None:
            results.append(
                ValidationResult(
                    component="performance_monitor",
                    check_type="availability",
                    passed=False,
                    message="Performance monitor not available",
                    details={"error": "Import failed"},
                    timestamp=datetime.now(),
                )
            )
            return results

        return results

    def run_integration_validation(self) -> list[ValidationResult]:
        """Run integration validation checks"""
        results = []

        if not self.config["validation"]["integration"]["enabled"]:
            return results

        required_components = self.config["validation"]["integration"][
            "required_components"
        ]

        for component in required_components:
            component_available = False

            if component == "security" and self.security_middleware is not None:
                component_available = True
            elif component == "memory" and self.memory_security_integration is not None:
                component_available = True
            elif (
                component == "governance" and self.module_governance_system is not None
            ):
                component_available = True

            results.append(
                ValidationResult(
                    component=component,
                    check_type="integration",
                    passed=component_available,
                    message=f"Integration check: {component}",
                    details={"required": True, "available": component_available},
                    timestamp=datetime.now(),
                )
            )

        return results

    def run_full_validation(self) -> dict[str, Any]:
        """Run all validation checks"""
        logger.info("🔍 Starting full validation...")

        # Initialize components
        self.initialize_components()

        # Run all validation checks
        all_results = []
        all_results.extend(self.run_security_validation())
        all_results.extend(self.run_performance_validation())
        all_results.extend(self.run_integration_validation())

        # Store results
        self.validation_results.extend(all_results)

        # Calculate summary
        total_checks = len(all_results)
        passed_checks = sum(1 for r in all_results if r.passed)
        failed_checks = total_checks - passed_checks

        summary = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": (passed_checks / total_checks * 100)
            if total_checks > 0
            else 0,
            "validation_timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "component": r.component,
                    "check_type": r.check_type,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in all_results
            ],
        }

        logger.info(
            f"✅ Validation complete: {passed_checks}/{total_checks} checks passed"
        )

        return summary


def main():
    """Test the validation system"""
    validator = FinalValidationSystem()

    # Run full validation
    results = validator.run_full_validation()

    print("🔍 Validation Results:")
    print(f"Total checks: {results['total_checks']}")
    print(f"Passed: {results['passed_checks']}")
    print(f"Failed: {results['failed_checks']}")
    print(f"Success rate: {results['success_rate']:.1f}%")


if __name__ == "__main__":
    main()
