"""
Run All Evaluations - Comprehensive Test Suite

This script runs all evaluation benchmarks and tests:
1. TruthfulQA (research standard)
2. HaluEval (hallucination detection)
3. Citation Rate Validation (custom tests)
4. Hallucination Reduction (custom tests)
5. Vectara HHEM (industry standard, optional)

Prerequisites:
- Backend must be running on localhost:8000
- Install dependencies: pip install transformers torch aiohttp
"""

import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"
API_HEALTH_ENDPOINT = f"{API_URL}/health"
MAX_WAIT_TIME = 60  # seconds


def check_backend_health() -> bool:
    """Check if backend is running and healthy"""
    try:
        response = requests.get(API_HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Backend health check failed: {e}")
        return False


def wait_for_backend(max_wait: int = MAX_WAIT_TIME) -> bool:
    """Wait for backend to be ready"""
    logger.info("Waiting for backend to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if check_backend_health():
            logger.info("✅ Backend is ready!")
            return True
        time.sleep(2)
        logger.info("⏳ Backend not ready yet, waiting...")
    
    logger.error("❌ Backend did not become ready in time")
    return False


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status"""
    logger.info("=" * 60)
    logger.info(f"Running: {description}")
    logger.info("=" * 60)
    logger.info(f"Command: {' '.join(command)}")
    logger.info("")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )
        logger.info("")
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("")
        logger.error(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run all evaluations"""
    logger.info("=" * 60)
    logger.info("STILLME COMPREHENSIVE EVALUATION SUITE")
    logger.info("=" * 60)
    logger.info("")
    
    # Check if backend is running
    if not check_backend_health():
        logger.warning("⚠️  Backend is not running!")
        logger.info("")
        logger.info("Please start the backend first:")
        logger.info("  Option 1: python start_backend.py")
        logger.info("  Option 2: .\\scripts\\start_api.ps1")
        logger.info("")
        
        response = input("Do you want to start the backend now? (y/n): ")
        if response.lower() == 'y':
            logger.info("Starting backend...")
            # Try to start backend
            try:
                backend_process = subprocess.Popen(
                    [sys.executable, "start_backend.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Backend process started (PID: {backend_process.pid})")
                logger.info("Waiting for backend to be ready...")
                
                if not wait_for_backend():
                    logger.error("❌ Failed to start backend")
                    return 1
            except Exception as e:
                logger.error(f"❌ Failed to start backend: {e}")
                return 1
        else:
            logger.error("❌ Cannot proceed without backend")
            return 1
    
    # Ensure output directory exists
    os.makedirs("data/evaluation", exist_ok=True)
    
    results = {
        "truthfulqa": False,
        "halu_eval": False,
        "citation_rate": False,
        "hallucination_reduction": False,
        "vectara_hhem": False
    }
    
    # 1. TruthfulQA Evaluation
    logger.info("")
    results["truthfulqa"] = run_command(
        [sys.executable, "-m", "evaluation.run_evaluation", "--benchmarks", "truthfulqa"],
        "TruthfulQA Benchmark (Research Standard)"
    )
    
    # 2. HaluEval Evaluation
    logger.info("")
    results["halu_eval"] = run_command(
        [sys.executable, "-m", "evaluation.run_evaluation", "--benchmarks", "halu_eval"],
        "HaluEval Benchmark (Hallucination Detection)"
    )
    
    # 3. Citation Rate Validation
    logger.info("")
    results["citation_rate"] = run_command(
        [sys.executable, "scripts/test_citation_rate_validation.py"],
        "Citation Rate Validation Test"
    )
    
    # 4. Hallucination Reduction Test
    logger.info("")
    results["hallucination_reduction"] = run_command(
        [sys.executable, "scripts/test_hallucination_reduction.py"],
        "Hallucination Reduction Test"
    )
    
    # 5. Vectara HHEM (Optional - requires transformers)
    logger.info("")
    logger.info("Checking if Vectara HHEM is available...")
    try:
        import transformers
        logger.info("✅ transformers library available")
        results["vectara_hhem"] = run_command(
            [sys.executable, "scripts/test_vectara_hhem.py"],
            "Vectara HHEM Evaluation (Industry Standard)"
        )
    except ImportError:
        logger.warning("⚠️  transformers library not available, skipping Vectara HHEM")
        logger.info("   Install with: pip install transformers torch")
        results["vectara_hhem"] = None
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.info("")
    
    for test_name, success in results.items():
        if success is None:
            status = "⏭️  SKIPPED"
        elif success:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        logger.info(f"{test_name:30s} {status}")
    
    logger.info("")
    logger.info("Results saved to: data/evaluation/")
    logger.info("")
    
    # Count successes
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    logger.info(f"Total: {passed}/{total} evaluations passed")
    
    if passed == total:
        logger.info("🎉 All evaluations completed successfully!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} evaluation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())




