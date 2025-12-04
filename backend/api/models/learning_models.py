"""
Learning API request and response models with comprehensive validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from .common_models import sanitize_string, validate_url, validate_non_empty_string


class LearningRequest(BaseModel):
    """Request to add learning content"""
    content: str = Field(..., min_length=10, max_length=50000, description="Learning content")
    source: str = Field(..., min_length=1, max_length=1000, description="Content source")
    content_type: str = Field(default="knowledge", max_length=50, description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate and sanitize content"""
        if not isinstance(v, str):
            raise ValueError("Content must be a string")
        
        # Sanitize content
        v = sanitize_string(v, max_length=50000)
        
        # Check minimum length after sanitization
        if len(v.strip()) < 10:
            raise ValueError("Content must be at least 10 characters long")
        
        return v
    
    @validator('source')
    def validate_source(cls, v):
        """Validate source (can be URL or text)"""
        if not isinstance(v, str):
            raise ValueError("Source must be a string")
        
        v = v.strip()
        
        if len(v) < 1:
            raise ValueError("Source cannot be empty")
        
        if len(v) > 1000:
            raise ValueError("Source must not exceed 1000 characters")
        
        # If it looks like a URL, validate it
        if v.startswith(('http://', 'https://')):
            try:
                v = validate_url(v)
            except ValueError:
                # If URL validation fails, just sanitize as string
                v = sanitize_string(v, max_length=1000)
        else:
            # Sanitize as regular string
            v = sanitize_string(v, max_length=1000)
        
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type"""
        if not isinstance(v, str):
            raise ValueError("Content type must be a string")
        
        v = sanitize_string(v, max_length=50)
        
        # Allowed content types
        allowed_types = ['knowledge', 'conversation', 'article', 'document', 'foundational', 'other']
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata structure"""
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Limit metadata size
        if len(str(v)) > 10000:
            raise ValueError("Metadata is too large (max 10000 characters when serialized)")
        
        # Recursively sanitize string values in metadata
        def sanitize_metadata(obj):
            if isinstance(obj, str):
                return sanitize_string(obj, max_length=1000)
            elif isinstance(obj, dict):
                return {k: sanitize_metadata(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_metadata(item) for item in obj]
            else:
                return obj
        
        return sanitize_metadata(v)
    
    class Config:
        schema_extra = {
            "example": {
                "content": "StillMe is a transparent AI learning system...",
                "source": "https://example.com/article",
                "content_type": "knowledge",
                "metadata": {"author": "StillMe Team"}
            }
        }


class LearningResponse(BaseModel):
    """Response from learning content addition"""
    success: bool
    knowledge_id: Optional[int] = Field(None, ge=1, description="ID of added knowledge item")
    message: str = Field(..., min_length=1, max_length=500, description="Response message")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate response message"""
        return validate_non_empty_string(v, field_name="message", min_length=1, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "knowledge_id": 123,
                "message": "Knowledge added successfully"
            }
        }

