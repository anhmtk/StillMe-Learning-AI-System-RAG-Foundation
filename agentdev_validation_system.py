"""AgentDev Validation System"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Validation result"""
    success: bool
    message: str
    severity: ErrorSeverity
    details: dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AgentDevValidator:
    """AgentDev validation system"""

    def __init__(self):
        self.logger = logger
        self.validation_history: list[ValidationResult] = []
        self.logger.info("✅ AgentDevValidator initialized")

    def validate_agentdev_task(self, task: dict[str, Any]) -> ValidationResult:
        """Validate AgentDev task"""
        try:
            # Basic validation
            required_fields = ["id", "description", "type"]
            missing_fields = [field for field in required_fields if field not in task]

            if missing_fields:
                return ValidationResult(
                    success=False,
                    message=f"Missing required fields: {missing_fields}",
                    severity=ErrorSeverity.HIGH
                )

            return ValidationResult(
                success=True,
                message="Task validation passed",
                severity=ErrorSeverity.LOW
            )

        except Exception as e:
            self.logger.error(f"❌ Task validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Validation error: {e}",
                severity=ErrorSeverity.CRITICAL
            )

    def validate_code_quality(self, code: str) -> ValidationResult:
        """Validate code quality"""
        try:
            issues = []

            # Basic quality checks
            if len(code.split('\n')) > 1000:
                issues.append("Code too long")

            if code.count('if') + code.count('for') + code.count('while') > 50:
                issues.append("High complexity")

            if issues:
                return ValidationResult(
                    success=False,
                    message=f"Quality issues: {', '.join(issues)}",
                    severity=ErrorSeverity.MEDIUM,
                    details={"issues": issues}
                )

            return ValidationResult(
                success=True,
                message="Code quality validation passed",
                severity=ErrorSeverity.LOW
            )

        except Exception as e:
            self.logger.error(f"❌ Code quality validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Quality validation error: {e}",
                severity=ErrorSeverity.CRITICAL
            )

    def get_validation_summary(self) -> dict[str, Any]:
        """Get validation summary"""
        try:
            total_validations = len(self.validation_history)
            successful_validations = len([r for r in self.validation_history if r.success])
            failed_validations = total_validations - successful_validations

            return {
                "total_validations": total_validations,
                "successful": successful_validations,
                "failed": failed_validations,
                "success_rate": (successful_validations / total_validations * 100) if total_validations > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get validation summary: {e}")
            return {"error": str(e)}
