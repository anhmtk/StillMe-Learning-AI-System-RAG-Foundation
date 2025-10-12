"""
Compatibility shim for stillme_core.legacy_component

This module provides backward compatibility for the refactored stillme_core.modern_component.
Please update your imports to use the canonical module directly.

Old import (deprecated):
    from stillme_core.legacy_component import SomeClass

New import (recommended):
    from stillme_core.modern_component import SomeClass
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "Importing from stillme_core.legacy_component is deprecated. "
    "Please use stillme_core.modern_component instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from canonical module
try:
    from stillme_core.modern_component import *  # noqa: F403, F401
except ImportError:
    # Fallback if canonical module doesn't exist yet
    pass
