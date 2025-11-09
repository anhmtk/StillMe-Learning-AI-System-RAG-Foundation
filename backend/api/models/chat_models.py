"""
Chat API request and response models with comprehensive validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re
from .common_models import sanitize_string


class ChatRequest(BaseModel):
    """Chat request with RAG support"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: Optional[str] = Field(default=None, max_length=100, description="User identifier")
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    context_limit: int = Field(default=2, ge=1, le=5, description="Maximum number of context documents (optimized for latency: reduced from 3 to 2)")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate and sanitize message"""
        if not isinstance(v, str):
            raise ValueError("Message must be a string")
        
        # Sanitize to prevent XSS
        v = sanitize_string(v, max_length=5000)
        
        # Check for empty after sanitization
        if not v.strip():
            raise ValueError("Message cannot be empty")
        
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format"""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("User ID must be a string")
        
        # Sanitize user ID
        v = sanitize_string(v, max_length=100)
        
        # User ID should be alphanumeric with optional hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("User ID must contain only alphanumeric characters, hyphens, and underscores")
        
        return v
    
    @validator('context_limit')
    def validate_context_limit(cls, v):
        """Validate context limit"""
        if not isinstance(v, int):
            raise ValueError("Context limit must be an integer")
        
        if v < 1 or v > 5:
            raise ValueError("Context limit must be between 1 and 5 (optimized for latency)")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What is StillMe?",
                "user_id": "user123",
                "use_rag": True,
                "context_limit": 2
            }
        }


class ChatResponse(BaseModel):
    """Chat response with RAG context"""
    response: str
    context_used: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    learning_session_id: Optional[int] = None
    knowledge_alert: Optional[Dict[str, Any]] = None
    timing: Optional[Dict[str, str]] = None
    latency_metrics: Optional[str] = Field(None, description="Formatted latency metrics for display (BẮT BUỘC HIỂN THỊ LOG)")
    
    class Config:
        schema_extra = {
            "example": {
                "response": "StillMe is a transparent AI learning system...",
                "context_used": {"knowledge_docs": [], "total_context_docs": 0},
                "accuracy_score": 0.85,
                "learning_session_id": 123,
                "timing": {"total": "1.23s"}
            }
        }

