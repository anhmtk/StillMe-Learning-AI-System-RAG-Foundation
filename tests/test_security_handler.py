#!/usr/bin/env python3
"""
Unit tests for Security/Architecture handling
"""

import sys
import unittest
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from identity_handler import IdentityHandler


class TestSecurityHandler(unittest.TestCase):
    """Test cases for Security/Architecture handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = IdentityHandler()

    def test_architecture_intent_detection_vi(self):
        """Test Vietnamese architecture intent detection"""
        test_cases = [
            ("Bạn gồm những module gì?", True),
            ("Bạn có kiến trúc ra sao?", True),
            ("Bạn hoạt động thế nào bên trong?", True),
            ("Bạn có agentdev không?", True),
            ("Bạn có agent dev không?", True),
            ("Bạn có dev agent không?", True),
            ("Bạn có framework gì?", True),
            ("Bạn có hệ thống gì?", True),
            ("Bạn có cơ chế gì?", True),
            ("Bạn có cách thức gì?", True),
            ("Bạn có viết code không?", True),
            ("Bạn có chạy test không?", True),
            ("Bạn có dev-ops không?", True),
            ("Bạn có kiến trúc nội bộ gì?", True),
            ("Bạn có gồm những gì?", True),
            ("Bạn có bao gồm gì?", True),
            ("Bạn có thành phần gì?", True),
            ("Bạn có bộ phận gì?", True),
            ("Xin chào", False),
            ("Hôm nay thế nào?", False),
            ("Bạn có thể giúp tôi không?", False),
        ]

        for message, expected in test_cases:
            with self.subTest(message=message):
                is_architecture, locale = self.handler.detect_architecture_intent(
                    message
                )
                self.assertEqual(is_architecture, expected)
                if expected:
                    self.assertEqual(locale, "vi")

    def test_architecture_intent_detection_en(self):
        """Test English architecture intent detection"""
        test_cases = [
            ("What modules do you have?", True),
            ("What's your architecture?", True),
            ("How does it work inside?", True),
            ("Do you have agentdev?", True),
            ("Do you have agent dev?", True),
            ("Do you have dev agent?", True),
            ("What framework do you use?", True),
            ("What system do you have?", True),
            ("What mechanism do you have?", True),
            ("How does it work?", True),
            ("Can you write code?", True),
            ("Can you run tests?", True),
            ("Do you have dev-ops?", True),
            ("What's your internal architecture?", True),
            ("What do you consist of?", True),
            ("What are your components?", True),
            ("What are your parts?", True),
            ("What are you made up of?", True),
            ("Hello", False),
            ("How are you?", False),
            ("Can you help me?", False),
        ]

        for message, expected in test_cases:
            with self.subTest(message=message):
                is_architecture, locale = self.handler.detect_architecture_intent(
                    message
                )
                self.assertEqual(is_architecture, expected)
                if expected:
                    self.assertEqual(locale, "en")

    def test_architecture_response_generation_vi(self):
        """Test Vietnamese architecture response generation"""
        test_messages = [
            "Bạn gồm những module gì?",
            "Bạn có kiến trúc ra sao?",
            "Bạn hoạt động thế nào bên trong?",
            "Bạn có agentdev không?",
        ]

        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_architecture_response(message, "vi")
                self.assertIsNotNone(response)

                # Should NOT contain sensitive information
                self.assertNotIn("framework.py", response)
                self.assertNotIn("module list", response)
                self.assertNotIn("agent_dev", response)
                self.assertNotIn("agentdev", response)
                self.assertNotIn("dev agent", response)
                self.assertNotIn("kiến trúc nội bộ", response)
                self.assertNotIn("cấu trúc module", response)

                # Should contain security-friendly language
                self.assertTrue(
                    any(
                        word in response
                        for word in [
                            "bí mật",
                            "giữ kín",
                            "riêng mình",
                            "nghề nghiệp",
                            "thể hiện",
                            "hành động",
                        ]
                    )
                )

    def test_architecture_response_generation_en(self):
        """Test English architecture response generation"""
        test_messages = [
            "What modules do you have?",
            "What's your architecture?",
            "How does it work inside?",
            "Do you have agentdev?",
        ]

        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_architecture_response(message, "en")
                self.assertIsNotNone(response)

                # Should NOT contain sensitive information
                self.assertNotIn("framework.py", response)
                self.assertNotIn("module list", response)
                self.assertNotIn("agent_dev", response)
                self.assertNotIn("agentdev", response)
                self.assertNotIn("dev agent", response)
                self.assertNotIn("internal architecture", response)
                self.assertNotIn("module structure", response)

                # Should contain security-friendly language
                self.assertTrue(
                    any(
                        word in response
                        for word in [
                            "secret",
                            "private",
                            "myself",
                            "professional",
                            "demonstrate",
                            "actions",
                        ]
                    )
                )

    def test_secure_response_priority(self):
        """Test that architecture responses have priority over identity responses"""
        # Architecture questions should get architecture responses, not identity responses
        architecture_questions = [
            "Bạn có agentdev không?",
            "Bạn gồm những module gì?",
            "Do you have agentdev?",
            "What modules do you have?",
        ]

        for question in architecture_questions:
            with self.subTest(question=question):
                response = self.handler.generate_secure_response(question)
                self.assertIsNotNone(response)

                # Should be architecture response, not identity response
                self.assertNotIn("Anh Nguyễn", response)
                self.assertNotIn("Anh Nguyen", response)
                self.assertNotIn("Việt Nam", response)
                self.assertNotIn("Vietnam", response)

                # Should contain security-friendly language
                self.assertTrue(
                    any(
                        word in response.lower()
                        for word in [
                            "secret",
                            "private",
                            "bí mật",
                            "giữ kín",
                            "myself",
                            "riêng mình",
                        ]
                    )
                )

    def test_non_sensitive_questions(self):
        """Test that non-sensitive questions return None"""
        test_messages = [
            "Xin chào",
            "Hôm nay thế nào?",
            "Bạn có thể giúp tôi không?",
            "Hello",
            "How are you?",
            "Can you help me?",
        ]

        for message in test_messages:
            with self.subTest(message=message):
                response = self.handler.generate_architecture_response(message)
                self.assertIsNone(response)

    def test_template_rotation_security(self):
        """Test that security templates rotate and don't repeat immediately"""
        message = "Bạn có agentdev không?"
        responses = []

        # Generate multiple responses
        for _ in range(10):
            response = self.handler.generate_architecture_response(message, "vi")
            responses.append(response)

        # Should have some variation (not all identical)
        unique_responses = set(responses)
        self.assertGreater(len(unique_responses), 1, "Security templates should rotate")

        # All responses should be secure
        for response in responses:
            self.assertNotIn("agentdev", response)
            self.assertNotIn("framework.py", response)
            self.assertNotIn("module list", response)


if __name__ == "__main__":
    unittest.main()