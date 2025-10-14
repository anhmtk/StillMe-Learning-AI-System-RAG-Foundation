"""
PII Redactor for Enterprise Audit & Privacy
===========================================

Redacts Personally Identifiable Information (PII) from text while preserving format.
Supports email, phone, names, IP addresses, tokens, and identification numbers.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import re
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Types of PII that can be detected and redacted"""

    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    IP_ADDRESS = "ip"
    TOKEN = "token"
    ID_NUMBER = "id_number"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"


@dataclass
class PIIMatch:
    """Represents a detected PII match"""

    pii_type: PIIType
    original_text: str
    redacted_text: str
    start_pos: int
    end_pos: int
    confidence: float


class PIIRedactor:
    """
    Advanced PII Redactor with format preservation and tagging

    Features:
    - Format-preserving redaction (e.g., j***@d***.com)
    - Tagged redaction with [REDACTED:<type>]
    - Unicode support
    - Configurable patterns
    - Confidence scoring
    """

    def __init__(self, config: dict | None = None):
        """Initialize PII redactor with configuration"""
        self.config = config or {}
        self.patterns = self._build_patterns()
        self.redaction_tag = self.config.get("redaction_tag", True)
        self.preserve_format = self.config.get("preserve_format", True)

    def _build_patterns(self) -> dict[PIIType, list[tuple[re.Pattern, float]]]:
        """Build regex patterns for PII detection"""
        patterns = {}

        # Email patterns (including Unicode)
        patterns[PIIType.EMAIL] = [
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), 0.95),
            (
                re.compile(
                    r"\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b"
                ),
                0.90,
            ),
            (
                re.compile(r"\b[\w._%+-]+@[\w.-]+\.[\w]{2,}\b", re.UNICODE),
                0.85,
            ),  # Unicode support
            (
                re.compile(r"\b[\w._%+-]+\s*@\s*[\w.-]+\s*\.\s*[\w]{2,}\b", re.UNICODE),
                0.80,
            ),  # Unicode with spaces
        ]

        # Phone patterns (international formats)
        patterns[PIIType.PHONE] = [
            (
                re.compile(
                    r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
                ),
                0.90,
            ),
            (re.compile(r"\b\+?[1-9]\d{1,14}\b"), 0.85),  # International format
            (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), 0.88),
        ]

        # Name patterns (heuristic-based, including Unicode)
        patterns[PIIType.NAME] = [
            (re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"), 0.70),  # First Last
            (re.compile(r"\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b"), 0.75),  # First M. Last
            (re.compile(r"\b[A-Z][a-z]+, [A-Z][a-z]+\b"), 0.80),  # Last, First
            (
                re.compile(r"\b[\u4e00-\u9fff]+\b", re.UNICODE),
                0.60,
            ),  # Chinese characters
            (
                re.compile(r"\b[\u0400-\u04ff]+\b", re.UNICODE),
                0.60,
            ),  # Cyrillic characters
            (
                re.compile(r"\b[\u3040-\u309f\u30a0-\u30ff]+\b", re.UNICODE),
                0.60,
            ),  # Japanese characters
        ]

        # IP address patterns
        patterns[PIIType.IP_ADDRESS] = [
            (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), 0.95),
            (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"), 0.95),  # IPv6
        ]

        # Token patterns (API keys, bearer tokens, etc.)
        patterns[PIIType.TOKEN] = [
            (re.compile(r"\b[A-Za-z0-9]{32,}\b"), 0.60),  # Generic long token
            (re.compile(r"\bBearer\s+[A-Za-z0-9._-]+\b", re.IGNORECASE), 0.90),
            (re.compile(r"\bapi[_-]?key[_-]?[A-Za-z0-9._-]+\b", re.IGNORECASE), 0.85),
            (re.compile(r"\b[A-Za-z0-9._-]{20,}\b"), 0.50),  # Potential token
            (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), 0.95),  # OpenAI-style API key
            (re.compile(r"\bpk-[A-Za-z0-9]{16,}\b"), 0.95),  # OpenAI-style public key
        ]

        # ID number patterns
        patterns[PIIType.ID_NUMBER] = [
            (re.compile(r"\b\d{9,12}\b"), 0.70),  # Generic long number
            (re.compile(r"\b[A-Z]{2,3}\d{6,8}\b"), 0.80),  # License-like
        ]

        # Credit card patterns
        patterns[PIIType.CREDIT_CARD] = [
            (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), 0.90),
            (re.compile(r"\b\d{13,19}\b"), 0.60),  # Generic card number
        ]

        # SSN patterns
        patterns[PIIType.SSN] = [
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0.95),
            (re.compile(r"\b\d{9}\b"), 0.70),  # Generic 9-digit
        ]

        return patterns

    def redact(self, text: str) -> tuple[str, list[PIIMatch]]:
        """
        Redact PII from text and return redacted text with match details

        Args:
            text: Input text to redact

        Returns:
            Tuple of (redacted_text, list_of_matches)
        """
        matches = []
        redacted_text = text

        # Process each PII type
        for pii_type, pattern_list in self.patterns.items():
            for pattern, confidence in pattern_list:
                for match in pattern.finditer(text):
                    original = match.group()
                    redacted = self._redact_pii(original, pii_type)

                    pii_match = PIIMatch(
                        pii_type=pii_type,
                        original_text=original,
                        redacted_text=redacted,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                    )
                    matches.append(pii_match)

        # Sort matches by position (reverse order for safe replacement)
        matches.sort(key=lambda x: x.start_pos, reverse=True)

        # Apply redactions
        for match in matches:
            redacted_text = (
                redacted_text[: match.start_pos]
                + match.redacted_text
                + redacted_text[match.end_pos :]
            )

        return redacted_text, matches

    def _redact_pii(self, text: str, pii_type: PIIType) -> str:
        """Redact individual PII item while preserving format"""
        if not self.preserve_format:
            return f"[REDACTED:{pii_type.value}]"

        # Format-preserving redaction
        if pii_type == PIIType.EMAIL:
            return self._redact_email(text)
        elif pii_type == PIIType.PHONE:
            return self._redact_phone(text)
        elif pii_type == PIIType.NAME:
            return self._redact_name(text)
        elif pii_type == PIIType.IP_ADDRESS:
            return self._redact_ip(text)
        elif pii_type == PIIType.TOKEN:
            return self._redact_token(text)
        elif pii_type == PIIType.ID_NUMBER:
            return self._redact_id_number(text)
        elif pii_type == PIIType.CREDIT_CARD:
            return self._redact_credit_card(text)
        elif pii_type == PIIType.SSN:
            return self._redact_ssn(text)
        else:
            return f"[REDACTED:{pii_type.value}]"

    def _redact_email(self, email: str) -> str:
        """Redact email while preserving format"""
        if "@" not in email:
            return f"[REDACTED:{PIIType.EMAIL.value}]"

        local, domain = email.split("@", 1)
        if len(local) <= 2:
            redacted_local = local[0] + "*" * (len(local) - 1)
        else:
            redacted_local = local[0] + "*" * (len(local) - 2) + local[-1]

        if "." in domain:
            domain_parts = domain.split(".")
            if len(domain_parts) >= 2:
                redacted_domain = (
                    domain_parts[0][0]
                    + "*" * (len(domain_parts[0]) - 1)
                    + "."
                    + domain_parts[-1]
                )
            else:
                redacted_domain = domain[0] + "*" * (len(domain) - 1)
        else:
            redacted_domain = domain[0] + "*" * (len(domain) - 1)

        redacted = f"{redacted_local}@{redacted_domain}"

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.EMAIL.value}]"
        return redacted

    def _redact_phone(self, phone: str) -> str:
        """Redact phone while preserving format"""
        # Extract digits
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10:
            return f"[REDACTED:{PIIType.PHONE.value}]"

        # Preserve format with asterisks
        redacted = phone
        digit_count = 0
        for i, char in enumerate(phone):
            if char.isdigit():
                if digit_count < 3 or digit_count >= len(digits) - 4:
                    pass  # Keep first 3 and last 4 digits
                else:
                    redacted = redacted[:i] + "*" + redacted[i + 1 :]
                digit_count += 1

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.PHONE.value}]"
        return redacted

    def _redact_name(self, name: str) -> str:
        """Redact name while preserving format"""
        parts = name.split()
        if len(parts) < 2:
            return f"[REDACTED:{PIIType.NAME.value}]"

        redacted_parts = []
        for part in parts:
            if len(part) <= 2:
                redacted_parts.append(part[0] + "*" * (len(part) - 1))
            else:
                redacted_parts.append(part[0] + "*" * (len(part) - 2) + part[-1])

        redacted = " ".join(redacted_parts)

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.NAME.value}]"
        return redacted

    def _redact_ip(self, ip: str) -> str:
        """Redact IP address while preserving format"""
        if ":" in ip:  # IPv6
            parts = ip.split(":")
            if len(parts) >= 4:
                redacted_parts = parts[:2] + ["****"] * (len(parts) - 4) + parts[-2:]
                redacted = ":".join(redacted_parts)
            else:
                redacted = "****:" * (len(parts) - 1) + "****"
        else:  # IPv4
            parts = ip.split(".")
            if len(parts) == 4:
                redacted = f"{parts[0]}.{parts[1]}.***.{parts[3]}"
            else:
                redacted = "***." * (len(parts) - 1) + "***"

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.IP_ADDRESS.value}]"
        return redacted

    def _redact_token(self, token: str) -> str:
        """Redact token while preserving format"""
        if len(token) <= 8:
            return f"[REDACTED:{PIIType.TOKEN.value}]"

        # Keep first 4 and last 4 characters
        redacted = token[:4] + "*" * (len(token) - 8) + token[-4:]

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.TOKEN.value}]"
        return redacted

    def _redact_id_number(self, id_num: str) -> str:
        """Redact ID number while preserving format"""
        if len(id_num) <= 6:
            return f"[REDACTED:{PIIType.ID_NUMBER.value}]"

        # Keep first 2 and last 2 characters
        redacted = id_num[:2] + "*" * (len(id_num) - 4) + id_num[-2:]

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.ID_NUMBER.value}]"
        return redacted

    def _redact_credit_card(self, card: str) -> str:
        """Redact credit card while preserving format"""
        digits = re.sub(r"\D", "", card)
        if len(digits) < 13:
            return f"[REDACTED:{PIIType.CREDIT_CARD.value}]"

        # Keep first 4 and last 4 digits
        redacted_digits = digits[:4] + "*" * (len(digits) - 8) + digits[-4:]

        # Restore original format
        redacted = card
        digit_count = 0
        for i, char in enumerate(card):
            if char.isdigit():
                redacted = (
                    redacted[:i] + redacted_digits[digit_count] + redacted[i + 1 :]
                )
                digit_count += 1

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.CREDIT_CARD.value}]"
        return redacted

    def _redact_ssn(self, ssn: str) -> str:
        """Redact SSN while preserving format"""
        digits = re.sub(r"\D", "", ssn)
        if len(digits) != 9:
            return f"[REDACTED:{PIIType.SSN.value}]"

        # Keep first 3 and last 4 digits
        redacted_digits = digits[:3] + "**" + digits[-4:]

        # Restore original format
        if "-" in ssn:
            redacted = (
                f"{redacted_digits[:3]}-{redacted_digits[3:5]}-{redacted_digits[5:]}"
            )
        else:
            redacted = redacted_digits

        if self.redaction_tag:
            return f"{redacted} [REDACTED:{PIIType.SSN.value}]"
        return redacted

    def get_stats(self, matches: list[PIIMatch]) -> dict[str, int]:
        """Get statistics about redacted PII"""
        stats = {}
        for match in matches:
            pii_type = match.pii_type.value
            stats[pii_type] = stats.get(pii_type, 0) + 1
        return stats


# Global instance for easy import
default_redactor = PIIRedactor()