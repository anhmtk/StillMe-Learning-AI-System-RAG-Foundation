"""
Legacy AgentDev System - Hệ thống AgentDev cũ

⚠️ DEPRECATED: This module contains legacy AgentDev implementations.
Use agent-dev/ for new development.

This module provides backward compatibility for:
- AgentDevSuper: Legacy super agent implementation
- AgentDevReal: Legacy real agent implementation  
- AgentDevBrain: Legacy brain implementation

Author: StillMe AI Team
Version: 1.0.0 (Legacy)
Status: DEPRECATED - Use agent-dev/ instead
"""

__version__ = "1.0.0"
__status__ = "DEPRECATED"
__author__ = "StillMe AI Team"

# Import legacy components for backward compatibility
from .agentdev_super import AgentDevSuper
from .agentdev_real import AgentDevReal
from .agentdev_brain import AgentDevBrain

__all__ = [
    "AgentDevSuper",
    "AgentDevReal", 
    "AgentDevBrain"
]

# Deprecation warning
import warnings
warnings.warn(
    "stillme-core.core.legacy_agentdev is deprecated. "
    "Use agent-dev/ for new development.",
    DeprecationWarning,
    stacklevel=2
)
