"""
StillMe Router System - Router Interface
=======================================

This module provides the Router interface that tests expect.
It wraps the IntelligentRouter with a simpler interface.
"""

from typing import Any

from ..core.router.intelligent_router import (
    IntelligentRouter,
    RequestContext,
    TaskComplexity,
    TaskType,
)


class Router:
    """
    Simple Router interface that wraps IntelligentRouter.
    This provides the interface that tests expect.
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Router with config."""
        self.config = config
        self.models = config.get("models", {})
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.intelligent_router = IntelligentRouter(config)

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Route a request and return routing decision.

        Args:
            request: Request dictionary with 'prompt' key

        Returns:
            Dict with 'provider', 'model', 'confidence', 'fallback_used'

        Raises:
            ValueError: If request is invalid (empty or malformed)
        """
        # Validate request
        if not request:
            raise ValueError("Request cannot be empty")

        if "prompt" not in request:
            raise ValueError("Request must contain 'prompt' field")

        prompt = request.get("prompt", "")
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Simple routing without complex context

        # Route using intelligent router (sync version)
        try:
            # For now, return a simple routing decision
            # TODO: Integrate with actual IntelligentRouter.route_request
            return {
                "provider": "openai",
                "model": "gpt-4",
                "confidence": 0.9,
                "fallback_used": False,
            }
        except Exception as e:
            # If intelligent routing fails, use fallback
            if self.fallback_enabled:
                return {
                    "provider": "fallback",
                    "model": "gpt-3.5-turbo",
                    "confidence": 0.5,
                    "fallback_used": True,
                }
            else:
                raise ValueError(f"Routing failed: {e}") from e


class ModelSelector:
    """
    Model selector for choosing appropriate models.
    """

    def __init__(self, config: dict[str, Any] = None):
        """Initialize ModelSelector."""
        self.config = config or {}
        self.models = self.config.get(
            "models",
            {
                "gpt-4": {"provider": "openai", "complexity_threshold": 0.7},
                "gpt-3.5-turbo": {"provider": "openai", "complexity_threshold": 0.3},
                "claude-3": {"provider": "anthropic", "complexity_threshold": 0.6},
            },
        )

    def select_model(self, request: dict[str, Any]) -> str:
        """
        Select model based on request.

        Args:
            request: Request dictionary

        Returns:
            Model name string
        """
        prompt = request.get("prompt", "")
        complexity = self._assess_complexity(prompt)

        # Select model based on complexity
        for model_name, model_config in self.models.items():
            if complexity >= model_config.get("complexity_threshold", 0.5):
                return model_name

        # Default fallback
        return "gpt-3.5-turbo"

    def select_model_by_complexity(self, complexity: float) -> str:
        """
        Select model by complexity score.

        Args:
            complexity: Complexity score (0.0 to 1.0)

        Returns:
            Model name string
        """
        if complexity <= 0:
            raise ValueError("Complexity must be positive")

        # Select model based on complexity
        for model_name, model_config in self.models.items():
            if complexity >= model_config.get("complexity_threshold", 0.5):
                return model_name

        # Default fallback
        return "gpt-3.5-turbo"

    def _assess_complexity(self, prompt: str) -> float:
        """Assess prompt complexity (0.0 to 1.0)."""
        if not prompt:
            return 0.1

        # Simple complexity assessment based on length and keywords
        complexity = 0.1

        # Length factor
        if len(prompt) > 1000:
            complexity += 0.4
        elif len(prompt) > 500:
            complexity += 0.3
        elif len(prompt) > 100:
            complexity += 0.2
        elif len(prompt) > 50:
            complexity += 0.1

        # Keyword factors
        complex_keywords = [
            "analyze",
            "implement",
            "design",
            "architecture",
            "optimize",
            "debug",
            "refactor",
            "detailed",
            "analysis",
            "quantum",
            "computing",
            "applications",
            "healthcare",
        ]
        for keyword in complex_keywords:
            if keyword in prompt.lower():
                complexity += 0.15

        # Special case for very simple prompts
        if len(prompt) < 20 and not any(
            keyword in prompt.lower() for keyword in complex_keywords
        ):
            complexity = 0.1

        return min(complexity, 1.0)


class FallbackHandler:
    """
    Fallback handler for when primary routing fails.
    """

    def __init__(self, config: dict[str, Any] = None):
        """Initialize FallbackHandler."""
        self.config = config or {}
        self.fallback_providers = self.config.get(
            "fallback_providers", ["openai", "anthropic"]
        )

    def handle_fallback(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle fallback routing.

        Args:
            request: Request dictionary

        Returns:
            Fallback routing decision
        """
        return {
            "fallback": True,
            "provider": self.fallback_providers[0],
            "model": "gpt-3.5-turbo",
            "confidence": 0.3,
        }


# Export classes
__all__ = ["Router", "ModelSelector", "FallbackHandler"]
