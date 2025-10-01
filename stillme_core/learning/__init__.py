"""
StillMe Learning Module
Interactive Dashboard & Automation System for AI learning management.
"""

__version__ = "2.1.0"
__author__ = "StillMe AI Framework"

# Import new learning system components
from .proposals import ContentSource, LearningPriority, LearningProposal, ProposalStatus
from .proposals_manager import ProposalsManager

__all__ = [
    # Learning Proposals System
    'LearningProposal',
    'LearningPriority',
    'ContentSource',
    'ProposalStatus',
    'ProposalsManager'
]
