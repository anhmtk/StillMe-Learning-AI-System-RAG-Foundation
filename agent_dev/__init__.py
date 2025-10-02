"""
AgentDev System - Hệ thống phát triển và sửa lỗi tự động cho StillMe AI

AgentDev System is an intelligent development assistant that provides:
- Automated code fixing and optimization
- Validation and quality assurance
- Honest reporting with evidence
- Integration with StillMe AI core

Author: StillMe AI Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Team"
__description__ = "Intelligent Development Assistant for StillMe AI"

# Import main components
from .core.agent_mode import AgentMode
from .core.agentdev import AgentDev

__all__ = [
    "AgentDev",
    "AgentMode"
]
