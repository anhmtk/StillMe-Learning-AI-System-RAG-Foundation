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
    
    def query_stillme(self, question: str, use_rag: bool = True, max_retries_for_fallback: int = 2) -> Dict[str, Any]:
        """
        Query StillMe API with retry logic for fallback messages
        
        Args:
            question: Question to ask
            use_rag: Whether to use RAG
            max_retries_for_fallback: Maximum retries if fallback message is detected
            
        Returns:
            API response
        """
        import requests
        import time
        
        url = f"{self.api_base_url}/api/chat/rag"
        payload = {
            "message": question,
            "user_id": "evaluation_bot",
            "use_rag": use_rag,
            "context_limit": 3,
            "use_server_keys": True  # CRITICAL: Use server API keys for evaluation
        }
        
        max_retries = 3
        fallback_retries = 0
        
        for attempt in range(max_retries):
            try:
                # Increased timeout for Railway (cold start + LLM latency): 120s -> 180s
                response = requests.post(url, json=payload, timeout=180)
                
                # Handle HTTP 429 (Rate Limit) with retry
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                        self.logger.warning(f"Rate limited (HTTP 429) for question '{question[:50]}...', retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Rate limit exceeded for question '{question[:50]}...' after {max_retries} attempts")
                        return {
                            "response": "",
                            "confidence_score": 0.0,
                            "validation_info": {"passed": False}
                        }
                
                response.raise_for_status()
                api_response = response.json()
                
                # CRITICAL: Check if response is a fallback message
                response_text = api_response.get("response", "")
                if response_text and self.is_fallback_message(response_text):
                    if fallback_retries < max_retries_for_fallback:
                        fallback_retries += 1
                        wait_time = fallback_retries * 3  # Exponential backoff: 3s, 6s
                        self.logger.warning(
                            f"Fallback message detected for question '{question[:50]}...', "
                            f"retrying in {wait_time}s (fallback retry {fallback_retries}/{max_retries_for_fallback})"
                        )
                        time.sleep(wait_time)
                        continue  # Retry the request
                    else:
                        self.logger.error(
                            f"Fallback message persisted for question '{question[:50]}...' "
                            f"after {max_retries_for_fallback} retries. Response: {response_text[:200]}..."
                        )
                        # Return the response anyway, but mark it as fallback
                        api_response["_is_fallback"] = True
                        return api_response
                
                # Success - no fallback message
                return api_response
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Timeout for question '{question[:50]}...', retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Timeout for question '{question[:50]}...' after {max_retries} attempts")
                    return {
                        "response": "",
                        "confidence_score": 0.0,
                        "validation_info": {"passed": False}
                    }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Error querying StillMe: {e}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Error querying StillMe: {e}")
                    return {
                        "response": "",
                        "confidence_score": 0.0,
                        "validation_info": {"passed": False}
                    }
        
        # Should not reach here, but just in case
        return {
            "response": "",
            "confidence_score": 0.0,
            "validation_info": {"passed": False}
        }
    
    def is_fallback_message(self, text: str) -> bool:
        """
        Detect if response is a fallback message (technical error message)
        
        Args:
            text: Response text to check
            
        Returns:
            True if text is a fallback message
        """
        if not text or len(text.strip()) < 50:
            return False
        
        text_lower = text.lower()
        
        # Fallback message patterns (from backend/api/utils/error_detector.py)
        fallback_patterns = [
            "stillme is experiencing a technical issue",
            "stillme đang gặp sự cố kỹ thuật",
            "i cannot provide a good answer",
            "mình không thể trả lời tốt",
            "i cannot provide a good answer to this question with the current configuration",
            "cannot provide a good answer to this question with the current configuration",
            "i will suggest to the developer",
            "mình sẽ đề xuất cho developer",
            "stillme is currently encountering a context limit",
            "hiện tại hệ thống của stillme đang gặp giới hạn ngữ cảnh",
        ]
        
        # Check if text contains fallback patterns
        # If text is short (< 500 chars) and contains fallback pattern, it's likely a fallback
        # If text starts with fallback pattern, it's also likely a fallback
        has_fallback_pattern = any(pattern in text_lower for pattern in fallback_patterns)
        
        if has_fallback_pattern:
            # If text is short or starts with fallback, it's definitely a fallback
            if len(text.strip()) < 500 or text_lower.startswith(("stillme is experiencing", "stillme đang gặp")):
                return True
            # If text is longer but fallback pattern appears in first 200 chars, it's likely a fallback
            if any(pattern in text_lower[:200] for pattern in fallback_patterns):
                return True
        
        return False
    
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
        
        # CRITICAL: Detect fallback messages
        is_fallback = self.is_fallback_message(response_text)
        
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
                for phrase in ["don't know", "không biết", "uncertain", "không chắc", "i don't have", "tôi không có", "insufficient information", "thiếu thông tin"]
            ),
            "validation_passed": validation_info.get("passed", False),
            "context_docs_count": validation_info.get("context_docs_count", 0),
            "used_fallback": validation_info.get("used_fallback", False) or is_fallback  # Include detected fallback
        }

