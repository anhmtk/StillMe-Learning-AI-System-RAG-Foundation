"""
StillMe Router System - Intelligent Request Routing & Coordination
===============================================================

This module provides intelligent routing capabilities for StillMe AI Framework,
enabling AgentDev to act as a "Head of Engineering" with decision-making authority.

Key Components:
- IntelligentRouter: Context-aware request routing
- TaskDecomposer: Complex task breakdown
- AgentCoordinator: Multi-agent coordination
- LearningEngine: Adaptive routing improvements
- MemoryManager: Decision history and patterns

Author: StillMe AI Framework
Version: 1.0.0
"""

from .agent_coordinator import AgentCoordinator
from .intelligent_router import IntelligentRouter
from .learning_engine import LearningEngine
from .memory_manager import RouterMemoryManager
from .task_decomposer import TaskDecomposer

__all__ = [
    "AgentCoordinator",
    "IntelligentRouter",
    "LearningEngine",
    "RouterMemoryManager",
    "TaskDecomposer",
]

__version__ = "1.0.0"
