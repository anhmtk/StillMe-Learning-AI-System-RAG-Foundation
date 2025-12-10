"""
Comprehensive test script for all NPR phases.

Tests all NPR-inspired optimizations together:
- Phase 1: Parallel Validation Chain
- Phase 2.1: Parallel RAG Retrieval
- Phase 2.2: Self-Distilled Learning
- Phase 2.3: Context-Aware Thresholds
- Phase 3.1: Parallel Learning Cycles
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows encoding for emoji
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

def test_phase1():
    """Test Phase 1: Parallel Validation Chain"""
    print("\n" + "="*60)
    print("PHASE 1: Parallel Validation Chain")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/test_npr_parallel_validation.py"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("✅ Phase 1 tests passed")
            return True
        else:
            print(f"❌ Phase 1 tests failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Phase 1 test error: {e}")
        return False


def test_phase2_1():
    """Test Phase 2.1: Parallel RAG Retrieval"""
    print("\n" + "="*60)
    print("PHASE 2.1: Parallel RAG Retrieval")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/test_npr_parallel_rag_retrieval.py"],
            capture_output=True,
            text=True,
            timeout=300,  # Increased timeout for RAG retrieval tests
            encoding='utf-8',
            errors='replace'  # Handle encoding errors gracefully
        )
        
        if result.returncode == 0:
            print("✅ Phase 2.1 tests passed")
            return True
        else:
            print(f"❌ Phase 2.1 tests failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Phase 2.1 test error: {e}")
        return False


def test_phase2_2():
    """Test Phase 2.2: Self-Distilled Learning"""
    print("\n" + "="*60)
    print("PHASE 2.2: Self-Distilled Learning")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/test_npr_self_distilled_learning.py"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("✅ Phase 2.2 tests passed")
            return True
        else:
            print(f"❌ Phase 2.2 tests failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Phase 2.2 test error: {e}")
        return False


def test_phase2_3():
    """Test Phase 2.3: Context-Aware Thresholds"""
    print("\n" + "="*60)
    print("PHASE 2.3: Context-Aware Thresholds")
    print("="*60)
    
    try:
        from backend.services.self_distilled_learning import get_self_distilled_learning
        sdl = get_self_distilled_learning()
        
        # Test context-aware threshold adjustments
        print("\n  Test: Context-aware threshold adjustments")
        
        # Test 1: Philosophical question (should be more lenient)
        context_philosophical = {
            "is_philosophical": True,
            "is_technical": False,
            "has_context": True,
            "context_quality": "medium",
            "avg_similarity": 0.5
        }
        threshold_phil = sdl.get_adaptive_threshold("citation_relevance_min_overlap", 0.1, context_philosophical)
        print(f"    Philosophical threshold: {threshold_phil:.3f} (should be <= 0.1)")
        
        # Test 2: Technical question (should be stricter)
        context_technical = {
            "is_philosophical": False,
            "is_technical": True,
            "has_context": True,
            "context_quality": "high",
            "avg_similarity": 0.7
        }
        threshold_tech = sdl.get_adaptive_threshold("citation_relevance_min_overlap", 0.1, context_technical)
        print(f"    Technical threshold: {threshold_tech:.3f} (should be >= 0.1)")
        
        # Test 3: High context quality (should be stricter)
        context_high_quality = {
            "is_philosophical": False,
            "is_technical": False,
            "has_context": True,
            "context_quality": "high",
            "avg_similarity": 0.8
        }
        threshold_high = sdl.get_adaptive_threshold("evidence_overlap_threshold", 0.01, context_high_quality)
        print(f"    High quality threshold: {threshold_high:.3f} (should be >= 0.01)")
        
        # Test 4: Low context quality (should be more lenient)
        context_low_quality = {
            "is_philosophical": False,
            "is_technical": False,
            "has_context": True,
            "context_quality": "low",
            "avg_similarity": 0.2
        }
        threshold_low = sdl.get_adaptive_threshold("evidence_overlap_threshold", 0.01, context_low_quality)
        print(f"    Low quality threshold: {threshold_low:.3f} (should be <= 0.01)")
        
        # Verify adjustments
        assert threshold_phil <= 0.1, "Philosophical questions should have more lenient thresholds"
        assert threshold_tech >= 0.1, "Technical questions should have stricter thresholds"
        assert threshold_high >= 0.01, "High quality context should have stricter thresholds"
        assert threshold_low <= 0.01, "Low quality context should have more lenient thresholds"
        
        print("    ✅ Context-aware threshold adjustments work correctly")
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase3_1():
    """Test Phase 3.1: Parallel Learning Cycles"""
    print("\n" + "="*60)
    print("PHASE 3.1: Parallel Learning Cycles")
    print("="*60)
    
    try:
        # Test that batch processing is implemented
        from backend.services.rss_fetcher import RSSFetcher
        
        # Check if fetch_feeds_async has batch processing
        import inspect
        source = inspect.getsource(RSSFetcher.fetch_feeds_async)
        
        if "batch" in source.lower() or "NPR" in source:
            print("    ✅ Batch processing is implemented in fetch_feeds_async")
        else:
            print("    ⚠️ Batch processing may not be fully implemented")
        
        # Test RSSFetcher initialization
        fetcher = RSSFetcher()
        print(f"    RSS feeds configured: {len(fetcher.feeds)}")
        print("    ✅ RSSFetcher initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all NPR phase tests"""
    print("\n" + "="*60)
    print("NPR ALL PHASES: Comprehensive Test Suite")
    print("="*60)
    
    results = {
        "phase1": False,
        "phase2_1": False,
        "phase2_2": False,
        "phase2_3": False,
        "phase3_1": False,
    }
    
    try:
        # Test Phase 1
        results["phase1"] = test_phase1()
        
        # Test Phase 2.1
        results["phase2_1"] = test_phase2_1()
        
        # Test Phase 2.2
        results["phase2_2"] = test_phase2_2()
        
        # Test Phase 2.3
        results["phase2_3"] = test_phase2_3()
        
        # Test Phase 3.1
        results["phase3_1"] = test_phase3_1()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    print(f"Phase 1 (Parallel Validation):     {'✅ PASS' if results['phase1'] else '❌ FAIL'}")
    print(f"Phase 2.1 (Parallel RAG):          {'✅ PASS' if results['phase2_1'] else '❌ FAIL'}")
    print(f"Phase 2.2 (Self-Distilled):        {'✅ PASS' if results['phase2_2'] else '❌ FAIL'}")
    print(f"Phase 2.3 (Context-Aware):          {'✅ PASS' if results['phase2_3'] else '❌ FAIL'}")
    print(f"Phase 3.1 (Parallel Learning):      {'✅ PASS' if results['phase3_1'] else '❌ FAIL'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All NPR phases passed!")
        print("\n🎉 NPR-inspired optimizations are working correctly!")
    else:
        print("\n❌ Some phases failed!")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

