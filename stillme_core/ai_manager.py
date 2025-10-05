"""
StillMe AI Manager - Stub Implementation
========================================

# TODO[stabilize]: This is a temporary stub to fix import errors.
# Full implementation needed for production use.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIManagerConfig:
    """AI Manager configuration"""

    model_preferences: dict[str, Any] | None = None
    timeout: float = 30.0
    max_retries: int = 3


class AIManager:
    """
    AI Manager - Stub Implementation

    # TODO[stabilize]: Implement full AI management functionality
    """

    def __init__(self, config: AIManagerConfig | None = None):
        """Initialize AI Manager"""
        self.config = config or AIManagerConfig()
        logger.warning("AIManager: Using stub implementation - not for production")

    def health(self) -> dict[str, Any]:
        """Health check"""
        return {"ollama_up": True, "model_present": True, "tiny_generate_ok": True}

    def set_mode(self, mode: str) -> bool:
        """Set AI mode"""
        logger.warning(f"AIManager.set_mode({mode}): Stub implementation")
        return True

    def compute_number(self, expression: str) -> int | float:
        """Compute mathematical expression"""
        logger.warning(f"AIManager.compute_number({expression}): Stub implementation")
        try:
            # Basic safety check
            if any(char in expression for char in ["import", "exec", "eval", "__"]):
                raise ValueError("Unsafe expression")
            return eval(expression)
        except Exception as e:
            logger.error(f"Compute error: {e}")
            return 0

    def generate_patch(self, plan_item: Any, context: str = "") -> str | None:
        """Generate patch for plan item - Stub implementation"""
        logger.warning("AIManager.generate_patch(): Stub implementation")
        # Return a simple stub patch
        return f"# Stub patch for {getattr(plan_item, 'id', 'unknown')}\n# Context: {context[:100]}"


# Convenience functions for backward compatibility
def health() -> dict[str, Any]:
    """Health check function"""
    manager = AIManager()
    return manager.health()


def set_mode(mode: str) -> bool:
    """Set mode function"""
    manager = AIManager()
    return manager.set_mode(mode)


def compute_number(expression: str) -> int | float:
    """Compute number function"""
    manager = AIManager()
    return manager.compute_number(expression)
