#!/usr/bin/env python3
"""
Test script đơn giản để test dev intent detection
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _detect_dev_intent(prompt: str) -> bool:
    """Detect if user request is for development task"""
    dev_keywords = [
        "viết code", "tạo code", "lập trình", "code", "programming",
        "tạo app", "tạo ứng dụng", "build", "compile",
        "tạo tool", "tạo công cụ", "utility", "script",
        "sửa lỗi", "fix bug", "linting", "quality", "lỗi",
        "error", "bug", "debug", "refactor", "optimize"
    ]
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in dev_keywords)

def test_dev_intent_detection():
    """Test dev intent detection"""
    print("🤖 StillMe AI - Dev Intent Detection Test")
    print("=" * 50)

    # Test cases
    test_cases = [
        "Tôi có 73 lỗi trong IDE, hãy giúp tôi sửa chúng",
        "Viết code cho web scraper Python",
        "Tạo ứng dụng calculator đơn giản",
        "Sửa lỗi linting trong project",
        "Xin chào, bạn có khỏe không?",
        "Bạn có thể giúp tôi lập trình không?",
        "Tạo tool để backup database",
        "Build ứng dụng mobile",
        "Hôm nay thời tiết thế nào?",
        "Code review cho function này"
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {message}")
        print("-" * 40)

        # Test intent detection
        is_dev_intent = _detect_dev_intent(message)
        print(f"🔍 Dev Intent Detected: {is_dev_intent}")

        if is_dev_intent:
            print("🎯 Would route to AgentDev")
            print("✅ User would get: Code/text response from AgentDev")
        else:
            print("💬 Would use normal StillMe processing")
            print("✅ User would get: General chat response")

def test_agentdev_direct():
    """Test AgentDev trực tiếp"""
    print("\n\n🤖 AgentDev Direct Test")
    print("=" * 50)

    try:
        from stillme_core.ai_manager import dev_agent
        print("✅ AgentDev module loaded successfully")

        # Test AgentDev
        result = dev_agent("Sửa lỗi linting trong project", mode="fast")
        print(f"✅ AgentDev Response: {result[:200]}...")

    except Exception as e:
        print(f"❌ AgentDev Error: {e}")

if __name__ == "__main__":
    test_dev_intent_detection()
    test_agentdev_direct()
