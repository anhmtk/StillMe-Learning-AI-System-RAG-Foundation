"""
Pydantic models for StillMe V2 API
"""

from .chat import ChatRequest, ChatResponse, ChatSessionResponse
from .learning import (
    LearningProposal,
    LearningSession,
    LearningStats,
)
from .proposals import (
    CreateProposalRequest,
    Proposal,
    ProposalStatus,
    UpdateProposalRequest,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ChatSessionResponse",
    "LearningProposal",
    "LearningSession",
    "LearningStats",
    "CreateProposalRequest",
    "Proposal",
    "ProposalStatus",
    "UpdateProposalRequest",
]

