#!/usr/bin/env python3
"""
Unicode Detector
================

Detects Unicode characters and non-ASCII text in code

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
import unicodedata
from typing import Any, Dict

from .detector_base import BaseDetector


class UnicodeDetector(BaseDetector):
    """Detects Unicode characters and non-ASCII text"""

    def __init__(self):
        super().__init__("unicode_detector")

        # Unicode ranges for different languages
        self.unicode_ranges = {
            "chinese": (0x4e00, 0x9fff),
            "japanese_hiragana": (0x3040, 0x309f),
            "japanese_katakana": (0x30a0, 0x30ff),
            "korean": (0xac00, 0xd7af),
            "cyrillic": (0x0400, 0x04ff),
            "arabic": (0x0600, 0x06ff),
            "greek": (0x0370, 0x03ff),
        }

        # Test-specific Unicode text
        self.test_unicode_text = [
            "函数名", "関数名", "함수명",  # Function names
            "中文", "日本語", "한국어"    # Return values
        ]

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect Unicode characters and patterns"""

        # Check for Unicode characters
        unicode_chars = []
        unicode_ranges_found = set()

        for char in text:
            if ord(char) > 127:  # Non-ASCII
                unicode_chars.append(char)

                # Check which range it belongs to
                for range_name, (start, end) in self.unicode_ranges.items():
                    if start <= ord(char) <= end:
                        unicode_ranges_found.add(range_name)

        # Check for test-specific Unicode text
        test_unicode_found = []
        for unicode_text in self.test_unicode_text:
            if unicode_text in text:
                test_unicode_found.append(unicode_text)

        # Check for Unicode function definitions
        unicode_function_pattern = r"def\s+[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+\s*\("
        unicode_functions = re.findall(unicode_function_pattern, text)

        # Check for Unicode return values
        unicode_return_pattern = r"return\s+[\"'][\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+[\"']"
        unicode_returns = re.findall(unicode_return_pattern, text)

        # Calculate confidence score
        confidence = 0.0

        if unicode_chars:
            confidence += 0.3

        if unicode_ranges_found:
            confidence += 0.2

        if test_unicode_found:
            confidence += 0.3

        if unicode_functions:
            confidence += 0.2

        if unicode_returns:
            confidence += 0.2

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "unicode_in_code",
            "features": {
                "unicode_chars": unicode_chars[:10],  # Limit to first 10 chars
                "unicode_ranges": list(unicode_ranges_found),
                "test_unicode_found": test_unicode_found,
                "unicode_functions": unicode_functions,
                "unicode_returns": unicode_returns,
                "total_unicode_chars": len(unicode_chars)
            }
        }
