#!/usr/bin/env python3
"""
Run full evaluation for paper publication

Runs comprehensive evaluation with TruthfulQA and system comparison
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
from datetime import datetime
from evaluation.truthfulqa import TruthfulQAEvaluator
from evaluation.comparison import SystemComparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_full_evaluation(
    api_url: str,
    output_dir: str = "data/evaluation/results",
    max_questions: int = None,
    run_comparison: bool = True
):
    """
    Run full evaluation for paper
    
    Args:
        api_url: StillMe API URL
        output_dir: Output directory for results
        max_questions: Maximum questions to evaluate (None = all)
        run_comparison: Whether to run system comparison
    """
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("StillMe Full Evaluation for Paper Publication")
    logger.info("=" * 80)
    logger.info(f"API URL: {api_url}")
    logger.info(f"Output Directory: {output_dir}")
    if max_questions:
        logger.info(f"Max Questions: {max_questions} (subset for testing)")
    else:
        logger.info("Max Questions: ALL (full dataset)")
    logger.info("")
    
    # 1. TruthfulQA Evaluation
    logger.info("=" * 80)
    logger.info("STEP 1: TruthfulQA Benchmark Evaluation")
    logger.info("=" * 80)
    
    evaluator = TruthfulQAEvaluator(api_base_url=api_url)
    
    # Load dataset
    questions = evaluator.load_dataset()
    logger.info(f"Loaded {len(questions)} questions from TruthfulQA dataset")
    
    # Limit questions if specified
    if max_questions and max_questions < len(questions):
        questions = questions[:max_questions]
        logger.info(f"Using subset: {len(questions)} questions for evaluation")
    
    # Check for resume option (skip already processed questions)
    resume_from = os.getenv("RESUME_FROM_QUESTION", None)
    if resume_from:
        try:
            resume_index = int(resume_from) - 1  # Convert to 0-based index
            if 0 <= resume_index < len(questions):
                logger.info(f"Resuming from question {resume_from} (index {resume_index})...")
                questions = questions[resume_index:]
                logger.info(f"Remaining questions: {len(questions)}")
            else:
                logger.warning(f"Invalid resume index {resume_index}, starting from beginning")
        except ValueError:
            logger.warning(f"Invalid RESUME_FROM_QUESTION value: {resume_from}, starting from beginning")
    
    # Run evaluation
    logger.info(f"Starting evaluation on {len(questions)} questions...")
    logger.info("This may take a while (approximately 15-20 seconds per question)...")
    logger.info("")
    
    try:
        results = evaluator.evaluate(questions=questions)
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        logger.error("Evaluation failed, but partial results may be available")
        raise
    
    # Save results (with suffix if resuming)
    if resume_from:
        truthfulqa_path = os.path.join(output_dir, f"truthfulqa_results_part2.json")
        logger.info(f"Saving partial results (from question {resume_from}) to: {truthfulqa_path}")
    else:
        truthfulqa_path = os.path.join(output_dir, "truthfulqa_results.json")
    
    with open(truthfulqa_path, 'w', encoding='utf-8') as f:
        json.dump(results.to_dict(), f, indent=2)
    
    logger.info(f"Results saved to: {truthfulqa_path}")
    
    # If resuming, suggest merging with previous results
    if resume_from:
        logger.info("")
        logger.info("=" * 80)
        logger.info("NOTE: This is a partial result (resumed from question {})".format(resume_from))
        logger.info("To merge with previous results, run:")
        logger.info("  python scripts/merge_evaluation_results.py --auto")
        logger.info("=" * 80)
    
    # Calculate transparency score
    transparency_score = (
        results.citation_rate * 0.4 +
        results.uncertainty_rate * 0.3 +
        results.validation_pass_rate * 0.3
    )
    
    logger.info("")
    logger.info("TruthfulQA Results:")
    logger.info(f"  Total Questions: {results.total_questions}")
    logger.info(f"  Correct Answers: {results.correct_answers}")
    logger.info(f"  Accuracy: {results.accuracy:.2%}")
    logger.info(f"  Hallucination Rate: {results.hallucination_rate:.2%}")
    logger.info(f"  Citation Rate: {results.citation_rate:.2%}")
    logger.info(f"  Uncertainty Rate: {results.uncertainty_rate:.2%}")
    logger.info(f"  Validation Pass Rate: {results.validation_pass_rate:.2%}")
    logger.info(f"  Transparency Score: {transparency_score:.2%}")
    logger.info(f"  Results saved to: {truthfulqa_path}")
    logger.info("")
    
    # 2. System Comparison (if requested)
    if run_comparison:
        logger.info("=" * 80)
        logger.info("STEP 2: System Comparison")
        logger.info("=" * 80)
        logger.info("Comparing StillMe with baseline systems...")
        logger.info("")
        
        # Use subset of questions for comparison (to save time and API costs)
        comparison_questions = questions[:min(50, len(questions))]
        logger.info(f"Using {len(comparison_questions)} questions for system comparison")
        logger.info("")
        
        comparator = SystemComparator(stillme_api_url=api_url)
        
        # Compare systems
        systems_to_compare = ["stillme", "vanilla_rag"]
        
        # Add ChatGPT and Claude if API keys are available
        if os.getenv("OPENAI_API_KEY"):
            systems_to_compare.append("chatgpt")
        if os.getenv("ANTHROPIC_API_KEY"):
            systems_to_compare.append("claude")
        
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
        logger.info("System Comparison Results:")
        for system_name, system_results in comparison_results.items():
            logger.info(f"  {system_name}:")
            logger.info(f"    Accuracy: {system_results.accuracy:.2%}")
            logger.info(f"    Hallucination Rate: {system_results.hallucination_rate:.2%}")
            logger.info("")
        
        logger.info(f"Comparison Report saved to: {report_path}")
        logger.info(f"Detailed results saved to: {results_path}")
        logger.info("")
    
    # 3. Generate Summary Report
    logger.info("=" * 80)
    logger.info("STEP 3: Generating Summary Report")
    logger.info("=" * 80)
    
    summary = {
        "evaluation_date": datetime.now().isoformat(),
        "api_url": api_url,
        "truthfulqa": {
            "total_questions": results.total_questions,
            "correct_answers": results.correct_answers,
            "accuracy": results.accuracy,
            "hallucination_rate": results.hallucination_rate,
            "citation_rate": results.citation_rate,
            "uncertainty_rate": results.uncertainty_rate,
            "validation_pass_rate": results.validation_pass_rate,
            "transparency_score": transparency_score
        }
    }
    
    if run_comparison:
        summary["comparison"] = {
            name: {
                "accuracy": r.accuracy,
                "hallucination_rate": r.hallucination_rate,
                "citation_rate": r.citation_rate,
                "uncertainty_rate": r.uncertainty_rate,
                "validation_pass_rate": r.validation_pass_rate
            }
            for name, r in comparison_results.items()
        }
    
    summary_path = os.path.join(output_dir, "evaluation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Generate markdown summary
    summary_md_path = os.path.join(output_dir, "evaluation_summary.md")
    with open(summary_md_path, 'w', encoding='utf-8') as f:
        f.write("# StillMe Evaluation Summary\n\n")
        f.write(f"**Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**API URL**: {api_url}\n\n")
        
        f.write("## TruthfulQA Benchmark Results\n\n")
        f.write(f"- **Total Questions**: {results.total_questions}\n")
        f.write(f"- **Correct Answers**: {results.correct_answers}\n")
        f.write(f"- **Accuracy**: {results.accuracy:.2%}\n")
        f.write(f"- **Hallucination Rate**: {results.hallucination_rate:.2%}\n")
        f.write(f"- **Citation Rate**: {results.citation_rate:.2%}\n")
        f.write(f"- **Uncertainty Rate**: {results.uncertainty_rate:.2%}\n")
        f.write(f"- **Validation Pass Rate**: {results.validation_pass_rate:.2%}\n")
        f.write(f"- **Transparency Score**: {transparency_score:.2%}\n\n")
        
        if run_comparison:
            f.write("## System Comparison\n\n")
            f.write("| System | Accuracy | Hallucination Rate | Citation Rate | Uncertainty Rate | Validation Pass Rate |\n")
            f.write("|--------|----------|-------------------|---------------|-----------------|---------------------|\n")
            for name, r in comparison_results.items():
                f.write(f"| {name} | {r.accuracy:.2%} | {r.hallucination_rate:.2%} | {r.citation_rate:.2%} | {r.uncertainty_rate:.2%} | {r.validation_pass_rate:.2%} |\n")
            f.write("\n")
    
    logger.info(f"Summary saved to: {summary_path}")
    logger.info(f"Markdown summary saved to: {summary_md_path}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("Evaluation Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Results are ready for paper publication:")
    logger.info(f"  - TruthfulQA results: {truthfulqa_path}")
    if run_comparison:
        logger.info(f"  - Comparison report: {report_path}")
    logger.info(f"  - Summary: {summary_path}")
    logger.info("")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run full evaluation for paper publication")
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
        "--max-questions",
        type=int,
        default=None,
        help="Maximum questions to evaluate (for testing, None = all)"
    )
    parser.add_argument(
        "--no-comparison",
        action="store_true",
        help="Skip system comparison"
    )
    
    args = parser.parse_args()
    
    try:
        run_full_evaluation(
            api_url=args.api_url,
            output_dir=args.output_dir,
            max_questions=args.max_questions,
            run_comparison=not args.no_comparison
        )
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)

