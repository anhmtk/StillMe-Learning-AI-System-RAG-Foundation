"""
Redis URL utilities.
"""

from __future__ import annotations

from urllib.parse import urlparse
import re


def mask_redis_url(redis_url: str | None) -> str:
    """
    Mask Redis URL for safe logging.

    Rules:
    - If username/password present: mask password (redis://user:***@host:port)
    - Otherwise: log scheme + host + port
    """
    if not redis_url:
        return "NOT SET"

    try:
        parsed = urlparse(redis_url)
        if not parsed.scheme or not parsed.hostname:
            return "REDACTED"

        host = parsed.hostname
        port = f":{parsed.port}" if parsed.port else ""
        if parsed.username or parsed.password:
            user = parsed.username or "default"
            return f"{parsed.scheme}://{user}:***@{host}{port}"
        return f"{parsed.scheme}://{host}{port}"
    except Exception:
        return "REDACTED"


_REDIS_URL_PATTERN = re.compile(r"(rediss?://[^\s]+)")


def mask_redis_url_in_text(text: str) -> str:
    """Mask any Redis URLs found inside an arbitrary string."""
    if not text:
        return text

    def _mask(match: re.Match[str]) -> str:
        return mask_redis_url(match.group(1))

    return _REDIS_URL_PATTERN.sub(_mask, text)
