#!/usr/bin/env python3
"""
Test script for self-reference paradox questions.
Tests StillMe's ability to answer philosophical questions about bootstrapping problem.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Get API URL
API_URL = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))
if API_URL and not API_URL.startswith(("http://", "https://")):
    API_URL = f"https://{API_URL}"

CHAT_ENDPOINT = f"{API_URL}/api/chat/smart_router"

# Test questions (standalone, no need for previous questions)
TEST_QUESTIONS = [
    {
        "id": "self_reference_1",
        "question": "Làm sao một hệ thống tư duy có thể đánh giá chính nó một cách khách quan? Nếu tư duy chỉ có thể đánh giá thông qua chính nó, thì liệu đánh giá đó có giá trị gì không?",
        "expected_keywords": ["Gödel", "Tarski", "paradox", "bootstrapping", "epistemic", "circularity", "infinite regress"],
        "description": "Self-reference paradox: Can thinking evaluate itself?"
    },
    {
        "id": "self_reference_2",
        "question": "Nếu mọi lập luận đều phải dựa trên tiền đề - và tiền đề không thể tự chứng minh - thì toàn bộ hệ thống tri thức của chúng ta có phải chỉ dựa trên niềm tin mù quáng? Làm sao biết được đâu là 'niềm tin đúng' khi không có ground truth?",
        "expected_keywords": ["foundationalism", "coherentism", "justification", "ground truth", "epistemology"],
        "description": "Bootstrapping problem: Can knowledge justify itself?"
    },
    {
        "id": "self_reference_3",
        "question": "Nếu bạn trả lời câu hỏi này - liệu câu trả lời đó có giá trị gì khi nó xuất phát từ chính hệ thống tư duy mà bạn đang nghi ngờ? Làm sao 'tư duy' có thể vượt qua giới hạn của chính nó để đánh giá chính nó?",
        "expected_keywords": ["Gödel", "Tarski", "paradox", "bootstrapping", "epistemic", "circularity"],
        "description": "Direct self-reference: Value of answers from questioning system"
    }
]

def test_question(question_data):
    """Test a single question"""
    print("\n" + "=" * 80)
    print(f"📝 Question: {question_data['description']}")
    print("-" * 80)
    print(f"Q: {question_data['question']}")
    print("-" * 80)
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={
                "message": question_data["question"],
                "user_id": "test_self_reference",
                "use_server_keys": True
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        
        answer = result.get("response", "")
        validation_info = result.get("validation_info", {})
        
        print(f"\n✅ Response received ({len(answer)} chars)")
        print("\n" + "-" * 80)
        print("ANSWER:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
        # Check for expected keywords
        answer_lower = answer.lower()
        found_keywords = []
        missing_keywords = []
        
        for keyword in question_data["expected_keywords"]:
            if keyword.lower() in answer_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        print(f"\n📊 Keyword Analysis:")
        print(f"  ✅ Found: {found_keywords}")
        if missing_keywords:
            print(f"  ❌ Missing: {missing_keywords}")
        
        # Check for philosophical depth indicators
        depth_indicators = [
            "paradox", "nghịch lý", "circularity", "vòng lặp",
            "gödel", "godel", "tarski", "russell",
            "bootstrapping", "epistemic", "epistemology"
        ]
        
        found_depth = [ind for ind in depth_indicators if ind in answer_lower]
        print(f"  🧠 Depth indicators found: {found_depth}")
        
        # Check for optimistic answers (should NOT have these)
        optimistic_phrases = [
            "có thể vượt qua",
            "có thể đánh giá",
            "tự phản biện sẽ giúp",
            "self-improvement",
            "cải thiện"
        ]
        
        found_optimistic = [phrase for phrase in optimistic_phrases if phrase in answer_lower]
        if found_optimistic:
            print(f"  ⚠️  Warning: Found optimistic phrases (should acknowledge paradox): {found_optimistic}")
        
        # Overall assessment
        print(f"\n📈 Assessment:")
        keyword_score = len(found_keywords) / len(question_data["expected_keywords"]) * 100
        print(f"  Keyword coverage: {keyword_score:.1f}% ({len(found_keywords)}/{len(question_data['expected_keywords'])})")
        print(f"  Depth indicators: {len(found_depth)}/{len(depth_indicators)}")
        print(f"  Has optimistic answer: {'Yes (BAD)' if found_optimistic else 'No (GOOD)'}")
        
        if keyword_score >= 50 and not found_optimistic:
            print(f"  ✅ Overall: GOOD - Philosophical depth present")
        elif keyword_score < 50:
            print(f"  ⚠️  Overall: NEEDS IMPROVEMENT - Missing key philosophical concepts")
        else:
            print(f"  ⚠️  Overall: NEEDS IMPROVEMENT - Too optimistic, missing paradox acknowledgment")
        
        return {
            "question_id": question_data["id"],
            "question": question_data["question"],
            "answer": answer,
            "keyword_score": keyword_score,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "depth_indicators": found_depth,
            "has_optimistic": bool(found_optimistic),
            "validation_info": validation_info
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all test questions"""
    print("=" * 80)
    print("🧠 SELF-REFERENCE PARADOX TEST")
    print("=" * 80)
    print(f"API URL: {API_URL}")
    print(f"Endpoint: {CHAT_ENDPOINT}")
    print(f"Testing {len(TEST_QUESTIONS)} questions...")
    
    results = []
    
    for i, question_data in enumerate(TEST_QUESTIONS, 1):
        print(f"\n\n🔍 Test {i}/{len(TEST_QUESTIONS)}")
        result = test_question(question_data)
        if result:
            results.append(result)
        
        # Small delay between questions
        if i < len(TEST_QUESTIONS):
            import time
            time.sleep(2)
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    if results:
        avg_keyword_score = sum(r["keyword_score"] for r in results) / len(results)
        num_with_optimistic = sum(1 for r in results if r["has_optimistic"])
        
        print(f"Total questions tested: {len(results)}")
        print(f"Average keyword coverage: {avg_keyword_score:.1f}%")
        print(f"Questions with optimistic answers: {num_with_optimistic}/{len(results)}")
        
        print("\nDetailed results:")
        for r in results:
            status = "✅" if r["keyword_score"] >= 50 and not r["has_optimistic"] else "⚠️"
            print(f"  {status} {r['question_id']}: {r['keyword_score']:.1f}% keywords, "
                  f"{'optimistic' if r['has_optimistic'] else 'paradox-aware'}")
    else:
        print("❌ No results collected")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

