#!/usr/bin/env python3
"""
AgentMode - MINIMAL CONTRACT derived from tests/usages
"""

from typing import TYPE_CHECKING
from enum import Enum


class AgentMode(Enum):
    """Agent mode enum - MINIMAL CONTRACT derived from tests/usages"""

    SIMPLE = "simple"
    SENIOR = "senior"


__all__ = ["AgentMode"]
