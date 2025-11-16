#!/usr/bin/env python3
"""
Run system comparison only (for testing with new API keys)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
# Note: Environment variables set directly (e.g., $env:OPENAI_API_KEY) take precedence
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        # Load .env but don't override existing environment variables
        # This means if you set $env:OPENAI_API_KEY in PowerShell, it will be used instead
        load_dotenv(env_path, override=False)
        print(f"✅ Loaded .env file from: {env_path}")
        print("   (Environment variables set directly take precedence)")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        # Try to load from current directory
        load_dotenv(override=False)
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
    print("   Install with: pip install python-dotenv")
    print("   Or set environment variables directly in PowerShell")

import json
import logging
from evaluation.comparison import SystemComparator
from evaluation.truthfulqa import TruthfulQAEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_comparison(
    api_url: str,
    output_dir: str = "data/evaluation/results",
    num_questions: int = 50
):
    """
    Run system comparison only
    
    Args:
        api_url: StillMe API URL
        output_dir: Output directory for results
        num_questions: Number of questions to use for comparison
    """
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("System Comparison Only")
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
    
    # Run comparison
    comparator = SystemComparator(stillme_api_url=api_url)
    
    # Determine which systems to compare
    systems_to_compare = ["stillme", "vanilla_rag"]
    
    if os.getenv("OPENAI_API_KEY"):
        systems_to_compare.append("chatgpt")
        logger.info("✅ OpenAI API key found - will compare with ChatGPT")
    else:
        logger.warning("⚠️  OPENAI_API_KEY not set - skipping ChatGPT")
    
    if os.getenv("DEEPSEEK_API_KEY"):
        systems_to_compare.append("deepseek")
        logger.info("✅ DEEPSEEK_API_KEY found - will compare with DeepSeek")
    else:
        logger.warning("⚠️  DEEPSEEK_API_KEY not set - skipping DeepSeek")
    
    if os.getenv("OPENROUTER_API_KEY"):
        systems_to_compare.append("openrouter")
        logger.info("✅ OPENROUTER_API_KEY found - will compare with OpenRouter")
    else:
        logger.warning("⚠️  OPENROUTER_API_KEY not set - skipping OpenRouter")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        systems_to_compare.append("claude")
        logger.info("✅ ANTHROPIC_API_KEY found - will compare with Claude")
    else:
        logger.warning("⚠️  ANTHROPIC_API_KEY not set - skipping Claude")
    
    logger.info("")
    logger.info(f"Comparing systems: {', '.join(systems_to_compare)}")
    logger.info("This may take a while...")
    logger.info("")
    
    comparison_results = comparator.compare_systems(
        questions=comparison_questions,
        systems=systems_to_compare
    )
    
    # Generate comparison report
    report_path = os.path.join(output_dir, "comparison_report.md")
    report = comparator.generate_comparison_report(
        comparison_results,
        output_path=report_path
    )
    
    # Save detailed results
    results_dict = {name: r.to_dict() for name, r in comparison_results.items()}
    results_path = os.path.join(output_dir, "comparison_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("System Comparison Results")
    logger.info("=" * 80)
    logger.info("")
    
    for system_name, system_results in comparison_results.items():
        logger.info(f"{system_name.upper()}:")
        logger.info(f"  Accuracy: {system_results.accuracy:.2%}")
        logger.info(f"  Hallucination Rate: {system_results.hallucination_rate:.2%}")
        logger.info(f"  Citation Rate: {system_results.citation_rate:.2%}")
        logger.info(f"  Uncertainty Rate: {system_results.uncertainty_rate:.2%}")
        logger.info(f"  Validation Pass Rate: {system_results.validation_pass_rate:.2%}")
        
        transparency_score = (
            system_results.citation_rate * 0.4 +
            system_results.uncertainty_rate * 0.3 +
            system_results.validation_pass_rate * 0.3
        )
        logger.info(f"  Transparency Score: {transparency_score:.2%}")
        logger.info("")
    
    logger.info(f"Comparison Report saved to: {report_path}")
    logger.info(f"Detailed results saved to: {results_path}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("Comparison Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run system comparison only")
    parser.add_argument(
        "--api-url",
        type=str,
        default="https://stillme-backend-production.up.railway.app",
        help="StillMe API base URL"
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
        default=50,
        help="Number of questions to use for comparison"
    )
    
    args = parser.parse_args()
    
    try:
        run_comparison(
            api_url=args.api_url,
            output_dir=args.output_dir,
            num_questions=args.num_questions
        )
    except KeyboardInterrupt:
        logger.info("\nComparison interrupted by user")
    except Exception as e:
        logger.error(f"Comparison error: {e}", exc_info=True)

