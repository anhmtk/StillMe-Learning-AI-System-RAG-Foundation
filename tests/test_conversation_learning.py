"""
Test cases for Conversation Learning Extractor
"""

import pytest
from backend.services.conversation_learning_extractor import (
    ConversationLearningExtractor,
    validate_learning_content
)


class TestConversationLearningExtractor:
    """Test ConversationLearningExtractor"""
    
    def test_init(self):
        """Test extractor initialization"""
        extractor = ConversationLearningExtractor()
        assert extractor is not None
    
    def test_analyze_question_not_learning(self):
        """Test that questions are not detected as learning material"""
        extractor = ConversationLearningExtractor()
        proposal = extractor.analyze_conversation_for_learning(
            user_message="What is artificial intelligence?",
            assistant_response="AI is..."
        )
        assert proposal is None
    
    def test_analyze_short_message_not_learning(self):
        """Test that short messages are not detected as learning material"""
        extractor = ConversationLearningExtractor()
        proposal = extractor.analyze_conversation_for_learning(
            user_message="That's interesting.",
            assistant_response="Thank you."
        )
        assert proposal is None
    
    def test_analyze_valuable_knowledge(self):
        """Test that valuable knowledge is detected"""
        extractor = ConversationLearningExtractor()
        valuable_message = """
        Artificial intelligence is a branch of computer science that aims to create 
        intelligent machines capable of performing tasks that typically require human intelligence. 
        These tasks include learning, reasoning, problem-solving, perception, and language understanding. 
        AI systems can be categorized into narrow AI, which is designed for specific tasks, 
        and general AI, which aims to replicate human cognitive abilities across a wide range of tasks.
        """
        proposal = extractor.analyze_conversation_for_learning(
            user_message=valuable_message,
            assistant_response="Thank you for sharing this information."
        )
        assert proposal is not None
        assert proposal.get("knowledge_score", 0) >= 0.6
        assert "knowledge_snippet" in proposal
        assert "reason" in proposal
    
    def test_analyze_personal_info_filtered(self):
        """Test that messages with personal info are filtered out"""
        extractor = ConversationLearningExtractor()
        personal_message = """
        My name is John Doe and my email is john@example.com. 
        I was born on 1990-01-01. Here's some information about AI...
        """
        proposal = extractor.analyze_conversation_for_learning(
            user_message=personal_message,
            assistant_response="Thank you."
        )
        assert proposal is None
    
    def test_format_permission_request_english(self):
        """Test permission request formatting in English"""
        extractor = ConversationLearningExtractor()
        proposal = {
            "knowledge_snippet": "AI is a branch of computer science...",
            "reason": "Contains valuable definition",
            "knowledge_score": 0.8
        }
        request = extractor.format_permission_request(proposal, language="en")
        assert "Learning Request" in request
        assert "AI is a branch" in request
        assert "Your Rights" in request
    
    def test_format_permission_request_vietnamese(self):
        """Test permission request formatting in Vietnamese"""
        extractor = ConversationLearningExtractor()
        proposal = {
            "knowledge_snippet": "Trí tuệ nhân tạo là một nhánh của khoa học máy tính...",
            "reason": "Chứa định nghĩa có giá trị",
            "knowledge_score": 0.8
        }
        request = extractor.format_permission_request(proposal, language="vi")
        assert "Yêu cầu học tập" in request
        assert "Trí tuệ nhân tạo" in request
        assert "Quyền của bạn" in request


class TestValidateLearningContent:
    """Test content validation"""
    
    def test_validate_too_short(self):
        """Test that content too short is rejected"""
        is_valid, error = validate_learning_content("Short")
        assert not is_valid
        assert "too short" in error.lower()
    
    def test_validate_too_long(self):
        """Test that content too long is rejected"""
        long_content = "A" * 3000
        is_valid, error = validate_learning_content(long_content)
        assert not is_valid
        assert "too long" in error.lower()
    
    def test_validate_personal_info(self):
        """Test that content with personal info is rejected"""
        content_with_email = "Here's some information about AI. Contact me at john@example.com for more."
        is_valid, error = validate_learning_content(content_with_email)
        assert not is_valid
        assert "personal information" in error.lower()
    
    def test_validate_spam(self):
        """Test that spam content is rejected"""
        spam_content = "Buy now! Get rich quick! Click here for free money!"
        is_valid, error = validate_learning_content(spam_content)
        assert not is_valid
        assert "spam" in error.lower()
    
    def test_validate_valid_content(self):
        """Test that valid content passes validation"""
        valid_content = """
        Artificial intelligence is a branch of computer science that aims to create 
        intelligent machines. These systems can learn from data and make decisions 
        based on patterns they discover. Machine learning is a subset of AI that 
        focuses on algorithms that can improve their performance over time.
        """
        is_valid, error = validate_learning_content(valid_content)
        assert is_valid
        assert error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

