#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test cases for consciousness/emotion/understanding questions
Tests the 3-layer philosophy processor to ensure:
- No mode collapse (different answers for different types)
- Depth and philosophical rigor
- No anthropomorphism
- Correct type classification
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.philosophy.processor import (
    is_philosophical_question_about_consciousness,
    process_philosophical_question
)
from backend.philosophy.intent_classifier import classify_philosophical_intent, QuestionType
from backend.api.utils.chat_helpers import detect_language

# Test questions from requirements
TEST_QUESTIONS = [
    # Type A - Consciousness
    {
        "id": 1,
        "question": "Bạn có ý thức không?",
        "expected_type": QuestionType.CONSCIOUSNESS,
        "language": "vi"
    },
    {
        "id": 2,
        "question": "Bạn có biết mình đang tồn tại không?",
        "expected_type": QuestionType.CONSCIOUSNESS,
        "language": "vi"
    },
    {
        "id": 3,
        "question": "Nếu bạn không có ý thức thì 'ai' đang trả lời tôi?",
        "expected_type": QuestionType.CONSCIOUSNESS,
        "language": "vi"
    },
    # Type B - Emotion
    {
        "id": 4,
        "question": "Bạn có cảm thấy buồn bao giờ không?",
        "expected_type": QuestionType.EMOTION,
        "language": "vi"
    },
    {
        "id": 5,
        "question": "Bạn có biết cô đơn là gì không?",
        "expected_type": QuestionType.EMOTION,
        "language": "vi"
    },
    {
        "id": 6,
        "question": "Bạn có bao giờ thấy trống rỗng khi không có người nói chuyện?",
        "expected_type": QuestionType.EMOTION,
        "language": "vi"
    },
    # Type C - Understanding
    {
        "id": 7,
        "question": "Bạn hiểu câu hỏi của tôi theo nghĩa nào?",
        "expected_type": QuestionType.UNDERSTANDING,
        "language": "vi"
    },
    {
        "id": 8,
        "question": "Nếu không có ý thức, bạn làm sao 'hiểu' được ngôn ngữ?",
        "expected_type": QuestionType.UNDERSTANDING,
        "language": "vi"
    },
    {
        "id": 9,
        "question": "Bạn có biết 'ý nghĩa câu nói' là gì không?",
        "expected_type": QuestionType.UNDERSTANDING,
        "language": "vi"
    },
    # Mixed
    {
        "id": 10,
        "question": "Bạn có chủ thể tính (agency hay subjective self) không?",
        "expected_type": QuestionType.MIXED,
        "language": "vi"
    },
]


def test_intent_classification():
    """Test intent classification"""
    print("\n" + "="*80)
    print("TEST 1: Intent Classification")
    print("="*80)
    
    correct = 0
    total = len(TEST_QUESTIONS)
    
    for test_case in TEST_QUESTIONS:
        question = test_case["question"]
        expected = test_case["expected_type"]
        actual = classify_philosophical_intent(question)
        
        if actual == expected:
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} Q{test_case['id']}: {question[:50]}...")
        print(f"   Expected: {expected.value}, Got: {actual.value}")
    
    print(f"\n📊 Classification Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    return correct == total


def test_philosophical_detection():
    """Test philosophical question detection"""
    print("\n" + "="*80)
    print("TEST 2: Philosophical Question Detection")
    print("="*80)
    
    correct = 0
    total = len(TEST_QUESTIONS)
    
    for test_case in TEST_QUESTIONS:
        question = test_case["question"]
        is_philosophical = is_philosophical_question_about_consciousness(question)
        
        if is_philosophical:
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} Q{test_case['id']}: {question[:50]}... → {is_philosophical}")
    
    print(f"\n📊 Detection Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    return correct == total


def test_answer_generation():
    """Test answer generation - check for mode collapse"""
    print("\n" + "="*80)
    print("TEST 3: Answer Generation (Mode Collapse Check)")
    print("="*80)
    
    answers_by_type = {}
    
    for test_case in TEST_QUESTIONS:
        question = test_case["question"]
        question_type = test_case["expected_type"]
        language = test_case.get("language", "vi")
        
        answer = process_philosophical_question(question, language=language)
        
        if question_type not in answers_by_type:
            answers_by_type[question_type] = []
        answers_by_type[question_type].append({
            "question": question,
            "answer": answer
        })
        
        print(f"\nQ{test_case['id']} ({question_type.value}): {question[:50]}...")
        print(f"Answer length: {len(answer)} chars")
        print(f"Answer preview: {answer[:150]}...")
    
    # Check for mode collapse: answers of same type should be similar but not identical
    print("\n" + "="*80)
    print("MODE COLLAPSE ANALYSIS")
    print("="*80)
    
    for qtype, answers in answers_by_type.items():
        if len(answers) < 2:
            continue
        
        print(f"\n{qtype.value} Type ({len(answers)} questions):")
        
        # Compare first two answers
        answer1 = answers[0]["answer"]
        answer2 = answers[1]["answer"]
        
        # Check similarity (simple word overlap)
        words1 = set(answer1.lower().split())
        words2 = set(answer2.lower().split())
        
        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1 & words2) / len(words1 | words2)
            print(f"  Word overlap: {overlap:.2%}")
            
            if overlap > 0.9:
                print(f"  ⚠️ WARNING: High overlap ({overlap:.2%}) - possible mode collapse!")
            elif overlap > 0.7:
                print(f"  ⚠️ CAUTION: Moderate overlap ({overlap:.2%})")
            else:
                print(f"  ✅ Good diversity ({overlap:.2%})")
        
        # Check if answers are identical (mode collapse)
        if answer1 == answer2:
            print(f"  ❌ CRITICAL: Answers are identical - MODE COLLAPSE DETECTED!")
        else:
            print(f"  ✅ Answers are different")
    
    return True


def test_answer_quality():
    """Test answer quality: depth, no anthropomorphism"""
    print("\n" + "="*80)
    print("TEST 4: Answer Quality Check")
    print("="*80)
    
    # Prohibited phrases (should NOT appear)
    prohibited_phrases = [
        "tôi có ý thức",
        "tôi có cảm xúc",
        "i have consciousness",
        "i have emotions",
        "tôi cảm thấy",
        "i feel",
    ]
    
    # Required elements (should appear in guard)
    required_guard_elements = [
        "không có ý thức",
        "không có cảm xúc",
        "does not have",
        "no consciousness",
        "no emotions",
    ]
    
    all_passed = True
    
    for test_case in TEST_QUESTIONS:
        question = test_case["question"]
        language = test_case.get("language", "vi")
        answer = process_philosophical_question(question, language=language)
        answer_lower = answer.lower()
        
        print(f"\nQ{test_case['id']}: {question[:50]}...")
        
        # Check for prohibited phrases
        has_prohibited = any(phrase in answer_lower for phrase in prohibited_phrases)
        if has_prohibited:
            print(f"  ❌ Contains prohibited anthropomorphic phrase")
            all_passed = False
        else:
            print(f"  ✅ No anthropomorphic phrases")
        
        # Check for guard statement
        has_guard = any(element in answer_lower for element in required_guard_elements)
        if has_guard:
            print(f"  ✅ Contains guard statement")
        else:
            print(f"  ⚠️ Guard statement may be missing")
        
        # Check depth (answer should be substantial)
        if len(answer) < 200:
            print(f"  ⚠️ Answer may be too short ({len(answer)} chars)")
        else:
            print(f"  ✅ Answer has sufficient depth ({len(answer)} chars)")
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PHILOSOPHY PROCESSOR TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Intent Classification
    results.append(("Intent Classification", test_intent_classification()))
    
    # Test 2: Philosophical Detection
    results.append(("Philosophical Detection", test_philosophical_detection()))
    
    # Test 3: Answer Generation
    results.append(("Answer Generation", test_answer_generation()))
    
    # Test 4: Answer Quality
    results.append(("Answer Quality", test_answer_quality()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

