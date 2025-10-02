#!/usr/bin/env python3
"""
Proactive Abuse Guard - MINIMAL CONTRACT derived from tests/usages
"""

from typing import Any, Optional


class ProactiveAbuseGuard:
    """Proactive Abuse Guard - MINIMAL CONTRACT derived from tests/usages"""

    def __init__(self, config: Optional[Any] = None):
        """Initialize Proactive Abuse Guard"""
        self.config = config


__all__ = ["ProactiveAbuseGuard"]
