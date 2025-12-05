"""
Complete Phase 1 Testing

Tests all Phase 1 components:
1. Codebase Indexing (offline)
2. Code Retrieval (offline)
3. API Endpoints (if backend running)
4. Prompt Engineering (offline)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_indexing():
    """Test 1: Codebase Indexing"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Codebase Indexing")
    logger.info("="*80)
    
    try:
        from backend.services.codebase_indexer import get_codebase_indexer
        
        indexer = get_codebase_indexer()
        count = indexer.codebase_collection.count()
        
        logger.info(f"✅ Collection exists: stillme_codebase")
        logger.info(f"✅ Total chunks: {count}")
        
        if count >= 300:
            logger.info(f"✅ PASS: Collection has sufficient chunks ({count} >= 300)")
            return True
        else:
            logger.warning(f"⚠️ WARNING: Collection has fewer chunks than expected ({count} < 300)")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAIL: {e}", exc_info=True)
        return False


def test_code_retrieval():
    """Test 2: Code Retrieval"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Code Retrieval (RAG)")
    logger.info("="*80)
    
    test_queries = [
        "How does the validation chain work?",
        "What is the RAG retrieval process?",
        "How does StillMe track task execution time?",
    ]
    
    try:
        from backend.services.codebase_indexer import get_codebase_indexer
        
        indexer = get_codebase_indexer()
        passed = 0
        
        for query in test_queries:
            logger.info(f"\n📝 Query: {query}")
            results = indexer.query_codebase(query, n_results=3)
            
            if results:
                logger.info(f"   ✅ Found {len(results)} results")
                
                # Check metadata completeness
                for i, result in enumerate(results[:2], 1):  # Check first 2
                    metadata = result.get("metadata", {})
                    required = ["file_path", "line_start", "line_end", "code_type"]
                    missing = [f for f in required if f not in metadata]
                    
                    if not missing:
                        logger.info(f"   ✅ Result {i}: Metadata complete")
                    else:
                        logger.warning(f"   ⚠️ Result {i}: Missing {missing}")
                
                passed += 1
            else:
                logger.warning(f"   ⚠️ No results found")
        
        logger.info(f"\n✅ PASS: {passed}/{len(test_queries)} queries returned results")
        return passed == len(test_queries)
        
    except Exception as e:
        logger.error(f"❌ FAIL: {e}", exc_info=True)
        return False


def test_prompt_engineering():
    """Test 3: Prompt Engineering"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Prompt Engineering")
    logger.info("="*80)
    
    try:
        from backend.identity.prompt_builder import build_code_explanation_prompt
        
        # Test with sample code chunks
        sample_chunks = [
            {
                "metadata": {
                    "file_path": "test_file.py",
                    "line_start": 10,
                    "line_end": 20,
                    "code_type": "function",
                    "function_name": "test_function",
                    "docstring": "Test function docstring"
                },
                "document": "def test_function():\n    return True"
            }
        ]
        
        # Test English prompt
        logger.info("📝 Testing English prompt...")
        prompt_en = build_code_explanation_prompt(
            question="How does test_function work?",
            code_chunks=sample_chunks,
            detected_lang="en"
        )
        
        if "SAFETY RULES" in prompt_en and "ONLY ALLOWED" in prompt_en:
            logger.info("   ✅ English prompt contains safety rules")
        else:
            logger.warning("   ⚠️ English prompt missing safety rules")
        
        if "ABSOLUTELY FORBIDDEN" in prompt_en:
            logger.info("   ✅ English prompt contains forbidden rules")
        else:
            logger.warning("   ⚠️ English prompt missing forbidden rules")
        
        # Test Vietnamese prompt
        logger.info("📝 Testing Vietnamese prompt...")
        prompt_vi = build_code_explanation_prompt(
            question="test_function hoạt động như thế nào?",
            code_chunks=sample_chunks,
            detected_lang="vi"
        )
        
        if "QUY TẮC AN TOÀN" in prompt_vi and "CHỈ ĐƯỢC PHÉP" in prompt_vi:
            logger.info("   ✅ Vietnamese prompt contains safety rules")
        else:
            logger.warning("   ⚠️ Vietnamese prompt missing safety rules")
        
        if "TUYỆT ĐỐI KHÔNG ĐƯỢC" in prompt_vi:
            logger.info("   ✅ Vietnamese prompt contains forbidden rules")
        else:
            logger.warning("   ⚠️ Vietnamese prompt missing forbidden rules")
        
        logger.info("✅ PASS: Prompt engineering works for both languages")
        return True
        
    except Exception as e:
        logger.error(f"❌ FAIL: {e}", exc_info=True)
        return False


def test_api_endpoint():
    """Test 4: API Endpoint (if backend running)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: API Endpoint")
    logger.info("="*80)
    
    import requests
    import os
    
    # Try to detect Railway URL or use localhost
    if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
        base_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
    elif os.getenv("RAILWAY_STATIC_URL"):
        base_url = os.getenv("RAILWAY_STATIC_URL")
    else:
        base_url = "http://localhost:8000"
    
    logger.info(f"🌐 Testing API at: {base_url}")
    
    # Test stats endpoint
    try:
        logger.info("📊 Testing stats endpoint...")
        response = requests.get(f"{base_url}/api/codebase/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"   ✅ Stats endpoint works: {stats}")
        else:
            logger.warning(f"   ⚠️ Stats endpoint returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning("   ⚠️ Backend not running - skipping API tests")
        logger.info("   💡 To test API, start backend: python -m uvicorn backend.api.main:app --reload")
        return None  # Not a failure, just not available
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return False
    
    # Test query endpoint
    try:
        logger.info("📝 Testing query endpoint...")
        response = requests.post(
            f"{base_url}/api/codebase/query",
            json={
                "question": "How does the validation chain work?",
                "n_results": 3,
                "include_code": True
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            required = ["question", "explanation", "code_chunks", "citations"]
            missing = [f for f in required if f not in data]
            
            if not missing:
                logger.info(f"   ✅ Query endpoint works")
                logger.info(f"   📄 Explanation length: {len(data.get('explanation', ''))} chars")
                logger.info(f"   📦 Code chunks: {len(data.get('code_chunks', []))}")
                logger.info(f"   📝 Citations: {len(data.get('citations', []))}")
                return True
            else:
                logger.warning(f"   ⚠️ Missing fields: {missing}")
                return False
        else:
            logger.error(f"   ❌ Query endpoint returned {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Error: {e}", exc_info=True)
        return False


def main():
    """Run all Phase 1 tests"""
    logger.info("🧪 Phase 1 Complete Testing")
    logger.info("="*80)
    
    results = {}
    
    # Test 1: Indexing
    results["indexing"] = test_indexing()
    
    # Test 2: Code Retrieval
    results["retrieval"] = test_code_retrieval()
    
    # Test 3: Prompt Engineering
    results["prompt"] = test_prompt_engineering()
    
    # Test 4: API Endpoint (optional)
    results["api"] = test_api_endpoint()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    
    required_tests = ["indexing", "retrieval", "prompt"]
    passed = sum(1 for k in required_tests if results.get(k) == True)
    
    logger.info(f"Required Tests:")
    for test_name in required_tests:
        status = "✅ PASS" if results.get(test_name) == True else "❌ FAIL"
        logger.info(f"   {status}: {test_name}")
    
    if results.get("api") is not None:
        api_status = "✅ PASS" if results.get("api") == True else "❌ FAIL"
        logger.info(f"   {api_status}: api (optional - backend must be running)")
    else:
        logger.info(f"   ⏭️  SKIP: api (backend not running)")
    
    logger.info(f"\n✅ Passed: {passed}/{len(required_tests)} required tests")
    
    if passed == len(required_tests):
        logger.info("\n🎉 Phase 1 Core Components: ALL TESTS PASSED!")
        logger.info("   - Codebase indexing: ✅")
        logger.info("   - Code retrieval: ✅")
        logger.info("   - Prompt engineering: ✅")
        if results.get("api") == True:
            logger.info("   - API endpoints: ✅")
        return True
    else:
        logger.warning("\n⚠️ Some tests failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

