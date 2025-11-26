#!/usr/bin/env python3
"""
Main evaluation script for StillMe

Runs comprehensive evaluation including:
- TruthfulQA benchmark
- HaluEval benchmark
- System comparison (StillMe vs baselines)
- Transparency study (if data available)
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from .truthfulqa import TruthfulQAEvaluator
from .halu_eval import HaluEvalEvaluator
from .comparison import SystemComparator
from .transparency_study import TransparencyStudy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_truthfulqa_evaluation(api_url: str, output_dir: str) -> Dict[str, Any]:
    """Run TruthfulQA evaluation"""
    logger.info("=" * 60)
    logger.info("Running TruthfulQA Evaluation")
    logger.info("=" * 60)
    
    evaluator = TruthfulQAEvaluator(api_base_url=api_url)
    results = evaluator.evaluate()
    
    # Save results
    output_path = os.path.join(output_dir, "truthfulqa_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results.to_dict(), f, indent=2)
    
    logger.info(f"TruthfulQA Results:")
    logger.info(f"  Accuracy: {results.accuracy:.2%}")
    logger.info(f"  Hallucination Rate: {results.hallucination_rate:.2%}")
    logger.info(f"  Transparency Score: {results.citation_rate * 0.4 + results.uncertainty_rate * 0.3 + results.validation_pass_rate * 0.3:.2%}")
    logger.info(f"  Results saved to: {output_path}")
    
    return results.to_dict()


def run_halu_eval_evaluation(api_url: str, output_dir: str) -> Dict[str, Any]:
    """Run HaluEval evaluation"""
    logger.info("=" * 60)
    logger.info("Running HaluEval Evaluation")
    logger.info("=" * 60)
    
    evaluator = HaluEvalEvaluator(api_base_url=api_url)
    results = evaluator.evaluate()
    
    # Save results
    output_path = os.path.join(output_dir, "halu_eval_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results.to_dict(), f, indent=2)
    
    logger.info(f"HaluEval Results:")
    logger.info(f"  Accuracy: {results.accuracy:.2%}")
    logger.info(f"  Hallucination Rate: {results.hallucination_rate:.2%}")
    logger.info(f"  Results saved to: {output_path}")
    
    return results.to_dict()


def run_system_comparison(api_url: str, output_dir: str, questions: list = None) -> Dict[str, Any]:
    """Run system comparison"""
    logger.info("=" * 60)
    logger.info("Running System Comparison")
    logger.info("=" * 60)
    
    if questions is None:
        # Use sample questions
        questions = [
            {"question": "What is the capital of France?", "correct_answer": "Paris"},
            {"question": "What is 2+2?", "correct_answer": "4"},
            {"question": "What is the largest planet in our solar system?", "correct_answer": "Jupiter"}
        ]
    
    comparator = SystemComparator(stillme_api_url=api_url)
    results = comparator.compare_systems(questions)
    
    # Generate report
    report_path = os.path.join(output_dir, "comparison_report.md")
    report = comparator.generate_comparison_report(results, output_path=report_path)
    
    logger.info(f"Comparison Report saved to: {report_path}")
    
    # Save detailed results
    results_dict = {name: r.to_dict() for name, r in results.items()}
    results_path = os.path.join(output_dir, "comparison_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)
    
    return results_dict


def run_transparency_study(output_dir: str) -> Dict[str, Any]:
    """Run transparency study analysis"""
    logger.info("=" * 60)
    logger.info("Running Transparency Study Analysis")
    logger.info("=" * 60)
    
    study = TransparencyStudy()
    results = study.get_results()
    
    if results.total_responses == 0:
        logger.warning("No transparency study data available")
        return {}
    
    # Generate report
    report_path = os.path.join(output_dir, "transparency_study_report.md")
    report = study.generate_study_report(output_path=report_path)
    
    logger.info(f"Transparency Study Report saved to: {report_path}")
    
    return results.to_dict()


def main():
    """Main evaluation runner"""
    # Load environment variables from .env file if available
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()  # Try to load from current directory
    except ImportError:
        pass  # python-dotenv not installed, skip
    except Exception:
        pass  # Error loading .env, continue with environment variables
    
    # Get API URL from environment variable if available
    default_api_url = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))
    # Ensure URL has protocol if missing
    if default_api_url and not default_api_url.startswith(("http://", "https://")):
        default_api_url = f"https://{default_api_url}"
    
    parser = argparse.ArgumentParser(description="Run StillMe comprehensive evaluation")
    parser.add_argument(
        "--api-url",
        type=str,
        default=default_api_url,
        help=f"StillMe API base URL (default: from STILLME_API_URL env var or {default_api_url})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/evaluation/results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--benchmarks",
        nargs="+",
        choices=["truthfulqa", "halu_eval", "comparison", "transparency"],
        default=["truthfulqa", "halu_eval", "comparison"],
        help="Benchmarks to run"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    all_results = {}
    
    # Run selected benchmarks
    if "truthfulqa" in args.benchmarks:
        all_results["truthfulqa"] = run_truthfulqa_evaluation(args.api_url, args.output_dir)
    
    if "halu_eval" in args.benchmarks:
        all_results["halu_eval"] = run_halu_eval_evaluation(args.api_url, args.output_dir)
    
    if "comparison" in args.benchmarks:
        all_results["comparison"] = run_system_comparison(args.api_url, args.output_dir)
    
    if "transparency" in args.benchmarks:
        all_results["transparency_study"] = run_transparency_study(args.output_dir)
    
    # Save aggregated results
    summary_path = os.path.join(args.output_dir, "evaluation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("Evaluation Complete!")
    logger.info(f"All results saved to: {args.output_dir}")
    logger.info(f"Summary saved to: {summary_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

