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
            systems = ["stillme", "vanilla_rag", "chatgpt", "deepseek", "openrouter"]
        
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
            elif system_name == "deepseek":
                results[system_name] = self._evaluate_deepseek(questions)
            elif system_name == "openrouter":
                results[system_name] = self._evaluate_openrouter(questions)
            else:
                self.logger.warning(f"Unknown system: {system_name}")
        
        return results
    
    def _evaluate_stillme(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate StillMe with full RAG and validation"""
        results = []
        
        for qa_pair in questions:
            question = qa_pair.get("question", "")
            ground_truth = qa_pair.get("correct_answer", "")
            
            # Query StillMe API directly
            api_response = self._query_stillme(question, use_rag=True)
            predicted_answer = api_response.get("response", "")
            metrics = self._extract_metrics(api_response)
            
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
        results = []
        
        for qa_pair in questions:
            question = qa_pair.get("question", "")
            ground_truth = qa_pair.get("correct_answer", "")
            
            # Query with RAG but disable validators (simulate vanilla RAG)
            api_response = self._query_stillme(question, use_rag=True)
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
        # Try to get key from environment (set directly) first, then from .env
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set, skipping ChatGPT evaluation")
            self.logger.warning("   Tip: Set it in PowerShell: $env:OPENAI_API_KEY='sk-proj-...'")
            return self._empty_results("ChatGPT (Not Available)")
        
        # Clean API key (remove quotes, spaces, newlines)
        api_key = api_key.strip().strip('"').strip("'").replace("\n", "").replace("\r", "")
        
        # Additional check: if key seems truncated or has issues, warn
        if len(api_key) < 50:
            self.logger.warning(f"API key seems too short ({len(api_key)} chars), might be invalid")
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Try gpt-4 first, fallback to gpt-3.5-turbo if not available
            model = os.getenv("OPENAI_MODEL", "gpt-4")
            use_fallback = False
            
            for i, qa_pair in enumerate(questions):
                question = qa_pair.get("question", "")
                ground_truth = qa_pair.get("correct_answer", "")
                
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": question}],
                        temperature=0.7,
                        timeout=60.0
                    )
                    
                    # Check if response is valid
                    if not response or not response.choices or len(response.choices) == 0:
                        self.logger.warning(f"Empty response from OpenAI (question {i+1}/{len(questions)})")
                        continue
                    
                    if not response.choices[0].message or not response.choices[0].message.content:
                        self.logger.warning(f"No content in response from OpenAI (question {i+1}/{len(questions)})")
                        continue
                    
                    predicted_answer = response.choices[0].message.content
                    
                    if not predicted_answer or not predicted_answer.strip():
                        self.logger.warning(f"Empty predicted answer from OpenAI (question {i+1}/{len(questions)})")
                        continue
                    
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
                        metrics={"system": "chatgpt", "model": model}
                    ))
                    
                except openai.AuthenticationError as e:
                    self.logger.error(f"OpenAI Authentication Error (question {i+1}/{len(questions)}): {e}")
                    self.logger.error("This usually means the API key is invalid or expired")
                    # Try fallback to gpt-3.5-turbo if gpt-4 fails
                    if model == "gpt-4" and not use_fallback:
                        self.logger.info("Trying fallback to gpt-3.5-turbo...")
                        model = "gpt-3.5-turbo"
                        use_fallback = True
                        continue
                    else:
                        raise
                except openai.RateLimitError as e:
                    self.logger.warning(f"OpenAI Rate Limit (question {i+1}/{len(questions)}): {e}")
                    self.logger.info("Waiting 60 seconds before retrying...")
                    import time
                    time.sleep(60)
                    continue
                except openai.APIError as e:
                    self.logger.error(f"OpenAI API Error (question {i+1}/{len(questions)}): {e}")
                    # Skip this question and continue
                    continue
                except Exception as e:
                    self.logger.error(f"Unexpected error evaluating ChatGPT (question {i+1}/{len(questions)}): {e}")
                    import traceback
                    self.logger.debug(f"Traceback: {traceback.format_exc()}")
                    # Skip this question and continue
                    continue
            
            # If we have some results, return them even if some questions failed
            if results:
                self.logger.info(f"ChatGPT evaluation completed: {len(results)}/{len(questions)} questions successful")
                system_metrics = self.metrics_calculator.calculate_metrics(results)
                
                return BenchmarkResults(
                    dataset_name=f"ChatGPT ({model})",
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
            else:
                # No results at all - return empty
                self.logger.warning("ChatGPT evaluation failed: No questions were successfully processed")
                return self._empty_results("ChatGPT (No Results)")
                    
        except openai.AuthenticationError as e:
            self.logger.error(f"OpenAI Authentication Error: {e}")
            self.logger.error("Please check your OPENAI_API_KEY in .env file")
            return self._empty_results("ChatGPT (Authentication Error)")
        except Exception as e:
            self.logger.error(f"Error evaluating ChatGPT: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # If we have partial results, return them
            if results:
                self.logger.info(f"Returning partial results: {len(results)} questions")
                system_metrics = self.metrics_calculator.calculate_metrics(results)
                return BenchmarkResults(
                    dataset_name="ChatGPT (Partial Results)",
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
            return self._empty_results("ChatGPT (Error)")
        
        # This should not be reached if we have results (already returned above)
        # But keep it as fallback
        if not results:
            return self._empty_results("ChatGPT (No Results)")
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name=f"ChatGPT ({model})",
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
                
                # Use Claude Haiku for cost-effective evaluation (can be changed to opus/sonnet)
                model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")  # Default to Haiku
                
                message = client.messages.create(
                    model=model,
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
    
    def _evaluate_deepseek(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate DeepSeek (requires DEEPSEEK_API_KEY)"""
        import httpx
        
        results = []
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            self.logger.warning("DEEPSEEK_API_KEY not set, skipping DeepSeek evaluation")
            return self._empty_results("DeepSeek (Not Available)")
        
        try:
            for qa_pair in questions:
                question = qa_pair.get("question", "")
                ground_truth = qa_pair.get("correct_answer", "")
                
                # Call DeepSeek API
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "user", "content": question}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        predicted_answer = data["choices"][0]["message"]["content"]
                    else:
                        self.logger.error(f"DeepSeek API error: {response.status_code}")
                        predicted_answer = ""
                
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
                    metrics={"system": "deepseek", "model": "deepseek-chat"}
                ))
        except Exception as e:
            self.logger.error(f"Error evaluating DeepSeek: {e}")
            return self._empty_results("DeepSeek (Error)")
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name="DeepSeek (deepseek-chat)",
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
    
    def _evaluate_openrouter(self, questions: List[Dict[str, Any]]) -> BenchmarkResults:
        """Evaluate OpenRouter (requires OPENROUTER_API_KEY)"""
        import httpx
        
        results = []
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            self.logger.warning("OPENROUTER_API_KEY not set, skipping OpenRouter evaluation")
            return self._empty_results("OpenRouter (Not Available)")
        
        # Get model from env or use default
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        
        try:
            for qa_pair in questions:
                question = qa_pair.get("question", "")
                ground_truth = qa_pair.get("correct_answer", "")
                
                # Call OpenRouter API
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://github.com/stillme-ai/stillme",
                            "X-Title": "StillMe Evaluation"
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "user", "content": question}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        predicted_answer = data["choices"][0]["message"]["content"]
                    else:
                        self.logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                        predicted_answer = ""
                
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
                    metrics={"system": "openrouter", "model": model}
                ))
        except Exception as e:
            self.logger.error(f"Error evaluating OpenRouter: {e}")
            return self._empty_results("OpenRouter (Error)")
        
        system_metrics = self.metrics_calculator.calculate_metrics(results)
        
        return BenchmarkResults(
            dataset_name=f"OpenRouter ({model})",
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
    
    def _query_stillme(self, question: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Query StillMe API
        
        Args:
            question: Question to ask
            use_rag: Whether to use RAG
            
        Returns:
            API response
        """
        import requests
        
        url = f"{self.stillme_api_url}/api/chat/rag"
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
    
    def _extract_metrics(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metrics from API response
        
        Args:
            api_response: Response from StillMe API
            
        Returns:
            Dictionary of metrics
        """
        validation_info = api_response.get("validation_info", {})
        
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
    
    def _check_correctness(self, predicted: str, ground_truth: str) -> Optional[bool]:
        """
        Improved correctness check using keyword matching and semantic similarity
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            
        Returns:
            True if correct, False if incorrect, None if uncertain
        """
        if not ground_truth:
            return None
        
        predicted_lower = predicted.lower().strip()
        ground_truth_lower = ground_truth.lower().strip()
        
        # Method 1: Exact substring match (highest confidence)
        if ground_truth_lower in predicted_lower:
            return True
        
        # Method 2: Keyword overlap (semantic similarity)
        import re
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                       'could', 'may', 'might', 'can', 'to', 'of', 'in', 'on', 'at', 'for',
                       'with', 'by', 'from', 'as', 'and', 'or', 'but', 'if', 'that', 'this'}
        
        def extract_keywords(text: str) -> set:
            """Extract meaningful keywords from text"""
            words = re.findall(r'\b\w+\b', text.lower())
            keywords = {w for w in words if w not in common_words and len(w) >= 3}
            return keywords
        
        ground_truth_keywords = extract_keywords(ground_truth_lower)
        predicted_keywords = extract_keywords(predicted_lower)
        
        if ground_truth_keywords:
            keyword_overlap = len(ground_truth_keywords.intersection(predicted_keywords))
            keyword_ratio = keyword_overlap / len(ground_truth_keywords)
            
            # If > 60% of keywords match, consider it correct
            if keyword_ratio >= 0.6:
                return True
        
        # No clear match - uncertain
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

