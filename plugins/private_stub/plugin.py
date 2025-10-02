

class StubRouter:  # deliberately not inheriting to avoid hard dep
    """Public stub implementation for OSS mode.

    Provides basic model selection logic without requiring private code.
    This ensures the framework always runs in open-source mode.
    """

    def choose_model(self, prompt: str) -> str:
        """Choose model based on simple heuristics.

        Args:
            prompt: The input prompt to analyze

        Returns:
            Model identifier string
        """
        if not prompt:
            return "llama3:8b"

        p = prompt.lower()

        # Code-related prompts
        if "```" in prompt or "code" in p or "programming" in p or "function" in p:
            return "deepseek-coder:6.7b"

        # Image-related prompts
        if any(k in p for k in ("image", "photo", "png", "jpg", "jpeg", "picture", "visual")):
            return "llava:7b"

        # Math/science prompts
        if any(k in p for k in ("math", "calculate", "equation", "formula", "statistics")):
            return "deepseek-math:7b"

        # Default to general purpose model
        return "llama3:8b"
