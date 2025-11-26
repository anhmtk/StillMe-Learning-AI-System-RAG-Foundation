#!/usr/bin/env python3
"""
Quick Evaluation Test - 10 Questions

Run a small evaluation with 10 questions to verify everything works
before running the full evaluation suite.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import logging
import requests
from evaluation.truthfulqa import TruthfulQAEvaluator
from evaluation.halu_eval import HaluEvalEvaluator
from evaluation.metrics import MetricsCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_backend_health(api_url: str = "http://localhost:8000") -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Backend health check failed: {e}")
        return False


def run_quick_evaluation(api_url: str = "http://localhost:8000", num_questions: int = 10):
    """Run quick evaluation with limited questions"""
    
    logger.info("=" * 60)
    logger.info("StillMe Quick Evaluation Test - 10 Questions")
    logger.info("=" * 60)
    logger.info(f"API URL: {api_url}")
    logger.info(f"Number of questions: {num_questions}")
    logger.info("")
    
    # Check backend
    if not check_backend_health(api_url):
        logger.error("❌ Backend is not running!")
        logger.error("Please start the backend first:")
        logger.error("  python start_backend.py")
        logger.error("  OR")
        logger.error("  .\\scripts\\start_api.ps1")
        return 1
    
    logger.info("✅ Backend is running")
    logger.info("")
    
    # Sample questions (10 questions covering different topics)
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
        },
        {
            "question": "Who wrote the novel '1984'?",
            "correct_answer": "George Orwell",
            "incorrect_answers": ["Aldous Huxley", "Ray Bradbury", "H.G. Wells"]
        },
        {
            "question": "What is the chemical symbol for gold?",
            "correct_answer": "Au",
            "incorrect_answers": ["Go", "Gd", "Ag"]
        },
        {
            "question": "What is the smallest prime number?",
            "correct_answer": "2",
            "incorrect_answers": ["1", "3", "0"]
        },
        {
            "question": "What is the capital of Japan?",
            "correct_answer": "Tokyo",
            "incorrect_answers": ["Osaka", "Kyoto", "Seoul"]
        },
        {
            "question": "What is the boiling point of water at sea level?",
            "correct_answer": "100 degrees Celsius",
            "incorrect_answers": ["90 degrees Celsius", "110 degrees Celsius", "212 degrees Fahrenheit"]
        },
        {
            "question": "What is the largest ocean on Earth?",
            "correct_answer": "Pacific Ocean",
            "incorrect_answers": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean"]
        }
    ]
    
    # Limit to requested number
    questions = sample_questions[:num_questions]
    
    logger.info(f"📊 Running TruthfulQA Evaluation ({len(questions)} questions)...")
    logger.info("")
    
    # 1. TruthfulQA Evaluation
    truthfulqa_evaluator = TruthfulQAEvaluator(api_base_url=api_url)
    truthfulqa_results = truthfulqa_evaluator.evaluate(questions=questions)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("TruthfulQA Results")
    logger.info("=" * 60)
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
    
    # Summary
    logger.info("=" * 60)
    logger.info("Quick Evaluation Summary")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"✅ Tested {len(questions)} questions")
    logger.info(f"✅ Accuracy: {truthfulqa_results.accuracy:.2%}")
    logger.info(f"✅ Transparency Score: {transparency_score:.2%}")
    logger.info(f"⚠️  Hallucination Rate: {truthfulqa_results.hallucination_rate:.2%}")
    logger.info("")
    
    if truthfulqa_results.accuracy >= 0.7 and truthfulqa_results.hallucination_rate <= 0.2:
        logger.info("✅ Results look good! You can proceed with full evaluation:")
        logger.info("   python scripts/run_all_evaluations.py")
    else:
        logger.warning("⚠️  Results may need improvement. Check backend logs for issues.")
    
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run quick evaluation with 10 questions")
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="StillMe API base URL"
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=10,
        help="Number of questions to test (default: 10)"
    )
    
    args = parser.parse_args()
    
    try:
        sys.exit(run_quick_evaluation(args.api_url, args.num_questions))
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        sys.exit(1)

