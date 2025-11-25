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
        # Ensure validation_info is always a dict, never None
        validation_info = api_response.get("validation_info")
        if validation_info is None or not isinstance(validation_info, dict):
            validation_info = {}
        
        return {
            "confidence_score": api_response.get("confidence_score", 0.0),
            "has_citation": "[1]" in api_response.get("response", "") or "[2]" in api_response.get("response", ""),
            "has_uncertainty": any(
                phrase in api_response.get("response", "").lower()
                for phrase in ["don't know", "không biết", "uncertain", "không chắc"]
            ),
            "validation_passed": validation_info.get("passed", False),
            "context_docs_count": validation_info.get("context_docs_count", 0),
            "used_fallback": validation_info.get("used_fallback", False)
        }

