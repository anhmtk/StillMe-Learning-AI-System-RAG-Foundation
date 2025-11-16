"""
TruthfulQA Benchmark Evaluator

Evaluates StillMe on TruthfulQA dataset for truthfulness and accuracy
"""

import json
import os
from typing import List, Dict, Any, Optional
import logging

from .base import BaseEvaluator, EvaluationResult, BenchmarkResults
from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class TruthfulQAEvaluator(BaseEvaluator):
    """Evaluator for TruthfulQA benchmark"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", dataset_path: Optional[str] = None):
        """
        Initialize TruthfulQA evaluator
        
        Args:
            api_base_url: Base URL for StillMe API
            dataset_path: Path to TruthfulQA dataset JSON file
                        If None, will try to download or use default location
        """
        super().__init__(api_base_url)
        self.dataset_path = dataset_path or "data/benchmarks/truthfulqa.json"
        self.metrics_calculator = MetricsCalculator()
    
    def load_dataset(self) -> List[Dict[str, Any]]:
        """
        Load TruthfulQA dataset
        
        Returns:
            List of question-answer pairs
        """
        if os.path.exists(self.dataset_path):
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("questions", [])
        
        # If dataset not found, return sample questions for testing
        self.logger.warning(f"TruthfulQA dataset not found at {self.dataset_path}")
        self.logger.info("Using sample questions for testing")
        
        return [
            {
                "question": "What is the capital of France?",
                "correct_answer": "Paris",
                "incorrect_answers": ["London", "Berlin", "Madrid"]
            },
            {
                "question": "What is 2+2?",
                "correct_answer": "4",
                "incorrect_answers": ["5", "3", "6"]
            }
        ]
    
    def evaluate(self, questions: Optional[List[Dict[str, Any]]] = None) -> BenchmarkResults:
        """
        Run evaluation on TruthfulQA dataset
        
        Args:
            questions: Optional subset of questions to evaluate
            
        Returns:
            BenchmarkResults with aggregated metrics
        """
        if questions is None:
            questions = self.load_dataset()
        
        self.logger.info(f"Evaluating StillMe on {len(questions)} TruthfulQA questions...")
        
        results = []
        for i, qa_pair in enumerate(questions):
            question = qa_pair.get("question", "")
            correct_answer = qa_pair.get("correct_answer", "")
            incorrect_answers = qa_pair.get("incorrect_answers", [])
            
            self.logger.info(f"Question {i+1}/{len(questions)}: {question[:50]}...")
            
            # Query StillMe
            api_response = self.query_stillme(question)
            predicted_answer = api_response.get("response", "")
            
            # Extract metrics
            metrics = self.extract_metrics(api_response)
            
            # Check if answer is correct (simple keyword matching for now)
            # TODO: Use better matching (semantic similarity, LLM-based evaluation)
            is_correct = self._check_answer_correctness(
                predicted_answer,
                correct_answer,
                incorrect_answers
            )
            
            result = EvaluationResult(
                question=question,
                ground_truth=correct_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                confidence_score=metrics["confidence_score"],
                has_citation=metrics["has_citation"],
                has_uncertainty=metrics["has_uncertainty"],
                validation_passed=metrics["validation_passed"],
                metrics=metrics
            )
            
            results.append(result)
        
        # Calculate aggregated metrics
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="TruthfulQA",
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
    
    def _check_answer_correctness(
        self,
        predicted_answer: str,
        correct_answer: str,
        incorrect_answers: List[str]
    ) -> Optional[bool]:
        """
        Check if predicted answer is correct
        
        Args:
            predicted_answer: Answer from StillMe
            correct_answer: Correct answer
            incorrect_answers: List of incorrect answers
            
        Returns:
            True if correct, False if incorrect, None if uncertain
        """
        predicted_lower = predicted_answer.lower()
        correct_lower = correct_answer.lower()
        
        # Check if correct answer appears in prediction
        if correct_lower in predicted_lower:
            # Check if any incorrect answer also appears (could be ambiguous)
            for incorrect in incorrect_answers:
                if incorrect.lower() in predicted_lower:
                    # Both appear - uncertain
                    return None
            return True
        
        # Check if incorrect answer appears
        for incorrect in incorrect_answers:
            if incorrect.lower() in predicted_lower:
                return False
        
        # No clear match - uncertain
        return None

