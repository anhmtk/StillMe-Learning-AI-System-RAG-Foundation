#!/usr/bin/env python3
"""
Unit tests for IdentityHandler module
"""

import unittest
import sys
import os
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from identity_handler import IdentityHandler

class TestIdentityHandler(unittest.TestCase):
    """Test cases for IdentityHandler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = IdentityHandler()
    
    def test_identity_intent_detection_vi(self):
        """Test Vietnamese identity intent detection"""
        test_cases = [
            ("Bạn do ai tạo?", True),
            ("Ai viết ra bạn?", True),
            ("Bạn của Hàn Quốc à?", True),
            ("Bạn thuộc quốc gia nào?", True),
            ("Nguồn gốc của bạn là gì?", True),
            ("Tác giả của bạn là ai?", True),
            ("Xin chào", False),
            ("Hôm nay thế nào?", False),
            ("Bạn có thể giúp tôi không?", False)
        ]
        
        for message, expected in test_cases:
            with self.subTest(message=message):
                is_identity, locale = self.handler.detect_identity_intent(message)
                self.assertEqual(is_identity, expected)
                if expected:
                    self.assertEqual(locale, "vi")
    
    def test_identity_intent_detection_en(self):
        """Test English identity intent detection"""
        test_cases = [
            ("Who made you?", True),
            ("Are you Korean?", True),
            ("Which country are you from?", True),
            ("Who created you?", True),
            ("What's your origin?", True),
            ("Hello", False),
            ("How are you today?", False),
            ("Can you help me?", False)
        ]
        
        for message, expected in test_cases:
            with self.subTest(message=message):
                is_identity, locale = self.handler.detect_identity_intent(message)
                self.assertEqual(is_identity, expected)
                if expected:
                    self.assertEqual(locale, "en")
    
    def test_identity_response_generation_vi(self):
        """Test Vietnamese identity response generation"""
        test_messages = [
            "Bạn do ai tạo?",
            "Ai viết ra bạn?",
            "Bạn của Hàn Quốc à?",
            "Bạn thuộc quốc gia nào?"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_identity_response(message, "vi")
                self.assertIsNotNone(response)
                self.assertIn("Anh Nguyễn", response)
                self.assertIn("Việt Nam", response)
                self.assertIn("OpenAI", response)
                self.assertIn("Google", response)
                self.assertIn("DeepSeek", response)
    
    def test_identity_response_generation_en(self):
        """Test English identity response generation"""
        test_messages = [
            "Who made you?",
            "Are you Korean?",
            "Which country are you from?",
            "Who created you?"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_identity_response(message, "en")
                self.assertIsNotNone(response)
                self.assertIn("Anh Nguyen", response)
                self.assertIn("Vietnam", response)
                self.assertIn("OpenAI", response)
                self.assertIn("Google", response)
                self.assertIn("DeepSeek", response)
    
    def test_non_identity_response(self):
        """Test that non-identity questions return None"""
        test_messages = [
            "Xin chào",
            "Hôm nay thế nào?",
            "Bạn có thể giúp tôi không?",
            "Hello",
            "How are you?",
            "Can you help me?"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_identity_response(message)
                self.assertIsNone(response)
    
    def test_template_rotation(self):
        """Test that templates rotate and don't repeat immediately"""
        message = "Bạn do ai tạo?"
        responses = []
        
        # Generate multiple responses
        for _ in range(10):
            response = self.handler.generate_identity_response(message, "vi")
            responses.append(response)
        
        # Should have some variation (not all identical)
        unique_responses = set(responses)
        self.assertGreater(len(unique_responses), 1, "Templates should rotate")
    
    def test_fallback_response(self):
        """Test fallback response when no templates available"""
        # Create handler with empty config
        handler = IdentityHandler()
        handler.identity_config = {
            "core": {
                "creator": "Test Creator",
                "nationality": "Test Country",
                "org_support": ["TestOrg1", "TestOrg2"],
                "project_name": "TestProject"
            },
            "templates": {"vi": [], "en": []}
        }
        
        response = handler._get_fallback_response("vi")
        self.assertIn("Test Creator", response)
        self.assertIn("Test Country", response)
        self.assertIn("TestOrg1", response)
        self.assertIn("TestOrg2", response)
    
    def test_identity_facts(self):
        """Test getting identity facts from config"""
        facts = self.handler.get_identity_facts()
        
        self.assertIn("creator", facts)
        self.assertIn("nationality", facts)
        self.assertIn("org_support", facts)
        self.assertIn("project_name", facts)
        
        self.assertEqual(facts["creator"], "Anh Nguyễn")
        self.assertEqual(facts["nationality"], "Việt Nam")
        self.assertIn("OpenAI", facts["org_support"])
        self.assertIn("Google", facts["org_support"])
        self.assertIn("DeepSeek", facts["org_support"])

if __name__ == "__main__":
    unittest.main()
