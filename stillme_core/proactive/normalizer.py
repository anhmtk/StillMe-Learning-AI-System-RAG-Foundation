#!/usr/bin/env python3
"""
Text Normalizer for Proactive Abuse Guard
=========================================

Pre-processing module để chuẩn hóa text trước khi detect abuse patterns.

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
import unicodedata
from typing import Any


class TextNormalizer:
    """Text normalizer cho abuse detection"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # Normalization options
        self.normalize_emoji = self.config.get("normalize_emoji", True)
        self.collapse_whitespace = self.config.get("collapse_whitespace", True)
        self.remove_zero_width = self.config.get("remove_zero_width", True)
        self.canonicalize_punctuation = self.config.get(
            "canonicalize_punctuation", True
        )

        # Compile regex patterns for performance
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        # Zero-width characters
        self.zero_width_pattern = re.compile(r"[\u200b-\u200d\ufeff]")

        # Multiple whitespace
        self.whitespace_pattern = re.compile(r"\s+")

        # Repeated punctuation
        self.punctuation_pattern = re.compile(r"([.!?])\1{2,}")

        # Repeated emoji (simplified pattern)
        self.emoji_repeat_pattern = re.compile(
            r"([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF])\1{2,}"
        )

        # Special characters normalization
        self.special_chars_pattern = re.compile(r"[^\w\s\u4e00-\u9fff\u3400-\u4dbf]")

    def normalize(self, text: str) -> str:
        """
        Normalize text for abuse detection

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Step 1: Convert to lowercase
        normalized = text.lower()

        # Step 2: Remove zero-width characters
        if self.remove_zero_width:
            normalized = self.zero_width_pattern.sub("", normalized)

        # Step 3: Normalize Unicode
        normalized = unicodedata.normalize("NFKC", normalized)

        # Step 4: Canonicalize punctuation
        if self.canonicalize_punctuation:
            # Replace multiple punctuation with single
            normalized = self.punctuation_pattern.sub(r"\1", normalized)

            # Normalize quotes
            normalized = re.sub(r'["""]', '"', normalized)
            normalized = re.sub(r"[''']", "'", normalized)

        # Step 5: Normalize emoji
        if self.normalize_emoji:
            # Replace repeated emoji with single
            normalized = self.emoji_repeat_pattern.sub(r"\1", normalized)

            # Optionally convert emoji to names (for analysis)
            # This is more complex and would require emoji library

        # Step 6: Collapse whitespace
        if self.collapse_whitespace:
            normalized = self.whitespace_pattern.sub(" ", normalized)

        # Step 7: Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def extract_features(self, text: str) -> dict[str, Any]:
        """
        Extract normalization features for analysis

        Args:
            text: Input text

        Returns:
            Dictionary of normalization features
        """
        original_length = len(text)
        normalized = self.normalize(text)
        normalized_length = len(normalized)

        # Count special characters
        special_chars = len(self.special_chars_pattern.findall(text))

        # Count repeated characters
        repeated_chars = len(re.findall(r"(.)\1{2,}", text))

        # Count emoji
        emoji_count = len(
            re.findall(
                r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]",
                text,
            )
        )

        return {
            "original_length": original_length,
            "normalized_length": normalized_length,
            "compression_ratio": normalized_length / original_length
            if original_length > 0
            else 1.0,
            "special_chars": special_chars,
            "repeated_chars": repeated_chars,
            "emoji_count": emoji_count,
            "normalized_text": normalized,
        }

    def is_likely_abuse_pattern(self, text: str) -> bool:
        """
        Quick check if text contains likely abuse patterns

        Args:
            text: Input text

        Returns:
            True if likely abuse pattern detected
        """
        normalized = self.normalize(text)

        # Check for repeated characters (4+ times)
        if re.search(r"(.)\1{3,}", normalized):
            return True

        # Check for excessive special characters
        special_ratio = len(self.special_chars_pattern.findall(normalized)) / max(
            len(normalized), 1
        )
        if special_ratio > 0.5:  # More than 50% special characters
            return True

        # Check for excessive emoji
        emoji_ratio = len(
            re.findall(
                r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]",
                normalized,
            )
        ) / max(len(normalized), 1)
        if emoji_ratio > 0.3:  # More than 30% emoji
            return True

        return False


# Factory function for easy integration
def create_normalizer(config: dict[str, Any] | None = None) -> TextNormalizer:
    """Create a text normalizer instance"""
    return TextNormalizer(config)
