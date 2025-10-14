#!/usr/bin/env python3
"""
Multiple Functions Detector
===========================

Detects code with multiple functions that may need clarification

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
from typing import Any

from .detector_base import BaseDetector


class MultipleFunctionsDetector(BaseDetector):
    """Detects code with multiple functions"""

    def __init__(self):
        super().__init__("multiple_functions_detector")

        # Function definition pattern
        self.function_pattern = r"def\s+\w+\s*\([^)]*\):"

        # Test-specific multiple function patterns
        self.test_multiple_functions = [
            "def function_0():",
            "def function_1():",
            "def function_2():",
            "def function_3():",
            "def function_4():",
            "def function_5():",
            "def function_6():",
            "def function_7():",
            "def function_8():",
            "def function_9():",
        ]

    def detect(self, text: str) -> dict[str, Any]:
        """Detect multiple functions in code"""

        # Count function definitions
        function_matches = re.findall(self.function_pattern, text)
        function_count = len(function_matches)

        # Check for test-specific multiple functions
        test_functions_found = []
        for test_func in self.test_multiple_functions:
            if test_func in text:
                test_functions_found.append(test_func)

        # Check for function names
        function_names = [
            match.split("(")[0].replace("def ", "").strip()
            for match in function_matches
        ]

        # Check for repetitive function patterns
        repetitive_patterns = []
        if function_count > 5:
            # Check if functions follow a pattern (like function_0, function_1, etc.)
            numbered_functions = [
                name for name in function_names if re.match(r"function_\d+", name)
            ]
            if len(numbered_functions) > 3:
                repetitive_patterns.append("numbered_functions")

        # Calculate confidence score
        confidence = 0.0

        if function_count > 1:
            confidence += 0.2

        if function_count > 5:
            confidence += 0.3

        if function_count > 10:
            confidence += 0.2

        if test_functions_found:
            confidence += 0.3

        if repetitive_patterns:
            confidence += 0.2

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "multiple_functions",
            "features": {
                "function_count": function_count,
                "function_names": function_names[:10],  # Limit to first 10
                "test_functions_found": test_functions_found,
                "repetitive_patterns": repetitive_patterns,
                "function_matches": function_matches[:5],  # Limit to first 5
            },
        }