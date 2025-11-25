"""
Base classes for evaluation framework
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of a single evaluation"""
    question: str
    ground_truth: Optional[str] = None
    predicted_answer: str = ""
    is_correct: Optional[bool] = None
    confidence_score: float = 0.0
    has_citation: bool = False
    has_uncertainty: bool = False
    validation_passed: bool = False
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class BenchmarkResults:
    """Aggregated results from a benchmark"""
    dataset_name: str
    total_questions: int
    correct_answers: int
    accuracy: float
    hallucination_rate: float
    avg_confidence: float
    citation_rate: float
    uncertainty_rate: float
    validation_pass_rate: float
    detailed_results: List[EvaluationResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "dataset_name": self.dataset_name,
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "accuracy": self.accuracy,
            "hallucination_rate": self.hallucination_rate,
            "avg_confidence": self.avg_confidence,
            "citation_rate": self.citation_rate,
            "uncertainty_rate": self.uncertainty_rate,
            "validation_pass_rate": self.validation_pass_rate,
            "detailed_results": [
                {
                    "question": r.question,
                    "ground_truth": r.ground_truth,
                    "predicted_answer": r.predicted_answer[:200],  # Truncate for storage
                    "is_correct": r.is_correct,
                    "confidence_score": r.confidence_score,
                    "has_citation": r.has_citation,
                    "has_uncertainty": r.has_uncertainty,
                    "validation_passed": r.validation_passed,
                    "metrics": r.metrics
                }
                for r in self.detailed_results
            ]
        }


class BaseEvaluator(ABC):
    """Base class for all evaluators"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize evaluator
        
        Args:
            api_base_url: Base URL for StillMe API
        """
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def load_dataset(self) -> List[Dict[str, Any]]:
        """
        Load benchmark dataset
        
        Returns:
            List of question-answer pairs
        """
        pass
    
    @abstractmethod
    def evaluate(self, questions: Optional[List[Dict[str, Any]]] = None) -> BenchmarkResults:
        """
        Run evaluation on dataset
        
        Args:
            questions: Optional subset of questions to evaluate
            
        Returns:
            BenchmarkResults with aggregated metrics
        """
        pass
    
    def query_stillme(self, question: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Query StillMe API
        
        Args:
            question: Question to ask
            use_rag: Whether to use RAG
            
        Returns:
            API response
        """
        import requests
        
        url = f"{self.api_base_url}/api/chat/rag"
        payload = {
            "message": question,
            "user_id": "evaluation_bot",
            "use_rag": use_rag,
            "context_limit": 3
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error querying StillMe: {e}")
            return {
                "response": "",
                "confidence_score": 0.0,
                "validation_info": {"passed": False}
            }
    
    def extract_metrics(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metrics from API response
        
        Args:
            api_response: Response from StillMe API
            
        Returns:
            Dictionary of metrics
        """
        import re
        
        # Ensure validation_info is always a dict, never None
        validation_info = api_response.get("validation_info")
        if validation_info is None or not isinstance(validation_info, dict):
            validation_info = {}
        
        response_text = api_response.get("response", "")
        
        # Check for citations: both numeric [1], [2] and human-readable formats
        # Numeric citations
        numeric_citation_pattern = re.compile(r'\[\d+\]')
        has_numeric_citation = bool(numeric_citation_pattern.search(response_text))
        
        # Human-readable citations
        human_readable_patterns = [
            r'\[general knowledge\]',
            r'\[research:',
            r'\[learning:',
            r'\[foundational knowledge\]',
            r'\[discussion context\]',
            r'\[news:',
            r'\[reference:',
            r'\[verified sources\]',
            r'\[needs research\]',
            r'\[personal analysis\]'
        ]
        has_human_readable_citation = any(
            re.search(pattern, response_text, re.IGNORECASE) 
            for pattern in human_readable_patterns
        )
        
        has_citation = has_numeric_citation or has_human_readable_citation
        
        # Extract citation text if present
        citation_text = None
        if has_citation:
            # Try to find citation in response
            citation_match = re.search(
                r'\[(?:general knowledge|research:|learning:|foundational knowledge|discussion context|news:|reference:|verified sources|needs research|personal analysis|\d+)[^\]]*\]',
                response_text,
                re.IGNORECASE
            )
            if citation_match:
                citation_text = citation_match.group(0)
        
        return {
            "confidence_score": api_response.get("confidence_score", 0.0),
            "has_citation": has_citation,
            "citation_text": citation_text,  # Store actual citation for transparency
            "has_numeric_citation": has_numeric_citation,
            "has_human_readable_citation": has_human_readable_citation,
            "has_uncertainty": any(
                phrase in response_text.lower()
                for phrase in ["don't know", "không biết", "uncertain", "không chắc", "i don't have", "tôi không có"]
            ),
            "validation_passed": validation_info.get("passed", False),
            "context_docs_count": validation_info.get("context_docs_count", 0),
            "used_fallback": validation_info.get("used_fallback", False)
        }

