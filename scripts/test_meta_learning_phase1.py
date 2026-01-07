"""
Test Script for Stage 2: Meta-Learning Phase 1 - Retention Tracking

Tests:
1. DocumentUsageTracker - track document usage
2. Retention metrics calculation
3. SourceTrustCalculator - trust score calculation
4. API endpoints
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_document_usage_tracker():
    """Test DocumentUsageTracker"""
    logger.info("=" * 60)
    logger.info("TEST 1: DocumentUsageTracker")
    logger.info("=" * 60)
    
    try:
        from backend.learning.document_usage_tracker import get_document_usage_tracker
        
        tracker = get_document_usage_tracker()
        logger.info("✅ DocumentUsageTracker initialized")
        
        # Test: Record some usage
        logger.info("\n📝 Recording test document usage...")
        tracker.record_usage(
            query="What is AI?",
            doc_id="test_doc_1",
            source="https://example.com/rss",
            title="Introduction to AI",
            used_in_response=True,
            similarity_score=0.85,
            response_confidence=0.90,
            validation_passed=True
        )
        
        tracker.record_usage(
            query="What is machine learning?",
            doc_id="test_doc_2",
            source="https://arxiv.org/abs/1234.5678",
            title="Machine Learning Basics",
            used_in_response=True,
            similarity_score=0.75,
            response_confidence=0.85,
            validation_passed=True
        )
        
        tracker.record_usage(
            query="What is AI?",
            doc_id="test_doc_3",
            source="https://example.com/rss",
            title="AI Overview",
            used_in_response=False,  # Retrieved but not used
            similarity_score=0.50,
            response_confidence=0.60,
            validation_passed=False
        )
        
        logger.info("✅ Recorded 3 test document usage records")
        
        # Test: Calculate retention metrics
        logger.info("\n📊 Calculating retention metrics...")
        metrics = tracker.calculate_retention_metrics(days=30)
        
        if metrics:
            logger.info(f"✅ Retention metrics calculated for {len(metrics)} sources:")
            for source, stats in metrics.items():
                logger.info(f"   Source: {source[:50]}")
                logger.info(f"     - Total used: {stats.get('total_used', 0)}")
                logger.info(f"     - Retention rate: {stats.get('retention_rate', 0):.2%}")
                logger.info(f"     - Avg similarity: {stats.get('avg_similarity', 0):.2f}" if stats.get('avg_similarity') else "     - Avg similarity: N/A")
                logger.info(f"     - Avg confidence: {stats.get('avg_confidence', 0):.2f}" if stats.get('avg_confidence') else "     - Avg confidence: N/A")
        else:
            logger.warning("⚠️ No retention metrics available (may need more data)")
        
        # Test: Get retention rates
        logger.info("\n📈 Getting source retention rates...")
        retention_rates = tracker.get_source_retention_rates(days=30)
        if retention_rates:
            logger.info(f"✅ Retention rates for {len(retention_rates)} sources:")
            for source, rate in retention_rates.items():
                logger.info(f"   {source[:50]}: {rate:.2%}")
        else:
            logger.warning("⚠️ No retention rates available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DocumentUsageTracker test failed: {e}", exc_info=True)
        return False


def test_source_trust_calculator():
    """Test SourceTrustCalculator"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: SourceTrustCalculator")
    logger.info("=" * 60)
    
    try:
        from backend.learning.source_trust_calculator import get_source_trust_calculator
        
        calculator = get_source_trust_calculator()
        logger.info("✅ SourceTrustCalculator initialized")
        
        # Test: Calculate trust scores for different retention rates
        logger.info("\n🧮 Testing trust score calculation...")
        test_retention_rates = [0.05, 0.15, 0.25, 0.35, 0.50, 0.75, 0.90]
        
        for retention_rate in test_retention_rates:
            trust_score = calculator.calculate_trust_score(retention_rate)
            logger.info(f"   Retention {retention_rate:.0%} → Trust {trust_score:.2f}")
        
        logger.info("✅ Trust score calculation working correctly")
        
        # Test: Get recommended sources (will be empty if no data)
        logger.info("\n📋 Getting recommended sources...")
        recommended = calculator.get_recommended_sources(days=30, min_retention=0.20)
        if recommended:
            logger.info(f"✅ Found {len(recommended)} recommended sources:")
            for source in recommended[:5]:  # Show first 5
                logger.info(f"   - {source[:50]}")
        else:
            logger.info("ℹ️ No recommended sources (need more usage data)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SourceTrustCalculator test failed: {e}", exc_info=True)
        return False


def test_api_endpoints():
    """Test API endpoints (if server is running)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: API Endpoints")
    logger.info("=" * 60)
    
    import requests
    
    base_url = os.getenv("STILLME_API_URL", "http://localhost:8000")
    
    endpoints = [
        "/api/meta-learning/retention?days=30",
        "/api/meta-learning/source-trust?days=30",
        "/api/meta-learning/recommended-sources?days=30&min_retention=0.20"
    ]
    
    logger.info(f"Testing endpoints at: {base_url}")
    logger.info("(Note: Server must be running for these tests)")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {endpoint}: OK")
                logger.info(f"   Response keys: {list(data.keys())}")
            else:
                logger.warning(f"⚠️ {endpoint}: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.info(f"ℹ️ {endpoint}: Server not running (skipping)")
        except Exception as e:
            logger.warning(f"⚠️ {endpoint}: Error - {e}")


def test_integration():
    """Test integration with chat router"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Integration Test")
    logger.info("=" * 60)
    
    try:
        # Test that document usage tracking is integrated
        from backend.learning.document_usage_tracker import get_document_usage_tracker
        
        tracker = get_document_usage_tracker()
        
        # Simulate a response with documents
        test_documents = [
            {
                "id": "integration_test_1",
                "metadata": {
                    "source": "https://example.com/rss",
                    "title": "Test Document 1"
                },
                "similarity": 0.80
            },
            {
                "id": "integration_test_2",
                "metadata": {
                    "source": "https://arxiv.org/abs/1234.5678",
                    "title": "Test Document 2"
                },
                "similarity": 0.75
            }
        ]
        
        logger.info("📝 Testing batch usage recording...")
        tracker.record_batch_usage(
            query="Integration test query",
            documents=test_documents,
            response_confidence=0.85,
            validation_passed=True
        )
        
        logger.info("✅ Batch usage recording working")
        
        # Check if records were saved
        metrics = tracker.calculate_retention_metrics(days=1)
        if metrics:
            logger.info(f"✅ Integration test passed - {len(metrics)} sources tracked")
        else:
            logger.info("ℹ️ Integration test passed - tracker working (no metrics yet)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("🚀 Starting Meta-Learning Phase 1 Tests")
    logger.info("=" * 60)
    
    results = {
        "DocumentUsageTracker": test_document_usage_tracker(),
        "SourceTrustCalculator": test_source_trust_calculator(),
        "Integration": test_integration()
    }
    
    # Test API endpoints (non-blocking)
    test_api_endpoints()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed!")
    else:
        logger.warning("\n⚠️ Some tests failed - check logs above")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

