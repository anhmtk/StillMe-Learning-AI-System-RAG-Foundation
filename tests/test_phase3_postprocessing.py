"""
Test Phase 3: Simplify Post-Processing

Tests that rewrite only happens for CRITICAL issues:
- Missing citation (critical)
- Anthropomorphic language (critical)
- Language mismatch (critical)
- Topic drift (critical)
- Template-like response (critical)

Non-critical issues should NOT trigger rewrite:
- Minor formatting issues
- Style preferences
- Natural variation
- Depth, unpacking (optional)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.postprocessing.optimizer import PostProcessingOptimizer


def test_no_critical_issues_skip_rewrite():
    """Test: No critical issues - should skip rewrite"""
    print("\n" + "="*80)
    print("TEST 1: No Critical Issues - Skip Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with no critical issues (only minor issues)
    quality_result = {
        "quality": "needs_rewrite",
        "overall_score": 0.4,  # Low score but no critical issues
        "reasons": [
            "Lacks philosophical depth - missing meta-cognitive reflection",
            "Missing conceptual unpacking - doesn't examine assumptions",
            "Weak argument structure - lacks logical flow"
        ]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=None
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is False, "Should NOT rewrite when no critical issues"
    assert "no_critical_issues" in reason, "Reason should indicate no critical issues"
    
    print("[PASS] TEST 1 PASSED: Skipped rewrite for non-critical issues")


def test_anthropomorphic_language_rewrite():
    """Test: Anthropomorphic language - should rewrite"""
    print("\n" + "="*80)
    print("TEST 2: Anthropomorphic Language - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with anthropomorphic language (CRITICAL)
    quality_result = {
        "quality": "needs_rewrite",
        "overall_score": 0.5,
        "reasons": [
            "Contains anthropomorphic language - claims experience or feelings",
            "Lacks philosophical depth"  # Non-critical
        ]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=None
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when anthropomorphic language detected"
    assert "anthropomorphic_language" in reason, "Reason should mention anthropomorphic language"
    
    print("[PASS] TEST 2 PASSED: Rewrite triggered for anthropomorphic language")


def test_missing_citation_rewrite():
    """Test: Missing citation - should rewrite"""
    print("\n" + "="*80)
    print("TEST 3: Missing Citation - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with no critical issues
    quality_result = {
        "quality": "good",
        "overall_score": 0.8,
        "reasons": []
    }
    
    # But validation_result shows missing citation (CRITICAL)
    validation_result = {
        "passed": False,
        "reasons": ["missing_citation"]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=validation_result
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Validation result: {validation_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when missing citation detected"
    assert "missing_citation" in reason, "Reason should mention missing citation"
    
    print("[PASS] TEST 3 PASSED: Rewrite triggered for missing citation")


def test_language_mismatch_rewrite():
    """Test: Language mismatch - should rewrite"""
    print("\n" + "="*80)
    print("TEST 4: Language Mismatch - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with no critical issues
    quality_result = {
        "quality": "good",
        "overall_score": 0.8,
        "reasons": []
    }
    
    # But validation_result shows language mismatch (CRITICAL)
    validation_result = {
        "passed": False,
        "reasons": ["language_mismatch"]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=validation_result
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Validation result: {validation_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when language mismatch detected"
    assert "language_mismatch" in reason, "Reason should mention language mismatch"
    
    print("[PASS] TEST 4 PASSED: Rewrite triggered for language mismatch")


def test_topic_drift_rewrite():
    """Test: Topic drift - should rewrite"""
    print("\n" + "="*80)
    print("TEST 5: Topic Drift - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with topic drift (CRITICAL)
    quality_result = {
        "quality": "needs_rewrite",
        "overall_score": 0.4,
        "reasons": [
            "Topic drift detected - StillMe talks about consciousness/LLM when not asked",
            "Lacks philosophical depth"  # Non-critical
        ]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=None
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when topic drift detected"
    assert "topic_drift" in reason, "Reason should mention topic drift"
    
    print("[PASS] TEST 5 PASSED: Rewrite triggered for topic drift")


def test_template_like_rewrite():
    """Test: Template-like response - should rewrite"""
    print("\n" + "="*80)
    print("TEST 6: Template-like Response - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with template-like response (CRITICAL)
    quality_result = {
        "quality": "needs_rewrite",
        "overall_score": 0.3,
        "reasons": [
            "Template-like response detected - numbered lists or formulaic structure",
            "Lacks philosophical depth"  # Non-critical
        ]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=None
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when template-like response detected"
    assert "template_like" in reason, "Reason should mention template-like"
    
    print("[PASS] TEST 6 PASSED: Rewrite triggered for template-like response")


def test_multiple_critical_issues():
    """Test: Multiple critical issues - should rewrite"""
    print("\n" + "="*80)
    print("TEST 7: Multiple Critical Issues - Should Rewrite")
    print("="*80)
    
    optimizer = PostProcessingOptimizer()
    
    # Quality result with multiple critical issues
    quality_result = {
        "quality": "needs_rewrite",
        "overall_score": 0.2,
        "reasons": [
            "Contains anthropomorphic language - claims experience or feelings",
            "Topic drift detected - StillMe talks about consciousness/LLM when not asked",
            "Template-like response detected - numbered lists or formulaic structure"
        ]
    }
    
    validation_result = {
        "passed": False,
        "reasons": ["missing_citation", "language_mismatch"]
    }
    
    should_rewrite, reason = optimizer.should_rewrite(
        quality_result=quality_result,
        is_philosophical=False,
        response_length=500,
        validation_result=validation_result
    )
    
    print(f"Quality result: {quality_result}")
    print(f"Validation result: {validation_result}")
    print(f"Should rewrite: {should_rewrite}")
    print(f"Reason: {reason}")
    
    assert should_rewrite is True, "Should rewrite when multiple critical issues detected"
    # Should contain multiple critical issues
    assert "anthropomorphic_language" in reason or "topic_drift" in reason or "template_like" in reason or "missing_citation" in reason or "language_mismatch" in reason
    
    print("[PASS] TEST 7 PASSED: Rewrite triggered for multiple critical issues")


def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n" + "="*80)
    print("PHASE 3: SIMPLIFY POST-PROCESSING TEST SUITE")
    print("="*80)
    
    tests = [
        test_no_critical_issues_skip_rewrite,
        test_anthropomorphic_language_rewrite,
        test_missing_citation_rewrite,
        test_language_mismatch_rewrite,
        test_topic_drift_rewrite,
        test_template_like_rewrite,
        test_multiple_critical_issues
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n[FAILED] TEST FAILED: {test.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    if failed == 0:
        print("\n[PASS] ALL PHASE 3 TESTS PASSED!")
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

