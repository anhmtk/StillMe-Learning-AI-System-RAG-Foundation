"""
Abstract Post-Processing Interface

Defines the interface for post-processing systems that can:
- Evaluate response quality
- Rewrite responses if needed
- Sanitize style and content
- Track post-processing metrics
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PostProcessingResult:
    """Result of post-processing"""
    processed_text: str
    quality_score: float
    rewrite_attempted: bool = False
    rewrite_successful: bool = False
    processing_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class PostProcessor(ABC):
    """
    Abstract post-processing interface
    
    Defines the contract for post-processing systems that can:
    1. Evaluate response quality
    2. Rewrite responses if needed
    3. Sanitize style and content
    """
    
    @abstractmethod
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> PostProcessingResult:
        """
        Process and improve response text
        
        Args:
            text: Original response text
            context: Optional context (question, validation results, etc.)
            
        Returns:
            PostProcessingResult with processed text and metrics
        """
        pass
    
    @abstractmethod
    def evaluate_quality(self, text: str) -> float:
        """
        Evaluate quality of response text
        
        Args:
            text: Response text to evaluate
            
        Returns:
            Quality score (0.0-1.0)
        """
        pass

