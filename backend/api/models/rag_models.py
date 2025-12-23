"""
RAG API request and response models with comprehensive validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List
from .common_models import sanitize_string


class RAGQueryRequest(BaseModel):
    """Request to query RAG system"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    knowledge_limit: int = Field(default=3, ge=1, le=20, description="Maximum knowledge documents")
    conversation_limit: int = Field(default=2, ge=0, le=10, description="Maximum conversation documents")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and sanitize query"""
        if not isinstance(v, str):
            raise ValueError("Query must be a string")
        
        # Sanitize query
        v = sanitize_string(v, max_length=1000)
        
        # Check for empty after sanitization
        if not v.strip():
            raise ValueError("Query cannot be empty")
        
        return v
    
    @validator('knowledge_limit')
    def validate_knowledge_limit(cls, v):
        """Validate knowledge limit"""
        if not isinstance(v, int):
            raise ValueError("Knowledge limit must be an integer")
        
        if v < 1 or v > 20:
            raise ValueError("Knowledge limit must be between 1 and 20")
        
        return v
    
    @validator('conversation_limit')
    def validate_conversation_limit(cls, v):
        """Validate conversation limit"""
        if not isinstance(v, int):
            raise ValueError("Conversation limit must be an integer")
        
        if v < 0 or v > 10:
            raise ValueError("Conversation limit must be between 0 and 10")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is StillMe?",
                "knowledge_limit": 3,
                "conversation_limit": 2
            }
        }


class RAGQueryResponse(BaseModel):
    """Response from RAG query"""
    knowledge_docs: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge documents")
    conversation_docs: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation documents")
    total_context_docs: int = Field(0, ge=0, description="Total context documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_docs": [
                    {
                        "id": "doc1",
                        "content": "StillMe is a transparent AI system...",
                        "metadata": {}
                    }
                ],
                "conversation_docs": [],
                "total_context_docs": 1
            }
        }

