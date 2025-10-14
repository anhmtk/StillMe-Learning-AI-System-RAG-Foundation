#!/usr/bin/env python3
"""
StillMe Learning System Facade
==============================

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

# Public API
__all__ = [
    'LearningSystemFacade',
    'get_learning_system',
    'is_learning_available'
]