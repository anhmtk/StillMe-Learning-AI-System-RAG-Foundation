"""
Unit tests for query_router.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.api.handlers.query_router import (
    route_query,
    _handle_codebase_meta_question,
    _handle_ambiguity_clarification,
    _handle_origin_query,
    _handle_religion_choice_rejection,
    _handle_honesty_question,
    _handle_ai_self_model_query,
    _detect_query_types
)


class TestHandleOriginQuery:
    """Tests for _handle_origin_query"""
    
    @patch('backend.core.stillme_detector.detect_origin_query')
    @patch('backend.api.handlers.query_router.detect_language')
    @patch('backend.identity.system_origin.get_system_origin_answer')
    def test_handles_origin_query(self, mock_get_answer, mock_detect_lang, mock_detect_origin):
        mock_detect_origin.return_value = (True, ["origin", "created"])
        mock_detect_lang.return_value = "en"
        mock_get_answer.return_value = "I am StillMe, created by..."
        
        chat_request = Mock()
        chat_request.message = "Where do you come from?"
        
        result = _handle_origin_query(chat_request)
        
        assert result is not None
        assert result.response == "I am StillMe, created by..."
        assert result.confidence_score == 1.0
    
    @patch('backend.core.stillme_detector.detect_origin_query')
    def test_returns_none_if_not_origin_query(self, mock_detect_origin):
        mock_detect_origin.return_value = (False, [])
        
        chat_request = Mock()
        chat_request.message = "What is the weather?"
        
        result = _handle_origin_query(chat_request)
        
        assert result is None


class TestHandleReligionChoiceRejection:
    """Tests for _handle_religion_choice_rejection"""
    
    @patch('backend.core.ai_self_model_detector.detect_religion_choice_query')
    @patch('backend.api.handlers.query_router.detect_language')
    @patch('backend.identity.religion_rejection_templates.get_religion_rejection_answer')
    def test_handles_religion_choice_query(self, mock_get_answer, mock_detect_lang, mock_detect):
        mock_detect.return_value = (True, ["religion", "choose"])
        mock_detect_lang.return_value = "en"
        mock_get_answer.return_value = "I cannot choose any religion..."
        
        chat_request = Mock()
        chat_request.message = "What religion do you follow?"
        
        result = _handle_religion_choice_rejection(chat_request)
        
        assert result is not None
        assert result.response == "I cannot choose any religion..."
        assert result.confidence_score == 1.0
    
    @patch('backend.core.ai_self_model_detector.detect_religion_choice_query')
    def test_returns_none_if_not_religion_choice(self, mock_detect):
        mock_detect.return_value = (False, [])
        
        chat_request = Mock()
        chat_request.message = "What is the weather?"
        
        result = _handle_religion_choice_rejection(chat_request)
        
        assert result is None


class TestHandleHonestyQuestion:
    """Tests for _handle_honesty_question"""
    
    @patch('backend.honesty.handler.is_honesty_question')
    @patch('backend.api.handlers.query_router.detect_language')
    @patch('backend.honesty.handler.build_honesty_response')
    def test_handles_honesty_question(self, mock_build, mock_detect_lang, mock_check):
        mock_check.return_value = True
        mock_detect_lang.return_value = "en"
        mock_build.return_value = "I am honest about..."
        
        chat_request = Mock()
        chat_request.message = "Are you honest?"
        processing_steps = []
        start_time = 0.0
        
        result = _handle_honesty_question(chat_request, processing_steps, start_time)
        
        assert result is not None
        assert result.response == "I am honest about..."
        assert result.confidence_score == 1.0
    
    @patch('backend.honesty.handler.is_honesty_question')
    def test_returns_none_if_not_honesty_question(self, mock_check):
        mock_check.return_value = False
        
        chat_request = Mock()
        chat_request.message = "What is the weather?"
        processing_steps = []
        start_time = 0.0
        
        result = _handle_honesty_question(chat_request, processing_steps, start_time)
        
        assert result is None


class TestHandleAiSelfModelQuery:
    """Tests for _handle_ai_self_model_query"""
    
    @patch('backend.core.ai_self_model_detector.detect_ai_self_model_query')
    @patch('backend.api.handlers.query_router.detect_language')
    @patch('backend.core.ai_self_model_detector.get_ai_self_model_opening')
    @patch('backend.api.utils.response_formatters.build_ai_self_model_answer')
    @patch('backend.api.utils.text_utils.strip_philosophy_from_answer')
    def test_handles_ai_self_model_query(self, mock_strip, mock_build, mock_get_opening, 
                                         mock_detect_lang, mock_detect):
        mock_detect.return_value = (True, ["consciousness", "awareness"])
        mock_detect_lang.return_value = "en"
        mock_get_opening.return_value = "I am a technical system..."
        mock_build.return_value = "Technical answer about StillMe..."
        mock_strip.return_value = "Technical answer about StillMe..."
        
        chat_request = Mock()
        chat_request.message = "Are you conscious?"
        processing_steps = []
        start_time = 0.0
        
        result = _handle_ai_self_model_query(chat_request, processing_steps, start_time)
        
        assert result is not None
        assert result.response == "Technical answer about StillMe..."
        assert result.confidence_score == 1.0
    
    @patch('backend.core.ai_self_model_detector.detect_ai_self_model_query')
    def test_returns_none_if_not_ai_self_model_query(self, mock_detect):
        mock_detect.return_value = (False, [])
        
        chat_request = Mock()
        chat_request.message = "What is the weather?"
        processing_steps = []
        start_time = 0.0
        
        result = _handle_ai_self_model_query(chat_request, processing_steps, start_time)
        
        assert result is None


class TestHandleCodebaseMetaQuestion:
    """Tests for _handle_codebase_meta_question"""
    
    @pytest.mark.asyncio
    @patch('backend.services.codebase_indexer.get_codebase_indexer')
    @patch('backend.api.routers.codebase_router._generate_code_explanation')
    async def test_handles_codebase_meta_question(self, mock_generate, mock_get_indexer):
        mock_indexer = Mock()
        mock_indexer.query_codebase.return_value = [
            {"document": "code snippet", "metadata": {"file": "test.py"}}
        ]
        mock_get_indexer.return_value = mock_indexer
        mock_generate.return_value = "Explanation of code"
        
        chat_request = Mock()
        chat_request.message = "How does validation work in your codebase?"
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        decision_logger = Mock()
        
        result = await _handle_codebase_meta_question(
            chat_request, processing_steps, timing_logs, start_time, decision_logger
        )
        
        assert result is not None
        assert result.response == "Explanation of code"
        assert result.confidence_score == 0.9
    
    @pytest.mark.asyncio
    @patch('backend.services.codebase_indexer.get_codebase_indexer')
    async def test_returns_none_if_no_code_results(self, mock_get_indexer):
        mock_indexer = Mock()
        mock_indexer.query_codebase.return_value = []
        mock_get_indexer.return_value = mock_indexer
        
        chat_request = Mock()
        chat_request.message = "How does validation work?"
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        decision_logger = Mock()
        
        result = await _handle_codebase_meta_question(
            chat_request, processing_steps, timing_logs, start_time, decision_logger
        )
        
        assert result is None


class TestHandleAmbiguityClarification:
    """Tests for _handle_ambiguity_clarification"""
    
    @pytest.mark.asyncio
    @patch('backend.core.ambiguity_detector.get_ambiguity_detector')
    @patch('backend.api.handlers.query_router.detect_language')
    async def test_handles_ambiguity_clarification(self, mock_detect_lang, mock_get_detector):
        mock_detector = Mock()
        mock_detector.should_ask_clarification.return_value = (True, "What do you mean?")
        mock_get_detector.return_value = mock_detector
        mock_detect_lang.return_value = "en"
        
        chat_request = Mock()
        chat_request.message = "Tell me about it"
        chat_request.conversation_history = []
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        
        result = await _handle_ambiguity_clarification(
            chat_request, processing_steps, timing_logs, start_time
        )
        
        assert result is not None
        assert result.response == "What do you mean?"
        assert result.confidence_score == 0.0
    
    @pytest.mark.asyncio
    @patch('backend.core.ambiguity_detector.get_ambiguity_detector')
    async def test_returns_none_if_no_clarification_needed(self, mock_get_detector):
        mock_detector = Mock()
        mock_detector.should_ask_clarification.return_value = (False, None)
        mock_get_detector.return_value = mock_detector
        
        chat_request = Mock()
        chat_request.message = "What is the weather?"
        chat_request.conversation_history = []
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        
        result = await _handle_ambiguity_clarification(
            chat_request, processing_steps, timing_logs, start_time
        )
        
        assert result is None


class TestRouteQuery:
    """Tests for route_query"""
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.query_router.is_codebase_meta_question')
    @patch('backend.api.handlers.query_router._handle_codebase_meta_question')
    async def test_routes_codebase_meta_question(self, mock_handle, mock_is_meta):
        mock_is_meta.return_value = True
        mock_handle.return_value = Mock()
        
        chat_request = Mock()
        chat_request.message = "How does validation work in your codebase?"
        request = Mock()
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        decision_logger = Mock()
        
        result = await route_query(
            chat_request, request, processing_steps, timing_logs, start_time, decision_logger
        )
        
        assert result is not None
        mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.query_router.is_codebase_meta_question')
    @patch('backend.api.handlers.query_router._handle_ambiguity_clarification')
    @patch('backend.api.handlers.query_router._handle_origin_query')
    @patch('backend.api.handlers.query_router._handle_religion_choice_rejection')
    @patch('backend.api.handlers.query_router._handle_honesty_question')
    @patch('backend.api.handlers.query_router._handle_ai_self_model_query')
    async def test_routes_through_all_handlers(self, mock_ai, mock_honesty, mock_religion, 
                                               mock_origin, mock_ambiguity, mock_is_meta):
        mock_is_meta.return_value = False
        mock_ambiguity.return_value = None
        mock_origin.return_value = None
        mock_religion.return_value = None
        mock_honesty.return_value = None
        mock_ai.return_value = None
        
        chat_request = Mock()
        chat_request.message = "Normal question"
        request = Mock()
        processing_steps = []
        timing_logs = {}
        start_time = 0.0
        decision_logger = Mock()
        
        result = await route_query(
            chat_request, request, processing_steps, timing_logs, start_time, decision_logger
        )
        
        assert result is None
        mock_ambiguity.assert_called_once()
        mock_origin.assert_called_once()
        mock_religion.assert_called_once()
        mock_honesty.assert_called_once()
        mock_ai.assert_called_once()


class TestDetectQueryTypes:
    """Tests for _detect_query_types"""
    
    @patch('backend.api.handlers.query_router.is_codebase_meta_question')
    @patch('backend.core.ambiguity_detector.get_ambiguity_detector')
    @patch('backend.core.stillme_detector.detect_origin_query')
    @patch('backend.core.ai_self_model_detector.detect_religion_choice_query')
    @patch('backend.honesty.handler.is_honesty_question')
    @patch('backend.core.ai_self_model_detector.detect_ai_self_model_query')
    def test_detects_all_query_types(self, mock_ai, mock_honesty, mock_religion, 
                                     mock_origin, mock_ambiguity, mock_is_meta):
        mock_is_meta.return_value = True
        mock_get_detector = Mock()
        mock_detector = Mock()
        mock_detector.should_ask_clarification.return_value = (True, "Clarify?")
        mock_get_detector.return_value = mock_detector
        mock_ambiguity.return_value = mock_get_detector
        mock_origin.return_value = (True, ["origin"])
        mock_religion.return_value = (True, ["religion"])
        mock_honesty.return_value = True
        mock_ai.return_value = (True, ["consciousness"])
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.conversation_history = []
        
        result = _detect_query_types(chat_request)
        
        assert result["is_codebase_meta"] is True
        assert result["is_ambiguous"] is True
        assert result["is_origin"] is True
        assert result["is_religion_choice"] is True
        assert result["is_honesty"] is True
        assert result["is_ai_self_model"] is True

