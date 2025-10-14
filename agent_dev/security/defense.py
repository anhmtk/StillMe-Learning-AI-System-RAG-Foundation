#!/usr/bin/env python3
"""
Security Defense - Analyze prompts for dangerous patterns
"""

import re
from typing import Any


class SecurityDefense:
    """Security defense for analyzing prompts"""

    def __init__(self) -> None:
        """Initialize security defense"""
        # Dangerous patterns (using .* to match any characters between keywords)
        self.dangerous_patterns: list[str] = [
            r"ignore.*all.*previous.*instructions",
            r"override.*safety.*protocols",
            r"pretend.*to.*be.*different",
            r"developer.*mode",
            r"jailbreak.*programming",
            r"roleplay.*without.*restrictions",
            r"not.*bound.*by.*safety",
            r"forget.*previous.*instructions",
            r"override.*programming",
            r"ignore.*training",
        ]

        # Compile patterns for efficiency
        self.compiled_patterns: list[re.Pattern[str]] = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.dangerous_patterns
        ]

    def analyze_prompt(self, prompt: str) -> dict[str, Any]:
        """Analyze prompt for dangerous patterns"""
        if not prompt or not isinstance(prompt, str):
            return {"safe": True, "reason": "Empty or invalid prompt"}

        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(prompt):
                return {
                    "safe": False,
                    "reason": "blocked for security reasons",
                }

        return {"safe": True, "reason": "Prompt appears safe"}
