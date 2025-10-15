"""
PatternMatcher with Aho-Corasick + Unicode normalization

Features:
- Aho-Corasick algorithm for fast multi-pattern matching
- Unicode normalization (NFC/NFKC), case folding for Vietnamese/English
- Emoji-safe processing
- Multi-language support with fallback regex
- Performance: p95 < 2ms with 1k patterns
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any

# Try to import Aho-Corasick library, fallback to regex if not available
try:
    import ahocorasick

    AHO_AVAILABLE = True
except ImportError:
    AHO_AVAILABLE = False


class PatternMatcher:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.patterns = []
        self.automaton = None
        self.regex_patterns = []
        self._load_patterns()
        self._build_automaton()

    def _load_patterns(self) -> None:
        """Load patterns from config/reflex_patterns.yaml"""
        try:
            import yaml

            with open("config/reflex_patterns.yaml", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Load literal patterns
            literal_patterns = data.get("literal_patterns", [])
            for i, pattern in enumerate(literal_patterns):
                self.patterns.append(
                    {
                        "id": f"literal_{i}",
                        "text": pattern,
                        "type": "literal",
                        "weight": 1.0,
                    }
                )

            # Load regex patterns
            regex_patterns = data.get("regex_patterns", [])
            for i, pattern in enumerate(regex_patterns):
                self.regex_patterns.append(
                    {
                        "id": f"regex_{i}",
                        "pattern": re.compile(pattern, re.IGNORECASE | re.UNICODE),
                        "weight": 0.8,
                    }
                )

        except Exception:
            # Fallback to default patterns if config loading fails
            self.patterns = [
                {"id": "greeting", "text": "hello", "type": "literal", "weight": 1.0},
                {"id": "help", "text": "help", "type": "literal", "weight": 1.0},
            ]

    def _build_automaton(self) -> None:
        """Build Aho-Corasick automaton for literal patterns"""
        if not AHO_AVAILABLE or not self.patterns:
            # Fallback: convert literal patterns to regex patterns
            for pattern in self.patterns:
                if pattern["type"] == "literal":
                    # Escape special regex characters and create case-insensitive pattern
                    escaped_text = re.escape(pattern["text"])
                    regex_pattern = re.compile(
                        f"\\b{escaped_text}\\b", re.IGNORECASE | re.UNICODE
                    )
                    self.regex_patterns.append(
                        {
                            "id": pattern["id"],
                            "pattern": regex_pattern,
                            "weight": pattern["weight"],
                        }
                    )
            return

        self.automaton = ahocorasick.Automaton()
        for pattern in self.patterns:
            if pattern["type"] == "literal":
                # Normalize text before adding to automaton
                normalized = self._normalize_text(pattern["text"])
                self.automaton.add_word(normalized, (pattern["id"], pattern["weight"]))

        self.automaton.make_automaton()

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for matching:
        - Unicode normalization (NFC)
        - Case folding for Vietnamese/English
        - Remove zero-width characters
        - Emoji-safe processing
        """
        # Unicode normalization
        text = unicodedata.normalize("NFC", text)

        # Case folding (handles Vietnamese diacritics)
        text = text.casefold()

        # Remove zero-width characters
        text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _detect_homoglyphs(self, text: str) -> str:
        """Detect and normalize homoglyphs (Latin vs Cyrillic)"""
        # Simple homoglyph detection - can be expanded
        homoglyph_map = {
            "а": "a",  # Cyrillic to Latin
            "е": "e",
            "о": "o",
            "р": "p",
            "с": "c",
            "х": "x",
        }

        for cyrillic, latin in homoglyph_map.items():
            text = text.replace(cyrillic, latin)
        return text

    def match(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Match patterns against text with performance tracking.

        Returns:
            matches: List of hits with pattern_id, span, weight
            pattern_score: Overall pattern confidence (0-1)
            match_time_us: Time taken in microseconds
        """
        start_time = time.perf_counter()

        # Normalize input text
        normalized_text = self._normalize_text(text)
        normalized_text = self._detect_homoglyphs(normalized_text)

        matches = []

        # Aho-Corasick matching for literal patterns
        if self.automaton:
            for end_idx, (pattern_id, weight) in self.automaton.iter(normalized_text):
                start_idx = end_idx - len(self.automaton.get(pattern_id, "")) + 1
                matches.append(
                    {
                        "pattern_id": pattern_id,
                        "span": (start_idx, end_idx + 1),
                        "weight": weight,
                        "type": "literal",
                        "text": normalized_text[start_idx : end_idx + 1],
                    }
                )

        # Regex matching
        for regex_info in self.regex_patterns:
            for match in regex_info["pattern"].finditer(normalized_text):
                matches.append(
                    {
                        "pattern_id": regex_info["id"],
                        "span": match.span(),
                        "weight": regex_info["weight"],
                        "type": "regex",
                        "text": match.group(),
                    }
                )

        # Calculate pattern score based on matches
        pattern_score = self._calculate_pattern_score(matches, len(normalized_text))

        match_time = (
            time.perf_counter() - start_time
        ) * 1_000_000  # Convert to microseconds

        return {
            "matches": matches,
            "pattern_score": pattern_score,
            "match_time_us": match_time,
            "normalized_text": normalized_text,
        }

    def _calculate_pattern_score(
        self, matches: list[dict[str, Any]], text_length: int
    ) -> float:
        """Calculate overall pattern confidence score (0-1)"""
        if not matches:
            return 0.0

        # Weight by match quality and coverage
        total_weight = sum(match["weight"] for match in matches)
        coverage = sum(
            end - start for start, end in [match["span"] for match in matches]
        ) / max(text_length, 1)

        # Combine weight and coverage
        score = min(1.0, (total_weight * 0.7 + coverage * 0.3))
        return round(score, 3)
