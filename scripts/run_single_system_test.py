#!/usr/bin/env python3
"""
Run evaluation for a single system (for testing individual systems)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env file from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
    print("   Install with: pip install python-dotenv")

import json
import logging
from evaluation.comparison import SystemComparator
from evaluation.truthfulqa import TruthfulQAEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_single_system(
    system_name: str,
    api_url: str,
    output_dir: str = "data/evaluation/results",
    num_questions: int = 20
):
    """
    Run evaluation for a single system
    
    Args:
        system_name: System to evaluate (stillme, vanilla_rag, chatgpt, deepseek, openrouter)
        api_url: StillMe API URL (for stillme/vanilla_rag)
        output_dir: Output directory for results
        num_questions: Number of questions to use
    """
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info(f"Single System Evaluation: {system_name.upper()}")
    logger.info("=" * 80)
    logger.info(f"API URL: {api_url}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Number of Questions: {num_questions}")
    logger.info("")
    
    # Load questions from TruthfulQA dataset
    evaluator = TruthfulQAEvaluator(api_base_url=api_url)
    all_questions = evaluator.load_dataset()
    
    # Use subset
    questions = all_questions[:num_questions]
    logger.info(f"Using {len(questions)} questions from TruthfulQA dataset")
    logger.info("")
    
    # Convert to comparison format
    comparison_questions = [
        {
            "question": q.get("question", ""),
            "correct_answer": q.get("correct_answer", "")
        }
        for q in questions
    ]
    
    # Run evaluation
    comparator = SystemComparator(stillme_api_url=api_url)
    
    logger.info(f"Evaluating {system_name}...")
    logger.info("This may take a while...")
    logger.info("")
    
    # Evaluate single system
    if system_name == "stillme":
        results = comparator._evaluate_stillme(comparison_questions)
    elif system_name == "vanilla_rag":
        results = comparator._evaluate_vanilla_rag(comparison_questions)
    elif system_name == "chatgpt":
        results = comparator._evaluate_chatgpt(comparison_questions)
    elif system_name == "deepseek":
        results = comparator._evaluate_deepseek(comparison_questions)
    elif system_name == "openrouter":
        results = comparator._evaluate_openrouter(comparison_questions)
    elif system_name == "claude":
        results = comparator._evaluate_claude(comparison_questions)
    else:
        logger.error(f"Unknown system: {system_name}")
        logger.info("Available systems: stillme, vanilla_rag, chatgpt, deepseek, openrouter, claude")
        return
    
    # Save results
    results_path = os.path.join(output_dir, f"{system_name}_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results.to_dict(), f, indent=2)
    
    # Print results
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"{system_name.upper()} Results")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Total Questions: {results.total_questions}")
    logger.info(f"Correct Answers: {results.correct_answers}")
    logger.info(f"Accuracy: {results.accuracy:.2%}")
    logger.info(f"Hallucination Rate: {results.hallucination_rate:.2%}")
    logger.info(f"Citation Rate: {results.citation_rate:.2%}")
    logger.info(f"Uncertainty Rate: {results.uncertainty_rate:.2%}")
    logger.info(f"Validation Pass Rate: {results.validation_pass_rate:.2%}")
    
    transparency_score = (
        results.citation_rate * 0.4 +
        results.uncertainty_rate * 0.3 +
        results.validation_pass_rate * 0.3
    )
    logger.info(f"Transparency Score: {transparency_score:.2%}")
    logger.info("")
    logger.info(f"Results saved to: {results_path}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("Evaluation Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluation for a single system")
    parser.add_argument(
        "system",
        type=str,
        choices=["stillme", "vanilla_rag", "chatgpt", "deepseek", "openrouter", "claude"],
        help="System to evaluate"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="https://stillme-backend-production.up.railway.app",
        help="StillMe API base URL (for stillme/vanilla_rag)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/evaluation/results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=20,
        help="Number of questions to use"
    )
    
    args = parser.parse_args()
    
    try:
        run_single_system(
            system_name=args.system,
            api_url=args.api_url,
            output_dir=args.output_dir,
            num_questions=args.num_questions
        )
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)

