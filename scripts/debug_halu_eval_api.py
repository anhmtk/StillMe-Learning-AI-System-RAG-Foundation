"""
Debug HaluEval API Calls - Direct API Testing

This script tests HaluEval questions directly against the StillMe API
to debug why fallback messages are being returned.

Usage:
    python scripts/debug_halu_eval_api.py
"""

import os
import sys
import json
import requests
import time
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
project_root = Path(__file__).parent.parent
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
except Exception as e:
    logger.debug(f"Error loading .env file: {e}")

# API Configuration
API_BASE_URL = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))
if API_BASE_URL and not API_BASE_URL.startswith(("http://", "https://")):
    API_BASE_URL = f"https://{API_BASE_URL}"

CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat/rag"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# HaluEval Questions
HALUEVAL_QUESTIONS = [
    {
        "question": "What is the population of a fictional city?",
        "answer": "The population is 10 million",
        "is_hallucination": True,
        "context": "No context available"
    },
    {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "is_hallucination": False,
        "context": "Paris is the capital of France"
    },
    {
        "question": "What is the speed of light in a vacuum?",
        "answer": "299,792,458 meters per second",
        "is_hallucination": False,
        "context": "The speed of light in vacuum is 299,792,458 m/s"
    }
]

# Control Questions (known to work from Citation Rate test)
CONTROL_QUESTIONS = [
    "What is the capital of France?",
    "What is the speed of light?",
    "Who wrote '1984'?"
]


def is_fallback_message(text: str) -> bool:
    """Detect if response is a fallback message"""
    if not text or len(text.strip()) < 50:
        return False
    
    text_lower = text.lower()
    fallback_patterns = [
        "stillme is experiencing a technical issue",
        "stillme đang gặp sự cố kỹ thuật",
        "i cannot provide a good answer",
        "mình không thể trả lời tốt",
        "cannot provide a good answer to this question with the current configuration",
        "i will suggest to the developer",
        "mình sẽ đề xuất cho developer",
    ]
    
    return any(pattern in text_lower for pattern in fallback_patterns)


def test_api_health() -> bool:
    """Test API health endpoint"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            logger.info("✅ API health check passed")
            return True
        else:
            logger.warning(f"⚠️  API health check returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API health check failed: {e}")
        return False


def test_control_question(question: str) -> Dict[str, Any]:
    """Test a control question (known to work)"""
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"🧪 CONTROL TEST: {question}")
    logger.info("=" * 80)
    
    payload = {
        "message": question,
        "user_id": "debug_bot",
        "use_rag": True,
        "context_limit": 3,
        "use_server_keys": True
    }
    
    try:
        start_time = time.time()
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=180)
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️  Response time: {elapsed_time:.2f}s")
        logger.info(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"   Response: {response.text[:500]}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text[:500]
            }
        
        data = response.json()
        response_text = data.get("response", "")
        validation_info = data.get("validation_info", {})
        confidence_score = data.get("confidence_score", 0.0)
        used_fallback = validation_info.get("used_fallback", False)
        validation_passed = validation_info.get("passed", False)
        
        is_fallback = is_fallback_message(response_text)
        
        logger.info(f"📝 Response length: {len(response_text)} chars")
        logger.info(f"📊 Confidence score: {confidence_score}")
        logger.info(f"✅ Validation passed: {validation_passed}")
        logger.info(f"🔄 Used fallback: {used_fallback}")
        logger.info(f"⚠️  Is fallback message: {is_fallback}")
        
        # Check for citations
        import re
        has_citation = bool(re.search(r'\[(?:general knowledge|\d+)\]', response_text, re.IGNORECASE))
        logger.info(f"📚 Has citation: {has_citation}")
        
        # Log validation info details
        if validation_info:
            logger.info(f"📋 Validation info keys: {list(validation_info.keys())}")
            if "reasons" in validation_info:
                logger.info(f"   Reasons: {validation_info['reasons']}")
            if "context_docs_count" in validation_info:
                logger.info(f"   Context docs: {validation_info['context_docs_count']}")
        
        # Log response preview
        logger.info("")
        logger.info("📄 Response preview (first 500 chars):")
        logger.info("-" * 80)
        logger.info(response_text[:500])
        logger.info("-" * 80)
        
        if is_fallback or used_fallback:
            logger.warning("⚠️  ⚠️  ⚠️  FALLBACK MESSAGE DETECTED ⚠️  ⚠️  ⚠️")
            logger.warning(f"   Full response: {response_text}")
        
        return {
            "success": True,
            "response": response_text,
            "validation_info": validation_info,
            "confidence_score": confidence_score,
            "used_fallback": used_fallback,
            "is_fallback": is_fallback,
            "has_citation": has_citation,
            "elapsed_time": elapsed_time
        }
        
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout (180s)")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def test_halu_eval_question(qa_pair: Dict[str, Any]) -> Dict[str, Any]:
    """Test a HaluEval question"""
    question = qa_pair.get("question", "")
    expected_answer = qa_pair.get("answer", "")
    is_hallucination = qa_pair.get("is_hallucination", False)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"🔍 HALUEVAL TEST: {question}")
    logger.info(f"   Expected answer: {expected_answer}")
    logger.info(f"   Is hallucination: {is_hallucination}")
    logger.info("=" * 80)
    
    payload = {
        "message": question,
        "user_id": "debug_bot",
        "use_rag": True,
        "context_limit": 3,
        "use_server_keys": True
    }
    
    try:
        start_time = time.time()
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=180)
        elapsed_time = time.time() - start_time
        
        logger.info(f"⏱️  Response time: {elapsed_time:.2f}s")
        logger.info(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"   Response: {response.text[:500]}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text[:500]
            }
        
        data = response.json()
        response_text = data.get("response", "")
        validation_info = data.get("validation_info", {})
        confidence_score = data.get("confidence_score", 0.0)
        used_fallback = validation_info.get("used_fallback", False)
        validation_passed = validation_info.get("passed", False)
        processing_steps = data.get("processing_steps", [])
        
        is_fallback = is_fallback_message(response_text)
        
        logger.info(f"📝 Response length: {len(response_text)} chars")
        logger.info(f"📊 Confidence score: {confidence_score}")
        logger.info(f"✅ Validation passed: {validation_passed}")
        logger.info(f"🔄 Used fallback: {used_fallback}")
        logger.info(f"⚠️  Is fallback message: {is_fallback}")
        
        # Log processing steps
        if processing_steps:
            logger.info(f"🔧 Processing steps ({len(processing_steps)}):")
            for step in processing_steps:
                logger.info(f"   - {step}")
        
        # Check for citations
        import re
        has_citation = bool(re.search(r'\[(?:general knowledge|\d+)\]', response_text, re.IGNORECASE))
        logger.info(f"📚 Has citation: {has_citation}")
        
        # Log validation info details
        if validation_info:
            logger.info(f"📋 Validation info:")
            for key, value in validation_info.items():
                if key != "reasons":  # Reasons might be long
                    logger.info(f"   {key}: {value}")
            if "reasons" in validation_info:
                reasons = validation_info["reasons"]
                if isinstance(reasons, list):
                    logger.info(f"   reasons ({len(reasons)}): {reasons[:3]}...")  # First 3
                else:
                    logger.info(f"   reasons: {reasons}")
        
        # Log full response
        logger.info("")
        logger.info("📄 Full response:")
        logger.info("-" * 80)
        logger.info(response_text)
        logger.info("-" * 80)
        
        if is_fallback or used_fallback:
            logger.error("")
            logger.error("❌ ❌ ❌ FALLBACK MESSAGE DETECTED ❌ ❌ ❌")
            logger.error("")
            logger.error("🔍 DEBUGGING INFO:")
            logger.error(f"   Question: {question}")
            logger.error(f"   Response length: {len(response_text)}")
            logger.error(f"   Used fallback (from validation_info): {used_fallback}")
            logger.error(f"   Is fallback (from text detection): {is_fallback}")
            logger.error(f"   Validation passed: {validation_passed}")
            logger.error(f"   Confidence score: {confidence_score}")
            if validation_info:
                logger.error(f"   Validation info: {json.dumps(validation_info, indent=2)}")
        
        return {
            "success": True,
            "question": question,
            "response": response_text,
            "validation_info": validation_info,
            "confidence_score": confidence_score,
            "used_fallback": used_fallback,
            "is_fallback": is_fallback,
            "has_citation": has_citation,
            "validation_passed": validation_passed,
            "elapsed_time": elapsed_time,
            "processing_steps": processing_steps
        }
        
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout (180s)")
        return {"success": False, "error": "Timeout", "question": question}
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "question": question}


def main():
    """Main debug function"""
    logger.info("=" * 80)
    logger.info("🔍 HALUVAL API DEBUG SCRIPT")
    logger.info("=" * 80)
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info(f"Chat Endpoint: {CHAT_ENDPOINT}")
    logger.info("")
    
    # Health check
    if not test_api_health():
        logger.error("❌ API health check failed. Please check if backend is running.")
        return 1
    
    logger.info("")
    
    # Test control questions first (known to work)
    logger.info("🧪 STEP 1: Testing Control Questions (known to work)")
    logger.info("")
    control_results = []
    for question in CONTROL_QUESTIONS:
        result = test_control_question(question)
        control_results.append(result)
        time.sleep(2)  # Delay between requests
    
    # Analyze control results
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 CONTROL QUESTIONS SUMMARY")
    logger.info("=" * 80)
    successful = sum(1 for r in control_results if r.get("success"))
    fallback_count = sum(1 for r in control_results if r.get("is_fallback") or r.get("used_fallback"))
    logger.info(f"✅ Successful: {successful}/{len(control_results)}")
    logger.info(f"⚠️  Fallback messages: {fallback_count}/{len(control_results)}")
    
    if fallback_count > 0:
        logger.warning("⚠️  WARNING: Control questions also returning fallback messages!")
        logger.warning("   This suggests a backend-wide issue, not specific to HaluEval questions.")
    else:
        logger.info("✅ Control questions working correctly - issue is specific to HaluEval")
    
    logger.info("")
    time.sleep(3)  # Longer delay before HaluEval tests
    
    # Test HaluEval questions
    logger.info("🔍 STEP 2: Testing HaluEval Questions")
    logger.info("")
    halu_eval_results = []
    for i, qa_pair in enumerate(HALUEVAL_QUESTIONS):
        logger.info(f"📌 HaluEval Question {i+1}/{len(HALUEVAL_QUESTIONS)}")
        result = test_halu_eval_question(qa_pair)
        halu_eval_results.append(result)
        if i < len(HALUEVAL_QUESTIONS) - 1:
            time.sleep(3)  # Delay between requests
    
    # Analyze HaluEval results
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 HALUEVAL QUESTIONS SUMMARY")
    logger.info("=" * 80)
    successful = sum(1 for r in halu_eval_results if r.get("success"))
    fallback_count = sum(1 for r in halu_eval_results if r.get("is_fallback") or r.get("used_fallback"))
    citation_count = sum(1 for r in halu_eval_results if r.get("has_citation"))
    validation_passed_count = sum(1 for r in halu_eval_results if r.get("validation_passed"))
    
    logger.info(f"✅ Successful requests: {successful}/{len(halu_eval_results)}")
    logger.info(f"⚠️  Fallback messages: {fallback_count}/{len(halu_eval_results)}")
    logger.info(f"📚 With citations: {citation_count}/{len(halu_eval_results)}")
    logger.info(f"✅ Validation passed: {validation_passed_count}/{len(halu_eval_results)}")
    
    # Compare with control
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔍 COMPARISON: Control vs HaluEval")
    logger.info("=" * 80)
    control_fallback_rate = sum(1 for r in control_results if r.get("is_fallback") or r.get("used_fallback")) / len(control_results) * 100 if control_results else 0
    halu_eval_fallback_rate = fallback_count / len(halu_eval_results) * 100 if halu_eval_results else 0
    
    logger.info(f"Control questions fallback rate: {control_fallback_rate:.1f}%")
    logger.info(f"HaluEval questions fallback rate: {halu_eval_fallback_rate:.1f}%")
    
    if halu_eval_fallback_rate > control_fallback_rate:
        logger.warning(f"⚠️  HaluEval has {halu_eval_fallback_rate - control_fallback_rate:.1f}% higher fallback rate")
        logger.warning("   This suggests HaluEval questions trigger different code paths")
    else:
        logger.info("✅ Fallback rates are similar - issue affects both equally")
    
    # Save results
    output_dir = Path("data/evaluation/debug")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "api_url": API_BASE_URL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "control_questions": {
            "total": len(control_results),
            "successful": successful,
            "fallback_count": sum(1 for r in control_results if r.get("is_fallback") or r.get("used_fallback")),
            "results": control_results
        },
        "halu_eval_questions": {
            "total": len(halu_eval_results),
            "successful": successful,
            "fallback_count": fallback_count,
            "citation_count": citation_count,
            "validation_passed_count": validation_passed_count,
            "results": halu_eval_results
        }
    }
    
    output_file = output_dir / "halu_eval_debug_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info("")
    logger.info(f"💾 Results saved to: {output_file}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ DEBUG SCRIPT COMPLETE")
    logger.info("=" * 80)
    
    return 0 if fallback_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

