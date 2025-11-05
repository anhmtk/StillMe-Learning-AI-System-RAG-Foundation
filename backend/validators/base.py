"""
Base classes for StillMe validators
"""

from typing import Protocol, List, Optional
from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of a validation check"""
    
    passed: bool
    """Whether validation passed"""
    
    reasons: List[str] = []
    """List of failure reasons or warnings"""
    
    patched_answer: Optional[str] = None
    """Auto-patched answer if validator can fix issues"""
    
    class Config:
        """Pydantic config"""
        frozen = True


class Validator(Protocol):
    """Protocol for validators"""
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Run validation on answer with context documents
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with passed status and reasons
        """
        ...

