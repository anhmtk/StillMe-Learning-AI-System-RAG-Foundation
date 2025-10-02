"""
🔍 VALIDATION FRAMEWORK

Core validation framework for StillMe components.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """A validation rule"""
    name: str
    description: str
    validator: Callable[[Any], bool]
    error_message: str


@dataclass
class ValidationResult:
    """Result of a validation"""
    rule_name: str
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class ValidationFramework:
    """
    Core validation framework
    """

    def __init__(self, config_path: str = "config/validation_config.json"):
        self.config = self._load_config(config_path)
        self.rules: Dict[str, ValidationRule] = {}
        self.results: List[ValidationResult] = []
        self.security_middleware = None
        self.performance_monitor = None
        self.integration_bridge = None
        self.memory_security_integration = None
        self.module_governance_system = None

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load validation configuration"""
        default_config = {
            "validation": {
                "enabled": True,
                "strict_mode": False,
                "log_level": "INFO"
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            logger.warning(f"Could not load validation config: {e}")

        return default_config

    def add_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added validation rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove a validation rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed validation rule: {rule_name}")

    def validate(self, data: Any, rule_name: Optional[str] = None) -> List[ValidationResult]:
        """Validate data against rules"""
        results = []
        
        if not self.config["validation"]["enabled"]:
            return results

        rules_to_check = []
        if rule_name:
            if rule_name in self.rules:
                rules_to_check = [self.rules[rule_name]]
            else:
                logger.warning(f"Rule not found: {rule_name}")
                return results
        else:
            rules_to_check = list(self.rules.values())

        for rule in rules_to_check:
            try:
                passed = rule.validator(data)
                result = ValidationResult(
                    rule_name=rule.name,
                    passed=passed,
                    message=rule.error_message if not passed else "Validation passed",
                    details={"data_type": type(data).__name__},
                    timestamp=datetime.now()
                )
                results.append(result)
                
                if not passed:
                    logger.warning(f"Validation failed: {rule.name} - {rule.error_message}")
                else:
                    logger.debug(f"Validation passed: {rule.name}")
                    
            except Exception as e:
                result = ValidationResult(
                    rule_name=rule.name,
                    passed=False,
                    message=f"Validation error: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.now()
                )
                results.append(result)
                logger.error(f"Validation error in rule {rule.name}: {e}")

        # Store results
        self.results.extend(results)
        return results

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

    def run_component_validation(self) -> Dict[str, Any]:
        """Run validation on all components"""
        logger.info("🔍 Starting component validation...")
        
        # Initialize components
        self.initialize_components()
        
        # Run validation
        all_results = []
        
        # Validate security middleware
        if self.security_middleware:
            security_results = self._validate_security_middleware()
            all_results.extend(security_results)
        
        # Validate performance monitor
        if self.performance_monitor:
            performance_results = self._validate_performance_monitor()
            all_results.extend(performance_results)
        
        # Validate integration bridge
        if self.integration_bridge:
            integration_results = self._validate_integration_bridge()
            all_results.extend(integration_results)
        
        # Calculate summary
        total_checks = len(all_results)
        passed_checks = sum(1 for r in all_results if r.passed)
        failed_checks = total_checks - passed_checks
        
        summary = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            "validation_timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in all_results
            ]
        }
        
        logger.info(f"✅ Component validation complete: {passed_checks}/{total_checks} checks passed")
        
        return summary

    def _validate_security_middleware(self) -> List[ValidationResult]:
        """Validate security middleware"""
        results = []
        
        # Test input validation
        test_input = "<script>alert('xss')</script>"
        validation_result = self.security_middleware.validate_input(test_input)
        
        results.append(ValidationResult(
            rule_name="security_input_validation",
            passed=not validation_result["is_valid"],
            message="Security middleware should block XSS attempts",
            details={
                "test_input": test_input,
                "is_valid": validation_result["is_valid"],
                "threats_detected": validation_result["threats_detected"]
            },
            timestamp=datetime.now()
        ))
        
        return results

    def _validate_performance_monitor(self) -> List[ValidationResult]:
        """Validate performance monitor"""
        results = []
        
        try:
            summary = self.performance_monitor.get_performance_summary()
            results.append(ValidationResult(
                rule_name="performance_monitor_availability",
                passed=True,
                message="Performance monitor is working",
                details={"summary": summary},
                timestamp=datetime.now()
            ))
        except Exception as e:
            results.append(ValidationResult(
                rule_name="performance_monitor_availability",
                passed=False,
                message="Performance monitor failed",
                details={"error": str(e)},
                timestamp=datetime.now()
            ))
        
        return results

    def _validate_integration_bridge(self) -> List[ValidationResult]:
        """Validate integration bridge"""
        results = []
        
        results.append(ValidationResult(
            rule_name="integration_bridge_availability",
            passed=self.integration_bridge is not None,
            message="Integration bridge should be available",
            details={"available": self.integration_bridge is not None},
            timestamp=datetime.now()
        ))
        
        return results

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        if not self.results:
            return {"message": "No validation results available"}
        
        total_results = len(self.results)
        passed_results = sum(1 for r in self.results if r.passed)
        failed_results = total_results - passed_results
        
        return {
            "total_validations": total_results,
            "passed_validations": passed_results,
            "failed_validations": failed_results,
            "success_rate": (passed_results / total_results * 100) if total_results > 0 else 0,
            "last_validation": max(r.timestamp for r in self.results).isoformat(),
            "recent_results": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "message": r.message,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in sorted(self.results, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }


def main():
    """Test the validation framework"""
    framework = ValidationFramework()
    
    # Add some test rules
    framework.add_rule(ValidationRule(
        name="not_empty",
        description="Check if data is not empty",
        validator=lambda x: bool(x),
        error_message="Data cannot be empty"
    ))
    
    framework.add_rule(ValidationRule(
        name="is_string",
        description="Check if data is a string",
        validator=lambda x: isinstance(x, str),
        error_message="Data must be a string"
    ))
    
    # Test validation
    test_data = "Hello world"
    results = framework.validate(test_data)
    
    print("🔍 Validation Results:")
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.rule_name}: {result.message}")
    
    # Run component validation
    component_results = framework.run_component_validation()
    print(f"\n📊 Component Validation:")
    print(f"Total checks: {component_results['total_checks']}")
    print(f"Passed: {component_results['passed_checks']}")
    print(f"Failed: {component_results['failed_checks']}")
    print(f"Success rate: {component_results['success_rate']:.1f}%")


if __name__ == "__main__":
    main()
