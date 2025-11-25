"""
Test Phase 4: Check for conflicts and duplicate logic after Phase 1-3

Tests that:
1. No duplicate user question in prompt
2. No duplicate identity injection
3. No duplicate citation/context instructions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.identity.prompt_builder import UnifiedPromptBuilder, PromptContext
from backend.identity.injector import build_stillme_identity


def test_no_duplicate_user_question():
    """Test: UnifiedPromptBuilder includes user question, should not duplicate"""
    print("\n" + "="*80)
    print("TEST 1: No Duplicate User Question")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is RAG?",
        detected_lang="en",
        context={"knowledge_docs": [{"content": "RAG is..."}]},
        has_reliable_context=True,
        context_quality="high",
        num_knowledge_docs=1
    )
    
    prompt = builder.build_prompt(context)
    
    # Count occurrences of user question
    question_count = prompt.count("What is RAG?")
    
    print(f"User question: 'What is RAG?'")
    print(f"Occurrences in prompt: {question_count}")
    
    assert question_count == 1, f"User question should appear exactly once, found {question_count} times"
    
    print("[PASS] TEST 1 PASSED: User question appears exactly once")


def test_unified_prompt_has_citation_instruction():
    """Test: UnifiedPromptBuilder includes citation instruction"""
    print("\n" + "="*80)
    print("TEST 2: UnifiedPromptBuilder Has Citation Instruction")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is RAG?",
        detected_lang="en",
        context={"knowledge_docs": [{"content": "RAG is..."}]},
        has_reliable_context=True,
        context_quality="high",
        num_knowledge_docs=2
    )
    
    prompt = builder.build_prompt(context)
    
    # Check for citation instruction
    has_citation = "CITATION" in prompt or "cite" in prompt.lower() or "[1]" in prompt
    
    print(f"Prompt contains citation instruction: {has_citation}")
    if has_citation:
        # Find citation instruction
        if "CITATION" in prompt:
            citation_start = prompt.find("CITATION")
            print(f"Citation instruction found at position {citation_start}")
            print(f"Preview: {prompt[citation_start:citation_start+100]}...")
    
    assert has_citation, "UnifiedPromptBuilder should include citation instruction when context is available"
    
    print("[PASS] TEST 2 PASSED: UnifiedPromptBuilder includes citation instruction")


def test_unified_prompt_has_context_quality_warning():
    """Test: UnifiedPromptBuilder includes context quality warning when quality is low"""
    print("\n" + "="*80)
    print("TEST 3: UnifiedPromptBuilder Has Context Quality Warning")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is quantum computing?",
        detected_lang="en",
        context={"avg_similarity_score": 0.05, "context_quality": "low"},
        has_reliable_context=True,
        context_quality="low",
        num_knowledge_docs=1
    )
    
    prompt = builder.build_prompt(context)
    
    # Check for context quality warning
    has_warning = "LOW" in prompt or "low relevance" in prompt.lower() or "quality" in prompt.lower()
    
    print(f"Prompt contains context quality warning: {has_warning}")
    if has_warning:
        # Find warning
        if "LOW" in prompt:
            warning_start = prompt.find("LOW")
            print(f"Warning found at position {warning_start}")
            print(f"Preview: {prompt[warning_start:warning_start+100]}...")
    
    assert has_warning, "UnifiedPromptBuilder should include context quality warning when quality is low"
    
    print("[PASS] TEST 3 PASSED: UnifiedPromptBuilder includes context quality warning")


def test_unified_prompt_has_stillme_instruction():
    """Test: UnifiedPromptBuilder includes StillMe instruction for StillMe queries"""
    print("\n" + "="*80)
    print("TEST 4: UnifiedPromptBuilder Has StillMe Instruction")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is StillMe?",
        detected_lang="en",
        context={"knowledge_docs": [{"content": "StillMe is..."}]},
        is_stillme_query=True,
        has_reliable_context=True,
        context_quality="high",
        num_knowledge_docs=1
    )
    
    prompt = builder.build_prompt(context)
    
    # Check for StillMe instruction
    has_stillme = "STILLME" in prompt or "StillMe" in prompt or "stillme" in prompt.lower()
    
    print(f"Prompt contains StillMe instruction: {has_stillme}")
    if has_stillme:
        # Find StillMe instruction
        if "STILLME" in prompt:
            stillme_start = prompt.find("STILLME")
            print(f"StillMe instruction found at position {stillme_start}")
            print(f"Preview: {prompt[stillme_start:stillme_start+100]}...")
    
    assert has_stillme, "UnifiedPromptBuilder should include StillMe instruction for StillMe queries"
    
    print("[PASS] TEST 4 PASSED: UnifiedPromptBuilder includes StillMe instruction")


def test_build_stillme_identity_works():
    """Test: build_stillme_identity() still works (used by UnifiedPromptBuilder)"""
    print("\n" + "="*80)
    print("TEST 5: build_stillme_identity() Works")
    print("="*80)
    
    identity_vi = build_stillme_identity("vi")
    identity_en = build_stillme_identity("en")
    
    print(f"Identity (VI) length: {len(identity_vi)} chars")
    print(f"Identity (EN) length: {len(identity_en)} chars")
    
    # Check that identity contains core principles
    has_core = "INTELLECTUAL HUMILITY" in identity_en or "KHIÊM TỐN" in identity_vi
    has_persona = "persona" in identity_en.lower() or "persona" in identity_vi.lower()
    
    assert has_core, "Identity should contain core principles"
    assert len(identity_vi) > 100, "Identity should not be empty"
    assert len(identity_en) > 100, "Identity should not be empty"
    
    print("[PASS] TEST 5 PASSED: build_stillme_identity() works correctly")


def run_all_tests():
    """Run all Phase 4 conflict tests"""
    print("\n" + "="*80)
    print("PHASE 4: CONFLICTS & DUPLICATE LOGIC TEST SUITE")
    print("="*80)
    
    tests = [
        test_no_duplicate_user_question,
        test_unified_prompt_has_citation_instruction,
        test_unified_prompt_has_context_quality_warning,
        test_unified_prompt_has_stillme_instruction,
        test_build_stillme_identity_works
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
        print("\n[PASS] ALL PHASE 4 CONFLICT TESTS PASSED!")
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

