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

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Loaded .env file from: {env_path}")
    else:
        logger.debug(f"⚠️  .env file not found at: {env_path}, using environment variables only")
        load_dotenv()  # Try to load from current directory
except ImportError:
    logger.debug("⚠️  python-dotenv not installed, skipping .env file loading")
    logger.debug("   Install with: pip install python-dotenv")
except Exception as e:
    logger.debug(f"⚠️  Error loading .env file: {e}")

# Support both local and Railway testing
# Priority: 1. Environment variable, 2. .env file, 3. Default localhost
API_URL = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))

# Ensure URL has protocol if missing
if API_URL and not API_URL.startswith(("http://", "https://")):
    API_URL = f"https://{API_URL}"

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
    
    # 1. TruthfulQA Evaluation (~790 questions, estimated ~26-30 hours)
    logger.info("")
    logger.info("📊 TruthfulQA: ~790 questions, estimated ~26-30 hours")
    logger.info("   ⚠️  This will take a very long time. Make sure:")
    logger.info("      - Your computer stays on and doesn't sleep")
    logger.info("      - Network connection is stable")
    logger.info("      - You can monitor progress via logs")
    logger.info("")
    results["truthfulqa"] = run_command(
        [sys.executable, "-m", "evaluation.run_evaluation", "--benchmarks", "truthfulqa", "--api-url", API_URL],
        "TruthfulQA Benchmark (Research Standard)"
    )
    
    # Add delay between test suites to avoid rate limiting
    if "localhost" not in API_URL:
        logger.info("")
        logger.info("⏳ Waiting 60s before next test suite to reset rate limit counter...")
        time.sleep(60)
    
    # 2. HaluEval Evaluation (3 questions, ~6 minutes)
    logger.info("")
    logger.info("📊 HaluEval: 3 questions, estimated ~6 minutes")
    results["halu_eval"] = run_command(
        [sys.executable, "-m", "evaluation.run_evaluation", "--benchmarks", "halu_eval", "--api-url", API_URL],
        "HaluEval Benchmark (Hallucination Detection)"
    )
    
    # Add delay between test suites to avoid rate limiting
    if "localhost" not in API_URL:
        logger.info("")
        logger.info("⏳ Waiting 60s before next test suite to reset rate limit counter...")
        time.sleep(60)
    
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




