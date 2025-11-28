"""
Test script for EpistemicState classification

Tests the calculate_epistemic_state() function with various scenarios:
- KNOWN: High confidence, good citations, validation passed
- UNCERTAIN: Medium confidence, some warnings, or citations without context
- UNKNOWN: Fallback triggered, no context, critical validation failures
"""

import sys
import os
import logging

# Force UTF-8 encoding for console output (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 doesn't have reconfigure
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.core.epistemic_state import calculate_epistemic_state, EpistemicState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_known_state():
    """Test KNOWN state: high confidence, good citations, validation passed"""
    print("\n" + "="*60)
    print("TEST 1: KNOWN State")
    print("="*60)
    
    validation_info = {
        "passed": True,
        "reasons": [],
        "used_fallback": False,
        "confidence_score": 0.85,
        "context_docs_count": 3
    }
    
    response_text = "According to [1] and [2], the answer is X. [general knowledge] This is supported by multiple sources."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.85,
        response_text=response_text,
        context_docs_count=3
    )
    
    print(f"Expected: KNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.KNOWN else f"❌ FAIL")
    return state == EpistemicState.KNOWN


def test_uncertain_state():
    """Test UNCERTAIN state: medium confidence, some warnings"""
    print("\n" + "="*60)
    print("TEST 2: UNCERTAIN State")
    print("="*60)
    
    validation_info = {
        "passed": True,
        "reasons": ["citation_relevance_warning"],
        "used_fallback": False,
        "confidence_score": 0.55,
        "context_docs_count": 1
    }
    
    response_text = "Based on [1], the answer might be X. [general knowledge] However, there is some uncertainty."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.55,
        response_text=response_text,
        context_docs_count=1
    )
    
    print(f"Expected: UNCERTAIN")
    print(f"Got: {state.value}")
    print(f"[PASS]" if state == EpistemicState.UNCERTAIN else f"[FAIL]")
    return state == EpistemicState.UNCERTAIN


def test_unknown_fallback():
    """Test UNKNOWN state: fallback triggered"""
    print("\n" + "="*60)
    print("TEST 3: UNKNOWN State (Fallback)")
    print("="*60)
    
    validation_info = {
        "passed": False,
        "reasons": ["missing_citation"],
        "used_fallback": True,
        "confidence_score": 0.2,
        "context_docs_count": 0
    }
    
    response_text = "I don't have sufficient information to answer this question accurately."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.2,
        response_text=response_text,
        context_docs_count=0
    )
    
    print(f"Expected: UNKNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.UNKNOWN else f"❌ FAIL")
    return state == EpistemicState.UNKNOWN


def test_unknown_no_context():
    """Test UNKNOWN state: no context, low confidence"""
    print("\n" + "="*60)
    print("TEST 4: UNKNOWN State (No Context)")
    print("="*60)
    
    validation_info = {
        "passed": True,
        "reasons": [],
        "used_fallback": False,
        "confidence_score": 0.3,
        "context_docs_count": 0
    }
    
    response_text = "Based on general knowledge, the answer might be X."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.3,
        response_text=response_text,
        context_docs_count=0
    )
    
    print(f"Expected: UNKNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.UNKNOWN else f"❌ FAIL")
    return state == EpistemicState.UNKNOWN


def test_unknown_critical_failure():
    """Test UNKNOWN state: critical validation failure"""
    print("\n" + "="*60)
    print("TEST 5: UNKNOWN State (Critical Failure)")
    print("="*60)
    
    validation_info = {
        "passed": False,
        "reasons": ["factual_hallucination", "explicit_fake_entity"],
        "used_fallback": False,
        "confidence_score": 0.5,
        "context_docs_count": 2
    }
    
    response_text = "According to [1], the answer is X."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.5,
        response_text=response_text,
        context_docs_count=2
    )
    
    print(f"Expected: UNKNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.UNKNOWN else f"❌ FAIL")
    return state == EpistemicState.UNKNOWN


def test_uncertain_citations_no_context():
    """Test UNCERTAIN state: has citations but no RAG context (general knowledge)"""
    print("\n" + "="*60)
    print("TEST 6: UNCERTAIN State (Citations but No Context)")
    print("="*60)
    
    validation_info = {
        "passed": True,
        "reasons": [],
        "used_fallback": False,
        "confidence_score": 0.6,
        "context_docs_count": 0
    }
    
    response_text = "Based on [general knowledge], the answer is X."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.6,
        response_text=response_text,
        context_docs_count=0
    )
    
    print(f"Expected: UNCERTAIN")
    print(f"Got: {state.value}")
    print(f"[PASS]" if state == EpistemicState.UNCERTAIN else f"[FAIL]")
    return state == EpistemicState.UNCERTAIN


def test_known_high_confidence_with_warnings():
    """Test KNOWN state: high confidence even with warnings"""
    print("\n" + "="*60)
    print("TEST 7: KNOWN State (High Confidence with Warnings)")
    print("="*60)
    
    validation_info = {
        "passed": True,
        "reasons": ["citation_relevance_warning"],
        "used_fallback": False,
        "confidence_score": 0.85,
        "context_docs_count": 3
    }
    
    response_text = "According to [1] and [2], the answer is X."
    
    state = calculate_epistemic_state(
        validation_info=validation_info,
        confidence_score=0.85,
        response_text=response_text,
        context_docs_count=3
    )
    
    print(f"Expected: KNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.KNOWN else f"❌ FAIL")
    return state == EpistemicState.KNOWN


def test_edge_case_none_values():
    """Test edge case: None values"""
    print("\n" + "="*60)
    print("TEST 8: Edge Case (None Values)")
    print("="*60)
    
    state = calculate_epistemic_state(
        validation_info=None,
        confidence_score=None,
        response_text=None,
        context_docs_count=0
    )
    
    print(f"Expected: UNKNOWN")
    print(f"Got: {state.value}")
    print(f"✅ PASS" if state == EpistemicState.UNKNOWN else f"❌ FAIL")
    return state == EpistemicState.UNKNOWN


def main():
    """Run all tests"""
    print("="*60)
    print("EPISTEMIC STATE CLASSIFICATION TESTS")
    print("="*60)
    
    tests = [
        test_known_state,
        test_uncertain_state,
        test_unknown_fallback,
        test_unknown_no_context,
        test_unknown_critical_failure,
        test_uncertain_citations_no_context,
        test_known_high_confidence_with_warnings,
        test_edge_case_none_values
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with error: {e}", exc_info=True)
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

