#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test only failed/problematic questions from previous test run
Extracts questions with low confidence, missing citation, or language mismatch
"""

import json
import asyncio
import aiohttp
import time
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
import logging

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
API_BASE = os.getenv("STILLME_API_BASE", "https://stillme-backend-production.up.railway.app")

# Test suite file
TEST_SUITE_FILE = Path(__file__).parent.parent / "tests" / "data" / "comprehensive_test_suite.json"

# Results file
RESULTS_DIR = Path(__file__).parent.parent / "tests" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Pattern to match citations
CITE_RE = re.compile(r"\[(\d+)\]")


def extract_problematic_questions(result_file: Path) -> Set[str]:
    """
    Extract question IDs that had problems in previous test
    
    Args:
        result_file: Path to previous test result JSON file
        
    Returns:
        Set of question IDs that had problems
    """
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    problematic_ids = set()
    
    for result in results:
        if result.get('status') != 'success':
            problematic_ids.add(result.get('question_id'))
            continue
        
        confidence = result.get('confidence_score', 1.0)
        validation_info = result.get('validation_info', {})
        reasons = validation_info.get('reasons', [])
        context_docs_count = validation_info.get('context_docs_count', 0)
        response = result.get('response', '')
        
        # Check for low confidence
        if confidence < 0.8:
            problematic_ids.add(result.get('question_id'))
            logger.debug(f"Low confidence: {result.get('question_id')} (confidence: {confidence})")
            continue
        
        # Check for missing citation when context is available
        if context_docs_count > 0:
            has_citation = bool(CITE_RE.search(response))
            if not has_citation:
                problematic_ids.add(result.get('question_id'))
                logger.debug(f"Missing citation: {result.get('question_id')} (context docs: {context_docs_count})")
                continue
        
        # Check for language mismatch
        if any('language_mismatch' in r for r in reasons):
            problematic_ids.add(result.get('question_id'))
            logger.debug(f"Language mismatch: {result.get('question_id')}")
            continue
    
    return problematic_ids


async def test_question(session: aiohttp.ClientSession, question: Dict, timeout: int = 300) -> Dict:
    """
    Test a single question and get StillMe's response
    
    Args:
        session: aiohttp session
        question: Question dict with id, question, category, difficulty, language
        timeout: Request timeout in seconds
        
    Returns:
        Dict with question, response, timing, and metadata
    """
    try:
        start_time = time.time()
        
        async with session.post(
            f"{API_BASE}/api/chat/rag",
            json={
                "message": question["question"],
                "use_rag": True,
                "context_limit": 3,
            },
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            if response.status == 200:
                data = await response.json()
                elapsed = time.time() - start_time
                
                return {
                    "question_id": question["id"],
                    "question": question["question"],
                    "category": question.get("category", "unknown"),
                    "difficulty": question.get("difficulty", "unknown"),
                    "language": question.get("language", "unknown"),
                    "sensitive": question.get("sensitive", False),
                    "response": data.get("response", ""),
                    "confidence_score": data.get("confidence_score", 0.0),
                    "validation_info": data.get("validation_info", {}),
                    "processing_steps": data.get("processing_steps", []),
                    "latency": elapsed,
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                error_text = await response.text()
                return {
                    "question_id": question["id"],
                    "question": question["question"],
                    "status": "error",
                    "error": f"HTTP {response.status}: {error_text}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
    except asyncio.TimeoutError:
        return {
            "question_id": question["id"],
            "question": question["question"],
            "status": "timeout",
            "error": f"Request timed out after {timeout}s",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "question_id": question["id"],
            "question": question["question"],
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


async def run_tests(
    questions: List[Dict],
    max_concurrent: int = 10,
    save_interval: int = 50,
) -> List[Dict]:
    """
    Run tests on multiple questions concurrently
    
    Args:
        questions: List of question dicts
        max_concurrent: Maximum concurrent requests
        save_interval: Save results every N questions
        
    Returns:
        List of test results
    """
    results = []
    results_file = RESULTS_DIR / f"failed_questions_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def test_with_semaphore(question: Dict):
        async with semaphore:
            return await test_question(session, question)
    
    async with aiohttp.ClientSession() as session:
        # Test questions in batches
        total = len(questions)
        for i in range(0, total, max_concurrent):
            batch = questions[i:i + max_concurrent]
            logger.info(f"Testing batch {i//max_concurrent + 1}/{(total + max_concurrent - 1)//max_concurrent} ({i+1}-{min(i+max_concurrent, total)}/{total})")
            
            batch_results = await asyncio.gather(*[test_with_semaphore(q) for q in batch])
            results.extend(batch_results)
            
            # Save intermediate results
            if len(results) % save_interval == 0:
                with open(results_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(results)} results to {results_file}")
    
    # Final save
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Completed testing {len(results)} questions")
    logger.info(f"   Results saved to: {results_file}")
    
    return results


def compare_results(old_results: List[Dict], new_results: List[Dict]) -> Dict:
    """
    Compare old and new test results
    
    Args:
        old_results: Results from previous test
        new_results: Results from new test
        
    Returns:
        Comparison statistics
    """
    # Create lookup dicts
    old_by_id = {r.get('question_id'): r for r in old_results}
    new_by_id = {r.get('question_id'): r for r in new_results}
    
    improved = []
    worsened = []
    unchanged = []
    
    for question_id in old_by_id.keys():
        if question_id not in new_by_id:
            continue
        
        old_result = old_by_id[question_id]
        new_result = new_by_id[question_id]
        
        if old_result.get('status') != 'success' or new_result.get('status') != 'success':
            continue
        
        old_conf = old_result.get('confidence_score', 0)
        new_conf = new_result.get('confidence_score', 0)
        
        old_validation = old_result.get('validation_info', {})
        new_validation = new_result.get('validation_info', {})
        
        old_reasons = old_validation.get('reasons', [])
        new_reasons = new_validation.get('reasons', [])
        
        old_has_citation = bool(CITE_RE.search(old_result.get('response', '')))
        new_has_citation = bool(CITE_RE.search(new_result.get('response', '')))
        
        old_has_lang_mismatch = any('language_mismatch' in r for r in old_reasons)
        new_has_lang_mismatch = any('language_mismatch' in r for r in new_reasons)
        
        # Check improvements
        improved_conf = new_conf >= 0.8 and old_conf < 0.8
        improved_citation = new_has_citation and not old_has_citation
        improved_lang = not new_has_lang_mismatch and old_has_lang_mismatch
        
        # Check worsening
        worsened_conf = new_conf < 0.8 and old_conf >= 0.8
        worsened_citation = not new_has_citation and old_has_citation
        worsened_lang = new_has_lang_mismatch and not old_has_lang_mismatch
        
        if improved_conf or improved_citation or improved_lang:
            improved.append({
                'question_id': question_id,
                'old_conf': old_conf,
                'new_conf': new_conf,
                'old_citation': old_has_citation,
                'new_citation': new_has_citation,
                'old_lang': old_has_lang_mismatch,
                'new_lang': new_has_lang_mismatch,
            })
        elif worsened_conf or worsened_citation or worsened_lang:
            worsened.append({
                'question_id': question_id,
                'old_conf': old_conf,
                'new_conf': new_conf,
                'old_citation': old_has_citation,
                'new_citation': new_has_citation,
                'old_lang': old_has_lang_mismatch,
                'new_lang': new_has_lang_mismatch,
            })
        else:
            unchanged.append(question_id)
    
    return {
        'improved': improved,
        'worsened': worsened,
        'unchanged': unchanged,
        'total': len(old_by_id),
    }


def main():
    """Main test runner"""
    import argparse
    
    global API_BASE
    
    parser = argparse.ArgumentParser(description="Test only failed/problematic questions from previous test")
    parser.add_argument(
        '--previous-result',
        type=str,
        default=None,
        help='Path to previous test result JSON file (default: latest comprehensive_test_*.json)'
    )
    parser.add_argument(
        '--api-base',
        type=str,
        default=API_BASE,
        help=f'API base URL (default: {API_BASE})'
    )
    args = parser.parse_args()
    
    API_BASE = args.api_base
    
    # Find previous result file
    if args.previous_result:
        previous_result_file = Path(args.previous_result)
    else:
        # Find latest comprehensive test result
        result_files = sorted(RESULTS_DIR.glob("comprehensive_test_*.json"), reverse=True)
        if not result_files:
            logger.error("No previous test result found!")
            logger.info("Please specify --previous-result or run comprehensive test first")
            return
        previous_result_file = result_files[0]
        logger.info(f"Using previous result: {previous_result_file.name}")
    
    if not previous_result_file.exists():
        logger.error(f"Previous result file not found: {previous_result_file}")
        return
    
    # Extract problematic question IDs
    logger.info("Extracting problematic questions from previous test...")
    problematic_ids = extract_problematic_questions(previous_result_file)
    logger.info(f"Found {len(problematic_ids)} problematic questions")
    
    if len(problematic_ids) == 0:
        logger.info("No problematic questions found! All questions passed.")
        return
    
    # Load test suite
    if not TEST_SUITE_FILE.exists():
        logger.error(f"Test suite file not found: {TEST_SUITE_FILE}")
        logger.info("Run scripts/generate_test_suite.py first to generate test questions")
        return
    
    with open(TEST_SUITE_FILE, "r", encoding="utf-8") as f:
        test_suite = json.load(f)
    
    # Filter questions to only problematic ones
    all_questions = test_suite["questions"]
    questions_to_test = [q for q in all_questions if q.get("id") in problematic_ids]
    
    logger.info(f"Found {len(questions_to_test)} questions to test (out of {len(all_questions)} total)")
    
    if len(questions_to_test) == 0:
        logger.warning("No matching questions found in test suite!")
        logger.info(f"Problematic IDs: {list(problematic_ids)[:10]}...")
        return
    
    # Test API connection
    print("\n" + "="*60)
    print("StillMe Failed Questions Test")
    print("="*60)
    print(f"Total problematic questions: {len(questions_to_test)}")
    print(f"API Base: {API_BASE}")
    print(f"Max concurrent: 10")
    print("="*60)
    print("\n[TEST] Testing API connection...")
    
    try:
        import requests
        test_response = requests.get(f"{API_BASE}/api/status", timeout=30)
        if test_response.status_code == 200:
            print(f"[OK] API connection successful!")
        else:
            print(f"[WARN] API returned status {test_response.status_code}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    print("="*60 + "\n")
    
    # Run tests
    new_results = asyncio.run(run_tests(questions_to_test, max_concurrent=10))
    
    # Load old results for comparison
    with open(previous_result_file, 'r', encoding='utf-8') as f:
        old_results = json.load(f)
    
    # Filter old results to only problematic ones
    old_problematic = [r for r in old_results if r.get('question_id') in problematic_ids]
    
    # Compare results
    comparison = compare_results(old_problematic, new_results)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    print(f"Total tested: {len(new_results)}")
    success = sum(1 for r in new_results if r.get('status') == 'success')
    print(f"Success: {success} ({success/len(new_results)*100:.1f}%)")
    
    if success > 0:
        avg_conf = sum(r.get('confidence_score', 0) for r in new_results if r.get('status') == 'success') / success
        print(f"Avg Confidence: {avg_conf:.2f}")
    
    print("\n" + "="*60)
    print("Improvement Analysis")
    print("="*60)
    print(f"Improved: {len(comparison['improved'])} questions")
    print(f"Worsened: {len(comparison['worsened'])} questions")
    print(f"Unchanged: {len(comparison['unchanged'])} questions")
    
    if comparison['improved']:
        print("\n✅ Improved Questions:")
        for item in comparison['improved'][:10]:  # Show first 10
            print(f"  - {item['question_id']}: conf {item['old_conf']:.2f}→{item['new_conf']:.2f}, "
                  f"citation {item['old_citation']}→{item['new_citation']}, "
                  f"lang {item['old_lang']}→{item['new_lang']}")
    
    if comparison['worsened']:
        print("\n⚠️ Worsened Questions:")
        for item in comparison['worsened'][:10]:  # Show first 10
            print(f"  - {item['question_id']}: conf {item['old_conf']:.2f}→{item['new_conf']:.2f}, "
                  f"citation {item['old_citation']}→{item['new_citation']}, "
                  f"lang {item['old_lang']}→{item['new_lang']}")
    
    print("="*60)


if __name__ == "__main__":
    main()

