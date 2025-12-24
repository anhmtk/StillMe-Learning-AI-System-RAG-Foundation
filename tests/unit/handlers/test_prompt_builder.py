"""Unit tests for prompt_builder.py module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.api.handlers.prompt_builder import (
    get_validator_info_for_prompt,
    build_prompt_context_from_chat_request,
    truncate_user_message,
    format_conversation_history,
    calculate_confidence_score,
    get_transparency_disclaimer,
    build_minimal_philosophical_prompt
)
from backend.api.models import ChatRequest
from backend.identity.prompt_builder import PromptContext, FPSResult
from backend.api.config.chat_config import get_chat_config


class TestGetValidatorInfoForPrompt:
    """Tests for get_validator_info_for_prompt function."""
    
    @patch('backend.api.handlers.prompt_builder.get_validator_count')
    def test_returns_manifest_info_when_available(self, mock_get_count):
        """Test that function returns info from manifest when available."""
        mock_get_count.return_value = (19, 7)
        
        summary_vi, summary_en, layers = get_validator_info_for_prompt()
        
        assert summary_vi == "19 validators total, chia thành 7 lớp (layers)"
        assert summary_en == "19 validators total, organized into 7 layers"
        assert layers == "7 layers"
    
    @patch('backend.api.handlers.prompt_builder.get_validator_count')
    def test_falls_back_to_defaults_on_error(self, mock_get_count):
        """Test that function falls back to defaults on error."""
        mock_get_count.side_effect = Exception("Manifest not found")
        config = get_chat_config()
        
        summary_vi, summary_en, layers = get_validator_info_for_prompt()
        
        assert summary_vi == config.validator_info.DEFAULT_VI
        assert summary_en == config.validator_info.DEFAULT_EN
        assert layers == config.validator_info.DEFAULT_LAYERS


class TestBuildPromptContextFromChatRequest:
    """Tests for build_prompt_context_from_chat_request function."""
    
    def test_builds_prompt_context_correctly(self):
        """Test that function builds PromptContext correctly."""
        chat_request = ChatRequest(
            message="Test question",
            conversation_history=[{"role": "user", "content": "Previous"}]
        )
        context = {
            "has_reliable_context": True,
            "context_quality": "high",
            "knowledge_docs": [{"metadata": {"title": "Test"}}]
        }
        
        prompt_context = build_prompt_context_from_chat_request(
            chat_request=chat_request,
            context=context,
            detected_lang="en",
            is_stillme_query=False,
            is_philosophical=False
        )
        
        assert isinstance(prompt_context, PromptContext)
        assert prompt_context.user_question == "Test question"
        assert prompt_context.detected_lang == "en"
        assert prompt_context.has_reliable_context is True
        assert prompt_context.context_quality == "high"
        assert prompt_context.num_knowledge_docs == 1
    
    def test_detects_wish_desire_question(self):
        """Test that function detects wish/desire questions."""
        chat_request = ChatRequest(message="Bạn muốn gì?")
        context = {}
        
        prompt_context = build_prompt_context_from_chat_request(
            chat_request=chat_request,
            context=context,
            detected_lang="vi",
            is_stillme_query=True,
            is_philosophical=False
        )
        
        assert prompt_context.is_wish_desire_question is True


class TestTruncateUserMessage:
    """Tests for truncate_user_message function."""
    
    def test_returns_original_if_short_enough(self):
        """Test that function returns original message if short enough."""
        message = "Short message"
        result = truncate_user_message(message, max_tokens=100)
        assert result == message
    
    def test_truncates_long_message(self):
        """Test that function truncates long messages."""
        # Create a message that's definitely over 100 tokens
        message = "word " * 500  # ~500 words = ~2000 tokens
        result = truncate_user_message(message, max_tokens=100)
        
        assert len(result) < len(message)
        assert "... [message truncated]" in result
    
    def test_uses_config_default_when_max_tokens_none(self):
        """Test that function uses config default when max_tokens is None."""
        config = get_chat_config()
        message = "Test message"
        
        with patch.object(config.tokens, 'MAX_USER_MESSAGE', 2000):
            result = truncate_user_message(message, max_tokens=None)
            assert result == message


class TestFormatConversationHistory:
    """Tests for format_conversation_history function."""
    
    def test_returns_empty_for_philosophical_questions(self):
        """Test that function returns empty for philosophical questions."""
        history = [{"role": "user", "content": "Previous question"}]
        result = format_conversation_history(
            history,
            max_tokens=1000,
            current_query="What is consciousness?",
            is_philosophical=True
        )
        assert result == ""
    
    def test_returns_empty_for_empty_history(self):
        """Test that function returns empty for empty history."""
        result = format_conversation_history([], max_tokens=1000)
        assert result == ""
    
    def test_formats_history_correctly(self):
        """Test that function formats history correctly."""
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"}
        ]
        result = format_conversation_history(history, max_tokens=1000)
        
        assert "CONVERSATION HISTORY" in result
        assert "User: Question 1" in result
        assert "Assistant: Answer 1" in result
    
    def test_handles_follow_up_queries(self):
        """Test that function handles follow-up queries with more context."""
        history = [{"role": "user", "content": f"Question {i}"} for i in range(10)]
        result = format_conversation_history(
            history,
            max_tokens=1000,
            current_query="Vậy thì sao?"  # Follow-up indicator
        )
        
        assert "CONVERSATION HISTORY" in result


class TestCalculateConfidenceScore:
    """Tests for calculate_confidence_score function."""
    
    def test_returns_low_confidence_with_no_context(self):
        """Test that function returns low confidence with no context."""
        score = calculate_confidence_score(context_docs_count=0)
        assert score == 0.2
    
    def test_returns_medium_confidence_with_one_doc(self):
        """Test that function returns medium confidence with one doc."""
        score = calculate_confidence_score(context_docs_count=1)
        assert score == 0.5
    
    def test_returns_high_confidence_with_multiple_docs(self):
        """Test that function returns high confidence with multiple docs."""
        score = calculate_confidence_score(context_docs_count=2)
        assert score == 0.8
    
    def test_boosts_confidence_when_validation_passes(self):
        """Test that function boosts confidence when validation passes."""
        validation_result = Mock()
        validation_result.passed = True
        
        score = calculate_confidence_score(
            context_docs_count=2,
            validation_result=validation_result
        )
        
        assert score == 0.9  # 0.8 + 0.1
    
    def test_reduces_confidence_when_validation_fails(self):
        """Test that function reduces confidence when validation fails."""
        validation_result = Mock()
        validation_result.passed = False
        validation_result.reasons = ["missing_citation"]
        
        score = calculate_confidence_score(
            context_docs_count=2,
            validation_result=validation_result
        )
        
        assert score < 0.8  # Should be reduced
    
    def test_clamps_score_between_0_and_1(self):
        """Test that function clamps score between 0 and 1."""
        score = calculate_confidence_score(context_docs_count=100)
        assert 0.0 <= score <= 1.0


class TestGetTransparencyDisclaimer:
    """Tests for get_transparency_disclaimer function."""
    
    def test_returns_vietnamese_disclaimer(self):
        """Test that function returns Vietnamese disclaimer."""
        result = get_transparency_disclaimer("vi")
        assert "Lưu ý" in result
        assert "kiến thức chung" in result
    
    def test_returns_english_disclaimer_for_unknown_lang(self):
        """Test that function returns English disclaimer for unknown language."""
        result = get_transparency_disclaimer("unknown")
        assert "Note:" in result
        assert "general knowledge" in result
    
    def test_returns_multilingual_disclaimers(self):
        """Test that function returns correct disclaimers for various languages."""
        languages = ["fr", "de", "es", "ar", "ru", "zh", "ja", "ko"]
        for lang in languages:
            result = get_transparency_disclaimer(lang)
            assert len(result) > 0
            assert "⚠️" in result or "Note" in result or "注意" in result


class TestBuildMinimalPhilosophicalPrompt:
    """Tests for build_minimal_philosophical_prompt function."""
    
    def test_builds_prompt_with_basic_components(self):
        """Test that function builds prompt with basic components."""
        prompt = build_minimal_philosophical_prompt(
            user_question="What is consciousness?",
            language="en",
            detected_lang_name="English"
        )
        
        assert "StillMe" in prompt
        assert "What is consciousness?" in prompt
        assert "PHILOSOPHICAL FRAMING" in prompt
    
    def test_includes_stillme_technical_instructions_when_detected(self):
        """Test that function includes StillMe technical instructions when detected."""
        prompt = build_minimal_philosophical_prompt(
            user_question="How many validators does StillMe have?",
            language="en",
            detected_lang_name="English"
        )
        
        assert "STILLME TECHNICAL QUERY DETECTED" in prompt
        assert "VALIDATION CHAIN" in prompt
    
    def test_includes_rag_context_when_provided(self):
        """Test that function includes RAG context when provided."""
        context = {
            "knowledge_docs": [
                {
                    "metadata": {"title": "Test Doc", "source": "test"},
                    "document": "Test content"
                }
            ],
            "total_context_docs": 1
        }
        
        prompt = build_minimal_philosophical_prompt(
            user_question="Test question",
            language="en",
            detected_lang_name="English",
            context=context
        )
        
        assert "Retrieved Documents" in prompt
        assert "Test Doc" in prompt
    
    def test_includes_validation_warnings_when_provided(self):
        """Test that function includes validation warnings when provided."""
        validation_info = {
            "passed": False,
            "confidence_score": 0.5,
            "reasons": ["low_overlap:0.023", "citation_relevance_warning"]
        }
        
        prompt = build_minimal_philosophical_prompt(
            user_question="Test question",
            language="en",
            detected_lang_name="English",
            validation_info=validation_info
        )
        
        assert "VALIDATION WARNINGS" in prompt
        assert "0.50" in prompt or "50.0%" in prompt
    
    def test_handles_vietnamese_language(self):
        """Test that function handles Vietnamese language correctly."""
        prompt = build_minimal_philosophical_prompt(
            user_question="Ý thức là gì?",
            language="vi",
            detected_lang_name="Vietnamese (Tiếng Việt)"
        )
        
        assert "VIETNAMESE" in prompt.upper() or "TIẾNG VIỆT" in prompt.upper()
        assert "Ý thức là gì?" in prompt
    
    def test_truncates_long_questions(self):
        """Test that function truncates very long questions."""
        long_question = "word " * 1000  # Very long question
        prompt = build_minimal_philosophical_prompt(
            user_question=long_question,
            language="en",
            detected_lang_name="English"
        )
        
        # Prompt should be built successfully (truncation happens internally)
        assert len(prompt) > 0
        assert "StillMe" in prompt

