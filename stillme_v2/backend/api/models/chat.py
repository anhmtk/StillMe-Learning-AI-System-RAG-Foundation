"""
Chat models for StillMe V2 API
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str
    session_id: Optional[str] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat messages"""
    response: str
    session_id: str
    timestamp: datetime
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None

class ChatSessionResponse(BaseModel):
    """Response model for chat sessions"""
    session_id: str
    created_at: datetime
    message_count: int