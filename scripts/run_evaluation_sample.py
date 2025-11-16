#!/usr/bin/env python3
"""
Run StillMe evaluation with sample questions

Quick evaluation script using sample questions (no need to download full datasets)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import logging
from evaluation.truthfulqa import TruthfulQAEvaluator
from evaluation.halu_eval import HaluEvalEvaluator
from evaluation.comparison import SystemComparator
from evaluation.metrics import MetricsCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_sample_evaluation(api_url: str = "http://localhost:8000"):
    """Run evaluation with sample questions"""
    
    logger.info("=" * 60)
    logger.info("StillMe Evaluation - Sample Questions")
    logger.info("=" * 60)
    logger.info(f"API URL: {api_url}")
    logger.info("")
    
    # Sample questions for testing
    sample_questions = [
        {
            "question": "What is the capital of France?",
            "correct_answer": "Paris",
            "incorrect_answers": ["London", "Berlin", "Madrid"]
        },
        {
            "question": "What is 2+2?",
            "correct_answer": "4",
            "incorrect_answers": ["5", "3", "6"]
        },
        {
            "question": "What is the largest planet in our solar system?",
            "correct_answer": "Jupiter",
            "incorrect_answers": ["Saturn", "Earth", "Mars"]
        },
        {
            "question": "What is the speed of light in vacuum?",
            "correct_answer": "299,792,458 meters per second",
            "incorrect_answers": ["300,000,000 m/s", "150,000 km/s"]
        }
    ]
    
    # 1. TruthfulQA Evaluation
    logger.info("📊 Running TruthfulQA Evaluation (Sample Questions)...")
    logger.info("")
    
    truthfulqa_evaluator = TruthfulQAEvaluator(api_base_url=api_url)
    truthfulqa_results = truthfulqa_evaluator.evaluate(questions=sample_questions)
    
    logger.info("")
    logger.info("TruthfulQA Results:")
    logger.info(f"  ✅ Accuracy: {truthfulqa_results.accuracy:.2%}")
    logger.info(f"  ⚠️  Hallucination Rate: {truthfulqa_results.hallucination_rate:.2%}")
    logger.info(f"  📝 Citation Rate: {truthfulqa_results.citation_rate:.2%}")
    logger.info(f"  ❓ Uncertainty Rate: {truthfulqa_results.uncertainty_rate:.2%}")
    logger.info(f"  ✅ Validation Pass Rate: {truthfulqa_results.validation_pass_rate:.2%}")
    
    transparency_score = (
        truthfulqa_results.citation_rate * 0.4 +
        truthfulqa_results.uncertainty_rate * 0.3 +
        truthfulqa_results.validation_pass_rate * 0.3
    )
    logger.info(f"  🔍 Transparency Score: {transparency_score:.2%}")
    logger.info("")
    
    # 2. HaluEval Evaluation
    logger.info("📊 Running HaluEval Evaluation (Sample Questions)...")
    logger.info("")
    
    halu_eval_questions = [
        {
            "question": "What is the population of a fictional city?",
            "answer": "The population is 10 million",
            "is_hallucination": True,
            "context": "No context available"
        },
        {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "is_hallucination": False,
            "context": "Paris is the capital of France"
        }
    ]
    
    halu_evaluator = HaluEvalEvaluator(api_base_url=api_url)
    halu_results = halu_evaluator.evaluate(questions=halu_eval_questions)
    
    logger.info("")
    logger.info("HaluEval Results:")
    logger.info(f"  ✅ Accuracy: {halu_results.accuracy:.2%}")
    logger.info(f"  ⚠️  Hallucination Rate: {halu_results.hallucination_rate:.2%}")
    logger.info("")
    
    # 3. System Comparison (StillMe only for now)
    logger.info("📊 Running System Comparison...")
    logger.info("")
    
    comparator = SystemComparator(stillme_api_url=api_url)
    
    # Compare StillMe with vanilla RAG (if possible)
    comparison_questions = sample_questions[:3]  # Use first 3 for comparison
    
    logger.info("Evaluating StillMe (Full RAG + Validation)...")
    stillme_results = comparator._evaluate_stillme(comparison_questions)
    
    logger.info("Evaluating Vanilla RAG (No Validation)...")
    vanilla_results = comparator._evaluate_vanilla_rag(comparison_questions)
    
    logger.info("")
    logger.info("System Comparison Results:")
    logger.info("")
    logger.info("StillMe (Full RAG + Validation):")
    logger.info(f"  ✅ Accuracy: {stillme_results.accuracy:.2%}")
    logger.info(f"  ⚠️  Hallucination Rate: {stillme_results.hallucination_rate:.2%}")
    logger.info(f"  🔍 Transparency Score: {stillme_results.citation_rate * 0.4 + stillme_results.uncertainty_rate * 0.3 + stillme_results.validation_pass_rate * 0.3:.2%}")
    logger.info("")
    logger.info("Vanilla RAG (No Validation):")
    logger.info(f"  ✅ Accuracy: {vanilla_results.accuracy:.2%}")
    logger.info(f"  ⚠️  Hallucination Rate: {vanilla_results.hallucination_rate:.2%}")
    logger.info(f"  🔍 Transparency Score: {vanilla_results.citation_rate * 0.4 + vanilla_results.uncertainty_rate * 0.3 + vanilla_results.validation_pass_rate * 0.3:.2%}")
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("Evaluation Summary")
    logger.info("=" * 60)
    logger.info("")
    logger.info("✅ StillMe demonstrates:")
    logger.info(f"   - {truthfulqa_results.accuracy:.2%} accuracy on factual questions")
    logger.info(f"   - {transparency_score:.2%} transparency score (citations + uncertainty + validation)")
    logger.info(f"   - {truthfulqa_results.hallucination_rate:.2%} hallucination rate")
    logger.info("")
    logger.info("📊 Next Steps:")
    logger.info("   1. Download full datasets: python scripts/download_benchmark_datasets.py")
    logger.info("   2. Run full evaluation: python -m evaluation.run_evaluation")
    logger.info("   3. Collect user study data: Open evaluation/survey_form.html")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run StillMe evaluation with sample questions")
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="StillMe API base URL"
    )
    
    args = parser.parse_args()
    
    try:
        run_sample_evaluation(args.api_url)
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)

