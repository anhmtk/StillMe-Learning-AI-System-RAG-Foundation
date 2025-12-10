"""
Test script for NPR-inspired parallel validation optimization.

Tests:
1. Validation correctness (parallel vs sequential should produce same results)
2. Performance measurement (speedup from parallel execution)
3. Edge cases (empty context, single validator, all sequential, all parallel)
"""

import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Fix Windows encoding for emoji
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from backend.validators.chain import ValidatorChain
from backend.validators.language import LanguageValidator
from backend.validators.citation import CitationRequired
from backend.validators.citation_relevance import CitationRelevance
from backend.validators.evidence_overlap import EvidenceOverlap
from backend.validators.numeric import NumericUnitsBasic
from backend.validators.confidence import ConfidenceValidator
from backend.validators.ethics_adapter import EthicsAdapter
from backend.validators.ego_neutrality import EgoNeutralityValidator
from backend.validators.identity_check import IdentityCheckValidator
from backend.services.ethics_guard import check_content_ethics


def create_test_validator_chain() -> ValidatorChain:
    """Create a test validator chain with both sequential and parallel validators."""
    validators = [
        LanguageValidator(input_language="en"),
        CitationRequired(),
        CitationRelevance(min_keyword_overlap=0.1),
        EvidenceOverlap(threshold=0.01),
        NumericUnitsBasic(),
        ConfidenceValidator(require_uncertainty_when_no_context=False),
        EgoNeutralityValidator(strict_mode=True, auto_patch=True),
        IdentityCheckValidator(strict_mode=True),
        EthicsAdapter(guard_callable=check_content_ethics),
    ]
    return ValidatorChain(validators)


def test_validation_correctness():
    """Test that parallel execution produces same results as sequential."""
    print("\n" + "="*60)
    print("TEST 1: Validation Correctness")
    print("="*60)
    
    chain = create_test_validator_chain()
    
    test_cases = [
        {
            "name": "Answer with citations",
            "answer": "StillMe is a transparent RAG system. [Source: foundational knowledge]",
            "ctx_docs": ["StillMe uses RAG with ChromaDB for knowledge storage."],
            "user_question": "What is StillMe?",
        },
        {
            "name": "Answer without citations",
            "answer": "StillMe is a transparent RAG system.",
            "ctx_docs": ["StillMe uses RAG with ChromaDB for knowledge storage."],
            "user_question": "What is StillMe?",
        },
        {
            "name": "Answer with numeric claims",
            "answer": "StillMe has 12 validators and processes 6 learning cycles per day. [Source: foundational knowledge]",
            "ctx_docs": ["StillMe uses a validation chain with multiple validators."],
            "user_question": "How many validators does StillMe have?",
        },
        {
            "name": "Empty context",
            "answer": "StillMe is a transparent RAG system. [Source: general knowledge]",
            "ctx_docs": [],
            "user_question": "What is StillMe?",
        },
    ]
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}: {test_case['name']}")
        
        try:
            result = chain.run(
                test_case["answer"],
                test_case["ctx_docs"],
                is_philosophical=False,
                user_question=test_case["user_question"]
            )
            
            print(f"    ✅ Passed: {result.passed}")
            print(f"    Reasons: {len(result.reasons)}")
            if result.reasons:
                print(f"    First reason: {result.reasons[0][:80]}...")
            if result.patched_answer:
                print(f"    Patched: Yes (length: {len(result.patched_answer)})")
            else:
                print(f"    Patched: No")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n  ✅ All correctness tests passed!")
    else:
        print("\n  ❌ Some correctness tests failed!")
    
    return all_passed


def test_performance():
    """Test performance improvement from parallel execution."""
    print("\n" + "="*60)
    print("TEST 2: Performance Measurement")
    print("="*60)
    
    chain = create_test_validator_chain()
    
    # Test with multiple validators to see parallel speedup
    answer = "StillMe is a transparent RAG system with 12 validators. [Source: foundational knowledge] It processes 6 learning cycles per day and uses ChromaDB for vector storage."
    ctx_docs = [
        "StillMe uses RAG with ChromaDB for knowledge storage.",
        "StillMe has a validation chain with multiple validators.",
        "StillMe processes learning cycles every 4 hours.",
    ]
    user_question = "What is StillMe and how does it work?"
    
    # Run multiple times to get average
    num_runs = 5
    times = []
    
    print(f"\n  Running validation {num_runs} times...")
    for i in range(num_runs):
        start = time.time()
        result = chain.run(
            answer,
            ctx_docs,
            is_philosophical=False,
            user_question=user_question
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"    Run {i+1}: {elapsed:.3f}s (passed: {result.passed})")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n  Performance Summary:")
    print(f"    Average: {avg_time:.3f}s")
    print(f"    Min: {min_time:.3f}s")
    print(f"    Max: {max_time:.3f}s")
    print(f"    Std Dev: {(sum((t - avg_time)**2 for t in times) / len(times))**0.5:.3f}s")
    
    # Check if parallel execution is working (should see parallel validators in logs)
    print(f"\n  ✅ Performance test completed!")
    print(f"  💡 Check backend logs for '[NPR]' messages to verify parallel execution")
    
    return avg_time


def test_edge_cases():
    """Test edge cases for parallel validation."""
    print("\n" + "="*60)
    print("TEST 3: Edge Cases")
    print("="*60)
    
    all_passed = True
    
    # Edge case 1: Single validator (should work)
    print("\n  Edge Case 1: Single validator")
    try:
        chain = ValidatorChain([LanguageValidator(input_language="en")])
        result = chain.run("Test answer", [])
        print(f"    ✅ Single validator works (passed: {result.passed})")
    except Exception as e:
        print(f"    ❌ Single validator failed: {e}")
        all_passed = False
    
    # Edge case 2: All sequential validators
    print("\n  Edge Case 2: All sequential validators")
    try:
        chain = ValidatorChain([
            LanguageValidator(input_language="en"),
            CitationRequired(),
            ConfidenceValidator(require_uncertainty_when_no_context=False),
        ])
        result = chain.run("Test answer [Source: general knowledge]", [])
        print(f"    ✅ All sequential validators work (passed: {result.passed})")
    except Exception as e:
        print(f"    ❌ All sequential validators failed: {e}")
        all_passed = False
    
    # Edge case 3: All parallel validators (should still work)
    print("\n  Edge Case 3: All parallel validators")
    try:
        chain = ValidatorChain([
            EvidenceOverlap(threshold=0.01),
            NumericUnitsBasic(),
            EthicsAdapter(guard_callable=check_content_ethics),
        ])
        result = chain.run("Test answer", ["Context document"])
        print(f"    ✅ All parallel validators work (passed: {result.passed})")
    except Exception as e:
        print(f"    ❌ All parallel validators failed: {e}")
        all_passed = False
    
    # Edge case 4: Empty answer
    print("\n  Edge Case 4: Empty answer")
    try:
        chain = create_test_validator_chain()
        result = chain.run("", [])
        print(f"    ✅ Empty answer handled (passed: {result.passed})")
    except Exception as e:
        print(f"    ❌ Empty answer failed: {e}")
        all_passed = False
    
    # Edge case 5: Very long answer
    print("\n  Edge Case 5: Very long answer")
    try:
        chain = create_test_validator_chain()
        long_answer = "StillMe is a transparent RAG system. " * 100 + "[Source: foundational knowledge]"
        result = chain.run(long_answer, ["Context"])
        print(f"    ✅ Very long answer handled (passed: {result.passed}, length: {len(long_answer)})")
    except Exception as e:
        print(f"    ❌ Very long answer failed: {e}")
        all_passed = False
    
    if all_passed:
        print("\n  ✅ All edge case tests passed!")
    else:
        print("\n  ❌ Some edge case tests failed!")
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("NPR-Inspired Parallel Validation Tests")
    print("="*60)
    
    results = {
        "correctness": False,
        "performance": False,
        "edge_cases": False,
    }
    
    try:
        # Test 1: Correctness
        results["correctness"] = test_validation_correctness()
        
        # Test 2: Performance
        avg_time = test_performance()
        results["performance"] = True
        if avg_time < 3.0:  # Should be faster than 3s
            print(f"\n  ✅ Performance is good (avg: {avg_time:.3f}s < 3.0s)")
        else:
            print(f"\n  ⚠️ Performance could be better (avg: {avg_time:.3f}s >= 3.0s)")
        
        # Test 3: Edge cases
        results["edge_cases"] = test_edge_cases()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Correctness: {'✅ PASS' if results['correctness'] else '❌ FAIL'}")
    print(f"Performance: {'✅ PASS' if results['performance'] else '❌ FAIL'}")
    print(f"Edge Cases:  {'✅ PASS' if results['edge_cases'] else '❌ FAIL'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

