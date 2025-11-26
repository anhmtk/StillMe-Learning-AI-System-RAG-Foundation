"""
Run Quick Evaluations - Fast Test Suite (Skip TruthfulQA)

This script runs the faster evaluation benchmarks:
1. HaluEval (hallucination detection) - 3 questions
2. Citation Rate Validation (custom tests) - ~16 questions
3. Hallucination Reduction (custom tests) - 7 questions
4. Vectara HHEM (industry standard, optional)

Estimated time: ~30-40 minutes

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

# Support both local and Railway testing
API_URL = os.getenv("STILLME_API_URL", "http://localhost:8000")
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
    """Run quick evaluations (skip TruthfulQA)"""
    logger.info("=" * 60)
    logger.info("STILLME QUICK EVALUATION SUITE")
    logger.info("(Skipping TruthfulQA - 790 questions, ~26 hours)")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Estimated time: ~30-40 minutes")
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
        "halu_eval": False,
        "citation_rate": False,
        "hallucination_reduction": False,
        "vectara_hhem": False
    }
    
    start_time = time.time()
    
    # 1. HaluEval Evaluation (3 questions, ~6 minutes)
    logger.info("")
    logger.info("📊 HaluEval: 3 questions, estimated ~6 minutes")
    results["halu_eval"] = run_command(
        [sys.executable, "-m", "evaluation.run_evaluation", "--benchmarks", "halu_eval"],
        "HaluEval Benchmark (Hallucination Detection)"
    )
    
    # 2. Citation Rate Validation (~16 questions, ~10-15 minutes)
    logger.info("")
    logger.info("📊 Citation Rate: ~16 questions, estimated ~10-15 minutes")
    results["citation_rate"] = run_command(
        [sys.executable, "scripts/test_citation_rate_validation.py"],
        "Citation Rate Validation Test"
    )
    
    # 3. Hallucination Reduction Test (7 questions, ~7-10 minutes)
    logger.info("")
    logger.info("📊 Hallucination Reduction: 7 questions, estimated ~7-10 minutes")
    results["hallucination_reduction"] = run_command(
        [sys.executable, "scripts/test_hallucination_reduction.py"],
        "Hallucination Reduction Test"
    )
    
    # 4. Vectara HHEM (Optional - requires transformers)
    logger.info("")
    logger.info("Checking if Vectara HHEM is available...")
    try:
        import transformers
        logger.info("✅ transformers library available")
        logger.info("📊 Vectara HHEM: estimated ~5-10 minutes")
        results["vectara_hhem"] = run_command(
            [sys.executable, "scripts/test_vectara_hhem.py"],
            "Vectara HHEM Evaluation (Industry Standard)"
        )
    except ImportError:
        logger.warning("⚠️  transformers library not available, skipping Vectara HHEM")
        logger.info("   Install with: pip install transformers torch")
        results["vectara_hhem"] = None
    
    elapsed_time = time.time() - start_time
    elapsed_minutes = elapsed_time / 60
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("QUICK EVALUATION SUMMARY")
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
    logger.info(f"⏱️  Total time: {elapsed_minutes:.1f} minutes ({elapsed_time:.0f} seconds)")
    logger.info("")
    logger.info("Results saved to: data/evaluation/")
    logger.info("")
    
    # Count successes
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    logger.info(f"Total: {passed}/{total} evaluations passed")
    
    if passed == total:
        logger.info("🎉 All quick evaluations completed successfully!")
        logger.info("")
        logger.info("💡 To run TruthfulQA (790 questions, ~26 hours), use:")
        logger.info("   python scripts/run_all_evaluations.py")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} evaluation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

