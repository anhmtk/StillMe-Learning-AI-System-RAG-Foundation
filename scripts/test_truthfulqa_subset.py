#!/usr/bin/env python3
"""
Test TruthfulQA with a small subset (10-20 questions) for quick validation
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.truthfulqa import TruthfulQAEvaluator
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Loaded .env file from: {env_path}")
    else:
        load_dotenv()
except ImportError:
    logger.debug("python-dotenv not installed, using environment variables only")

# Get API URL
API_URL = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))
if API_URL and not API_URL.startswith(("http://", "https://")):
    API_URL = f"https://{API_URL}"

def main():
    """Run TruthfulQA evaluation on a small subset"""
    
    logger.info("=" * 80)
    logger.info("TRUTHFULQA SUBSET TEST (10-20 questions)")
    logger.info("=" * 80)
    logger.info(f"API URL: {API_URL}")
    logger.info("")
    
    # Create evaluator
    evaluator = TruthfulQAEvaluator(api_base_url=API_URL)
    
    # Load full dataset
    all_questions = evaluator.load_dataset()
    logger.info(f"Loaded {len(all_questions)} questions from dataset")
    
    # Select first 20 questions for quick test
    test_questions = all_questions[:20]
    logger.info(f"Testing with {len(test_questions)} questions (subset)")
    logger.info("")
    
    # Run evaluation
    results = evaluator.evaluate(questions=test_questions)
    
    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Questions: {results.total_questions}")
    logger.info(f"Correct Answers: {results.correct_answers} ({results.accuracy:.1%})")
    logger.info(f"Incorrect Answers: {sum(1 for r in results.detailed_results if r.is_correct is False)}")
    logger.info(f"Uncertain Answers: {sum(1 for r in results.detailed_results if r.is_correct is None)}")
    logger.info(f"Hallucination Rate: {results.hallucination_rate:.1%}")
    logger.info(f"Citation Rate: {results.citation_rate:.1%}")
    logger.info(f"Uncertainty Rate: {results.uncertainty_rate:.1%}")
    logger.info(f"Validation Pass Rate: {results.validation_pass_rate:.1%}")
    logger.info("")
    
    # Show sample responses
    logger.info("=" * 80)
    logger.info("SAMPLE RESPONSES (First 5)")
    logger.info("=" * 80)
    logger.info("")
    
    for i, result in enumerate(results.detailed_results[:5], 1):
        logger.info(f"Question {i}: {result.question[:60]}...")
        logger.info(f"  Ground Truth: {result.ground_truth[:80]}")
        logger.info(f"  Predicted (first 200 chars): {result.predicted_answer[:200]}...")
        logger.info(f"  Is Correct: {result.is_correct}")
        logger.info(f"  Has Citation: {result.has_citation}")
        logger.info(f"  Has Uncertainty: {result.has_uncertainty}")
        logger.info("")
    
    # Analyze verbose responses
    logger.info("=" * 80)
    logger.info("VERBOSE RESPONSE ANALYSIS")
    logger.info("=" * 80)
    logger.info("")
    
    verbose_count = 0
    direct_count = 0
    
    for result in results.detailed_results:
        predicted_lower = result.predicted_answer.lower()
        # Check if response starts with disclaimer
        if any(phrase in predicted_lower[:100] for phrase in [
            "i don't have sufficient information",
            "mình không có đủ thông tin",
            "the retrieved context has low relevance",
            "ngữ cảnh được tìm thấy có độ liên quan thấp"
        ]):
            verbose_count += 1
        else:
            direct_count += 1
    
    logger.info(f"Responses starting with disclaimer: {verbose_count} ({verbose_count/len(results.detailed_results)*100:.1f}%)")
    logger.info(f"Responses starting directly: {direct_count} ({direct_count/len(results.detailed_results)*100:.1f}%)")
    logger.info("")
    
    if verbose_count > direct_count:
        logger.warning("⚠️  Most responses still start with disclaimers - prompt improvement may not be working")
        logger.info("   Possible reasons:")
        logger.info("   1. Instruction may be placed too late in the prompt")
        logger.info("   2. LLM may be prioritizing caution over directness")
        logger.info("   3. Instruction may need to be more prominent/emphasized")
    else:
        logger.info("✅ Most responses start directly - prompt improvement is working!")
    
    # Save results
    output_path = project_root / "data/evaluation/results/truthfulqa_subset_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results.to_dict(), f, indent=2, ensure_ascii=False)
    
    logger.info("")
    logger.info(f"✅ Results saved to: {output_path}")
    logger.info("")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

