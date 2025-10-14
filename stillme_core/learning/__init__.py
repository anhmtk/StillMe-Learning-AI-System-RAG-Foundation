#!/usr/bin/env python3
"""
 fix/import-deps-sanitizer-wave-05-new
StillMe Learning Module
Interactive Dashboard & Automation System for AI learning management.

Facade aliases for stable imports to reduce dependency fragility.
"""

from typing import TYPE_CHECKING

__version__ = "2.1.0"
__author__ = "StillMe AI Framework"

# Lazy imports to avoid circular dependencies
def get_learning_proposal():
    """Get LearningProposal with lazy import"""
    from .proposals import LearningProposal
    return LearningProposal

def get_learning_priority():
    """Get LearningPriority with lazy import"""
    from .proposals import LearningPriority
    return LearningPriority

def get_content_source():
    """Get ContentSource with lazy import"""
    from .proposals import ContentSource
    return ContentSource

def get_proposal_status():
    """Get ProposalStatus with lazy import"""
    from .proposals import ProposalStatus
    return ProposalStatus

def get_proposals_manager():
    """Get ProposalsManager with lazy import"""
    from .proposals_manager import ProposalsManager
    return ProposalsManager

# Stable facade aliases
LearningProposal = get_learning_proposal()
LearningPriority = get_learning_priority()
ContentSource = get_content_source()
ProposalStatus = get_proposal_status()
ProposalsManager = get_proposals_manager()

StillMe Learning System Facade


Facade module để cung cấp stable API cho learning system,
giảm circular imports và tăng maintainability.
"""

from typing import TYPE_CHECKING, Any, Optional

# Lazy imports để tránh circular dependencies
def _get_evolutionary_learning_system():
    """Lazy import for evolutionary learning system"""
    try:
        from .evolutionary_learning_system import EvolutionaryLearningSystem
        return EvolutionaryLearningSystem
    except ImportError:
        return None

def _get_proposals_manager():
    """Lazy import for proposals manager"""
    try:
        from .proposals_manager import ProposalsManager
        return ProposalsManager
    except ImportError:
        return None

def _get_approval_system():
    """Lazy import for approval system"""
    try:
        from .approval_system import ApprovalSystem
        return ApprovalSystem
    except ImportError:
        return None

# Stable API exports
class LearningSystemFacade:
    """Facade for learning system components"""
    
    def __init__(self):
        self._evolutionary_system = None
        self._proposals_manager = None
        self._approval_system = None
    
    @property
    def evolutionary_system(self):
        """Get evolutionary learning system"""
        if self._evolutionary_system is None:
            cls = _get_evolutionary_learning_system()
            if cls:
                self._evolutionary_system = cls()
        return self._evolutionary_system
    
    @property
    def proposals_manager(self):
        """Get proposals manager"""
        if self._proposals_manager is None:
            cls = _get_proposals_manager()
            if cls:
                self._proposals_manager = cls()
        return self._proposals_manager
    
    @property
    def approval_system(self):
        """Get approval system"""
        if self._approval_system is None:
            cls = _get_approval_system()
            if cls:
                self._approval_system = cls()
        return self._approval_system
    
    def is_available(self) -> bool:
        """Check if learning system is available"""
        return (
            _get_evolutionary_learning_system() is not None and
            _get_proposals_manager() is not None and
            _get_approval_system() is not None
        )

# Convenience functions
def get_learning_system() -> Optional[LearningSystemFacade]:
    """Get learning system facade"""
    facade = LearningSystemFacade()
    return facade if facade.is_available() else None

def is_learning_available() -> bool:
    """Check if learning system is available"""
    facade = LearningSystemFacade()
    return facade.is_available()

# Type hints for external use
if TYPE_CHECKING:
    from .evolutionary_learning_system import EvolutionaryLearningSystem
    from .proposals_manager import ProposalsManager
    from .approval_system import ApprovalSystem
 main

# Public API
__all__ = [
 fix/import-deps-sanitizer-wave-05-new
    # Learning Proposals System
    "LearningProposal",
    "LearningPriority",
    "ContentSource",
    "ProposalStatus",
    "ProposalsManager",
    # Lazy import functions
    "get_learning_proposal",
    "get_learning_priority",
    "get_content_source",
    "get_proposal_status",
    "get_proposals_manager",
]

    'LearningSystemFacade',
    'get_learning_system',
    'is_learning_available'
]
 main
