"""
StillMe Core Utilities
=====================

Utility modules for safe file operations and common functions.
"""

from .io_safe import safe_read_text, safe_decode

__all__ = ["safe_read_text", "safe_decode"]
