"""
Test Codebase Q&A API Endpoint (Phase 1.3)

Tests the /api/codebase/query endpoint
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_codebase_api(base_url: str = "http://localhost:8000"):
    """Test codebase Q&A API endpoint"""
    
    logger.info("🧪 Testing Codebase Q&A API (Phase 1.3)...")
    
    # Test queries
    test_queries = [
        {
            "question": "How does the validation chain work?",
            "n_results": 3
        },
        {
            "question": "What is the RAG retrieval process?",
            "n_results": 3
        },
        {
            "question": "How does StillMe track task execution time?",
            "n_results": 2
        }
    ]
    
    results = []
    
    for i, query_data in enumerate(test_queries, 1):
        logger.info(f"\n📝 Test {i}: {query_data['question']}")
        
        try:
            # Make API request
            url = f"{base_url}/api/codebase/query"
            response = requests.post(
                url,
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"   ✅ Success!")
                logger.info(f"   Explanation: {data.get('explanation', '')[:200]}...")
                logger.info(f"   Code chunks: {len(data.get('code_chunks', []))}")
                logger.info(f"   Citations: {data.get('citations', [])}")
                
                # Verify response structure
                required_fields = ["question", "explanation", "code_chunks", "citations"]
                missing_fields = [f for f in required_fields if f not in data]
                if missing_fields:
                    logger.warning(f"   ⚠️ Missing fields: {missing_fields}")
                else:
                    logger.info(f"   ✅ Response structure valid")
                
                results.append({
                    "test": i,
                    "question": query_data['question'],
                    "status": "success",
                    "chunks": len(data.get('code_chunks', [])),
                    "citations": len(data.get('citations', []))
                })
            else:
                logger.error(f"   ❌ Failed with status {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                results.append({
                    "test": i,
                    "question": query_data['question'],
                    "status": "failed",
                    "status_code": response.status_code
                })
        
        except requests.exceptions.ConnectionError:
            logger.error(f"   ❌ Could not connect to {base_url}")
            logger.error(f"   Make sure the backend is running!")
            return False
        except Exception as e:
            logger.error(f"   ❌ Error: {e}", exc_info=True)
            results.append({
                "test": i,
                "question": query_data['question'],
                "status": "error",
                "error": str(e)
            })
    
    # Test stats endpoint
    logger.info("\n📊 Testing stats endpoint...")
    try:
        url = f"{base_url}/api/codebase/stats"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"   ✅ Stats: {data}")
        else:
            logger.warning(f"   ⚠️ Stats endpoint returned {response.status_code}")
    except Exception as e:
        logger.warning(f"   ⚠️ Stats endpoint error: {e}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    success_count = sum(1 for r in results if r.get("status") == "success")
    logger.info(f"Passed: {success_count}/{len(test_queries)}")
    
    for result in results:
        status_icon = "✅" if result.get("status") == "success" else "❌"
        logger.info(f"{status_icon} Test {result['test']}: {result.get('status', 'unknown')}")
        if result.get("status") == "success":
            logger.info(f"   Chunks: {result.get('chunks', 0)}, Citations: {result.get('citations', 0)}")
    
    return success_count == len(test_queries)


if __name__ == "__main__":
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logger.info(f"🌐 Testing against: {base_url}")
    
    success = test_codebase_api(base_url)
    sys.exit(0 if success else 1)

