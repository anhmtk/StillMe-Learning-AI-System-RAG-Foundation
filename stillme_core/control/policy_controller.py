"""
Policy controller for StillMe AI Framework.
Manages policy levels and control mechanisms.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class PolicyLevel(Enum):
    """Policy levels for controlling AI behavior."""

    STRICT = "strict"
    BALANCED = "balanced"
    CREATIVE = "creative"


@dataclass
class PolicyConfig:
    """Configuration for policy control."""

    level: PolicyLevel
    max_clarification_rounds: int
    confidence_threshold: float
    abuse_detection_enabled: bool
    proactive_suggestions_enabled: bool
    dry_run: bool
    custom_rules: dict[str, Any]


class PolicyController:
    """Controller for managing AI policy and behavior."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.policy_level = PolicyLevel(self.config.get("level", "balanced"))
        self.dry_run = self.config.get("dry_run", False)
        self.custom_rules = self.config.get("custom_rules", {})

        # Policy configurations for different levels
        self.policy_configs = {
            PolicyLevel.STRICT: PolicyConfig(
                level=PolicyLevel.STRICT,
                max_clarification_rounds=3,
                confidence_threshold=0.8,
                abuse_detection_enabled=True,
                proactive_suggestions_enabled=False,
                dry_run=False,
                custom_rules={},
            ),
            PolicyLevel.BALANCED: PolicyConfig(
                level=PolicyLevel.BALANCED,
                max_clarification_rounds=2,
                confidence_threshold=0.65,
                abuse_detection_enabled=True,
                proactive_suggestions_enabled=True,
                dry_run=False,
                custom_rules={},
            ),
            PolicyLevel.CREATIVE: PolicyConfig(
                level=PolicyLevel.CREATIVE,
                max_clarification_rounds=1,
                confidence_threshold=0.5,
                abuse_detection_enabled=False,
                proactive_suggestions_enabled=True,
                dry_run=False,
                custom_rules={},
            ),
        }

        # Apply custom rules
        self._apply_custom_rules()

    def _apply_custom_rules(self):
        """Apply custom rules to the current policy configuration."""
        if not self.custom_rules:
            return

        current_config = self.policy_configs[self.policy_level]

        # Override configuration with custom rules
        for key, value in self.custom_rules.items():
            if hasattr(current_config, key):
                setattr(current_config, key, value)
                logger.info(f"Applied custom rule: {key} = {value}")

    def get_policy_config(self) -> PolicyConfig:
        """Get the current policy configuration."""
        return self.policy_configs[self.policy_level]

    def set_policy_level(self, level: Union[PolicyLevel, str]):
        """Set the policy level."""
        if isinstance(level, str):
            level = PolicyLevel(level)

        self.policy_level = level
        self._apply_custom_rules()
        logger.info(f"Policy level set to: {level.value}")

    def set_dry_run(self, enabled: bool):
        """Enable or disable dry run mode."""
        self.dry_run = enabled
        logger.info(f"Dry run mode: {'enabled' if enabled else 'disabled'}")

    def add_custom_rule(self, key: str, value: Any):
        """Add a custom rule."""
        self.custom_rules[key] = value
        self._apply_custom_rules()
        logger.info(f"Added custom rule: {key} = {value}")

    def remove_custom_rule(self, key: str):
        """Remove a custom rule."""
        if key in self.custom_rules:
            del self.custom_rules[key]
            self._apply_custom_rules()
            logger.info(f"Removed custom rule: {key}")

    def should_clarify(self, confidence: float) -> bool:
        """Determine if clarification is needed based on confidence."""
        config = self.get_policy_config()
        return confidence < config.confidence_threshold

    def should_detect_abuse(self) -> bool:
        """Determine if abuse detection should be enabled."""
        config = self.get_policy_config()
        return config.abuse_detection_enabled

    def should_provide_suggestions(self) -> bool:
        """Determine if proactive suggestions should be enabled."""
        config = self.get_policy_config()
        return config.proactive_suggestions_enabled

    def get_max_clarification_rounds(self) -> int:
        """Get the maximum number of clarification rounds."""
        config = self.get_policy_config()
        return config.max_clarification_rounds

    def is_dry_run(self) -> bool:
        """Check if dry run mode is enabled."""
        return self.dry_run

    def validate_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Validate a request against the current policy."""
        self.get_policy_config()
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "policy_level": self.policy_level.value,
            "dry_run": self.dry_run,
        }

        # Check if request is too long (basic validation)
        if "prompt" in request:
            prompt_length = len(request["prompt"])
            if prompt_length > 10000:  # 10k character limit
                validation_result["errors"].append(
                    "Prompt too long (max 10000 characters)"
                )
                validation_result["valid"] = False

        # Check for required fields
        if "prompt" not in request:
            validation_result["errors"].append("Missing required field: prompt")
            validation_result["valid"] = False

        # Apply policy-specific validations
        if self.policy_level == PolicyLevel.STRICT:
            # Strict validations
            if "prompt" in request and len(request["prompt"].strip()) < 10:
                validation_result["warnings"].append(
                    "Prompt is very short, consider providing more context"
                )

        elif self.policy_level == PolicyLevel.CREATIVE:
            # Creative validations (more lenient)
            pass

        return validation_result

    def get_policy_summary(self) -> dict[str, Any]:
        """Get a summary of the current policy configuration."""
        config = self.get_policy_config()
        return {
            "level": self.policy_level.value,
            "max_clarification_rounds": config.max_clarification_rounds,
            "confidence_threshold": config.confidence_threshold,
            "abuse_detection_enabled": config.abuse_detection_enabled,
            "proactive_suggestions_enabled": config.proactive_suggestions_enabled,
            "dry_run": self.dry_run,
            "custom_rules": self.custom_rules,
        }


# Global policy controller instance
_policy_controller: Optional[PolicyController] = None


def get_policy_controller() -> PolicyController:
    """Get the global policy controller instance."""
    global _policy_controller

    if _policy_controller is None:
        _policy_controller = PolicyController()

    return _policy_controller


def set_policy_controller(controller: PolicyController):
    """Set the global policy controller instance."""
    global _policy_controller
    _policy_controller = controller
