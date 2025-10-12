"""
StillMe Compatibility Package

This package provides backward compatibility shims for refactored modules.
All imports from this package will emit deprecation warnings.

Usage:
    # Old way (deprecated):
    from stillme_compat.old_module import SomeClass

    # New way (recommended):
    from stillme_core.new_module import SomeClass
"""

import warnings

# Emit a general deprecation warning when this package is imported
warnings.warn(
    "stillme_compat package is deprecated. Please update your imports to use "
    "the canonical modules directly. See documentation for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

__version__ = "1.0.0"
__all__ = []
