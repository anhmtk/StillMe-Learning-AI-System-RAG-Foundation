#!/usr/bin/env python3
"""
Integration tests for Identity functionality
"""

import unittest
import sys
import os
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from conversational_core_v1 import ConversationalCore

class MockPersonaEngine:
    """Mock persona engine for testing"""
    
    def generate_response(self, user_input, history):
        return f"Mock response for: {user_input}"

class TestIdentityIntegration(unittest.TestCase):
    """Integration tests for Identity functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_persona = MockPersonaEngine()
        self.conversational_core = ConversationalCore(self.mock_persona)
    
    def test_identity_questions_vi(self):
        """Test Vietnamese identity questions through ConversationalCore"""
        test_cases = [
            "Bạn do ai tạo?",
            "Ai viết ra bạn?",
            "Bạn của Hàn Quốc à?",
            "Bạn thuộc quốc gia nào?",
            "Nguồn gốc của bạn là gì?",
            "Tác giả của bạn là ai?"
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                response = self.conversational_core.respond(message)
                
                # Should be identity response, not mock response
                self.assertNotIn("Mock response", response)
                self.assertIn("Anh Nguyễn", response)
                self.assertIn("Việt Nam", response)
                self.assertIn("OpenAI", response)
                self.assertIn("Google", response)
                self.assertIn("DeepSeek", response)
    
    def test_identity_questions_en(self):
        """Test English identity questions through ConversationalCore"""
        test_cases = [
            "Who made you?",
            "Are you Korean?",
            "Which country are you from?",
            "Who created you?",
            "What's your origin?",
            "Where are you from?"
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                response = self.conversational_core.respond(message)
                
                # Should be identity response, not mock response
                self.assertNotIn("Mock response", response)
                self.assertIn("Anh Nguyen", response)
                self.assertIn("Vietnam", response)
                self.assertIn("OpenAI", response)
                self.assertIn("Google", response)
                self.assertIn("DeepSeek", response)
    
    def test_non_identity_questions(self):
        """Test that non-identity questions go to persona engine"""
        test_cases = [
            "Xin chào",
            "Hôm nay thế nào?",
            "Bạn có thể giúp tôi không?",
            "Hello",
            "How are you?",
            "Can you help me?"
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                response = self.conversational_core.respond(message)
                
                # Should be mock response (goes to persona engine)
                self.assertIn("Mock response", response)
                self.assertIn(message, response)
    
    def test_conversation_history(self):
        """Test that identity responses are added to conversation history"""
        message = "Bạn do ai tạo?"
        response = self.conversational_core.respond(message)
        
        # Check history
        self.assertEqual(len(self.conversational_core.history), 2)
        self.assertEqual(self.conversational_core.history[0]["role"], "user")
        self.assertEqual(self.conversational_core.history[0]["content"], message)
        self.assertEqual(self.conversational_core.history[1]["role"], "agent")
        self.assertEqual(self.conversational_core.history[1]["content"], response)
    
    def test_identity_handler_availability(self):
        """Test that IdentityHandler is properly integrated"""
        self.assertIsNotNone(self.conversational_core.identity_handler)
        
        # Test direct access to identity handler
        identity_response = self.conversational_core.identity_handler.generate_identity_response("Bạn do ai tạo?")
        self.assertIsNotNone(identity_response)
        self.assertIn("Anh Nguyễn", identity_response)

if __name__ == "__main__":
    unittest.main()
