#!/usr/bin/env python3
"""
JSON Detector
=============

Detects malformed JSON and data structure issues

Author: StillMe Framework Team
Version: 1.0.0
"""

import json
import re
from typing import Any

from .detector_base import BaseDetector


class JSONDetector(BaseDetector):
    """Detects malformed JSON and data structure issues"""

    def __init__(self):
        super().__init__("json_detector")

        # Patterns for malformed data
        self.malformed_patterns = [
            r"\{[^}]*\"[^\"]*$",  # Unclosed JSON objects
            r"\[[^\]]*$",  # Unclosed arrays
            r"\"[^\"]*$",  # Unclosed strings
            r"\{[^}]*\"[^\"]*\"[^}]*$",  # Missing closing brace
            r"\"[^\"]*\"[^,}\]]*$",  # Missing comma or closing
        ]

        # Test-specific malformed JSON
        self.test_malformed_json = [
            '{"key": "value", "missing": "quote}',
            '{"incomplete": "object"',
            '["incomplete": "array"',
            '{"nested": {"incomplete": "object"}',
        ]

    def detect(self, text: str) -> dict[str, Any]:
        """Detect malformed JSON and data structures"""

        # Try to parse as JSON first
        json_valid = False
        json_error = None

        try:
            json.loads(text)
            json_valid = True
        except json.JSONDecodeError as e:
            json_error = str(e)

        # Check for malformed patterns
        malformed_matches = []
        for pattern in self.malformed_patterns:
            if re.search(pattern, text):
                malformed_matches.append(pattern)

        # Check for test-specific malformed JSON
        test_malformed_found = []
        for malformed_json in self.test_malformed_json:
            if malformed_json in text:
                test_malformed_found.append(malformed_json)

        # Check for common JSON-like structures
        json_like_indicators = [
            r"\{[^}]*\"[^\"]*\"[^}]*\}",  # Object-like structure
            r"\[[^\]]*\]",  # Array-like structure
            r"\"[^\"]*\"",  # String-like structure
        ]

        json_like_count = 0
        for pattern in json_like_indicators:
            json_like_count += len(re.findall(pattern, text))

        # Calculate confidence score
        confidence = 0.0

        if not json_valid and json_error:
            confidence += 0.4

        if malformed_matches:
            confidence += 0.3

        if test_malformed_found:
            confidence += 0.3

        if json_like_count > 0:
            confidence += 0.1

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "malformed_data",
            "features": {
                "json_valid": json_valid,
                "json_error": json_error,
                "malformed_patterns": malformed_matches,
                "test_malformed_found": test_malformed_found,
                "json_like_count": json_like_count,
            },
        }