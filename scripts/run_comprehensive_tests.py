#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run comprehensive test suite with thousands of questions
Tests StillMe with diverse questions and collects feedback
"""

import json
import asyncio
import aiohttp
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
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
# IMPORTANT: Change this to your backend URL!
# - Local: "http://localhost:8000"
# - Railway: "https://stillme-backend-production.up.railway.app"
# - Or set via environment variable: STILLME_API_BASE
API_BASE = "https://stillme-backend-production.up.railway.app"  # Change this

# Test suite file
TEST_SUITE_FILE = Path(__file__).parent.parent / "tests" / "data" / "comprehensive_test_suite.json"

# Results file
RESULTS_DIR = Path(__file__).parent.parent / "tests" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


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
    max_questions: Optional[int] = None,
    save_interval: int = 100,
) -> List[Dict]:
    """
    Run tests on multiple questions concurrently
    
    Args:
        questions: List of question dicts
        max_concurrent: Maximum concurrent requests
        max_questions: Maximum number of questions to test (None = all)
        save_interval: Save results every N questions
        
    Returns:
        List of test results
    """
    if max_questions:
        questions = questions[:max_questions]
    
    results = []
    results_file = RESULTS_DIR / f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
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


def analyze_results(results: List[Dict]) -> Dict:
    """Analyze test results and generate statistics"""
    total = len(results)
    success = sum(1 for r in results if r.get("status") == "success")
    errors = sum(1 for r in results if r.get("status") == "error")
    timeouts = sum(1 for r in results if r.get("status") == "timeout")
    
    if success > 0:
        avg_latency = sum(r.get("latency", 0) for r in results if r.get("status") == "success") / success
        avg_confidence = sum(r.get("confidence_score", 0) for r in results if r.get("status") == "success") / success
    else:
        avg_latency = 0
        avg_confidence = 0
    
    # Group by category
    by_category = {}
    for r in results:
        if r.get("status") == "success":
            cat = r.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "success": 0, "avg_confidence": 0}
            by_category[cat]["total"] += 1
            by_category[cat]["success"] += 1
            by_category[cat]["avg_confidence"] += r.get("confidence_score", 0)
    
    for cat in by_category:
        if by_category[cat]["total"] > 0:
            by_category[cat]["avg_confidence"] /= by_category[cat]["total"]
    
    return {
        "total": total,
        "success": success,
        "errors": errors,
        "timeouts": timeouts,
        "success_rate": (success / total * 100) if total > 0 else 0,
        "avg_latency": avg_latency,
        "avg_confidence": avg_confidence,
        "by_category": by_category,
    }


def main():
    """Main test runner"""
    # Check API_BASE
    if API_BASE == "http://localhost:8000":
        print("⚠️  WARNING: API_BASE is set to localhost:8000")
        print("   If your backend is deployed on Railway, set STILLME_API_BASE environment variable:")
        print("   set STILLME_API_BASE=https://stillme-backend-production.up.railway.app")
        print("   Or edit scripts/run_comprehensive_tests.py and change API_BASE")
        print()
        try:
            response = input("Continue with localhost:8000? (y/n): ")
            if response.lower() != 'y':
                print("Exiting. Please set STILLME_API_BASE environment variable or edit the script.")
                return
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode, just continue
            pass
    
    # Load test suite
    if not TEST_SUITE_FILE.exists():
        logger.error(f"Test suite file not found: {TEST_SUITE_FILE}")
        logger.info("Run scripts/generate_test_suite.py first to generate test questions")
        return
    
    with open(TEST_SUITE_FILE, "r", encoding="utf-8") as f:
        test_suite = json.load(f)
    
    questions = test_suite["questions"]
    logger.info(f"Loaded {len(questions)} test questions")
    
    # Run tests
    print("\n" + "="*60)
    print("StillMe Comprehensive Test Suite")
    print("="*60)
    print(f"Total questions: {len(questions)}")
    print(f"API Base: {API_BASE}")
    print(f"Max concurrent: 10")
    print("="*60)
    print("\n[TEST] Testing API connection...")
    
    # Test API connection first
    try:
        import requests
        test_response = requests.get(f"{API_BASE}/api/status", timeout=30)
        if test_response.status_code == 200:
            print(f"[OK] API connection successful!")
        else:
            print(f"[WARN] API returned status {test_response.status_code}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print(f"\nPlease check:")
        print(f"  1. Backend is running at {API_BASE}")
        print(f"  2. If deployed on Railway, set STILLME_API_BASE environment variable")
        print(f"  3. Network/firewall is not blocking the connection")
        return
    
    print("="*60 + "\n")
    
    results = asyncio.run(run_tests(questions, max_concurrent=10, max_questions=None))
    
    # Analyze results
    stats = analyze_results(results)
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']} ({stats['success_rate']:.1f}%)")
    print(f"Errors: {stats['errors']}")
    print(f"Timeouts: {stats['timeouts']}")
    print(f"Avg Latency: {stats['avg_latency']:.2f}s")
    print(f"Avg Confidence: {stats['avg_confidence']:.2f}")
    print("\nBy Category:")
    for cat, cat_stats in stats["by_category"].items():
        print(f"  {cat}: {cat_stats['success']}/{cat_stats['total']} ({cat_stats['avg_confidence']:.2f} confidence)")
    print("="*60)


if __name__ == "__main__":
    main()

