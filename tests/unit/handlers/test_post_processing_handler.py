"""
Unit tests for post_processing_handler.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.api.handlers.post_processing_handler import (
    process_response,
    _sanitize_response,
    _build_ctx_docs_for_rewrite,
    _evaluate_response_quality,
    _rewrite_response,
    _detect_factual_question,
    _re_add_citations_after_rewrite
)


class TestSanitizeResponse:
    """Tests for _sanitize_response"""
    
    @patch('backend.postprocessing.style_sanitizer.get_style_sanitizer')
    def test_sanitizes_response(self, mock_get_sanitizer):
        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = "Sanitized response"
        mock_get_sanitizer.return_value = mock_sanitizer
        
        result = _sanitize_response("Raw response", False, "en")
        
        assert result == "Sanitized response"
        mock_sanitizer.sanitize.assert_called_once_with("Raw response", is_philosophical=False)
    
    @patch('backend.postprocessing.style_sanitizer.get_style_sanitizer')
    def test_falls_back_to_original_if_empty(self, mock_get_sanitizer):
        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = ""
        mock_get_sanitizer.return_value = mock_sanitizer
        
        result = _sanitize_response("Original response", False, "en")
        
        assert result == "Original response"
    
    @patch('backend.postprocessing.style_sanitizer.get_style_sanitizer')
    def test_falls_back_if_removed_more_than_50_percent(self, mock_get_sanitizer):
        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = "Short"  # Less than 50% of "Original response"
        mock_get_sanitizer.return_value = mock_sanitizer
        
        result = _sanitize_response("Original response with more content", False, "en")
        
        assert result == "Original response with more content"


class TestBuildCtxDocsForRewrite:
    """Tests for _build_ctx_docs_for_rewrite"""
    
    def test_builds_from_context(self):
        context = {
            "knowledge_docs": [{"content": "Knowledge 1"}],
            "conversation_docs": [{"content": "Conversation 1"}],
            "has_reliable_context": True,
            "context_quality": "high"
        }
        
        ctx_docs, has_reliable, quality, has_foundational = _build_ctx_docs_for_rewrite(
            context, None, False
        )
        
        assert ctx_docs == ["Knowledge 1", "Conversation 1"]
        assert has_reliable is True
        assert quality == "high"
        assert has_foundational is False
    
    def test_detects_foundational_context(self):
        context = {
            "knowledge_docs": [
                {"content": "Knowledge 1", "metadata": {"source": "CRITICAL_FOUNDATION"}}
            ],
            "conversation_docs": []
        }
        
        ctx_docs, has_reliable, quality, has_foundational = _build_ctx_docs_for_rewrite(
            context, None, True  # is_stillme_query=True
        )
        
        assert has_foundational is True
    
    def test_uses_ctx_docs_if_no_context(self):
        ctx_docs_list = ["Doc 1", "Doc 2"]
        
        ctx_docs, has_reliable, quality, has_foundational = _build_ctx_docs_for_rewrite(
            None, ctx_docs_list, False
        )
        
        assert ctx_docs == ctx_docs_list


class TestEvaluateResponseQuality:
    """Tests for _evaluate_response_quality"""
    
    @patch('backend.postprocessing.quality_evaluator.get_quality_evaluator')
    def test_uses_cached_quality(self, mock_get_evaluator):
        mock_optimizer = Mock()
        mock_optimizer.get_cached_quality_result.return_value = {"overall_score": 0.8}
        
        chat_request = Mock()
        chat_request.message = "Test question"
        
        result = _evaluate_response_quality(
            "Response", False, chat_request, mock_optimizer, False
        )
        
        assert result == {"overall_score": 0.8}
        mock_optimizer.get_cached_quality_result.assert_called_once()
    
    @patch('backend.postprocessing.quality_evaluator.get_quality_evaluator')
    @patch('backend.core.stillme_detector.detect_stillme_query')
    def test_evaluates_and_caches(self, mock_detect, mock_get_evaluator):
        mock_optimizer = Mock()
        mock_optimizer.get_cached_quality_result.return_value = None
        
        mock_evaluator = Mock()
        mock_evaluator.evaluate.return_value = {"overall_score": 0.7}
        mock_get_evaluator.return_value = mock_evaluator
        
        mock_detect.return_value = (False, None)
        
        chat_request = Mock()
        chat_request.message = "Test question"
        
        result = _evaluate_response_quality(
            "Response", False, chat_request, mock_optimizer, False
        )
        
        assert result == {"overall_score": 0.7}
        mock_evaluator.evaluate.assert_called_once()
        mock_optimizer.cache_quality_result.assert_called_once()


class TestDetectFactualQuestion:
    """Tests for _detect_factual_question"""
    
    def test_detects_year_pattern(self):
        assert _detect_factual_question("What happened in 1945?") is True
    
    def test_detects_philosopher_names(self):
        assert _detect_factual_question("What did Plato say?") is True
        assert _detect_factual_question("Tell me about Gödel") is True
    
    def test_detects_paradox_keywords(self):
        assert _detect_factual_question("Explain the Chinese room paradox") is True
    
    def test_detects_comparison_pattern(self):
        assert _detect_factual_question("Searle và Dennett") is True
    
    def test_returns_false_for_non_factual(self):
        assert _detect_factual_question("How are you?") is False
        assert _detect_factual_question("What is love?") is False


class TestReAddCitationsAfterRewrite:
    """Tests for _re_add_citations_after_rewrite"""
    
    def test_keeps_response_if_citations_exist(self):
        response_with_citations = "This is a response [1] with citations [2]"
        
        chat_request = Mock()
        chat_request.message = "Test question"
        
        result = _re_add_citations_after_rewrite(
            response_with_citations, None, [], False, chat_request
        )
        
        assert result == response_with_citations
    
    @patch('backend.validators.citation.CitationRequired')
    def test_re_adds_citations_for_factual_question(self, mock_citation_class):
        mock_validator = Mock()
        mock_result = Mock()
        mock_result.patched_answer = "Response with [1] citation"
        mock_validator.run.return_value = mock_result
        mock_citation_class.return_value = mock_validator
        
        chat_request = Mock()
        chat_request.message = "What happened in 1945?"
        
        result = _re_add_citations_after_rewrite(
            "Response without citations", None, [], False, chat_request
        )
        
        assert result == "Response with [1] citation"
        mock_validator.run.assert_called_once()


class TestProcessResponse:
    """Tests for process_response"""
    
    @pytest.mark.asyncio
    @patch('backend.postprocessing.optimizer.get_postprocessing_optimizer')
    async def test_skips_if_optimizer_says_skip(self, mock_get_optimizer):
        mock_optimizer = Mock()
        mock_optimizer.should_skip_postprocessing.return_value = (True, "test_reason")
        mock_get_optimizer.return_value = mock_optimizer
        
        chat_request = Mock()
        chat_request.message = "Test question"
        processing_steps = []
        timing_logs = {}
        
        result, time_taken = await process_response(
            "Response", None, "en", False, False, chat_request,
            None, processing_steps, timing_logs
        )
        
        assert result == "Response"
        assert time_taken == 0.0
        assert timing_logs["postprocessing"] == "skipped"
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.post_processing_handler._sanitize_response')
    @patch('backend.api.handlers.post_processing_handler.is_technical_error')
    @patch('backend.api.handlers.post_processing_handler.is_fallback_message')
    @patch('backend.postprocessing.optimizer.get_postprocessing_optimizer')
    async def test_skips_if_technical_error(self, mock_get_optimizer, mock_is_fallback, mock_is_error, mock_sanitize):
        mock_sanitize.return_value = "Sanitized"
        mock_is_error.return_value = (True, "error_type")
        mock_is_fallback.return_value = False
        
        mock_optimizer = Mock()
        mock_optimizer.should_skip_postprocessing.return_value = (False, None)
        mock_get_optimizer.return_value = mock_optimizer
        
        chat_request = Mock()
        chat_request.message = "Test question"
        processing_steps = []
        timing_logs = {}
        
        result, time_taken = await process_response(
            "Response", None, "en", False, False, chat_request,
            None, processing_steps, timing_logs
        )
        
        assert result == "Sanitized"
        assert "Technical error detected" in processing_steps[0]
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.post_processing_handler._sanitize_response')
    @patch('backend.api.handlers.post_processing_handler.is_technical_error')
    @patch('backend.api.handlers.post_processing_handler.is_fallback_message')
    @patch('backend.api.handlers.post_processing_handler._build_ctx_docs_for_rewrite')
    @patch('backend.api.handlers.post_processing_handler._evaluate_response_quality')
    @patch('backend.api.handlers.post_processing_handler._rewrite_response')
    @patch('backend.api.handlers.post_processing_handler._re_add_citations_after_rewrite')
    @patch('backend.postprocessing.optimizer.get_postprocessing_optimizer')
    async def test_full_pipeline(self, mock_get_optimizer, mock_re_add, mock_rewrite, mock_evaluate, 
                                  mock_build_ctx, mock_is_fallback, mock_is_error, mock_sanitize):
        mock_sanitize.return_value = "Sanitized"
        mock_is_error.return_value = (False, None)
        mock_is_fallback.return_value = False
        mock_build_ctx.return_value = ([], False, None, False)
        mock_evaluate.return_value = {"overall_score": 0.8}
        mock_rewrite.return_value = "Rewritten"
        mock_re_add.return_value = "Final"
        
        mock_optimizer = Mock()
        mock_optimizer.should_skip_postprocessing.return_value = (False, None)
        mock_get_optimizer.return_value = mock_optimizer
        
        chat_request = Mock()
        chat_request.message = "Test question"
        processing_steps = []
        timing_logs = {}
        
        result, time_taken = await process_response(
            "Response", {}, "en", False, False, chat_request,
            None, processing_steps, timing_logs
        )
        
        assert result == "Final"
        assert time_taken > 0
        assert "postprocessing" in timing_logs

