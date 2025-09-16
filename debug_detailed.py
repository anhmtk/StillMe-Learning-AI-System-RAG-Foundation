#!/usr/bin/env python3
"""Detailed debug script to test StillMe AI Server logic"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stillme-core'))

from stable_ai_server import StillMeAI

def test_coding_question_detailed():
    """Test coding question processing with detailed logging"""
    print("🧪 Testing coding question with detailed logging...")
    
    # Initialize AI
    ai = StillMeAI()
    
    # Test message
    message = "viết code python để tính tổng 2 số"
    locale = "vi"
    
    print(f"📝 Message: {message}")
    print(f"🌍 Locale: {locale}")
    
    try:
        # Test dev intent detection
        is_dev = ai._detect_dev_intent(message)
        print(f"🔍 Dev intent detected: {is_dev}")
        
        # Test secure intent check
        secure_response = ai._check_secure_intent(message, locale)
        print(f"🔒 Secure response: {secure_response}")
        
        # Test individual conditions
        message_lower = message.lower()
        
        # Test rule check
        rule_words = ["anh", "gọi mình", "xưng e", "quy tắc", "bất di bất dịch"]
        rule_match = any(word in message_lower for word in rule_words)
        print(f"📋 Rule check: {rule_match}")
        
        # Test greeting check
        greeting_words = ["hello", "hi", "xin chào", "chào"]
        greeting_match = any(word in message_lower for word in greeting_words)
        print(f"👋 Greeting check: {greeting_match}")
        
        # Test status check
        status_words = ["status", "trạng thái", "health"]
        status_match = any(word in message_lower for word in status_words)
        print(f"📊 Status check: {status_match}")
        
        # Test test check
        test_match = "test" in message_lower
        print(f"🧪 Test check: {test_match}")
        
        # Test creator check
        creator_words = ["anh nguyễn", "nguyễn", "tạo ra", "cha đẻ", "người tạo"]
        creator_match = any(word in message_lower for word in creator_words)
        print(f"👨‍💻 Creator check: {creator_match}")
        
        # Test help check
        help_words = ["help", "giúp", "hỗ trợ"]
        help_match = any(word in message_lower for word in help_words)
        print(f"❓ Help check: {help_match}")
        
        # Test programming check
        programming_words = ["code", "programming", "lập trình", "python", "javascript", "viết code", "tạo code"]
        programming_match = any(word in message_lower for word in programming_words)
        print(f"💻 Programming check: {programming_match}")
        
        # Test AI check
        ai_words = ["ai", "artificial intelligence", "trí tuệ nhân tạo", "bạn là ai", "bạn do ai tạo ra", "nguồn gốc"]
        ai_match = any(word in message_lower for word in ai_words)
        print(f"🤖 AI check: {ai_match}")
        
        # Test full processing
        print("\n🚀 Testing full processing...")
        response = ai.process_message(message, locale)
        print(f"🤖 Final response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coding_question_detailed()
