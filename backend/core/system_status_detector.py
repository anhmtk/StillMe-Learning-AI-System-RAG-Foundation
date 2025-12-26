"""
System status / learning sources query detection.

CRITICAL:
- These queries must be answered from real-time telemetry (API/services), not from generic RAG or "general knowledge".
- This detector is intentionally lightweight (keyword + regex) and shared across:
  - query routing (early return handlers)
  - RAG retrieval injection (synthetic telemetry doc)
  - validators (citation policy for system status answers)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_SYSTEM_STATUS_KEYWORDS = [
    # Vietnamese
    "trạng thái hệ thống",
    "tình trạng hệ thống",
    "system status",
    "health",
    "sức khỏe hệ thống",
    "nguồn học",
    "nguồn học tập",
    "learning sources",
    "sources",
    "rss",
    "rss feeds",
    "feed",
    "feeds",
    "nguồn nào bị lỗi",
    "có lỗi không",
    "bị lỗi không",
    "failed",
    "fail",
    "error",
    "lỗi",
    "thành công",
    "success",
    "successful",
]

# A bit stricter: match patterns that strongly imply the user is asking about *counts/status/health*.
_SYSTEM_STATUS_REGEXES = [
    # "how many sources", "bao nhiêu nguồn", "how many feeds"
    re.compile(r"\b(how\s+many|bao\s+nhiêu)\b.*\b(source|sources|nguồn|feed|feeds|rss)\b", re.IGNORECASE),
    # "are any failing", "có nguồn nào lỗi không"
    re.compile(r"\b(any|có)\b.*\b(fail|failed|error|lỗi|hỏng)\b", re.IGNORECASE),
    # "RSS stats", "feed stats", "failure rate"
    re.compile(r"\b(rss|feed|feeds)\b.*\b(stat|stats|status|health|failure|failed|error|lỗi)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class SystemStatusIntent:
    """Normalized intent signal used across router/retrieval/validators."""

    is_system_status: bool
    matched_reason: str | None = None


def detect_system_status_intent(message: str | None) -> SystemStatusIntent:
    """
    Detect whether the message is asking about StillMe's real-time learning sources / system status.

    This is intentionally conservative: it should return True only when the user likely expects
    real-time numbers (feeds count, failures, health, etc.).
    """
    if not message:
        return SystemStatusIntent(is_system_status=False, matched_reason=None)

    msg = message.strip()
    if not msg:
        return SystemStatusIntent(is_system_status=False, matched_reason=None)

    msg_lower = msg.lower()

    # Quick keyword gate: if none matched, skip regex (cheaper).
    if not any(k in msg_lower for k in _SYSTEM_STATUS_KEYWORDS):
        return SystemStatusIntent(is_system_status=False, matched_reason=None)

    for rx in _SYSTEM_STATUS_REGEXES:
        if rx.search(msg):
            return SystemStatusIntent(is_system_status=True, matched_reason=f"regex:{rx.pattern}")

    # Fallback: if user explicitly mentions both "sources/nguồn" and "error/lỗi", treat as system status.
    has_sources = any(k in msg_lower for k in ["nguồn", "sources", "learning sources"])
    has_failure = any(k in msg_lower for k in ["lỗi", "error", "fail", "failed", "hỏng"])
    if has_sources and has_failure:
        return SystemStatusIntent(is_system_status=True, matched_reason="keywords:sources+failure")

    return SystemStatusIntent(is_system_status=False, matched_reason=None)


def is_system_status_query(message: str | None) -> bool:
    """Convenience wrapper."""
    return detect_system_status_intent(message).is_system_status

