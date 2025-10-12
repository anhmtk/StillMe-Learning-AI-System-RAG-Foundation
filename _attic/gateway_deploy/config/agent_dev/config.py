"""
AgentDev Configuration - Configuration cho AgentDev system

This module provides AgentDev-specific configuration:
- Validation settings
- Quality thresholds
- AgentDev behavior parameters

Author: StillMe AI Team
Version: 2.0.0
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentDevConfig:
    """AgentDev system configuration"""

    # Validation settings
    validation_enabled: bool = (
        os.getenv("AGENTDEV_VALIDATION_ENABLED", "true").lower() == "true"
    )
    validation_timeout: int = int(os.getenv("AGENTDEV_VALIDATION_TIMEOUT", "60"))

    # Quality thresholds
    min_quality_score: float = float(os.getenv("AGENTDEV_MIN_QUALITY_SCORE", "70.0"))
    max_critical_errors: int = int(os.getenv("AGENTDEV_MAX_CRITICAL_ERRORS", "0"))

    # Behavior settings
    honest_mode: bool = os.getenv("AGENTDEV_HONEST_MODE", "true").lower() == "true"
    evidence_required: bool = (
        os.getenv("AGENTDEV_EVIDENCE_REQUIRED", "true").lower() == "true"
    )

    # Performance settings
    max_fixes_per_session: int = int(os.getenv("AGENTDEV_MAX_FIXES_PER_SESSION", "50"))
    fix_timeout: int = int(os.getenv("AGENTDEV_FIX_TIMEOUT", "300"))

    @classmethod
    def from_env(cls) -> "AgentDevConfig":
        """Create AgentDevConfig from environment variables"""
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "validation_enabled": self.validation_enabled,
            "validation_timeout": self.validation_timeout,
            "min_quality_score": self.min_quality_score,
            "max_critical_errors": self.max_critical_errors,
            "honest_mode": self.honest_mode,
            "evidence_required": self.evidence_required,
            "max_fixes_per_session": self.max_fixes_per_session,
            "fix_timeout": self.fix_timeout,
        }
