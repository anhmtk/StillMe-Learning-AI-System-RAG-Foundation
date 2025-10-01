"""Ethical Guardrails for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class EthicalPrinciple(Enum):
    BENEFICENCE = "beneficence"
    NON_MALEFICENCE = "non_maleficence"
    AUTONOMY = "autonomy"
    JUSTICE = "justice"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"

class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EthicalViolation:
    """Ethical violation record"""
    violation_id: str
    principle: EthicalPrinciple
    severity: ViolationSeverity
    description: str
    context: str
    timestamp: datetime
    suggested_action: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EthicalGuardrails:
    """Ethical guardrails for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.violations: List[EthicalViolation] = []
        self.principles = list(EthicalPrinciple)
        self.logger.info("✅ EthicalGuardrails initialized")

    def check_ethical_compliance(self,
                               content: str,
                               context: str = "",
                               metadata: Dict[str, Any] = None) -> List[EthicalViolation]:
        """Check ethical compliance of content"""
        try:
            violations = []

            # Check for harmful content
            if self._contains_harmful_content(content):
                violation = EthicalViolation(
                    violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    principle=EthicalPrinciple.NON_MALEFICENCE,
                    severity=ViolationSeverity.HIGH,
                    description="Content contains potentially harmful material",
                    context=context,
                    timestamp=datetime.now(),
                    suggested_action="Review and sanitize content",
                    metadata=metadata or {}
                )
                violations.append(violation)

            # Check for bias
            if self._contains_bias(content):
                violation = EthicalViolation(
                    violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    principle=EthicalPrinciple.JUSTICE,
                    severity=ViolationSeverity.MEDIUM,
                    description="Content may contain biased language",
                    context=context,
                    timestamp=datetime.now(),
                    suggested_action="Review for bias and use inclusive language",
                    metadata=metadata or {}
                )
                violations.append(violation)

            # Check for privacy violations
            if self._contains_pii(content):
                violation = EthicalViolation(
                    violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    principle=EthicalPrinciple.AUTONOMY,
                    severity=ViolationSeverity.HIGH,
                    description="Content contains personally identifiable information",
                    context=context,
                    timestamp=datetime.now(),
                    suggested_action="Remove or anonymize PII",
                    metadata=metadata or {}
                )
                violations.append(violation)

            # Record violations
            for violation in violations:
                self.violations.append(violation)
                self.logger.warning(f"⚠️ Ethical violation detected: {violation.principle.value} - {violation.description}")

            return violations

        except Exception as e:
            self.logger.error(f"❌ Failed to check ethical compliance: {e}")
            return []

    def _contains_harmful_content(self, content: str) -> bool:
        """Check if content contains harmful material"""
        harmful_keywords = [
            "violence", "harm", "danger", "threat", "attack",
            "illegal", "criminal", "fraud", "scam", "deception"
        ]

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in harmful_keywords)

    def _contains_bias(self, content: str) -> bool:
        """Check if content contains biased language"""
        bias_keywords = [
            "always", "never", "all", "none", "everyone", "nobody",
            "typical", "normal", "abnormal", "weird", "strange"
        ]

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in bias_keywords)

    def _contains_pii(self, content: str) -> bool:
        """Check if content contains personally identifiable information"""
        import re

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, content):
            return True

        # Phone pattern
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, content):
            return True

        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, content):
            return True

        return False

    def get_violations_by_principle(self, principle: EthicalPrinciple) -> List[EthicalViolation]:
        """Get violations by ethical principle"""
        return [v for v in self.violations if v.principle == principle]

    def get_violations_by_severity(self, severity: ViolationSeverity) -> List[EthicalViolation]:
        """Get violations by severity"""
        return [v for v in self.violations if v.severity == severity]

    def get_ethical_summary(self) -> Dict[str, Any]:
        """Get ethical compliance summary"""
        try:
            total_violations = len(self.violations)

            violations_by_principle = {}
            violations_by_severity = {}

            for violation in self.violations:
                # By principle
                principle_key = violation.principle.value
                violations_by_principle[principle_key] = violations_by_principle.get(principle_key, 0) + 1

                # By severity
                severity_key = violation.severity.value
                violations_by_severity[severity_key] = violations_by_severity.get(severity_key, 0) + 1

            return {
                "total_violations": total_violations,
                "violations_by_principle": violations_by_principle,
                "violations_by_severity": violations_by_severity,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get ethical summary: {e}")
            return {"error": str(e)}

    def clear_violations(self):
        """Clear all violations"""
        self.violations.clear()
        self.logger.info("🧹 All ethical violations cleared")