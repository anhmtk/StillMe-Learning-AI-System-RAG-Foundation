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
from .core.enhanced_agentdev import EnhancedAgentDev
from .validation.validation_system import AgentDevValidator
from .validation.integration import AgentDevIntegration

__all__ = [
    "EnhancedAgentDev",
    "AgentDevValidator", 
    "AgentDevIntegration"
]
