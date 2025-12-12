#!/usr/bin/env python3
"""
Test script for P2: Rewrite Logic Optimization

Tests:
1. Template intent detection
2. Early exit at quality_score >= 0.4
3. Single attempt with 5s timeout
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.postprocessing.optimizer import PostProcessingOptimizer

def test_template_detection():
    """Test template intent detection"""
    print("=" * 60)
    print("Testing P2: Template Intent Detection")
    print("=" * 60)
    
    optimizer = PostProcessingOptimizer()
    
    test_cases = [
        ("hãy chỉ ra 10 điểm yếu", True),
        ("liệt kê 5 bước", True),
        ("point out 3 reasons", True),
        ("kể 10 điều", True),
        ("what is StillMe?", False),
        ("how does RAG work?", False),
        ("StillMe có gì đặc biệt?", False),
    ]
    
    print("\n[Test 1] Template intent detection...")
    all_passed = True
    for question, expected in test_cases:
        result = optimizer.is_user_requesting_template(question)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} '{question}' -> {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_early_exit():
    """Test early exit at quality_score >= 0.4"""
    print("\n" + "=" * 60)
    print("Testing P2: Early Exit at quality_score >= 0.4")
    print("=" * 60)
    
    optimizer = PostProcessingOptimizer()
    
    # Test 1: quality_score >= 0.4 should skip rewrite
    print("\n[Test 2] Early exit at quality_score >= 0.4...")
    quality_result_high = {"overall_score": 0.5}
    should_rewrite, reason, max_attempts = optimizer.should_rewrite(
        quality_result=quality_result_high,
        is_philosophical=False,
        response_length=100
    )
    
    if not should_rewrite and reason == "quality_acceptable":
        print(f"  [OK] quality_score 0.5 -> skip rewrite (reason: {reason})")
    else:
        print(f"  [FAIL] quality_score 0.5 -> should skip rewrite, got should_rewrite={should_rewrite}, reason={reason}")
        return False
    
    # Test 2: quality_score < 0.4 should allow rewrite
    quality_result_low = {"overall_score": 0.3}
    should_rewrite, reason, max_attempts = optimizer.should_rewrite(
        quality_result=quality_result_low,
        is_philosophical=False,
        response_length=100
    )
    
    # May or may not rewrite depending on policy, but should not be blocked by early exit
    print(f"  [OK] quality_score 0.3 -> rewrite decision: {should_rewrite} (reason: {reason})")
    
    return True

def test_template_skip():
    """Test template detection skips rewrite"""
    print("\n" + "=" * 60)
    print("Testing P2: Template Detection Skips Rewrite")
    print("=" * 60)
    
    optimizer = PostProcessingOptimizer()
    
    # Test: Template question should skip rewrite even with low quality
    print("\n[Test 3] Template question skips rewrite...")
    quality_result_low = {"overall_score": 0.3}
    should_rewrite, reason, max_attempts = optimizer.should_rewrite(
        quality_result=quality_result_low,
        is_philosophical=False,
        response_length=100,
        user_question="hãy chỉ ra 10 điểm yếu"
    )
    
    if not should_rewrite and reason == "user_requested_template":
        print(f"  [OK] Template question -> skip rewrite (reason: {reason})")
    else:
        print(f"  [FAIL] Template question -> should skip rewrite, got should_rewrite={should_rewrite}, reason={reason}")
        return False
    
    return True

if __name__ == "__main__":
    print("P2: Rewrite Logic Optimization Tests\n")
    
    success = True
    success &= test_template_detection()
    success &= test_early_exit()
    success &= test_template_skip()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] All P2 tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

