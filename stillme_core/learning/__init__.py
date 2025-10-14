"""
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

__all__ = [
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
