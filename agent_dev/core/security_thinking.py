#!/usr/bin/env python3
"""
Security Thinking Shim
=====================

PEP 562 compatibility shim for agent_dev.security.defense
Re-exports dynamic imports without using * or # noqa
"""

from typing import TYPE_CHECKING
import sys
from typing import Any

# Import the actual security defense module
try:
    if TYPE_CHECKING:
        from agent_dev.security.defense import *

    _security_module = sys.modules["agent_dev.security.defense"]
except ImportError:
    _security_module = None


def __getattr__(name: str) -> Any:
    """
    PEP 562 __getattr__ for dynamic re-export
    """
    if _security_module is not None:
        return getattr(_security_module, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """
    PEP 562 __dir__ for proper introspection
    """
    if _security_module is not None:
        return dir(_security_module)
    return []