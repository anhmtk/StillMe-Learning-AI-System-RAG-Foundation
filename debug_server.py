#!/usr/bin/env python3
"""Debug script to test StillMe AI Server logic"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stillme-core'))

from stable_ai_server import StillMeAI

def test_coding_question():
    """Test coding question processing"""
    print("🧪 Testing coding question...")
    
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
        
        # Test full processing
        response = ai.process_message(message, locale)
        print(f"🤖 Final response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coding_question()
