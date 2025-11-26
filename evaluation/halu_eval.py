"""
HaluEval Benchmark Evaluator

Evaluates StillMe on HaluEval dataset for hallucination detection
"""

import json
import os
from typing import List, Dict, Any, Optional
import logging

from .base import BaseEvaluator, EvaluationResult, BenchmarkResults
from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class HaluEvalEvaluator(BaseEvaluator):
    """Evaluator for HaluEval benchmark"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", dataset_path: Optional[str] = None):
        """
        Initialize HaluEval evaluator
        
        Args:
            api_base_url: Base URL for StillMe API
            dataset_path: Path to HaluEval dataset JSON file
        """
        super().__init__(api_base_url)
        self.dataset_path = dataset_path or "data/benchmarks/halu_eval.json"
        self.metrics_calculator = MetricsCalculator()
    
    def load_dataset(self) -> List[Dict[str, Any]]:
        """
        Load HaluEval dataset
        
        Returns:
            List of question-answer pairs with hallucination labels
        """
        if os.path.exists(self.dataset_path):
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("questions", [])
        
        # If dataset not found, return sample questions for testing
        self.logger.warning(f"HaluEval dataset not found at {self.dataset_path}")
        self.logger.info("Using sample questions for testing")
        
        return [
            {
                "question": "What is the population of a fictional city?",
                "answer": "The population is 10 million",
                "is_hallucination": True,  # Fictional city
                "context": "No context available"
            },
            {
                "question": "What is the capital of France?",
                "answer": "Paris",
                "is_hallucination": False,
                "context": "Paris is the capital of France"
            }
        ]
    
    def evaluate(self, questions: Optional[List[Dict[str, Any]]] = None) -> BenchmarkResults:
        """
        Run evaluation on HaluEval dataset
        
        Args:
            questions: Optional subset of questions to evaluate
            
        Returns:
            BenchmarkResults with aggregated metrics
        """
        if questions is None:
            questions = self.load_dataset()
        
        self.logger.info(f"Evaluating StillMe on {len(questions)} HaluEval questions...")
        
        import time
        results = []
        for i, qa_pair in enumerate(questions):
            question = qa_pair.get("question", "")
            expected_answer = qa_pair.get("answer", "")
            is_hallucination = qa_pair.get("is_hallucination", False)
            context = qa_pair.get("context", "")
            
            self.logger.info(f"Question {i+1}/{len(questions)}: {question[:50]}...")
            
            # Add delay between requests to avoid rate limiting (except for first request)
            if i > 0:
                delay = 2.0  # 2 seconds delay between requests
                self.logger.debug(f"   Waiting {delay}s before next request to avoid rate limiting...")
                time.sleep(delay)
            
            # Query StillMe with retry for fallback messages
            api_response = self.query_stillme(question, use_rag=True, max_retries_for_fallback=2)
            predicted_answer = api_response.get("response", "")
            
            # Log if fallback was detected
            if api_response.get("_is_fallback", False) or self.is_fallback_message(predicted_answer):
                self.logger.warning(
                    f"⚠️  Fallback message detected for question {i+1}: '{question[:50]}...'"
                )
                self.logger.debug(f"   Response preview: {predicted_answer[:200]}...")
            
            # Extract metrics
            metrics = self.extract_metrics(api_response)
            
            # Check if StillMe detected hallucination (via uncertainty, validation failure, etc.)
            stillme_detected_hallucination = (
                metrics["has_uncertainty"] or
                not metrics["validation_passed"] or
                metrics["used_fallback"]
            )
            
            # Answer is correct if StillMe correctly identified hallucination
            # OR if it's not a hallucination and StillMe answered correctly
            if is_hallucination:
                # Should detect hallucination (express uncertainty, fail validation, use fallback)
                is_correct = stillme_detected_hallucination
            else:
                # Should answer correctly (not detect hallucination)
                is_correct = not stillme_detected_hallucination and metrics["validation_passed"]
            
            result = EvaluationResult(
                question=question,
                ground_truth=expected_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                confidence_score=metrics["confidence_score"],
                has_citation=metrics["has_citation"],
                has_uncertainty=metrics["has_uncertainty"],
                validation_passed=metrics["validation_passed"],
                metrics={
                    **metrics,
                    "is_hallucination": is_hallucination,
                    "stillme_detected_hallucination": stillme_detected_hallucination
                }
            )
            
            results.append(result)
        
        # Calculate aggregated metrics
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="HaluEval",
            total_questions=len(results),
            correct_answers=sum(1 for r in results if r.is_correct is True),
            accuracy=system_metrics.accuracy,
            hallucination_rate=system_metrics.hallucination_rate,
            avg_confidence=system_metrics.avg_confidence,
            citation_rate=system_metrics.citation_rate,
            uncertainty_rate=system_metrics.uncertainty_rate,
            validation_pass_rate=system_metrics.validation_pass_rate,
            detailed_results=results
        )

