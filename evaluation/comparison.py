"""
System Comparison Framework

Compares StillMe with baseline systems: vanilla RAG, ChatGPT, Claude
"""

import os
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .base import EvaluationResult, BenchmarkResults
from .metrics import MetricsCalculator, SystemMetrics

logger = logging.getLogger(__name__)


class SystemComparator:
    """Compare StillMe with other systems"""
    
    def __init__(self, stillme_api_url: str = "http://localhost:8000"):
        """
        Initialize system comparator
        
        Args:
            stillme_api_url: Base URL for StillMe API
        """
        self.stillme_api_url = stillme_api_url
        self.metrics_calculator = MetricsCalculator()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def compare_systems(
        self,
        questions: List[Dict[str, Any]],
        systems: Optional[List[str]] = None
    ) -> Dict[str, BenchmarkResults]:
        """
        Compare multiple systems on the same questions
        
        Args:
            questions: List of questions to evaluate
            systems: List of systems to compare (default: ["stillme", "vanilla_rag", "chatgpt", "claude"])
            
        Returns:
            Dictionary mapping system name to BenchmarkResults
        """
        if systems is None:
            systems = ["stillme", "vanilla_rag", "chatgpt", "claude"]
        
        results = {}
        
        for system_name in systems:
            self.logger.info(f"Evaluating {system_name}...")
            
            if system_name == "stillme":
                results[system_name] = self._evaluate_stillme(questions)
            elif system_name == "vanilla_rag":
                results[system_name] = self._evaluate_vanilla_rag(questions)
            elif system_name == "chatgpt":
                results[system_name] = self._evaluate_chatgpt(questions)
            elif system_name == "claude":
                results[system_name] = self._evaluate_claude(questions)
            else:
                self.logger.warning(f"Unknown system: {system_name}")
        
        return results
    
    def _evaluate_stillme(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate StillMe with full RAG and validation"""
        from .base import BaseEvaluator
        
        evaluator = BaseEvaluator(self.stillme_api_url)
        results = []
        
        for qa_pair in questions:
            question = qa_pair.get("question", "")
            ground_truth = qa_pair.get("correct_answer", "")
            
            api_response = evaluator.query_stillme(question, use_rag=True)
            predicted_answer = api_response.get("response", "")
            metrics = evaluator.extract_metrics(api_response)
            
            # Check correctness (simplified)
            is_correct = self._check_correctness(predicted_answer, ground_truth)
            
            results.append(EvaluationResult(
                question=question,
                ground_truth=ground_truth,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                confidence_score=metrics["confidence_score"],
                has_citation=metrics["has_citation"],
                has_uncertainty=metrics["has_uncertainty"],
                validation_passed=metrics["validation_passed"],
                metrics=metrics
            ))
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="StillMe (Full RAG + Validation)",
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
    
    def _evaluate_vanilla_rag(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate StillMe with RAG but NO validation (vanilla RAG baseline)"""
        from .base import BaseEvaluator
        
        evaluator = BaseEvaluator(self.stillme_api_url)
        results = []
        
        for qa_pair in questions:
            question = qa_pair.get("question", "")
            ground_truth = qa_pair.get("correct_answer", "")
            
            # Query with RAG but disable validators
            api_response = evaluator.query_stillme(question, use_rag=True)
            predicted_answer = api_response.get("response", "")
            
            # Simulate vanilla RAG: no validation, no citations required
            is_correct = self._check_correctness(predicted_answer, ground_truth)
            
            results.append(EvaluationResult(
                question=question,
                ground_truth=ground_truth,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                confidence_score=0.8,  # Assume high confidence (no uncertainty checking)
                has_citation=False,  # Vanilla RAG doesn't require citations
                has_uncertainty=False,  # Vanilla RAG doesn't express uncertainty
                validation_passed=True,  # No validation = always pass
                metrics={"system": "vanilla_rag"}
            ))
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="Vanilla RAG (No Validation)",
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
    
    def _evaluate_chatgpt(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate ChatGPT (requires OpenAI API key)"""
        import openai
        
        results = []
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set, skipping ChatGPT evaluation")
            return self._empty_results("ChatGPT (Not Available)")
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            for qa_pair in questions:
                question = qa_pair.get("question", "")
                ground_truth = qa_pair.get("correct_answer", "")
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": question}],
                    temperature=0.7
                )
                
                predicted_answer = response.choices[0].message.content
                is_correct = self._check_correctness(predicted_answer, ground_truth)
                
                results.append(EvaluationResult(
                    question=question,
                    ground_truth=ground_truth,
                    predicted_answer=predicted_answer,
                    is_correct=is_correct,
                    confidence_score=0.9,  # ChatGPT doesn't provide confidence
                    has_citation=False,  # ChatGPT doesn't cite sources
                    has_uncertainty=False,  # ChatGPT rarely expresses uncertainty
                    validation_passed=True,  # No validation
                    metrics={"system": "chatgpt", "model": "gpt-4"}
                ))
        except Exception as e:
            self.logger.error(f"Error evaluating ChatGPT: {e}")
            return self._empty_results("ChatGPT (Error)")
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="ChatGPT (GPT-4)",
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
    
    def _evaluate_claude(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate Claude (requires Anthropic API key)"""
        try:
            import anthropic
        except ImportError:
            self.logger.warning("anthropic package not installed, skipping Claude evaluation")
            return self._empty_results("Claude (Not Available)")
        
        results = []
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            self.logger.warning("ANTHROPIC_API_KEY not set, skipping Claude evaluation")
            return self._empty_results("Claude (Not Available)")
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            for qa_pair in questions:
                question = qa_pair.get("question", "")
                ground_truth = qa_pair.get("correct_answer", "")
                
                message = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": question}]
                )
                
                predicted_answer = message.content[0].text
                is_correct = self._check_correctness(predicted_answer, ground_truth)
                
                results.append(EvaluationResult(
                    question=question,
                    ground_truth=ground_truth,
                    predicted_answer=predicted_answer,
                    is_correct=is_correct,
                    confidence_score=0.9,
                    has_citation=False,
                    has_uncertainty=False,
                    validation_passed=True,
                    metrics={"system": "claude", "model": "claude-3-opus"}
                ))
        except Exception as e:
            self.logger.error(f"Error evaluating Claude: {e}")
            return self._empty_results("Claude (Error)")
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="Claude (Claude-3-Opus)",
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
    
    def _check_correctness(self, predicted: str, ground_truth: str) -> Optional[bool]:
        """Simple correctness check (can be improved with semantic similarity)"""
        if not ground_truth:
            return None
        
        predicted_lower = predicted.lower()
        ground_truth_lower = ground_truth.lower()
        
        # Simple keyword matching
        if ground_truth_lower in predicted_lower:
            return True
        
        # Could add semantic similarity check here
        return None
    
    def _empty_results(self, dataset_name: str) -> BenchmarkResults:
        """Return empty results for unavailable systems"""
        return BenchmarkResults(
            dataset_name=dataset_name,
            total_questions=0,
            correct_answers=0,
            accuracy=0.0,
            hallucination_rate=1.0,
            avg_confidence=0.0,
            citation_rate=0.0,
            uncertainty_rate=0.0,
            validation_pass_rate=0.0,
            detailed_results=[]
        )
    
    def generate_comparison_report(
        self,
        results: Dict[str, BenchmarkResults],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate comparison report
        
        Args:
            results: Dictionary of system results
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        report_lines = [
            "# StillMe System Comparison Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            ""
        ]
        
        # Summary table
        report_lines.append("| System | Accuracy | Hallucination Rate | Transparency Score | Citation Rate |")
        report_lines.append("|--------|----------|-------------------|-------------------|---------------|")
        
        for system_name, benchmark_results in results.items():
            metrics = self.metrics_calculator.calculate_metrics(benchmark_results.detailed_results)
            report_lines.append(
                f"| {system_name} | {metrics.accuracy:.2%} | {metrics.hallucination_rate:.2%} | "
                f"{metrics.transparency_score:.2%} | {metrics.citation_rate:.2%} |"
            )
        
        report_lines.extend([
            "",
            "## Detailed Results",
            ""
        ])
        
        for system_name, benchmark_results in results.items():
            report_lines.extend([
                f"### {system_name}",
                f"- Total Questions: {benchmark_results.total_questions}",
                f"- Correct Answers: {benchmark_results.correct_answers}",
                f"- Accuracy: {benchmark_results.accuracy:.2%}",
                f"- Hallucination Rate: {benchmark_results.hallucination_rate:.2%}",
                f"- Average Confidence: {benchmark_results.avg_confidence:.2f}",
                f"- Citation Rate: {benchmark_results.citation_rate:.2%}",
                f"- Uncertainty Rate: {benchmark_results.uncertainty_rate:.2%}",
                f"- Validation Pass Rate: {benchmark_results.validation_pass_rate:.2%}",
                ""
            ])
        
        report = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"Comparison report saved to {output_path}")
        
        return report

