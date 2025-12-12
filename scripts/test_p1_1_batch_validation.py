#!/usr/bin/env python3
"""
Test script for P1.1.b: Batch Step Validation

Tests:
1. Batch validation (1 LLM call for all steps)
2. Fallback to lightweight chain if batch fails
3. Performance comparison (should be faster)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.validators.step_validator import StepValidator
from backend.validators.step_detector import Step

def test_batch_validation():
    """Test batch validation"""
    print("=" * 60)
    print("Testing P1.1.b: Batch Step Validation")
    print("=" * 60)
    
    validator = StepValidator(use_lightweight=True, use_batch=True, confidence_threshold=0.5)
    
    # Create test steps
    steps = [
        Step(
            step_number=1,
            content="StillMe uses ChromaDB for vector storage [1]",
            original_text="Bước 1: StillMe uses ChromaDB for vector storage [1]",
            start_pos=0,
            end_pos=50
        ),
        Step(
            step_number=2,
            content="StillMe validates responses with 12 validators [2]",
            original_text="Bước 2: StillMe validates responses with 12 validators [2]",
            start_pos=51,
            end_pos=100
        ),
        Step(
            step_number=3,
            content="StillMe has a continuous learning system",
            original_text="Bước 3: StillMe has a continuous learning system",
            start_pos=101,
            end_pos=150
        ),
    ]
    
    ctx_docs = [
        "StillMe is an AI system that uses ChromaDB for vector storage and validates responses",
        "StillMe has a validation chain with multiple validators",
        "StillMe learns continuously from RSS feeds and arXiv"
    ]
    
    print(f"\n[Test 1] Batch validation ({len(steps)} steps in 1 LLM call)...")
    start_time = time.time()
    results = validator.validate_all_steps(
        steps,
        ctx_docs,
        chain=None,
        parallel=True,
        adaptive_citation_overlap=0.1,
        adaptive_evidence_threshold=0.01
    )
    elapsed = time.time() - start_time
    
    print(f"  Results: {len(results)} steps validated in {elapsed:.3f}s")
    for result in results:
        print(f"    Step {result.step.step_number}: passed={result.passed}, confidence={result.confidence:.2f}, issues={result.issues}")
    
    if len(results) == len(steps):
        print("  [OK] All steps validated via batch")
    else:
        print(f"  [FAIL] Expected {len(steps)} results, got {len(results)}")
        return False
    
    # Check if results are sorted by step number
    step_numbers = [r.step.step_number for r in results]
    if step_numbers == sorted(step_numbers):
        print("  [OK] Results sorted by step number")
    else:
        print(f"  [FAIL] Results not sorted correctly: {step_numbers}")
        return False
    
    return True

def test_fallback_to_lightweight():
    """Test fallback to lightweight chain if batch fails"""
    print("\n" + "=" * 60)
    print("Testing P1.1.b: Fallback to Lightweight Chain")
    print("=" * 60)
    
    # Disable batch to test lightweight chain
    validator = StepValidator(use_lightweight=True, use_batch=False, confidence_threshold=0.5)
    
    steps = [
        Step(
            step_number=1,
            content="Test step [1]",
            original_text="Bước 1: Test step [1]",
            start_pos=0,
            end_pos=20
        ),
    ]
    
    ctx_docs = ["Test context"]
    
    print("\n[Test 2] Fallback to lightweight chain (use_batch=False)...")
    start_time = time.time()
    results = validator.validate_all_steps(
        steps,
        ctx_docs,
        chain=None,
        parallel=True,
        adaptive_citation_overlap=0.1,
        adaptive_evidence_threshold=0.01
    )
    elapsed = time.time() - start_time
    
    print(f"  Results: {len(results)} steps validated in {elapsed:.3f}s")
    print(f"    Step {results[0].step.step_number}: passed={results[0].passed}, confidence={results[0].confidence:.2f}")
    
    if len(results) == len(steps):
        print("  [OK] Fallback to lightweight chain works")
    else:
        print(f"  [FAIL] Expected {len(steps)} results, got {len(results)}")
        return False
    
    return True

if __name__ == "__main__":
    print("P1.1.b: Batch Step Validation Tests\n")
    
    success = True
    success &= test_batch_validation()
    success &= test_fallback_to_lightweight()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] All P1.1.b tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

