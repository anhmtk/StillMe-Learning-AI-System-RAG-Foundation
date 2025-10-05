# stillme_core/decision_making/decision_engine.py
"""
Advanced Decision Making Engine for AgentDev
Implements Multi-Criteria Decision Analysis with ethical guardrails
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions the system can make"""

    CODE_CHANGE = "code_change"
    SECURITY_ACTION = "security_action"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"
    TEAM_COORDINATION = "team_coordination"
    EMERGENCY_RESPONSE = "emergency_response"


class DecisionStatus(Enum):
    """Status of a decision"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"


class RiskLevel(Enum):
    """Risk levels for decisions"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DecisionCriteria:
    """Criteria for decision making"""

    name: str
    weight: float  # 0.0 to 1.0
    threshold: float  # Minimum acceptable value
    importance: str  # "critical", "important", "nice_to_have"
    description: str


@dataclass
class DecisionContext:
    """Context information for decision making"""

    decision_id: str
    decision_type: DecisionType
    timestamp: float
    requester: str
    urgency: str
    business_impact: str
    technical_complexity: str
    resource_requirements: dict[str, Any]
    constraints: list[str]
    stakeholders: list[str]


@dataclass
class DecisionOption:
    """A decision option with evaluation results"""

    option_id: str
    name: str
    description: str
    criteria_scores: dict[str, float]
    overall_score: float
    risk_assessment: RiskLevel
    implementation_plan: dict[str, Any]
    rollback_plan: dict[str, Any]
    estimated_effort: float
    estimated_impact: float


@dataclass
class DecisionOutcome:
    """Complete decision outcome"""

    decision_id: str
    context: DecisionContext
    selected_option: DecisionOption
    alternatives: list[DecisionOption]
    decision_rationale: str
    confidence_score: float
    risk_mitigation: list[str]
    implementation_status: DecisionStatus
    validation_results: dict[str, Any] | None = None
    ethical_approval: bool = True
    audit_trail: list[dict[str, Any]] | None = None


class DecisionEngine:
    """
    Advanced Decision Making Engine with Multi-Criteria Analysis
    """

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or ".decision_config.json"
        self.decision_history: list[DecisionOutcome] = []
        self.criteria_weights: dict[str, float] = {}
        self.ethical_boundaries: list[str] = []
        self.performance_metrics: dict[str, list[float]] = {}

        # Load configuration
        self._load_configuration()

        # Initialize default criteria
        self._initialize_default_criteria()

        # Initialize ethical boundaries
        self._initialize_ethical_boundaries()

    def _load_configuration(self):
        """Load decision engine configuration"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    self.criteria_weights = config.get("criteria_weights", {})
                    self.ethical_boundaries = config.get("ethical_boundaries", [])
                    self.performance_metrics = config.get("performance_metrics", {})
            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}")
                self._create_default_configuration()
        else:
            self._create_default_configuration()

    def _create_default_configuration(self):
        """Create default configuration"""
        default_config = {
            "criteria_weights": {
                "security": 0.25,
                "performance": 0.20,
                "maintainability": 0.20,
                "business_value": 0.15,
                "resource_efficiency": 0.10,
                "user_experience": 0.10,
            },
            "ethical_boundaries": [
                "Never compromise system security",
                "Always maintain data privacy",
                "Ensure system stability",
                "Respect user autonomy",
                "Maintain transparency",
            ],
            "performance_metrics": {},
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")

    def _initialize_default_criteria(self):
        """Initialize default decision criteria"""
        if not self.criteria_weights:
            self.criteria_weights = {
                "security": 0.25,
                "performance": 0.20,
                "maintainability": 0.20,
                "business_value": 0.15,
                "resource_efficiency": 0.10,
                "user_experience": 0.10,
            }

    def _initialize_ethical_boundaries(self):
        """Initialize ethical boundaries"""
        if not self.ethical_boundaries:
            self.ethical_boundaries = [
                "Never compromise system security",
                "Always maintain data privacy",
                "Ensure system stability",
                "Respect user autonomy",
                "Maintain transparency",
            ]

    def make_decision(
        self,
        decision_type: DecisionType,
        options: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> DecisionOutcome:
        """
        Make a decision using multi-criteria analysis

        Args:
            decision_type: Type of decision to make
            options: List of decision options with their attributes
            context: Context information for the decision

        Returns:
            DecisionOutcome with the selected option and rationale
        """
        decision_id = str(uuid.uuid4())
        start_time = time.time()

        # Create decision context
        decision_context = DecisionContext(
            decision_id=decision_id,
            decision_type=decision_type,
            timestamp=start_time,
            requester=context.get("requester", "system"),
            urgency=context.get("urgency", "normal"),
            business_impact=context.get("business_impact", "medium"),
            technical_complexity=context.get("technical_complexity", "medium"),
            resource_requirements=context.get("resource_requirements", {}),
            constraints=context.get("constraints", []),
            stakeholders=context.get("stakeholders", []),
        )

        # Log decision start
        self._log_decision_event(
            decision_id,
            "decision_started",
            {"type": decision_type.value, "options_count": len(options)},
        )

        try:
            # Step 1: Evaluate options using multi-criteria analysis
            evaluated_options = self._evaluate_options(options, decision_context)

            # Step 2: Apply ethical guardrails
            ethical_filtered_options = self._apply_ethical_filter(
                evaluated_options, decision_context
            )

            if not ethical_filtered_options:
                return self._create_rejected_decision(
                    decision_context, "No options passed ethical validation"
                )

            # Step 3: Select best option
            selected_option = self._select_best_option(
                ethical_filtered_options, decision_context
            )

            # Step 4: Validate decision
            validation_result = self._validate_decision(
                selected_option, decision_context
            )

            if not validation_result.get("valid", False):
                return self._create_rejected_decision(
                    decision_context,
                    f"Decision validation failed: {validation_result.get('reason', 'Unknown')}",
                )

            # Step 5: Create decision outcome
            decision_outcome = DecisionOutcome(
                decision_id=decision_id,
                context=decision_context,
                selected_option=selected_option,
                alternatives=ethical_filtered_options,
                decision_rationale=self._generate_rationale(
                    selected_option, ethical_filtered_options
                ),
                confidence_score=self._calculate_confidence(
                    selected_option, ethical_filtered_options
                ),
                risk_mitigation=self._generate_risk_mitigation(selected_option),
                implementation_status=DecisionStatus.APPROVED,
                validation_results=validation_result,
                ethical_approval=True,
                audit_trail=self._get_audit_trail(decision_id),
            )

            # Step 6: Log decision completion
            self._log_decision_event(
                decision_id,
                "decision_completed",
                {
                    "selected_option": selected_option.name,
                    "confidence_score": decision_outcome.confidence_score,
                    "duration": time.time() - start_time,
                },
            )

            # Step 7: Store decision in history
            self.decision_history.append(decision_outcome)

            # Step 8: Update performance metrics
            self._update_performance_metrics(decision_outcome)

            return decision_outcome

        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            return self._create_rejected_decision(
                decision_context, f"Decision making failed: {e!s}"
            )

    def _evaluate_options(
        self, options: list[dict[str, Any]], context: DecisionContext
    ) -> list[DecisionOption]:
        """Evaluate options using multi-criteria analysis"""
        evaluated_options = []

        for i, option_data in enumerate(options):
            option_id = f"option_{i+1}_{int(time.time())}"

            # Calculate criteria scores
            criteria_scores = self._calculate_criteria_scores(option_data, context)

            # Calculate overall score
            overall_score = self._calculate_overall_score(criteria_scores)

            # Assess risk level
            risk_level = self._assess_risk_level(option_data, criteria_scores)

            # Create implementation plan
            implementation_plan = self._create_implementation_plan(option_data, context)

            # Create rollback plan
            rollback_plan = self._create_rollback_plan(option_data, context)

            # Estimate effort and impact
            estimated_effort = self._estimate_effort(option_data, context)
            estimated_impact = self._estimate_impact(option_data, context)

            option = DecisionOption(
                option_id=option_id,
                name=option_data.get("name", f"Option {i+1}"),
                description=option_data.get("description", ""),
                criteria_scores=criteria_scores,
                overall_score=overall_score,
                risk_assessment=risk_level,
                implementation_plan=implementation_plan,
                rollback_plan=rollback_plan,
                estimated_effort=estimated_effort,
                estimated_impact=estimated_impact,
            )

            evaluated_options.append(option)

        return evaluated_options

    def _calculate_criteria_scores(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> dict[str, float]:
        """Calculate scores for each criteria"""
        scores = {}

        # Security score
        scores["security"] = self._calculate_security_score(option_data, context)

        # Performance score
        scores["performance"] = self._calculate_performance_score(option_data, context)

        # Maintainability score
        scores["maintainability"] = self._calculate_maintainability_score(
            option_data, context
        )

        # Business value score
        scores["business_value"] = self._calculate_business_value_score(
            option_data, context
        )

        # Resource efficiency score
        scores["resource_efficiency"] = self._calculate_resource_efficiency_score(
            option_data, context
        )

        # User experience score
        scores["user_experience"] = self._calculate_user_experience_score(
            option_data, context
        )

        return scores

    def _calculate_security_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate security score for an option"""
        base_score = 0.5  # Neutral score

        # Check for security improvements
        if option_data.get("security_improvements"):
            base_score += 0.3

        # Check for security risks
        if option_data.get("security_risks"):
            base_score -= 0.4

        # Check for encryption usage
        if option_data.get("uses_encryption", False):
            base_score += 0.2

        # Check for authentication requirements
        if option_data.get("requires_authentication", False):
            base_score += 0.1

        return max(0.0, min(1.0, base_score))

    def _calculate_performance_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate performance score for an option"""
        base_score = 0.5

        # Check for performance improvements
        if option_data.get("performance_improvements"):
            base_score += 0.3

        # Check for performance impact
        performance_impact = option_data.get("performance_impact", 0)
        if performance_impact > 0:
            base_score += 0.2
        elif performance_impact < 0:
            base_score -= 0.3

        # Check for resource usage
        resource_usage = option_data.get("resource_usage", "medium")
        if resource_usage == "low":
            base_score += 0.1
        elif resource_usage == "high":
            base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _calculate_maintainability_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate maintainability score for an option"""
        base_score = 0.5

        # Check for code complexity
        complexity = option_data.get("complexity", "medium")
        if complexity == "low":
            base_score += 0.2
        elif complexity == "high":
            base_score -= 0.3

        # Check for documentation
        if option_data.get("has_documentation", False):
            base_score += 0.2

        # Check for test coverage
        test_coverage = option_data.get("test_coverage", 0)
        if test_coverage > 0.8:
            base_score += 0.2
        elif test_coverage < 0.5:
            base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _calculate_business_value_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate business value score for an option"""
        base_score = 0.5

        # Check for business impact
        business_impact = option_data.get("business_impact", "medium")
        if business_impact == "high":
            base_score += 0.3
        elif business_impact == "low":
            base_score -= 0.2

        # Check for user value
        user_value = option_data.get("user_value", "medium")
        if user_value == "high":
            base_score += 0.2
        elif user_value == "low":
            base_score -= 0.1

        # Check for revenue impact
        revenue_impact = option_data.get("revenue_impact", 0)
        if revenue_impact > 0:
            base_score += 0.2
        elif revenue_impact < 0:
            base_score -= 0.3

        return max(0.0, min(1.0, base_score))

    def _calculate_resource_efficiency_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate resource efficiency score for an option"""
        base_score = 0.5

        # Check for resource requirements
        resource_requirements = option_data.get("resource_requirements", {})
        if resource_requirements.get("cpu_usage", 0) < 0.5:
            base_score += 0.1
        if resource_requirements.get("memory_usage", 0) < 0.5:
            base_score += 0.1
        if resource_requirements.get("storage_usage", 0) < 0.5:
            base_score += 0.1

        # Check for cost efficiency
        cost = option_data.get("cost", 0)
        if cost == 0:
            base_score += 0.2
        elif cost > 1000:  # High cost threshold
            base_score -= 0.3

        return max(0.0, min(1.0, base_score))

    def _calculate_user_experience_score(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Calculate user experience score for an option"""
        base_score = 0.5

        # Check for UX improvements
        if option_data.get("ux_improvements"):
            base_score += 0.3

        # Check for accessibility
        if option_data.get("accessibility_compliant", False):
            base_score += 0.2

        # Check for usability
        usability = option_data.get("usability", "medium")
        if usability == "high":
            base_score += 0.2
        elif usability == "low":
            base_score -= 0.3

        return max(0.0, min(1.0, base_score))

    def _calculate_overall_score(self, criteria_scores: dict[str, float]) -> float:
        """Calculate overall weighted score"""
        total_score = 0.0
        total_weight = 0.0

        for criteria, score in criteria_scores.items():
            weight = self.criteria_weights.get(criteria, 0.1)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _assess_risk_level(
        self, option_data: dict[str, Any], criteria_scores: dict[str, float]
    ) -> RiskLevel:
        """Assess risk level for an option"""
        risk_factors = 0

        # Check for high-risk indicators
        if criteria_scores.get("security", 0.5) < 0.3:
            risk_factors += 2
        if criteria_scores.get("performance", 0.5) < 0.3:
            risk_factors += 1
        if option_data.get("experimental", False):
            risk_factors += 2
        if option_data.get("breaking_changes", False):
            risk_factors += 3
        if option_data.get("external_dependencies", 0) > 5:
            risk_factors += 1

        # Determine risk level
        if risk_factors >= 5:
            return RiskLevel.CRITICAL
        elif risk_factors >= 3:
            return RiskLevel.HIGH
        elif risk_factors >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _create_implementation_plan(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> dict[str, Any]:
        """Create implementation plan for an option"""
        return {
            "steps": option_data.get("implementation_steps", []),
            "timeline": option_data.get("timeline", "1-2 weeks"),
            "resources_needed": option_data.get("resources_needed", []),
            "dependencies": option_data.get("dependencies", []),
            "testing_requirements": option_data.get("testing_requirements", []),
            "deployment_strategy": option_data.get("deployment_strategy", "gradual"),
        }

    def _create_rollback_plan(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> dict[str, Any]:
        """Create rollback plan for an option"""
        return {
            "rollback_triggers": option_data.get("rollback_triggers", []),
            "rollback_steps": option_data.get("rollback_steps", []),
            "rollback_timeline": option_data.get("rollback_timeline", "immediate"),
            "data_backup_required": option_data.get("data_backup_required", True),
            "rollback_testing": option_data.get("rollback_testing", True),
        }

    def _estimate_effort(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Estimate effort required for an option"""
        base_effort = 1.0  # Base effort in person-days

        # Adjust based on complexity
        complexity = option_data.get("complexity", "medium")
        if complexity == "low":
            base_effort *= 0.5
        elif complexity == "high":
            base_effort *= 2.0
        elif complexity == "very_high":
            base_effort *= 3.0

        # Adjust based on team size
        team_size = len(context.stakeholders)
        if team_size > 5:
            base_effort *= 1.5  # Coordination overhead

        return base_effort

    def _estimate_impact(
        self, option_data: dict[str, Any], context: DecisionContext
    ) -> float:
        """Estimate impact of an option"""
        base_impact = 0.5  # Neutral impact

        # Adjust based on business impact
        business_impact = option_data.get("business_impact", "medium")
        if business_impact == "high":
            base_impact += 0.3
        elif business_impact == "low":
            base_impact -= 0.2

        # Adjust based on user count
        user_count = option_data.get("affected_users", 0)
        if user_count > 1000:
            base_impact += 0.2
        elif user_count > 100:
            base_impact += 0.1

        return max(0.0, min(1.0, base_impact))

    def _apply_ethical_filter(
        self, options: list[DecisionOption], context: DecisionContext
    ) -> list[DecisionOption]:
        """Apply ethical guardrails to filter options"""
        ethical_options = []

        for option in options:
            is_ethical = True

            # Check against ethical boundaries
            for boundary in self.ethical_boundaries:
                if not self._check_ethical_boundary(option, boundary):
                    is_ethical = False
                    break

            if is_ethical:
                ethical_options.append(option)
            else:
                self._log_decision_event(
                    context.decision_id,
                    "option_rejected_ethical",
                    {"option": option.name, "reason": "Ethical boundary violation"},
                )

        return ethical_options

    def _check_ethical_boundary(self, option: DecisionOption, boundary: str) -> bool:
        """Check if an option violates an ethical boundary"""
        # This is a simplified implementation
        # In practice, you'd have more sophisticated ethical checking

        if "security" in boundary.lower():
            return option.criteria_scores.get("security", 0.5) >= 0.3

        if "privacy" in boundary.lower():
            return "privacy_violation" not in option.description.lower()

        if "stability" in boundary.lower():
            return option.risk_assessment in [RiskLevel.LOW, RiskLevel.MEDIUM]

        return True  # Default to allowing if no specific check

    def _select_best_option(
        self, options: list[DecisionOption], context: DecisionContext
    ) -> DecisionOption:
        """Select the best option based on scores and risk assessment"""
        if not options:
            raise ValueError("No options available for selection")

        # Sort by overall score (descending) and risk level (ascending)
        sorted_options = sorted(
            options,
            key=lambda x: (x.overall_score, -self._risk_level_value(x.risk_assessment)),
            reverse=True,
        )

        return sorted_options[0]

    def _risk_level_value(self, risk_level: RiskLevel) -> int:
        """Convert risk level to numeric value for sorting"""
        risk_values = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }
        return risk_values.get(risk_level, 2)

    def _validate_decision(
        self, option: DecisionOption, context: DecisionContext
    ) -> dict[str, Any]:
        """Validate the selected decision"""
        validation_result = {"valid": True, "checks": [], "warnings": [], "errors": []}

        # Check minimum thresholds
        for criteria, score in option.criteria_scores.items():
            threshold = 0.3  # Default threshold
            if score < threshold:
                validation_result["warnings"].append(
                    f"{criteria} score ({score:.2f}) below threshold ({threshold})"
                )

        # Check risk level
        if option.risk_assessment == RiskLevel.CRITICAL:
            validation_result["errors"].append(
                "Critical risk level requires manual approval"
            )
            validation_result["valid"] = False

        # Check resource constraints
        if context.resource_requirements:
            # Add resource validation logic here
            pass

        return validation_result

    def _generate_rationale(
        self, selected_option: DecisionOption, alternatives: list[DecisionOption]
    ) -> str:
        """Generate decision rationale"""
        rationale = f"Selected '{selected_option.name}' with overall score {selected_option.overall_score:.2f} "
        rationale += f"and risk level {selected_option.risk_assessment.value}.\n\n"

        rationale += "Key factors:\n"
        for criteria, score in selected_option.criteria_scores.items():
            rationale += f"- {criteria}: {score:.2f}\n"

        if alternatives:
            rationale += f"\nConsidered {len(alternatives)} alternatives. "
            rationale += f"Best alternative: {alternatives[0].name} (score: {alternatives[0].overall_score:.2f})"

        return rationale

    def _calculate_confidence(
        self, selected_option: DecisionOption, alternatives: list[DecisionOption]
    ) -> float:
        """Calculate confidence in the decision"""
        if not alternatives:
            return 0.5  # No comparison possible

        # Calculate score difference with next best option
        score_diff = selected_option.overall_score - alternatives[0].overall_score

        # Base confidence on score difference and risk level
        base_confidence = min(0.9, 0.5 + score_diff * 2)

        # Adjust for risk level
        risk_adjustment = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.0,
            RiskLevel.HIGH: -0.1,
            RiskLevel.CRITICAL: -0.2,
        }

        confidence = base_confidence + risk_adjustment.get(
            selected_option.risk_assessment, 0
        )
        return max(0.1, min(0.95, confidence))

    def _generate_risk_mitigation(self, option: DecisionOption) -> list[str]:
        """Generate risk mitigation strategies"""
        mitigations = []

        if option.risk_assessment == RiskLevel.HIGH:
            mitigations.append("Implement comprehensive monitoring")
            mitigations.append("Prepare rollback plan")
            mitigations.append("Conduct thorough testing")

        if option.risk_assessment == RiskLevel.CRITICAL:
            mitigations.append("Require manual approval")
            mitigations.append("Implement staged rollout")
            mitigations.append("Prepare emergency response plan")

        # Add specific mitigations based on low scores
        for criteria, score in option.criteria_scores.items():
            if score < 0.4:
                mitigations.append(f"Address {criteria} concerns before implementation")

        return mitigations

    def _create_rejected_decision(
        self, context: DecisionContext, reason: str
    ) -> DecisionOutcome:
        """Create a rejected decision outcome"""
        from .decision_engine import DecisionOption

        rejected_option = DecisionOption(
            option_id="rejected",
            name="Rejected Option",
            description=reason,
            criteria_scores={},
            overall_score=0.0,
            risk_assessment=RiskLevel.CRITICAL,
            implementation_plan={},
            rollback_plan={},
            estimated_effort=0.0,
            estimated_impact=0.0,
        )

        return DecisionOutcome(
            decision_id=context.decision_id,
            context=context,
            selected_option=rejected_option,
            alternatives=[],
            decision_rationale=f"Decision rejected: {reason}",
            confidence_score=0.0,
            risk_mitigation=[],
            implementation_status=DecisionStatus.REJECTED,
            ethical_approval=False,
            audit_trail=self._get_audit_trail(context.decision_id),
        )

    def _log_decision_event(
        self, decision_id: str, event_type: str, data: dict[str, Any]
    ):
        """Log decision events for audit trail"""
        event = {
            "timestamp": time.time(),
            "decision_id": decision_id,
            "event_type": event_type,
            "data": data,
        }

        # In a real implementation, you'd log to a proper audit system
        logger.info(f"Decision Event: {event}")

    def _get_audit_trail(self, decision_id: str) -> list[dict[str, Any]]:
        """Get audit trail for a decision"""
        # This would typically query an audit log system
        return [
            {
                "timestamp": time.time(),
                "event": "decision_started",
                "decision_id": decision_id,
            }
        ]

    def _update_performance_metrics(self, outcome: DecisionOutcome):
        """Update performance metrics based on decision outcome"""
        # Track decision success rate
        if "decision_success_rate" not in self.performance_metrics:
            self.performance_metrics["decision_success_rate"] = []

        success_rate = (
            1.0 if outcome.implementation_status == DecisionStatus.APPROVED else 0.0
        )
        self.performance_metrics["decision_success_rate"].append(success_rate)

        # Keep only last 100 measurements
        if len(self.performance_metrics["decision_success_rate"]) > 100:
            self.performance_metrics["decision_success_rate"] = (
                self.performance_metrics["decision_success_rate"][-100:]
            )

    def get_decision_history(self, limit: int = 50) -> list[DecisionOutcome]:
        """Get recent decision history"""
        return self.decision_history[-limit:]

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        metrics = {}

        for metric_name, values in self.performance_metrics.items():
            if values:
                metrics[metric_name] = {
                    "current": values[-1],
                    "average": sum(values) / len(values),
                    "trend": (
                        "improving"
                        if len(values) > 1 and values[-1] > values[-2]
                        else "stable"
                    ),
                }

        return metrics

    def update_criteria_weights(self, new_weights: dict[str, float]):
        """Update criteria weights"""
        self.criteria_weights.update(new_weights)
        self._save_configuration()

    def add_ethical_boundary(self, boundary: str):
        """Add new ethical boundary"""
        if boundary not in self.ethical_boundaries:
            self.ethical_boundaries.append(boundary)
            self._save_configuration()

    def _save_configuration(self):
        """Save current configuration"""
        config = {
            "criteria_weights": self.criteria_weights,
            "ethical_boundaries": self.ethical_boundaries,
            "performance_metrics": self.performance_metrics,
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
