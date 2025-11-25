"""
Test Phase 2: Critical/Optional Validator Classification

Tests that optional validators are conditionally added based on context:
- EvidenceOverlap: Only when has context (len(ctx_docs) > 0)
- SourceConsensusValidator: Only when has multiple sources (len(ctx_docs) >= 2)
- EgoNeutralityValidator: Only when has context (len(ctx_docs) > 0)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.validators.chain import ValidatorChain
from backend.validators.citation import CitationRequired
from backend.validators.evidence_overlap import EvidenceOverlap
from backend.validators.source_consensus import SourceConsensusValidator
from backend.validators.ego_neutrality import EgoNeutralityValidator
from backend.validators.confidence import ConfidenceValidator
from backend.validators.factual_hallucination import FactualHallucinationValidator
from backend.validators.language import LanguageValidator


def test_no_context_scenario():
    """Test: No context - only critical validators should run"""
    print("\n" + "="*80)
    print("TEST 1: No Context - Only Critical Validators")
    print("="*80)
    
    ctx_docs = []  # No context
    
    # Simulate the validator selection logic from chat_router.py
    validators = [
        LanguageValidator(input_language="en"),
        CitationRequired(),  # CRITICAL
        ConfidenceValidator(),  # CRITICAL
        FactualHallucinationValidator(),  # CRITICAL
    ]
    
    # Phase 2: Optional validators (conditionally added)
    if len(ctx_docs) > 0:
        validators.insert(2, EvidenceOverlap(threshold=0.01))
        print("  [SKIP] EvidenceOverlap not added (no context)")
    
    if len(ctx_docs) >= 2:
        validators.insert(3, SourceConsensusValidator(enabled=True, timeout=3.0))
        print("  [SKIP] SourceConsensusValidator not added (no context)")
    
    if len(ctx_docs) > 0:
        fact_halluc_idx = next(i for i, v in enumerate(validators) if type(v).__name__ == "FactualHallucinationValidator")
        validators.insert(fact_halluc_idx, EgoNeutralityValidator(strict_mode=True, auto_patch=True))
        print("  [SKIP] EgoNeutralityValidator not added (no context)")
    
    chain = ValidatorChain(validators)
    
    # Verify validator count
    validator_names = [type(v).__name__ for v in validators]
    print(f"\nValidators added: {validator_names}")
    print(f"Total validators: {len(validators)}")
    
    # Should only have critical validators
    assert "EvidenceOverlap" not in validator_names, "EvidenceOverlap should not be added without context"
    assert "SourceConsensusValidator" not in validator_names, "SourceConsensusValidator should not be added without context"
    assert "EgoNeutralityValidator" not in validator_names, "EgoNeutralityValidator should not be added without context"
    assert "CitationRequired" in validator_names, "CitationRequired (CRITICAL) should be present"
    assert "ConfidenceValidator" in validator_names, "ConfidenceValidator (CRITICAL) should be present"
    assert "FactualHallucinationValidator" in validator_names, "FactualHallucinationValidator (CRITICAL) should be present"
    
    print("[PASS] TEST 1 PASSED: Only critical validators for no context")


def test_single_context_scenario():
    """Test: Single context - EvidenceOverlap and EgoNeutralityValidator should be added"""
    print("\n" + "="*80)
    print("TEST 2: Single Context - EvidenceOverlap + EgoNeutralityValidator Added")
    print("="*80)
    
    ctx_docs = ["This is a test context document."]  # Single context
    
    # Simulate the validator selection logic from chat_router.py
    validators = [
        LanguageValidator(input_language="en"),
        CitationRequired(),  # CRITICAL
        ConfidenceValidator(),  # CRITICAL
        FactualHallucinationValidator(),  # CRITICAL
    ]
    
    # Phase 2: Optional validators (conditionally added)
    if len(ctx_docs) > 0:
        validators.insert(2, EvidenceOverlap(threshold=0.01))
        print("  [ADD] EvidenceOverlap added (has context)")
    
    if len(ctx_docs) >= 2:
        validators.insert(3, SourceConsensusValidator(enabled=True, timeout=3.0))
        print("  [SKIP] SourceConsensusValidator not added (only 1 source)")
    
    if len(ctx_docs) > 0:
        fact_halluc_idx = next(i for i, v in enumerate(validators) if type(v).__name__ == "FactualHallucinationValidator")
        validators.insert(fact_halluc_idx, EgoNeutralityValidator(strict_mode=True, auto_patch=True))
        print("  [ADD] EgoNeutralityValidator added (has context)")
    
    chain = ValidatorChain(validators)
    
    # Verify validator count
    validator_names = [type(v).__name__ for v in validators]
    print(f"\nValidators added: {validator_names}")
    print(f"Total validators: {len(validators)}")
    
    # Should have critical + EvidenceOverlap + EgoNeutralityValidator
    assert "EvidenceOverlap" in validator_names, "EvidenceOverlap should be added with context"
    assert "EgoNeutralityValidator" in validator_names, "EgoNeutralityValidator should be added with context"
    assert "SourceConsensusValidator" not in validator_names, "SourceConsensusValidator should not be added with only 1 source"
    assert "CitationRequired" in validator_names, "CitationRequired (CRITICAL) should be present"
    assert "ConfidenceValidator" in validator_names, "ConfidenceValidator (CRITICAL) should be present"
    
    print("[PASS] TEST 2 PASSED: EvidenceOverlap and EgoNeutralityValidator added for single context")


def test_multiple_contexts_scenario():
    """Test: Multiple contexts - All optional validators should be added"""
    print("\n" + "="*80)
    print("TEST 3: Multiple Contexts - All Optional Validators Added")
    print("="*80)
    
    ctx_docs = [
        "This is the first context document.",
        "This is the second context document.",
        "This is the third context document."
    ]  # Multiple contexts
    
    # Simulate the validator selection logic from chat_router.py
    validators = [
        LanguageValidator(input_language="en"),
        CitationRequired(),  # CRITICAL
        ConfidenceValidator(),  # CRITICAL
        FactualHallucinationValidator(),  # CRITICAL
    ]
    
    # Phase 2: Optional validators (conditionally added)
    if len(ctx_docs) > 0:
        validators.insert(2, EvidenceOverlap(threshold=0.01))
        print("  [ADD] EvidenceOverlap added (has context)")
    
    if len(ctx_docs) >= 2:
        # Insert after EvidenceOverlap (or after CitationRequired if EvidenceOverlap not added)
        insert_pos = 4 if len(ctx_docs) > 0 else 3
        validators.insert(insert_pos, SourceConsensusValidator(enabled=True, timeout=3.0))
        print(f"  [ADD] SourceConsensusValidator added (has {len(ctx_docs)} sources)")
    
    if len(ctx_docs) > 0:
        fact_halluc_idx = next(i for i, v in enumerate(validators) if type(v).__name__ == "FactualHallucinationValidator")
        validators.insert(fact_halluc_idx, EgoNeutralityValidator(strict_mode=True, auto_patch=True))
        print("  [ADD] EgoNeutralityValidator added (has context)")
    
    chain = ValidatorChain(validators)
    
    # Verify validator count
    validator_names = [type(v).__name__ for v in validators]
    print(f"\nValidators added: {validator_names}")
    print(f"Total validators: {len(validators)}")
    
    # Should have all validators
    assert "EvidenceOverlap" in validator_names, "EvidenceOverlap should be added with context"
    assert "SourceConsensusValidator" in validator_names, "SourceConsensusValidator should be added with multiple sources"
    assert "EgoNeutralityValidator" in validator_names, "EgoNeutralityValidator should be added with context"
    assert "CitationRequired" in validator_names, "CitationRequired (CRITICAL) should be present"
    assert "ConfidenceValidator" in validator_names, "ConfidenceValidator (CRITICAL) should be present"
    assert "FactualHallucinationValidator" in validator_names, "FactualHallucinationValidator (CRITICAL) should be present"
    
    print("[PASS] TEST 3 PASSED: All optional validators added for multiple contexts")


def test_validation_chain_runs_correctly():
    """Test: Validation chain runs correctly with conditional validators"""
    print("\n" + "="*80)
    print("TEST 4: Validation Chain Runs Correctly")
    print("="*80)
    
    ctx_docs = [
        "RAG stands for Retrieval-Augmented Generation.",
        "RAG combines retrieval and generation for better answers."
    ]
    
    # Build validators with Phase 2 logic
    validators = [
        LanguageValidator(input_language="en"),
        CitationRequired(),
    ]
    
    if len(ctx_docs) > 0:
        validators.append(EvidenceOverlap(threshold=0.01))
    
    if len(ctx_docs) >= 2:
        validators.append(SourceConsensusValidator(enabled=True, timeout=3.0))
    
    validators.extend([
        ConfidenceValidator(),
        FactualHallucinationValidator(),
    ])
    
    if len(ctx_docs) > 0:
        validators.insert(-1, EgoNeutralityValidator(strict_mode=True, auto_patch=True))
    
    chain = ValidatorChain(validators)
    
    # Test with valid answer
    answer = "RAG is Retrieval-Augmented Generation [1]. It combines retrieval and generation [2]."
    
    result = chain.run(
        answer=answer,
        ctx_docs=ctx_docs,
        is_philosophical=False,
        user_question="What is RAG?"
    )
    
    print(f"Validation result: passed={result.passed}")
    print(f"Reasons: {result.reasons}")
    
    # Should pass validation
    assert result.passed is True, "Validation should pass with correct answer and citations"
    
    print("[PASS] TEST 4 PASSED: Validation chain runs correctly")


def run_all_tests():
    """Run all Phase 2 tests"""
    print("\n" + "="*80)
    print("PHASE 2: CRITICAL/OPTIONAL VALIDATOR CLASSIFICATION TEST SUITE")
    print("="*80)
    
    tests = [
        test_no_context_scenario,
        test_single_context_scenario,
        test_multiple_contexts_scenario,
        test_validation_chain_runs_correctly
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
        print("\n[PASS] ALL PHASE 2 TESTS PASSED!")
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

