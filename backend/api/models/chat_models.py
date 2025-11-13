"""
Chat API request and response models with comprehensive validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import re
from .common_models import sanitize_string


class ChatRequest(BaseModel):
    """Chat request with RAG support"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: Optional[str] = Field(default=None, max_length=100, description="User identifier")
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    context_limit: int = Field(default=3, ge=1, le=5, description="Maximum number of context documents (increased from 2 to 3 for better coverage)")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous conversation messages for context. Format: [{'role': 'user', 'content': '...', 'message_id': '...' (optional)}, {'role': 'assistant', 'content': '...', 'message_id': '...' (optional)}]")
    
    @field_validator('message')
    @classmethod
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
    
    @field_validator('user_id')
    @classmethod
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
    
    @field_validator('context_limit')
    @classmethod
    def validate_context_limit(cls, v):
        """Validate context limit"""
        if not isinstance(v, int):
            raise ValueError("Context limit must be an integer")
        
        if v < 1 or v > 5:
            raise ValueError("Context limit must be between 1 and 5")
        
        return v
    
    @field_validator('conversation_history', mode='before')
    @classmethod
    def validate_conversation_history(cls, v):
        """Validate and normalize conversation history
        
        CRITICAL: mode='before' ensures this runs BEFORE Pydantic type validation,
        allowing us to remove None values before Pydantic tries to validate types.
        This is equivalent to pre=True in Pydantic v1.
        """
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("conversation_history must be a list")
        
        # Normalize each message: remove None values (especially message_id: null)
        # This MUST happen before Pydantic validates types, hence pre=True
        normalized = []
        for msg in v:
            if not isinstance(msg, dict):
                raise ValueError("Each message in conversation_history must be a dict")
            
            # Remove None values to prevent Pydantic validation errors
            # This allows frontend to send message_id: null without errors
            cleaned_msg = {k: v_val for k, v_val in msg.items() if v_val is not None}
            normalized.append(cleaned_msg)
        
        return normalized
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is StillMe?",
                "user_id": "user123",
                "use_rag": True,
                "context_limit": 3
            }
        }


class ChatResponse(BaseModel):
    """Chat response with RAG context"""
    response: str
    message_id: Optional[str] = Field(None, description="Unique message ID for feedback tracking")
    context_used: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence in the answer (0.0 = uncertain, 1.0 = very confident)")
    validation_info: Optional[Dict[str, Any]] = Field(None, description="Validation results and fallback information")
    learning_suggestions: Optional[List[str]] = Field(None, description="Suggested topics to learn based on knowledge gaps")
    learning_session_id: Optional[int] = None
    knowledge_alert: Optional[Dict[str, Any]] = None
    learning_proposal: Optional[Dict[str, Any]] = Field(None, description="Proposal to learn from user conversation (requires permission)")
    permission_request: Optional[str] = Field(None, description="Permission request message to ask user if StillMe can learn from their input")
    timing: Optional[Dict[str, str]] = None
    latency_metrics: Optional[str] = Field(None, description="Formatted latency metrics for display (BẮT BUỘC HIỂN THỊ LOG)")
    processing_steps: Optional[List[str]] = Field(None, description="Real-time processing steps for status indicator (e.g., 'RAG retrieval...', 'Calling DeepSeek API...', 'Validation...')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "StillMe is a transparent AI learning system...",
                "context_used": {"knowledge_docs": [], "total_context_docs": 0},
                "accuracy_score": 0.85,
                "learning_session_id": 123,
                "timing": {"total": "1.23s"}
            }
        }

