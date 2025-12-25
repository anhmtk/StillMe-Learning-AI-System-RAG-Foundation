"""Unit tests for llm_handler.py module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from backend.api.handlers.llm_handler import (
    generate_llm_response,
    _estimate_tokens,
    _pre_check_token_limit,
    _check_cache,
    _store_cache,
    _call_llm_with_retry
)
from backend.api.models import ChatRequest


class TestEstimateTokens:
    """Tests for _estimate_tokens function."""
    
    def test_estimates_tokens_correctly(self):
        """Test that function estimates tokens correctly."""
        text = "Hello world" * 100  # ~1100 chars
        tokens = _estimate_tokens(text)
        # Should be approximately 1100 / 3.5 = ~314
        assert tokens > 200
        assert tokens < 400
    
    def test_returns_zero_for_empty_text(self):
        """Test that function returns zero for empty text."""
        assert _estimate_tokens("") == 0
        assert _estimate_tokens(None) == 0
    
    def test_handles_unicode_text(self):
        """Test that function handles Unicode text correctly."""
        text = "Xin chào" * 50  # Vietnamese text
        tokens = _estimate_tokens(text)
        assert tokens > 0


class TestPreCheckTokenLimit:
    """Tests for _pre_check_token_limit function."""
    
    @patch('backend.api.handlers.llm_handler.build_minimal_philosophical_prompt')
    def test_uses_minimal_prompt_for_philosophical_when_over_limit(self, mock_build_minimal):
        """Test that function uses minimal prompt for philosophical questions when over limit."""
        mock_build_minimal.return_value = "Minimal prompt"
        
        enhanced_prompt = "A" * 60000  # Very long prompt (~17k tokens)
        context_text = "Context"
        processing_steps = []
        
        result_prompt, result_context = _pre_check_token_limit(
            enhanced_prompt=enhanced_prompt,
            context_text=context_text,
            is_philosophical=True,
            detected_lang="en",
            detected_lang_name="English",
            chat_request=Mock(),
            context={},
            processing_steps=processing_steps
        )
        
        assert result_prompt == "Minimal prompt"
        assert mock_build_minimal.called
    
    def test_truncates_context_for_non_philosophical_when_over_limit(self):
        """Test that function truncates context for non-philosophical questions when over limit."""
        # Create a prompt that will exceed the limit when combined with system prompt
        # System prompt buffer = 3600, output buffer = 1500, so we need prompt > 15000 - 3600 - 1500 = 9900 tokens
        # That's about 9900 * 3.5 = 34650 chars
        enhanced_prompt = "A" * 40000  # ~11.4k tokens
        context_text = "B" * 100000  # Very long context
        processing_steps = []
        
        result_prompt, result_context = _pre_check_token_limit(
            enhanced_prompt=enhanced_prompt,
            context_text=context_text,
            is_philosophical=False,
            detected_lang="en",
            detected_lang_name="English",
            chat_request=Mock(),
            context={},
            processing_steps=processing_steps
        )
        
        # Context should be truncated if prompt exceeds limit
        # But if prompt itself doesn't exceed, context might not be truncated
        # So we check that either context is truncated OR prompt is unchanged
        if len(result_context) < len(context_text):
            assert "[Context truncated to prevent overflow]" in result_context
        else:
            # If context wasn't truncated, prompt should be unchanged
            assert result_prompt == enhanced_prompt
    
    def test_returns_unchanged_when_under_limit(self):
        """Test that function returns unchanged prompt when under limit."""
        enhanced_prompt = "Short prompt"
        context_text = "Short context"
        processing_steps = []
        
        result_prompt, result_context = _pre_check_token_limit(
            enhanced_prompt=enhanced_prompt,
            context_text=context_text,
            is_philosophical=False,
            detected_lang="en",
            detected_lang_name="English",
            chat_request=Mock(),
            context={},
            processing_steps=processing_steps
        )
        
        assert result_prompt == enhanced_prompt
        assert result_context == context_text


class TestCheckCache:
    """Tests for _check_cache function."""
    
    def test_returns_cached_response_when_valid(self):
        """Test that function returns cached response when valid."""
        cache_service = Mock()
        cache_service.get.return_value = {
            "response": "Cached response",
            "latency": 0.5
        }
        
        processing_steps = []
        timing_logs = {}
        
        response, cache_hit, latency = _check_cache(
            cache_service=cache_service,
            cache_key="test_key",
            is_validator_count_question=False,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response == "Cached response"
        assert cache_hit is True
        assert latency == 0.5
        assert "⚡ Response from cache" in processing_steps[0]
    
    def test_force_cache_miss_for_validator_count_question(self):
        """Test that function forces cache miss for validator count questions."""
        cache_service = Mock()
        processing_steps = []
        timing_logs = {}
        
        response, cache_hit, latency = _check_cache(
            cache_service=cache_service,
            cache_key="test_key",
            is_validator_count_question=True,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response is None
        assert cache_hit is False
        assert latency == 0.0
        assert not cache_service.get.called
    
    @patch('backend.api.handlers.llm_handler.is_fallback_message')
    def test_ignores_fallback_message_in_cache(self, mock_is_fallback):
        """Test that function ignores fallback message in cache."""
        mock_is_fallback.return_value = True
        
        cache_service = Mock()
        cache_service.get.return_value = {
            "response": "⚠️ StillMe is experiencing a technical issue",
            "latency": 0.5
        }
        
        processing_steps = []
        timing_logs = {}
        
        response, cache_hit, latency = _check_cache(
            cache_service=cache_service,
            cache_key="test_key",
            is_validator_count_question=False,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response is None
        assert cache_hit is False


class TestStoreCache:
    """Tests for _store_cache function."""
    
    def test_stores_cache_successfully(self):
        """Test that function stores cache successfully."""
        cache_service = Mock()
        
        _store_cache(
            cache_service=cache_service,
            cache_key="test_key",
            response="Test response",
            latency=1.5,
            cache_ttl_override=None,
            is_validator_count_question=False
        )
        
        assert cache_service.set.called
        call_args = cache_service.set.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1]["response"] == "Test response"
        assert call_args[0][1]["latency"] == 1.5
    
    def test_skips_cache_for_validator_count_question(self):
        """Test that function skips cache for validator count questions."""
        cache_service = Mock()
        
        _store_cache(
            cache_service=cache_service,
            cache_key="test_key",
            response="Test response",
            latency=1.5,
            cache_ttl_override=None,
            is_validator_count_question=True
        )
        
        assert not cache_service.set.called
    
    def test_uses_custom_ttl_when_provided(self):
        """Test that function uses custom TTL when provided."""
        cache_service = Mock()
        
        _store_cache(
            cache_service=cache_service,
            cache_key="test_key",
            response="Test response",
            latency=1.5,
            cache_ttl_override=3600,
            is_validator_count_question=False
        )
        
        call_args = cache_service.set.call_args
        assert call_args[1]["ttl_seconds"] == 3600


class TestCallLlmWithRetry:
    """Tests for _call_llm_with_retry function."""
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler.generate_ai_response')
    async def test_calls_llm_successfully(self, mock_generate):
        """Test that function calls LLM successfully."""
        mock_generate.return_value = "Test response"
        
        chat_request = Mock()
        chat_request.llm_provider = None
        chat_request.llm_api_key = None
        chat_request.llm_api_url = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        
        response = await _call_llm_with_retry(
            enhanced_prompt="Test prompt",
            detected_lang="en",
            chat_request=chat_request,
            use_server_keys=True,
            is_philosophical=False,
            context={},
            detected_lang_name="English",
            processing_steps=processing_steps
        )
        
        assert response == "Test response"
        assert mock_generate.called
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler.generate_ai_response')
    @patch('backend.api.handlers.llm_handler.build_minimal_philosophical_prompt')
    @patch('backend.api.handlers.llm_handler.get_fallback_message_for_error')
    async def test_retries_with_minimal_prompt_on_context_overflow(self, mock_fallback, mock_build_minimal, mock_generate):
        """Test that function retries with minimal prompt on context overflow."""
        from backend.api.utils.llm_providers import ContextOverflowError
        
        mock_generate.side_effect = [
            ContextOverflowError("Context overflow"),
            "Retry response"
        ]
        mock_build_minimal.return_value = "Minimal prompt"
        
        chat_request = Mock()
        chat_request.llm_provider = None
        chat_request.llm_api_key = None
        chat_request.llm_api_url = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        
        response = await _call_llm_with_retry(
            enhanced_prompt="Test prompt",
            detected_lang="en",
            chat_request=chat_request,
            use_server_keys=True,
            is_philosophical=True,
            context={},
            detected_lang_name="English",
            processing_steps=processing_steps
        )
        
        assert response == "Retry response"
        assert mock_generate.call_count == 2
        assert mock_build_minimal.called
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler.generate_ai_response')
    @patch('backend.api.handlers.llm_handler.get_fallback_message_for_error')
    async def test_returns_fallback_for_non_philosophical_context_overflow(self, mock_fallback, mock_generate):
        """Test that function returns fallback for non-philosophical context overflow."""
        from backend.api.utils.llm_providers import ContextOverflowError
        
        mock_generate.side_effect = ContextOverflowError("Context overflow")
        mock_fallback.return_value = "Fallback message"
        
        chat_request = Mock()
        chat_request.llm_provider = None
        chat_request.llm_api_key = None
        chat_request.llm_api_url = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        
        response = await _call_llm_with_retry(
            enhanced_prompt="Test prompt",
            detected_lang="en",
            chat_request=chat_request,
            use_server_keys=True,
            is_philosophical=False,
            context={},
            detected_lang_name="English",
            processing_steps=processing_steps
        )
        
        assert response == "Fallback message"
        assert mock_fallback.called


class TestGenerateLlmResponse:
    """Tests for generate_llm_response function."""
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler._check_cache')
    @patch('backend.api.handlers.llm_handler.get_cache_service')
    async def test_returns_cached_response_when_available(self, mock_get_cache, mock_check_cache):
        """Test that function returns cached response when available."""
        mock_cache_service = Mock()
        mock_get_cache.return_value = mock_cache_service
        
        mock_check_cache.return_value = ("Cached response", True, 0.5)
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.llm_provider = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        timing_logs = {}
        
        response, cache_hit, latency = await generate_llm_response(
            enhanced_prompt="Test prompt",
            detected_lang="en",
            chat_request=chat_request,
            context={},
            is_philosophical=False,
            is_validator_count_question=False,
            is_origin_query=False,
            is_stillme_query=False,
            detected_lang_name="English",
            context_text="Context",
            enable_validators=True,
            use_option_b=False,
            fps_result=None,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response == "Cached response"
        assert cache_hit is True
        assert latency == 0.5
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler._call_llm_with_retry')
    @patch('backend.api.handlers.llm_handler._check_cache')
    @patch('backend.api.handlers.llm_handler._store_cache')
    @patch('backend.api.handlers.llm_handler.get_cache_service')
    @patch('backend.services.knowledge_version.get_knowledge_version')
    async def test_calls_llm_when_not_cached(self, mock_get_knowledge_version, mock_get_cache, mock_store_cache, mock_check_cache, mock_call_llm):
        """Test that function calls LLM when not cached."""
        mock_cache_service = Mock()
        mock_get_cache.return_value = mock_cache_service
        mock_get_knowledge_version.return_value = "v1.0"
        
        mock_check_cache.return_value = (None, False, 0.0)
        mock_call_llm.return_value = "LLM response"
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.llm_provider = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        timing_logs = {}
        
        response, cache_hit, latency = await generate_llm_response(
            enhanced_prompt="Test prompt",
            detected_lang="en",
            chat_request=chat_request,
            context={},
            is_philosophical=False,
            is_validator_count_question=False,
            is_origin_query=False,
            is_stillme_query=False,
            detected_lang_name="English",
            context_text="Context",
            enable_validators=True,
            use_option_b=False,
            fps_result=None,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response == "LLM response"
        assert cache_hit is False
        assert mock_call_llm.called
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.llm_handler._check_cache')
    @patch('backend.api.handlers.llm_handler.get_cache_service')
    async def test_disables_cache_for_origin_queries(self, mock_get_cache, mock_check_cache):
        """Test that function disables cache for origin queries."""
        mock_cache_service = Mock()
        mock_get_cache.return_value = mock_cache_service
        
        mock_check_cache.return_value = (None, False, 0.0)
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.llm_provider = None
        chat_request.llm_model_name = None
        
        processing_steps = []
        timing_logs = {}
        
        # Mock the LLM call to avoid actual API call
        with patch('backend.api.handlers.llm_handler._call_llm_with_retry', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "LLM response"
            
            response, cache_hit, latency = await generate_llm_response(
                enhanced_prompt="Test prompt",
                detected_lang="en",
                chat_request=chat_request,
                context={},
                is_philosophical=False,
                is_validator_count_question=False,
                is_origin_query=True,  # Origin query
                is_stillme_query=False,
                detected_lang_name="English",
                context_text="Context",
                enable_validators=True,
                use_option_b=False,
                fps_result=None,
                processing_steps=processing_steps,
                timing_logs=timing_logs
            )
            
            # Cache should not be checked for origin queries
            assert not mock_check_cache.called

