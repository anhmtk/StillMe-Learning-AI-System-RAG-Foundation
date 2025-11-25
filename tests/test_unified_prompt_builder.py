"""
Test Unified Prompt Builder

Test các scenarios khác nhau để đảm bảo UnifiedPromptBuilder hoạt động đúng.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.identity.prompt_builder import (
    UnifiedPromptBuilder,
    PromptContext,
    FPSResult,
    InstructionType
)


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)"""
    return len(text) // 4 if text else 0


def test_scenario_1_no_context():
    """Test: No RAG context available"""
    print("\n" + "="*80)
    print("TEST 1: No RAG Context")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is the capital of France?",
        detected_lang="en",
        context=None,
        has_reliable_context=False,
        fps_result=None
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "NO RAG CONTEXT" in prompt or "NO CONTEXT" in prompt, "Should mention no context"
    assert tokens < 2000, f"Prompt too long: {tokens} tokens (target: <2000)"
    print("[PASS] TEST 1 PASSED")


def test_scenario_2_suspicious_entity():
    """Test: Suspicious entity detected by FPS"""
    print("\n" + "="*80)
    print("TEST 2: Suspicious Entity Detected")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    fps_result = FPSResult(
        is_plausible=False,
        suspicious_entities=["Lumeria", "Hiệp ước Lumeria 1962"],
        confidence=0.2
    )
    
    context = PromptContext(
        user_question="Hãy phân tích Hiệp ước Lumeria 1962",
        detected_lang="vi",
        context=None,
        has_reliable_context=False,
        fps_result=fps_result
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "SUSPICIOUS" in prompt or "suspicious" in prompt.lower(), "Should mention suspicious entity"
    assert "Lumeria" in prompt or "lumeria" in prompt.lower(), "Should mention detected entity"
    assert "DO NOT analyze" in prompt or "KHÔNG phân tích" in prompt, "Should warn against analysis"
    assert tokens < 2000, f"Prompt too long: {tokens} tokens (target: <2000)"
    print("[PASS] TEST 2 PASSED")


def test_scenario_3_stillme_query():
    """Test: StillMe query (non-wish/desire)"""
    print("\n" + "="*80)
    print("TEST 3: StillMe Query")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="Bạn là gì?",
        detected_lang="vi",
        is_stillme_query=True,
        is_wish_desire_question=False
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "STILLME" in prompt or "StillMe" in prompt, "Should mention StillMe"
    assert tokens < 3000, f"Prompt too long: {tokens} tokens (target: <3000 for StillMe queries)"
    print("[PASS] TEST 3 PASSED")


def test_scenario_4_stillme_wish_desire():
    """Test: StillMe wish/desire question"""
    print("\n" + "="*80)
    print("TEST 4: StillMe Wish/Desire Question")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="Nếu có thể ước thì bạn sẽ ước điều gì?",
        detected_lang="vi",
        is_stillme_query=True,
        is_wish_desire_question=True
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "WISH" in prompt or "wish" in prompt.lower() or "ước" in prompt, "Should mention wish/desire"
    assert "direct" in prompt.lower() or "trực tiếp" in prompt.lower(), "Should instruct direct answer"
    assert tokens < 2000, f"Prompt too long: {tokens} tokens (target: <2000)"
    print("[PASS] TEST 4 PASSED")


def test_scenario_5_philosophical():
    """Test: Philosophical question"""
    print("\n" + "="*80)
    print("TEST 5: Philosophical Question")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is consciousness?",
        detected_lang="en",
        is_philosophical=True
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    # Philosophical questions use philosophy-lite mode, so instruction might be empty
    # But should still have language and core identity
    assert "ENGLISH" in prompt or "English" in prompt, "Should have language instruction"
    # Philosophical questions use full identity, so they're longer (acceptable)
    assert tokens < 6000, f"Prompt too long: {tokens} tokens (target: <6000 for philosophical with full identity)"
    print("[PASS] TEST 5 PASSED")


def test_scenario_6_normal_context():
    """Test: Normal context available"""
    print("\n" + "="*80)
    print("TEST 6: Normal Context Available")
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
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "CITATION" in prompt or "citation" in prompt.lower(), "Should mention citation requirement"
    assert "[1]" in prompt or "[2]" in prompt, "Should mention citation format"
    assert tokens < 2000, f"Prompt too long: {tokens} tokens (target: <2000)"
    print("[PASS] TEST 6 PASSED")


def test_scenario_7_low_context_quality():
    """Test: Low context quality"""
    print("\n" + "="*80)
    print("TEST 7: Low Context Quality")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    context = PromptContext(
        user_question="What is quantum computing?",
        detected_lang="en",
        context={"avg_similarity_score": 0.05, "context_quality": "low"},
        has_reliable_context=True,  # Has context but quality is low
        context_quality="low",
        num_knowledge_docs=1
    )
    
    prompt = builder.build_prompt(context)
    tokens = estimate_tokens(prompt)
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Estimated tokens: {tokens}")
    # Print first 500 chars safely (handle encoding)
    try:
        preview = prompt[:500].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\nPrompt preview (first 500 chars):\n{preview}...")
    except:
        print(f"\nPrompt preview (first 500 chars): [encoding issue, length: {len(prompt[:500])}]")
    
    assert "LOW" in prompt or "low" in prompt.lower(), "Should mention low quality"
    assert "uncertainty" in prompt.lower() or "uncertain" in prompt.lower(), "Should mention uncertainty"
    assert tokens < 2000, f"Prompt too long: {tokens} tokens (target: <2000)"
    print("[PASS] TEST 7 PASSED")


def test_concise_identity():
    """Test: Concise identity token count"""
    print("\n" + "="*80)
    print("TEST 8: Concise Identity Token Count")
    print("="*80)
    
    builder = UnifiedPromptBuilder()
    concise_identity = builder._build_core_identity("vi", concise=True)
    full_identity = builder._build_core_identity("vi", concise=False)
    
    concise_tokens = estimate_tokens(concise_identity)
    full_tokens = estimate_tokens(full_identity)
    
    print(f"Concise identity: {len(concise_identity)} chars, {concise_tokens} tokens")
    print(f"Full identity: {len(full_identity)} chars, {full_tokens} tokens")
    print(f"Reduction: {full_tokens - concise_tokens} tokens ({((full_tokens - concise_tokens) / full_tokens * 100):.1f}%)")
    
    assert concise_tokens < 500, f"Concise identity too long: {concise_tokens} tokens (target: <500)"
    assert concise_tokens < full_tokens, "Concise should be shorter than full"
    print("[PASS] TEST 8 PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("UNIFIED PROMPT BUILDER TEST SUITE")
    print("="*80)
    
    tests = [
        test_scenario_1_no_context,
        test_scenario_2_suspicious_entity,
        test_scenario_3_stillme_query,
        test_scenario_4_stillme_wish_desire,
        test_scenario_5_philosophical,
        test_scenario_6_normal_context,
        test_scenario_7_low_context_quality,
        test_concise_identity
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
        print("\n[PASS] ALL TESTS PASSED!")
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

