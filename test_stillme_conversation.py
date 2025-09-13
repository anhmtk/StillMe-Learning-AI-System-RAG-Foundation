#!/usr/bin/env python3
"""
Test script để mô phỏng user nói chuyện với StillMe
và test luồng User → StillMe → AgentDev
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stillme_conversation():
    """Test conversation với StillMe"""
    print("🤖 StillMe AI - Test Conversation")
    print("=" * 50)

    # Import StillMe functions
    try:
        from app import _detect_dev_intent, generate_answer
        print("✅ StillMe modules loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load StillMe modules: {e}")
        return

    # Test cases
    test_cases = [
        "Tôi có 73 lỗi trong IDE, hãy giúp tôi sửa chúng",
        "Viết code cho web scraper Python",
        "Tạo ứng dụng calculator đơn giản",
        "Sửa lỗi linting trong project",
        "Xin chào, bạn có khỏe không?",
        "Bạn có thể giúp tôi lập trình không?"
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {message}")
        print("-" * 40)

        # Test intent detection
        is_dev_intent = _detect_dev_intent(message)
        print(f"🔍 Dev Intent Detected: {is_dev_intent}")

        if is_dev_intent:
            print("🎯 Routing to AgentDev...")
            try:
                # Test AgentDev routing
                from stillme_core.ai_manager import dev_agent
                result = dev_agent(message, mode="fast")
                if result and not result.startswith("[AIManager]"):
                    print(f"✅ AgentDev Response: {result[:100]}...")
                else:
                    print(f"⚠️ AgentDev Fallback: {result}")
            except Exception as e:
                print(f"❌ AgentDev Error: {e}")
        else:
            print("💬 Normal StillMe processing...")
            try:
                result = generate_answer(message)
                print(f"✅ StillMe Response: {result[:100]}...")
            except Exception as e:
                print(f"❌ StillMe Error: {e}")

if __name__ == "__main__":
    test_stillme_conversation()
