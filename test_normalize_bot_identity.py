#!/usr/bin/env python3
"""
Unit tests for normalize_bot_identity function
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stillme_desktop_app import StillMeDesktopApp
import tkinter as tk

def test_normalize_bot_identity():
    """Test normalize_bot_identity function with various inputs"""
    
    # Create a dummy app instance for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    app = StillMeDesktopApp(root)
    
    # Test cases
    test_cases = [
        # English patterns
        ("I am Gemma, an AI assistant", "I am StillMe, an AI assistant"),
        ("I'm OpenAI's ChatGPT", "I am StillMe's ChatGPT"),
        ("My name is DeepSeek", "My name is StillMe"),
        ("I'm called GPT-4", "I am StillMe"),
        ("I'm a model trained by Anthropic", "I am StillMe"),
        ("As a Gemma model, I can help", "As StillMe, I can help"),
        ("Gemma here, how can I help?", "StillMe here, how can I help?"),
        
        # Vietnamese patterns
        ("Mình là Gemma, trợ lý AI", "Mình là StillMe, trợ lý AI"),
        ("Tôi là OpenAI ChatGPT", "Mình là StillMe ChatGPT"),
        ("Mình tên DeepSeek", "Mình là StillMe"),
        ("Tôi tên GPT-4", "Mình là StillMe"),
        ("Mình là một trợ lý AI", "Mình là StillMe"),
        ("Tôi là một con model AI", "Mình là StillMe"),
        ("Mình là một cái AI assistant", "Mình là StillMe"),
        
        # Mixed content (should not change non-identity parts)
        ("Hello! I am Gemma. How can I help you today?", "Hello! I am StillMe. How can I help you today?"),
        ("Xin chào! Mình là DeepSeek. Bạn cần giúp gì?", "Xin chào! Mình là StillMe. Bạn cần giúp gì?"),
        
        # Edge cases
        ("", ""),
        ("Just a normal message", "Just a normal message"),
        ("I am not a bot", "I am not a bot"),
        ("Gemma is a good model", "Gemma is a good model"),  # Should not change when not self-identification
    ]
    
    print("🧪 Testing normalize_bot_identity function...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = app.normalize_bot_identity(input_text)
        
        if result == expected:
            print(f"✅ Test {i}: PASSED")
            print(f"   Input:    '{input_text}'")
            print(f"   Output:   '{result}'")
            passed += 1
        else:
            print(f"❌ Test {i}: FAILED")
            print(f"   Input:    '{input_text}'")
            print(f"   Expected: '{expected}'")
            print(f"   Got:      '{result}'")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_normalize_bot_identity()
    sys.exit(0 if success else 1)
