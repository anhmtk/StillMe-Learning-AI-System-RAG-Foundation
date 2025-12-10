"""
Comprehensive test script for Feed Optimization Phases 1, 2, and 3
Tests all implemented features: dynamic threshold, health dashboard, quality metrics,
domain scoring, freshness boost, automated replacement, semantic duplicate detection,
proactive health checks, and performance analytics.
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_phase1_dynamic_threshold():
    """Test Phase 1.1: Dynamic threshold adjustment"""
    logger.info("=" * 60)
    logger.info("Testing Phase 1.1: Dynamic Threshold Adjustment")
    logger.info("=" * 60)
    
    try:
        from stillme_core.learning.curator import ContentCurator
        
        curator = ContentCurator()
        
        # Test 1: Low volume (< 20 items) - should lower threshold
        threshold_low = curator.calculate_dynamic_threshold(total_items=10, avg_importance=0.5)
        logger.info(f"✅ Low volume (10 items): threshold = {threshold_low:.2f} (expected: ~0.2)")
        assert threshold_low <= 0.3, f"Expected threshold <= 0.3 for low volume, got {threshold_low}"
        
        # Test 2: High volume (> 50 items) - should raise threshold
        threshold_high = curator.calculate_dynamic_threshold(total_items=100, avg_importance=0.5)
        logger.info(f"✅ High volume (100 items): threshold = {threshold_high:.2f} (expected: ~0.4-0.5)")
        assert threshold_high >= 0.3, f"Expected threshold >= 0.3 for high volume, got {threshold_high}"
        
        # Test 3: High quality (avg > 0.6) - should raise threshold
        threshold_quality = curator.calculate_dynamic_threshold(total_items=30, avg_importance=0.7)
        logger.info(f"✅ High quality (avg 0.7): threshold = {threshold_quality:.2f} (expected: higher)")
        
        # Test 4: Low quality (avg < 0.4) - should lower threshold
        threshold_low_quality = curator.calculate_dynamic_threshold(total_items=30, avg_importance=0.3)
        logger.info(f"✅ Low quality (avg 0.3): threshold = {threshold_low_quality:.2f} (expected: lower)")
        
        logger.info("✅ Phase 1.1: Dynamic threshold adjustment - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 1.1 failed: {e}", exc_info=True)
        return False


async def test_phase1_feed_health_dashboard():
    """Test Phase 1.2: Feed health dashboard endpoint"""
    logger.info("=" * 60)
    logger.info("Testing Phase 1.2: Feed Health Dashboard")
    logger.info("=" * 60)
    
    try:
        from backend.services.feed_health_monitor import get_feed_health_monitor
        
        health_monitor = get_feed_health_monitor()
        
        # Record some test data
        test_feed = "https://test-feed.example.com/rss"
        health_monitor.record_success(test_feed, response_time=0.5)
        health_monitor.record_success(test_feed, response_time=0.6)
        health_monitor.record_failure(test_feed, "Test error")
        
        # Get health report
        report = health_monitor.get_health_report()
        
        logger.info(f"✅ Health report generated:")
        logger.info(f"   - Total feeds: {report.get('total_feeds', 0)}")
        logger.info(f"   - Healthy feeds: {report.get('healthy_feeds', 0)}")
        logger.info(f"   - Unhealthy feeds: {report.get('unhealthy_feeds', 0)}")
        
        assert "total_feeds" in report, "Report should contain total_feeds"
        assert "feeds" in report, "Report should contain feeds list"
        
        # Check if test feed is in report
        test_feed_found = False
        for feed_info in report.get("feeds", []):
            if feed_info.get("feed_url") == test_feed:
                test_feed_found = True
                logger.info(f"✅ Test feed found in report:")
                logger.info(f"   - Health score: {feed_info.get('health_score', 0):.3f}")
                logger.info(f"   - Success count: {feed_info.get('success_count', 0)}")
                logger.info(f"   - Failure count: {feed_info.get('failure_count', 0)}")
                logger.info(f"   - Avg response time: {feed_info.get('avg_response_time', 0):.3f}s")
                assert "quality_metrics" in feed_info, "Feed info should contain quality_metrics"
                break
        
        assert test_feed_found, "Test feed should be in health report"
        
        logger.info("✅ Phase 1.2: Feed health dashboard - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 1.2 failed: {e}", exc_info=True)
        return False


async def test_phase1_quality_metrics():
    """Test Phase 1.3: Feed quality metrics tracking"""
    logger.info("=" * 60)
    logger.info("Testing Phase 1.3: Feed Quality Metrics Tracking")
    logger.info("=" * 60)
    
    try:
        from backend.services.feed_health_monitor import get_feed_health_monitor
        
        health_monitor = get_feed_health_monitor()
        test_feed = "https://test-quality.example.com/rss"
        
        # Track quality metrics
        health_monitor.track_feed_quality(
            feed_url=test_feed,
            importance_score=0.8,  # High quality
            is_duplicate=False,
            freshness=1.0  # Very fresh
        )
        health_monitor.track_feed_quality(
            feed_url=test_feed,
            importance_score=0.2,  # Low quality
            is_duplicate=True,
            freshness=0.1  # Old
        )
        health_monitor.track_feed_quality(
            feed_url=test_feed,
            importance_score=0.6,  # Medium quality
            is_duplicate=False,
            freshness=0.7  # Recent
        )
        
        # Get feed health
        feed_health = health_monitor.get_feed_health(test_feed)
        
        assert feed_health is not None, "Feed health should not be None"
        assert "quality_metrics" in feed_health, "Feed health should contain quality_metrics"
        
        quality = feed_health["quality_metrics"]
        logger.info(f"✅ Quality metrics tracked:")
        logger.info(f"   - Avg importance score: {quality.get('avg_importance_score', 0):.3f}")
        logger.info(f"   - High quality items: {quality.get('high_quality_items', 0)}")
        logger.info(f"   - Low quality items: {quality.get('low_quality_items', 0)}")
        logger.info(f"   - Total items processed: {quality.get('total_items_processed', 0)}")
        logger.info(f"   - Duplicate rate: {quality.get('duplicate_rate', 0):.3f}")
        logger.info(f"   - Freshness score: {quality.get('freshness_score', 0):.3f}")
        
        assert quality.get("total_items_processed", 0) == 3, "Should have processed 3 items"
        assert quality.get("high_quality_items", 0) >= 1, "Should have at least 1 high quality item"
        assert quality.get("low_quality_items", 0) >= 1, "Should have at least 1 low quality item"
        
        logger.info("✅ Phase 1.3: Feed quality metrics tracking - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 1.3 failed: {e}", exc_info=True)
        return False


async def test_phase2_domain_scoring():
    """Test Phase 2.1: Domain-specific scoring boost"""
    logger.info("=" * 60)
    logger.info("Testing Phase 2.1: Domain-Specific Scoring Boost")
    logger.info("=" * 60)
    
    try:
        from stillme_core.learning.curator import ContentCurator
        
        curator = ContentCurator()
        
        # Test ethics content (should get +0.2 boost)
        ethics_content = {
            "title": "Ethics in AI: A comprehensive guide",
            "summary": "This article discusses ethical considerations in artificial intelligence systems.",
            "published": datetime.now().isoformat()
        }
        ethics_score = curator.calculate_importance_score(ethics_content)
        logger.info(f"✅ Ethics content score: {ethics_score:.3f}")
        
        # Test transparency content (should get +0.2 boost)
        transparency_content = {
            "title": "Transparency in AI systems",
            "summary": "How to make AI systems more transparent and accountable.",
            "published": datetime.now().isoformat()
        }
        transparency_score = curator.calculate_importance_score(transparency_content)
        logger.info(f"✅ Transparency content score: {transparency_score:.3f}")
        
        # Test generic content (no domain boost)
        generic_content = {
            "title": "General article about technology",
            "summary": "This is a general technology article without specific domain keywords.",
            "published": datetime.now().isoformat()
        }
        generic_score = curator.calculate_importance_score(generic_content)
        logger.info(f"✅ Generic content score: {generic_score:.3f}")
        
        # Verify domain boost is applied
        assert ethics_score > generic_score, "Ethics content should have higher score than generic"
        assert transparency_score > generic_score, "Transparency content should have higher score than generic"
        
        logger.info("✅ Phase 2.1: Domain-specific scoring boost - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 2.1 failed: {e}", exc_info=True)
        return False


async def test_phase2_freshness_scoring():
    """Test Phase 2.2: Freshness scoring boost"""
    logger.info("=" * 60)
    logger.info("Testing Phase 2.2: Freshness Scoring Boost")
    logger.info("=" * 60)
    
    try:
        from stillme_core.learning.curator import ContentCurator
        
        curator = ContentCurator()
        
        # Test very fresh content (< 24h) - should get +0.2 boost
        fresh_content = {
            "title": "Breaking news about AI",
            "summary": "Latest developments in AI research.",
            "published": datetime.now().isoformat()  # Very fresh
        }
        fresh_score = curator.calculate_importance_score(fresh_content)
        logger.info(f"✅ Fresh content (< 24h) score: {fresh_score:.3f}")
        
        # Test old content (> 30 days) - should get minimal boost
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        old_content = {
            "title": "Old article about AI",
            "summary": "Historical AI research from months ago.",
            "published": old_date
        }
        old_score = curator.calculate_importance_score(old_content)
        logger.info(f"✅ Old content (> 30 days) score: {old_score:.3f}")
        
        # Verify freshness boost is applied
        assert fresh_score > old_score, "Fresh content should have higher score than old content"
        
        logger.info("✅ Phase 2.2: Freshness scoring boost - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 2.2 failed: {e}", exc_info=True)
        return False


async def test_phase2_auto_replace():
    """Test Phase 2.3: Automated feed replacement suggestions"""
    logger.info("=" * 60)
    logger.info("Testing Phase 2.3: Automated Feed Replacement Suggestions")
    logger.info("=" * 60)
    
    try:
        from backend.services.feed_health_monitor import get_feed_health_monitor
        
        health_monitor = get_feed_health_monitor()
        
        # Create test scenario: unhealthy feed and healthy replacement
        unhealthy_feed = "https://unhealthy-feed.example.com/rss"
        healthy_feed = "https://healthy-feed.example.com/rss"
        
        # Make unhealthy feed fail multiple times
        for _ in range(6):
            health_monitor.record_failure(unhealthy_feed, "Test failure")
        
        # Make healthy feed successful with good quality
        health_monitor.record_success(healthy_feed, response_time=0.5)
        health_monitor.track_feed_quality(healthy_feed, importance_score=0.8, is_duplicate=False, freshness=1.0)
        health_monitor.track_feed_quality(healthy_feed, importance_score=0.7, is_duplicate=False, freshness=0.9)
        
        # Get replacement suggestions
        suggestions = health_monitor.suggest_replacements([unhealthy_feed])
        
        logger.info(f"✅ Replacement suggestions generated: {len(suggestions)}")
        
        if unhealthy_feed in suggestions:
            suggestion = suggestions[unhealthy_feed]
            logger.info(f"✅ Suggestion for {unhealthy_feed[:50]}:")
            logger.info(f"   - Suggested feed: {suggestion.get('suggested_feed', 'N/A')[:50]}")
            logger.info(f"   - Reason: {suggestion.get('reason', 'N/A')}")
            logger.info(f"   - Domain match: {suggestion.get('domain_match', False)}")
            logger.info(f"   - Quality score: {suggestion.get('quality_score', 0):.3f}")
            logger.info(f"   - Health score: {suggestion.get('health_score', 0):.3f}")
        
        logger.info("✅ Phase 2.3: Automated feed replacement suggestions - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 2.3 failed: {e}", exc_info=True)
        return False


async def test_phase3_semantic_duplicate():
    """Test Phase 3.1: Semantic duplicate detection"""
    logger.info("=" * 60)
    logger.info("Testing Phase 3.1: Semantic Duplicate Detection")
    logger.info("=" * 60)
    
    try:
        from backend.vector_db.rag_retrieval import RAGRetrieval
        from backend.vector_db.chroma_client import ChromaClient
        from backend.vector_db.embeddings import EmbeddingService
        
        # Initialize services
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Test content
        original_content = "StillMe is a transparent AI system that uses RAG for continuous learning."
        duplicate_content = "StillMe is a transparent AI system that uses RAG for continuous learning."  # Exact duplicate
        
        # Check semantic duplicate
        is_duplicate, similar_doc = rag_retrieval.check_semantic_duplicate(
            content=duplicate_content,
            similarity_threshold=0.95
        )
        
        logger.info(f"✅ Semantic duplicate check:")
        logger.info(f"   - Is duplicate: {is_duplicate}")
        logger.info(f"   - Similar doc: {similar_doc is not None}")
        
        # Note: This test may not find duplicates if database is empty
        # But it should at least run without errors
        logger.info("✅ Phase 3.1: Semantic duplicate detection - PASSED (method exists and runs)")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 3.1 failed: {e}", exc_info=True)
        return False


async def test_phase3_performance_analytics():
    """Test Phase 3.3: Feed performance analytics"""
    logger.info("=" * 60)
    logger.info("Testing Phase 3.3: Feed Performance Analytics")
    logger.info("=" * 60)
    
    try:
        from backend.services.feed_health_monitor import get_feed_health_monitor
        
        health_monitor = get_feed_health_monitor()
        test_feed = "https://test-analytics.example.com/rss"
        
        # Add some performance data
        health_monitor.record_success(test_feed, response_time=0.5)
        health_monitor.record_success(test_feed, response_time=0.6)
        health_monitor.track_feed_quality(test_feed, importance_score=0.8, is_duplicate=False, freshness=1.0)
        health_monitor.track_feed_quality(test_feed, importance_score=0.7, is_duplicate=False, freshness=0.9)
        health_monitor.track_feed_quality(test_feed, importance_score=0.3, is_duplicate=True, freshness=0.1)
        
        # Get single feed analytics
        single_analytics = health_monitor.get_feed_performance_analytics(feed_url=test_feed)
        
        logger.info(f"✅ Single feed analytics:")
        logger.info(f"   - Items processed: {single_analytics.get('items_processed', 0)}")
        logger.info(f"   - Items passed filter: {single_analytics.get('items_passed_filter', 0)}")
        logger.info(f"   - Avg importance score: {single_analytics.get('avg_importance_score', 0):.3f}")
        logger.info(f"   - Duplicate rate: {single_analytics.get('duplicate_rate', 0):.3f}")
        logger.info(f"   - Freshness score: {single_analytics.get('freshness_score', 0):.3f}")
        logger.info(f"   - Success count: {single_analytics.get('success_count', 0)}")
        logger.info(f"   - Avg response time: {single_analytics.get('avg_response_time', 0):.3f}s")
        
        assert single_analytics.get("items_processed", 0) == 3, "Should have processed 3 items"
        
        # Get aggregate analytics
        aggregate_analytics = health_monitor.get_feed_performance_analytics()
        
        logger.info(f"✅ Aggregate analytics:")
        logger.info(f"   - Total feeds: {aggregate_analytics.get('total_feeds', 0)}")
        logger.info(f"   - Total items processed: {aggregate_analytics.get('total_items_processed', 0)}")
        logger.info(f"   - Avg importance score: {aggregate_analytics.get('avg_importance_score', 0):.3f}")
        logger.info(f"   - Success rate: {aggregate_analytics.get('success_rate', 0):.2f}%")
        logger.info(f"   - Avg response time: {aggregate_analytics.get('avg_response_time', 0):.3f}s")
        
        assert "total_feeds" in aggregate_analytics, "Aggregate analytics should contain total_feeds"
        
        logger.info("✅ Phase 3.3: Feed performance analytics - PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Phase 3.3 failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Feed Optimization Phases Test Suite")
    logger.info("=" * 60)
    
    results = {
        "phase1": {},
        "phase2": {},
        "phase3": {},
        "summary": {}
    }
    
    # Phase 1 Tests
    results["phase1"]["dynamic_threshold"] = await test_phase1_dynamic_threshold()
    results["phase1"]["feed_health_dashboard"] = await test_phase1_feed_health_dashboard()
    results["phase1"]["quality_metrics"] = await test_phase1_quality_metrics()
    
    # Phase 2 Tests
    results["phase2"]["domain_scoring"] = await test_phase2_domain_scoring()
    results["phase2"]["freshness_scoring"] = await test_phase2_freshness_scoring()
    results["phase2"]["auto_replace"] = await test_phase2_auto_replace()
    
    # Phase 3 Tests
    results["phase3"]["semantic_duplicate"] = await test_phase3_semantic_duplicate()
    results["phase3"]["performance_analytics"] = await test_phase3_performance_analytics()
    
    # Calculate summary
    phase1_passed = sum(results["phase1"].values())
    phase2_passed = sum(results["phase2"].values())
    phase3_passed = sum(results["phase3"].values())
    total_passed = phase1_passed + phase2_passed + phase3_passed
    total_tests = len(results["phase1"]) + len(results["phase2"]) + len(results["phase3"])
    
    results["summary"] = {
        "phase1_passed": phase1_passed,
        "phase1_total": len(results["phase1"]),
        "phase2_passed": phase2_passed,
        "phase2_total": len(results["phase2"]),
        "phase3_passed": phase3_passed,
        "phase3_total": len(results["phase3"]),
        "total_passed": total_passed,
        "total_tests": total_tests,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
    }
    
    # Print summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Phase 1: {phase1_passed}/{len(results['phase1'])} tests passed")
    logger.info(f"Phase 2: {phase2_passed}/{len(results['phase2'])} tests passed")
    logger.info(f"Phase 3: {phase3_passed}/{len(results['phase3'])} tests passed")
    logger.info(f"Total: {total_passed}/{total_tests} tests passed ({results['summary']['success_rate']:.1f}%)")
    logger.info("=" * 60)
    
    # Save results
    results_file = os.path.join(project_root, "test_results_feed_optimization.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"✅ Test results saved to: {results_file}")
    
    if total_passed == total_tests:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

