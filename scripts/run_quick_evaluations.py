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


def warmup_railway(api_url: str) -> bool:
    """
    Warmup Railway service before running evaluations.
    This helps avoid cold start delays during actual tests.
    """
    logger.info("🔥 Warming up Railway service (to avoid cold start delays)...")
    
    try:
        # Health check first
        health_url = f"{api_url}/health"
        try:
            response = requests.get(health_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"⚠️ Health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Health check error: {e}")
            return False
        
        # Warmup request (simple question to wake up the service)
        chat_url = f"{api_url}/api/chat/rag"
        payload = {
            "message": "Hello",
            "use_rag": False,  # Skip RAG for faster warmup
            "user_id": "warmup_bot"
        }
        
        try:
            logger.info("   Sending warmup request...")
            response = requests.post(chat_url, json=payload, timeout=60)
            if response.status_code == 200:
                logger.info("✅ Railway service warmed up successfully")
                return True
            else:
                logger.warning(f"⚠️ Warmup request failed: HTTP {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Warmup request timed out (service may be slow, but continuing)")
            return True  # Continue anyway - service might just be slow
        except Exception as e:
            logger.warning(f"⚠️ Warmup request error: {e}")
            return True  # Continue anyway - warmup is optional
    
    except Exception as e:
        logger.warning(f"⚠️ Warmup failed: {e}, continuing anyway")
        return True  # Continue anyway - warmup is optional


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
    logger.info("=" * 60)
    logger.info(f"API URL: {API_URL}")
    logger.info("(Skipping TruthfulQA - 790 questions, ~26 hours)")
    logger.info("")
    logger.info("Estimated time: ~30-40 minutes")
    
    # Show helpful message about API URL source
    if "localhost" in API_URL:
        logger.info("💡 To test Railway, set STILLME_API_URL in .env file or environment variable:")
        logger.info("   Option 1: Add to .env file: STILLME_API_URL=https://stillme-backend-production.up.railway.app")
        logger.info("   Option 2: Set env var: $env:STILLME_API_URL='https://stillme-backend-production.up.railway.app'")
    else:
        logger.info(f"✅ Using Railway backend: {API_URL}")
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
    
    # Warmup Railway service (if not localhost) to avoid cold start delays
    if "localhost" not in API_URL and "127.0.0.1" not in API_URL:
        logger.info("")
        warmup_railway(API_URL)
        logger.info("")
    
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

