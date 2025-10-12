"""
Compatibility shim for stillme_core.old_module

This module provides backward compatibility for the refactored stillme_core.new_module.
Please update your imports to use the canonical module directly.

Old import (deprecated):
    from stillme_core.old_module import SomeClass

New import (recommended):
    from stillme_core.new_module import SomeClass
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "Importing from stillme_core.old_module is deprecated. "
    "Please use stillme_core.new_module instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from canonical module
try:
    from stillme_core.new_module import *  # noqa: F403, F401
except ImportError:
    # Fallback if canonical module doesn't exist yet
    pass
