#!/usr/bin/env python3
"""
AgentMode - MINIMAL CONTRACT derived from tests/usages
"""

from enum import Enum


class AgentMode(Enum):
    """Agent mode enum - MINIMAL CONTRACT derived from tests/usages"""

    SIMPLE = "simple"
    SENIOR = "senior"
    DRY_RUN = "dry_run"


__all__ = ["AgentMode"]
