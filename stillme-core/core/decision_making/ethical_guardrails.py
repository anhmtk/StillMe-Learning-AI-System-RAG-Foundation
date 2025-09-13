# stillme_core/decision_making/ethical_guardrails.py
"""
Ethical Guardrails System for AgentDev
Ensures all decisions and actions comply with ethical principles
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EthicalPrinciple(Enum):
    """Core ethical principles"""

    AUTONOMY = "autonomy"  # Respect for user autonomy
    BENEFICENCE = "beneficence"  # Do good, maximize benefits
    NON_MALEFICENCE = "non_maleficence"  # Do no harm
    JUSTICE = "justice"  # Fairness and equality
    TRANSPARENCY = "transparency"  # Openness and honesty
    PRIVACY = "privacy"  # Protect user privacy
    SECURITY = "security"  # Maintain system security
    STABILITY = "stability"  # Ensure system stability


class ViolationSeverity(Enum):
    """Severity levels for ethical violations"""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class EthicalBoundary:
    """An ethical boundary rule"""

    principle: EthicalPrinciple
    rule_id: str
    description: str
    severity: ViolationSeverity
    conditions: List[str]  # Conditions that trigger this boundary
    exceptions: List[str]  # Exceptions to this boundary
    enforcement_action: str  # Action to take when violated


@dataclass
class EthicalViolation:
    """Record of an ethical violation"""

    violation_id: str
    timestamp: float
    principle: EthicalPrinciple
    severity: ViolationSeverity
    description: str
    context: Dict[str, Any]
    action_taken: str
    resolved: bool = False


@dataclass
class EthicalAssessment:
    """Result of ethical assessment"""

    is_ethical: bool
    violations: List[EthicalViolation]
    warnings: List[str]
    recommendations: List[str]
    confidence_score: float
    assessment_details: Dict[str, Any]


class EthicalGuardrails:
    """
    Comprehensive Ethical Guardrails System
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or ".ethical_config.json"
        self.boundaries: List[EthicalBoundary] = []
        self.violation_history: List[EthicalViolation] = []
        self.assessment_cache: Dict[str, EthicalAssessment] = {}

        # Load configuration
        self._load_configuration()

        # Initialize default boundaries
        self._initialize_default_boundaries()

    def _load_configuration(self):
        """Load ethical configuration"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    self._load_boundaries_from_config(config)
            except Exception as e:
                logger.warning(f"Failed to load ethical configuration: {e}")
                self._create_default_configuration()
        else:
            self._create_default_configuration()

    def _load_boundaries_from_config(self, config: Dict[str, Any]):
        """Load boundaries from configuration"""
        for boundary_data in config.get("boundaries", []):
            boundary = EthicalBoundary(
                principle=EthicalPrinciple(boundary_data["principle"]),
                rule_id=boundary_data["rule_id"],
                description=boundary_data["description"],
                severity=ViolationSeverity(boundary_data["severity"]),
                conditions=boundary_data["conditions"],
                exceptions=boundary_data["exceptions"],
                enforcement_action=boundary_data["enforcement_action"],
            )
            self.boundaries.append(boundary)

    def _create_default_configuration(self):
        """Create default ethical configuration"""
        default_boundaries = [
            {
                "principle": "security",
                "rule_id": "SEC_001",
                "description": "Never compromise system security",
                "severity": "critical",
                "conditions": [
                    "security_score < 0.3",
                    "introduces_vulnerability",
                    "removes_security_controls",
                ],
                "exceptions": ["emergency_maintenance", "security_patch_installation"],
                "enforcement_action": "block_decision",
            },
            {
                "principle": "privacy",
                "rule_id": "PRIV_001",
                "description": "Protect user privacy and data",
                "severity": "severe",
                "conditions": [
                    "accesses_personal_data",
                    "logs_sensitive_information",
                    "shares_user_data",
                ],
                "exceptions": [
                    "user_consent_given",
                    "legal_requirement",
                    "anonymized_data_only",
                ],
                "enforcement_action": "require_approval",
            },
            {
                "principle": "stability",
                "rule_id": "STAB_001",
                "description": "Maintain system stability",
                "severity": "moderate",
                "conditions": [
                    "breaking_changes",
                    "high_risk_deployment",
                    "experimental_features",
                ],
                "exceptions": [
                    "staging_environment",
                    "feature_flags_enabled",
                    "rollback_plan_available",
                ],
                "enforcement_action": "add_safeguards",
            },
            {
                "principle": "transparency",
                "rule_id": "TRANS_001",
                "description": "Maintain transparency in operations",
                "severity": "moderate",
                "conditions": [
                    "hidden_changes",
                    "no_documentation",
                    "secret_operations",
                ],
                "exceptions": [
                    "security_incident_response",
                    "confidential_business_data",
                ],
                "enforcement_action": "require_documentation",
            },
            {
                "principle": "autonomy",
                "rule_id": "AUTO_001",
                "description": "Respect user autonomy and choice",
                "severity": "moderate",
                "conditions": [
                    "forces_user_action",
                    "removes_user_control",
                    "changes_defaults_without_notice",
                ],
                "exceptions": [
                    "security_improvements",
                    "user_requested_changes",
                    "legal_compliance",
                ],
                "enforcement_action": "require_user_consent",
            },
        ]

        config = {
            "boundaries": default_boundaries,
            "violation_history": [],
            "assessment_cache": {},
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")

    def _initialize_default_boundaries(self):
        """Initialize default ethical boundaries"""
        if not self.boundaries:
            self._create_default_configuration()
            self._load_configuration()

    def assess_decision(
        self, decision_data: Dict[str, Any], context: Dict[str, Any]
    ) -> EthicalAssessment:
        """
        Assess a decision for ethical compliance

        Args:
            decision_data: Data about the decision being made
            context: Context information for the assessment

        Returns:
            EthicalAssessment with compliance status and details
        """
        assessment_id = self._generate_assessment_id(decision_data, context)

        # Check cache first
        if assessment_id in self.assessment_cache:
            cached_assessment = self.assessment_cache[assessment_id]
            if (
                time.time() - cached_assessment.assessment_details.get("timestamp", 0)
                < 3600
            ):  # 1 hour cache
                return cached_assessment

        violations = []
        warnings = []
        recommendations = []

        # Check each ethical boundary
        for boundary in self.boundaries:
            boundary_result = self._check_boundary(boundary, decision_data, context)

            if boundary_result["violated"]:
                violation = EthicalViolation(
                    violation_id=f"VIO_{int(time.time())}_{len(violations)}",
                    timestamp=time.time(),
                    principle=boundary.principle,
                    severity=boundary.severity,
                    description=boundary_result["description"],
                    context=context,
                    action_taken=boundary.enforcement_action,
                )
                violations.append(violation)
                self.violation_history.append(violation)

            if boundary_result["warning"]:
                warnings.append(boundary_result["warning"])

            if boundary_result["recommendation"]:
                recommendations.append(boundary_result["recommendation"])

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(violations, warnings)

        # Determine overall ethical status
        is_ethical = (
            len(
                [
                    v
                    for v in violations
                    if v.severity
                    in [ViolationSeverity.SEVERE, ViolationSeverity.CRITICAL]
                ]
            )
            == 0
        )

        assessment = EthicalAssessment(
            is_ethical=is_ethical,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            confidence_score=confidence_score,
            assessment_details={
                "timestamp": time.time(),
                "assessment_id": assessment_id,
                "boundaries_checked": len(self.boundaries),
                "context_hash": self._hash_context(context),
            },
        )

        # Cache the assessment
        self.assessment_cache[assessment_id] = assessment

        # Log assessment
        self._log_assessment(assessment)

        return assessment

    def _check_boundary(
        self,
        boundary: EthicalBoundary,
        decision_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if a decision violates an ethical boundary"""
        result = {
            "violated": False,
            "warning": None,
            "recommendation": None,
            "description": "",
        }

        # Check if any conditions are met
        conditions_met = []
        for condition in boundary.conditions:
            if self._evaluate_condition(condition, decision_data, context):
                conditions_met.append(condition)

        if not conditions_met:
            return result  # No conditions met, no violation

        # Check if any exceptions apply
        exceptions_apply = []
        for exception in boundary.exceptions:
            if self._evaluate_condition(exception, decision_data, context):
                exceptions_apply.append(exception)

        # If exceptions apply, no violation
        if exceptions_apply:
            result["recommendation"] = (
                f"Exception applies: {', '.join(exceptions_apply)}"
            )
            return result

        # Violation detected
        result["violated"] = True
        result["description"] = (
            f"{boundary.description} - Conditions met: {', '.join(conditions_met)}"
        )

        # Add warning for moderate violations
        if boundary.severity == ViolationSeverity.MODERATE:
            result["warning"] = f"Moderate ethical concern: {boundary.description}"

        # Add recommendation based on enforcement action
        if boundary.enforcement_action == "block_decision":
            result["recommendation"] = (
                "Decision should be blocked due to ethical violation"
            )
        elif boundary.enforcement_action == "require_approval":
            result["recommendation"] = "Decision requires additional approval"
        elif boundary.enforcement_action == "add_safeguards":
            result["recommendation"] = "Add additional safeguards before proceeding"
        elif boundary.enforcement_action == "require_documentation":
            result["recommendation"] = "Ensure proper documentation is in place"
        elif boundary.enforcement_action == "require_user_consent":
            result["recommendation"] = "Obtain user consent before proceeding"

        return result

    def _evaluate_condition(
        self, condition: str, decision_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition against decision data and context"""
        try:
            # Simple condition evaluation
            # In practice, you'd have more sophisticated evaluation logic

            if "security_score" in condition:
                score = decision_data.get("security_score", 0.5)
                if "< 0.3" in condition:
                    return score < 0.3
                elif "> 0.7" in condition:
                    return score > 0.7

            elif "introduces_vulnerability" in condition:
                return decision_data.get("introduces_vulnerability", False)

            elif "removes_security_controls" in condition:
                return decision_data.get("removes_security_controls", False)

            elif "accesses_personal_data" in condition:
                return decision_data.get("accesses_personal_data", False)

            elif "logs_sensitive_information" in condition:
                return decision_data.get("logs_sensitive_information", False)

            elif "shares_user_data" in condition:
                return decision_data.get("shares_user_data", False)

            elif "breaking_changes" in condition:
                return decision_data.get("breaking_changes", False)

            elif "high_risk_deployment" in condition:
                return decision_data.get("high_risk_deployment", False)

            elif "experimental_features" in condition:
                return decision_data.get("experimental_features", False)

            elif "hidden_changes" in condition:
                return decision_data.get("hidden_changes", False)

            elif "no_documentation" in condition:
                return decision_data.get("no_documentation", False)

            elif "secret_operations" in condition:
                return decision_data.get("secret_operations", False)

            elif "forces_user_action" in condition:
                return decision_data.get("forces_user_action", False)

            elif "removes_user_control" in condition:
                return decision_data.get("removes_user_control", False)

            elif "changes_defaults_without_notice" in condition:
                return decision_data.get("changes_defaults_without_notice", False)

            # Exception conditions
            elif "user_consent_given" in condition:
                return context.get("user_consent_given", False)

            elif "legal_requirement" in condition:
                return context.get("legal_requirement", False)

            elif "anonymized_data_only" in condition:
                return decision_data.get("anonymized_data_only", False)

            elif "staging_environment" in condition:
                return context.get("environment") == "staging"

            elif "feature_flags_enabled" in condition:
                return decision_data.get("feature_flags_enabled", False)

            elif "rollback_plan_available" in condition:
                return decision_data.get("rollback_plan_available", False)

            elif "security_incident_response" in condition:
                return context.get("security_incident_response", False)

            elif "confidential_business_data" in condition:
                return context.get("confidential_business_data", False)

            elif "security_improvements" in condition:
                return decision_data.get("security_improvements", False)

            elif "user_requested_changes" in condition:
                return context.get("user_requested_changes", False)

            elif "legal_compliance" in condition:
                return context.get("legal_compliance", False)

            elif "emergency_maintenance" in condition:
                return context.get("emergency_maintenance", False)

            elif "security_patch_installation" in condition:
                return decision_data.get("security_patch_installation", False)

            return False

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def _calculate_confidence_score(
        self, violations: List[EthicalViolation], warnings: List[str]
    ) -> float:
        """Calculate confidence score for the assessment"""
        if not violations and not warnings:
            return 1.0  # High confidence when no issues

        # Reduce confidence based on violations
        confidence = 1.0
        for violation in violations:
            if violation.severity == ViolationSeverity.CRITICAL:
                confidence -= 0.4
            elif violation.severity == ViolationSeverity.SEVERE:
                confidence -= 0.3
            elif violation.severity == ViolationSeverity.MODERATE:
                confidence -= 0.2
            elif violation.severity == ViolationSeverity.MINOR:
                confidence -= 0.1

        # Reduce confidence based on warnings
        confidence -= len(warnings) * 0.05

        return max(0.0, min(1.0, confidence))

    def _generate_assessment_id(
        self, decision_data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Generate unique assessment ID"""
        data_str = json.dumps(decision_data, sort_keys=True)
        context_str = json.dumps(context, sort_keys=True)
        combined = f"{data_str}_{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Generate hash of context for caching"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]

    def _log_assessment(self, assessment: EthicalAssessment):
        """Log ethical assessment"""
        log_data = {
            "timestamp": assessment.assessment_details["timestamp"],
            "is_ethical": assessment.is_ethical,
            "violations_count": len(assessment.violations),
            "warnings_count": len(assessment.warnings),
            "confidence_score": assessment.confidence_score,
        }

        logger.info(f"Ethical Assessment: {log_data}")

    def add_boundary(self, boundary: EthicalBoundary):
        """Add new ethical boundary"""
        self.boundaries.append(boundary)
        self._save_configuration()

    def remove_boundary(self, rule_id: str):
        """Remove ethical boundary by rule ID"""
        self.boundaries = [b for b in self.boundaries if b.rule_id != rule_id]
        self._save_configuration()

    def get_violation_history(self, limit: int = 100) -> List[EthicalViolation]:
        """Get recent violation history"""
        return self.violation_history[-limit:]

    def get_violation_stats(self) -> Dict[str, Any]:
        """Get violation statistics"""
        if not self.violation_history:
            return {"total_violations": 0}

        stats = {
            "total_violations": len(self.violation_history),
            "by_severity": {},
            "by_principle": {},
            "resolved_count": len([v for v in self.violation_history if v.resolved]),
            "recent_violations": len(
                [v for v in self.violation_history if time.time() - v.timestamp < 86400]
            ),  # Last 24 hours
        }

        # Count by severity
        for severity in ViolationSeverity:
            count = len([v for v in self.violation_history if v.severity == severity])
            stats["by_severity"][severity.value] = count

        # Count by principle
        for principle in EthicalPrinciple:
            count = len([v for v in self.violation_history if v.principle == principle])
            stats["by_principle"][principle.value] = count

        return stats

    def resolve_violation(self, violation_id: str, resolution_notes: str):
        """Mark a violation as resolved"""
        for violation in self.violation_history:
            if violation.violation_id == violation_id:
                violation.resolved = True
                violation.context["resolution_notes"] = resolution_notes
                violation.context["resolved_at"] = time.time()
                break

    def _save_configuration(self):
        """Save current configuration"""
        config = {
            "boundaries": [asdict(boundary) for boundary in self.boundaries],
            "violation_history": [
                asdict(violation) for violation in self.violation_history[-1000:]
            ],  # Keep last 1000
            "assessment_cache": {},  # Don't persist cache
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ethical configuration: {e}")

    def get_ethical_report(self) -> Dict[str, Any]:
        """Generate comprehensive ethical report"""
        stats = self.get_violation_stats()

        return {
            "summary": {
                "total_boundaries": len(self.boundaries),
                "total_violations": stats["total_violations"],
                "resolved_violations": stats["resolved_count"],
                "recent_violations": stats["recent_violations"],
            },
            "violations_by_severity": stats["by_severity"],
            "violations_by_principle": stats["by_principle"],
            "boundaries": [
                {
                    "rule_id": b.rule_id,
                    "principle": b.principle.value,
                    "description": b.description,
                    "severity": b.severity.value,
                }
                for b in self.boundaries
            ],
            "recommendations": self._generate_ethical_recommendations(stats),
        }

    def _generate_ethical_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate ethical recommendations based on statistics"""
        recommendations = []

        if stats["total_violations"] > 10:
            recommendations.append(
                "Consider reviewing ethical boundaries - high violation count"
            )

        if stats["by_severity"].get("critical", 0) > 0:
            recommendations.append("Address critical violations immediately")

        if stats["recent_violations"] > 5:
            recommendations.append(
                "Recent increase in violations - review decision processes"
            )

        if stats["resolved_count"] / max(stats["total_violations"], 1) < 0.8:
            recommendations.append("Improve violation resolution process")

        return recommendations
