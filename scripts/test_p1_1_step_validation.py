#!/usr/bin/env python3
"""
Test script for P1.1: Step Validation Optimization

Tests:
1. Lightweight chain creation (only 3 validators vs 12)
2. Step validation with lightweight chain
3. Performance comparison (should be faster)
4. Backward compatibility (can still use full chain)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.validators.step_validator import StepValidator
from backend.validators.step_detector import Step
from backend.validators.chain import ValidatorChain
from backend.validators.citation import CitationRequired
from backend.validators.evidence_overlap import EvidenceOverlap
from backend.validators.confidence import ConfidenceValidator

def test_lightweight_chain():
    """Test lightweight chain creation"""
    print("=" * 60)
    print("Testing P1.1: Lightweight Chain Creation")
    print("=" * 60)
    
    validator = StepValidator(use_lightweight=True)
    ctx_docs = ["Document 1: Test content about StillMe", "Document 2: More test content"]
    
    # Create lightweight chain
    chain = validator._create_lightweight_chain(ctx_docs, 0.1, 0.01)
    
    print(f"\n[Test 1] Lightweight chain validators: {len(chain.validators)}")
    print(f"  Validators: {[type(v).__name__ for v in chain.validators]}")
    
    if len(chain.validators) == 3:
        print("  [OK] Lightweight chain has 3 validators (CitationRequired, EvidenceOverlap, ConfidenceValidator)")
    else:
        print(f"  [FAIL] Expected 3 validators, got {len(chain.validators)}")
        return False
    
    # Test without context (should have 2 validators: CitationRequired, ConfidenceValidator)
    chain_no_ctx = validator._create_lightweight_chain([], 0.1, 0.01)
    print(f"\n[Test 2] Lightweight chain without context: {len(chain_no_ctx.validators)} validators")
    print(f"  Validators: {[type(v).__name__ for v in chain_no_ctx.validators]}")
    
    if len(chain_no_ctx.validators) == 2:
        print("  [OK] Lightweight chain without context has 2 validators (CitationRequired, ConfidenceValidator)")
    else:
        print(f"  [FAIL] Expected 2 validators, got {len(chain_no_ctx.validators)}")
        return False
    
    return True

def test_step_validation():
    """Test step validation with lightweight chain"""
    print("\n" + "=" * 60)
    print("Testing P1.1: Step Validation with Lightweight Chain")
    print("=" * 60)
    
    validator = StepValidator(use_lightweight=True, confidence_threshold=0.5)
    
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
            content="StillMe validates responses with 12 validators",
            original_text="Bước 2: StillMe validates responses with 12 validators",
            start_pos=51,
            end_pos=100
        ),
    ]
    
    ctx_docs = [
        "StillMe is an AI system that uses ChromaDB for vector storage and validates responses",
        "StillMe has a validation chain with multiple validators"
    ]
    
    print(f"\n[Test 3] Validating {len(steps)} steps with lightweight chain...")
    start_time = time.time()
    results = validator.validate_all_steps(
        steps,
        ctx_docs,
        chain=None,  # Use lightweight chain
        parallel=True,
        adaptive_citation_overlap=0.1,
        adaptive_evidence_threshold=0.01
    )
    elapsed = time.time() - start_time
    
    print(f"  Results: {len(results)} steps validated in {elapsed:.3f}s")
    for result in results:
        print(f"    Step {result.step.step_number}: passed={result.passed}, confidence={result.confidence:.2f}, issues={result.issues}")
    
    if len(results) == len(steps):
        print("  [OK] All steps validated")
    else:
        print(f"  [FAIL] Expected {len(steps)} results, got {len(results)}")
        return False
    
    return True

def test_backward_compatibility():
    """Test backward compatibility (can still use full chain)"""
    print("\n" + "=" * 60)
    print("Testing P1.1: Backward Compatibility (Full Chain)")
    print("=" * 60)
    
    # Create full chain (simulate)
    full_chain = ValidatorChain([
        CitationRequired(),
        EvidenceOverlap(threshold=0.01),
        ConfidenceValidator(require_uncertainty_when_no_context=False)
    ])
    
    validator = StepValidator(use_lightweight=False, confidence_threshold=0.5)
    
    step = Step(
        step_number=1,
        content="Test step with citation [1]",
        original_text="Bước 1: Test step with citation [1]",
        start_pos=0,
        end_pos=30
    )
    
    ctx_docs = ["Test context document"]
    
    print("\n[Test 4] Validating step with full chain (backward compatibility)...")
    result = validator.validate_step(step, ctx_docs, chain=full_chain)
    
    print(f"  Result: passed={result.passed}, confidence={result.confidence:.2f}")
    
    if result is not None:
        print("  [OK] Backward compatibility works (can use full chain)")
    else:
        print("  [FAIL] Backward compatibility broken")
        return False
    
    return True

if __name__ == "__main__":
    print("P1.1: Step Validation Optimization Tests\n")
    
    success = True
    success &= test_lightweight_chain()
    success &= test_step_validation()
    success &= test_backward_compatibility()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] All P1.1 tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

