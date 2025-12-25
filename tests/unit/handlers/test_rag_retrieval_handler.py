"""Unit tests for rag_retrieval_handler.py module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.api.handlers.rag_retrieval_handler import (
    retrieve_rag_context,
    _prepare_exclude_types,
    _force_inject_manifest,
    _retrieve_origin_context,
    _retrieve_historical_context,
    _retrieve_validator_count_context,
    _retrieve_stillme_context,
    _retrieve_news_article_context,
    _retrieve_normal_context,
    _check_and_filter_critical_foundation,
    _log_rag_retrieval_decision
)
from backend.api.models import ChatRequest
from backend.vector_db.rag_retrieval import RAGRetrieval
from backend.core.decision_logger import AgentType, DecisionType


class TestPrepareExcludeTypes:
    """Tests for _prepare_exclude_types function."""
    
    def test_returns_style_guide_for_non_philosophical(self):
        """Test that function returns style_guide for non-philosophical questions."""
        result = _prepare_exclude_types(is_philosophical=False)
        assert "style_guide" in result
        assert "technical" not in result
    
    def test_returns_both_for_philosophical(self):
        """Test that function returns both technical and style_guide for philosophical questions."""
        result = _prepare_exclude_types(is_philosophical=True)
        assert "style_guide" in result
        assert "technical" in result


class TestCheckAndFilterCriticalFoundation:
    """Tests for _check_and_filter_critical_foundation function."""
    
    def test_filters_critical_foundation_docs(self):
        """Test that function filters out CRITICAL_FOUNDATION documents."""
        context = {
            "knowledge_docs": [
                {
                    "metadata": {
                        "source": "CRITICAL_FOUNDATION",
                        "title": "Manifest"
                    }
                },
                {
                    "metadata": {
                        "source": "RSS",
                        "title": "News Article"
                    }
                }
            ],
            "conversation_docs": [],
            "total_context_docs": 2
        }
        
        result = _check_and_filter_critical_foundation(context)
        
        assert len(result["knowledge_docs"]) == 1
        assert result["knowledge_docs"][0]["metadata"]["source"] == "RSS"
        assert result["total_context_docs"] == 1
    
    def test_handles_empty_context(self):
        """Test that function handles empty context."""
        context = {
            "knowledge_docs": [],
            "conversation_docs": [],
            "total_context_docs": 0
        }
        
        result = _check_and_filter_critical_foundation(context)
        
        assert len(result["knowledge_docs"]) == 0
        assert result["total_context_docs"] == 0


class TestRetrieveRagContext:
    """Tests for retrieve_rag_context function."""
    
    def test_returns_none_when_rag_disabled(self):
        """Test that function returns None when RAG is disabled."""
        chat_request = ChatRequest(message="Test", use_rag=False)
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=None,
            is_origin_query=False,
            is_validator_count_question=False,
            is_stillme_query=False,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is None
    
    def test_returns_none_when_rag_retrieval_none(self):
        """Test that function returns None when rag_retrieval is None."""
        chat_request = ChatRequest(message="Test", use_rag=True)
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=None,
            is_origin_query=False,
            is_validator_count_question=False,
            is_stillme_query=False,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is None
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_origin_context')
    def test_routes_to_origin_context(self, mock_retrieve_origin):
        """Test that function routes to origin context for origin queries."""
        chat_request = ChatRequest(message="Who created StillMe?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_retrieve_origin.return_value = {
            "knowledge_docs": [{"metadata": {"source": "PROVENANCE"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=mock_rag_retrieval,
            is_origin_query=True,
            is_validator_count_question=False,
            is_stillme_query=False,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_origin.assert_called_once()
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_validator_count_context')
    def test_routes_to_validator_count_context(self, mock_retrieve_validator):
        """Test that function routes to validator count context for validator count questions."""
        chat_request = ChatRequest(message="How many validators?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_retrieve_validator.return_value = {
            "knowledge_docs": [{"metadata": {"source": "CRITICAL_FOUNDATION"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=mock_rag_retrieval,
            is_origin_query=False,
            is_validator_count_question=True,
            is_stillme_query=False,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_validator.assert_called_once()
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_stillme_context')
    def test_routes_to_stillme_context(self, mock_retrieve_stillme):
        """Test that function routes to StillMe context for StillMe queries."""
        chat_request = ChatRequest(message="What is StillMe?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_retrieve_stillme.return_value = {
            "knowledge_docs": [{"metadata": {"source": "CRITICAL_FOUNDATION"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=mock_rag_retrieval,
            is_origin_query=False,
            is_validator_count_question=False,
            is_stillme_query=True,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_stillme.assert_called_once()
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_news_article_context')
    def test_routes_to_news_article_context(self, mock_retrieve_news):
        """Test that function routes to news article context for news queries."""
        chat_request = ChatRequest(message="What is the latest news?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_retrieve_news.return_value = {
            "knowledge_docs": [{"metadata": {"source": "RSS"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=mock_rag_retrieval,
            is_origin_query=False,
            is_validator_count_question=False,
            is_stillme_query=False,
            is_news_article_query=True,
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_news.assert_called_once()
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_normal_context')
    def test_routes_to_normal_context(self, mock_retrieve_normal):
        """Test that function routes to normal context for regular queries."""
        chat_request = ChatRequest(message="What is AI?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_retrieve_normal.return_value = {
            "knowledge_docs": [{"metadata": {"source": "RSS"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=mock_rag_retrieval,
            is_origin_query=False,
            is_validator_count_question=False,
            is_stillme_query=False,
            is_news_article_query=False,
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_normal.assert_called_once()
    
    def test_treats_technical_your_system_as_stillme_query(self):
        """Test that technical questions about 'your system' are treated as StillMe queries."""
        chat_request = ChatRequest(message="How does RAG work in your system?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        
        with patch('backend.api.handlers.rag_retrieval_handler._retrieve_stillme_context') as mock_retrieve_stillme:
            mock_retrieve_stillme.return_value = {
                "knowledge_docs": [{"metadata": {"source": "CRITICAL_FOUNDATION"}}],
                "conversation_docs": [],
                "total_context_docs": 1
            }
            
            result = retrieve_rag_context(
                chat_request=chat_request,
                rag_retrieval=mock_rag_retrieval,
                is_origin_query=False,
                is_validator_count_question=False,
                is_stillme_query=False,  # Initially False
                is_news_article_query=False,
                is_philosophical=False,
                is_technical_question=True  # Technical question
            )
            
            # Should route to StillMe context because of "your system"
            assert result is not None
            mock_retrieve_stillme.assert_called_once()
    
    def test_adds_processing_step(self):
        """Test that function adds processing step when provided."""
        chat_request = ChatRequest(message="Test", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        processing_steps = []
        
        with patch('backend.api.handlers.rag_retrieval_handler._retrieve_normal_context') as mock_retrieve:
            mock_retrieve.return_value = {
                "knowledge_docs": [],
                "conversation_docs": [],
                "total_context_docs": 0
            }
            
            retrieve_rag_context(
                chat_request=chat_request,
                rag_retrieval=mock_rag_retrieval,
                is_origin_query=False,
                is_validator_count_question=False,
                is_stillme_query=False,
                is_news_article_query=False,
                is_philosophical=False,
                processing_steps=processing_steps
            )
            
            assert "🔍 Searching knowledge base..." in processing_steps


class TestRetrieveOriginContext:
    """Tests for _retrieve_origin_context function."""
    
    @patch('backend.api.handlers.rag_retrieval_handler._retrieve_historical_context')
    def test_falls_back_to_historical_when_no_provenance(self, mock_retrieve_historical):
        """Test that function falls back to historical retrieval when no provenance found."""
        chat_request = ChatRequest(message="Who created StillMe?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_rag_retrieval.chroma_client = Mock()
        mock_rag_retrieval.chroma_client.search_knowledge.return_value = []
        mock_rag_retrieval.embedding_service = Mock()
        mock_rag_retrieval.embedding_service.encode_text.return_value = [0.1] * 384
        
        mock_retrieve_historical.return_value = {
            "knowledge_docs": [],
            "conversation_docs": [],
            "total_context_docs": 0
        }
        
        result = _retrieve_origin_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False
        )
        
        assert result is not None
        mock_retrieve_historical.assert_called_once()


class TestRetrieveValidatorCountContext:
    """Tests for _retrieve_validator_count_context function."""
    
    @patch('backend.api.handlers.rag_retrieval_handler._force_inject_manifest')
    def test_force_injects_manifest(self, mock_force_inject):
        """Test that function force-injects manifest for validator count questions."""
        chat_request = ChatRequest(message="How many validators?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_rag_retrieval.retrieve_context.return_value = {
            "knowledge_docs": [],
            "conversation_docs": [],
            "total_context_docs": 0
        }
        
        mock_force_inject.return_value = {
            "knowledge_docs": [{"metadata": {"source": "CRITICAL_FOUNDATION"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = _retrieve_validator_count_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False
        )
        
        assert result is not None
        mock_force_inject.assert_called_once()


class TestRetrieveStillmeContext:
    """Tests for _retrieve_stillme_context function."""
    
    @patch('backend.api.handlers.rag_retrieval_handler.get_foundational_query_variants')
    def test_uses_query_variants(self, mock_get_variants):
        """Test that function uses query variants for StillMe queries."""
        chat_request = ChatRequest(message="What is StillMe?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_get_variants.return_value = ["variant1", "variant2", "variant3"]
        
        mock_rag_retrieval.retrieve_context.return_value = {
            "knowledge_docs": [{"id": "1", "metadata": {"source": "CRITICAL_FOUNDATION"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = _retrieve_stillme_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False,
            is_validator_count_question=False
        )
        
        assert result is not None
        assert mock_rag_retrieval.retrieve_context.call_count >= 1


class TestRetrieveNewsArticleContext:
    """Tests for _retrieve_news_article_context function."""
    
    @patch('backend.api.handlers.rag_retrieval_handler._check_and_filter_critical_foundation')
    def test_filters_critical_foundation(self, mock_filter):
        """Test that function filters CRITICAL_FOUNDATION for news queries."""
        chat_request = ChatRequest(message="What is the latest news?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_rag_retrieval.retrieve_context.return_value = {
            "knowledge_docs": [
                {"metadata": {"source": "CRITICAL_FOUNDATION"}},
                {"metadata": {"source": "RSS"}}
            ],
            "conversation_docs": [],
            "total_context_docs": 2
        }
        
        mock_filter.return_value = {
            "knowledge_docs": [{"metadata": {"source": "RSS"}}],
            "conversation_docs": [],
            "total_context_docs": 1
        }
        
        result = _retrieve_news_article_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False
        )
        
        assert result is not None
        mock_filter.assert_called_once()


class TestRetrieveNormalContext:
    """Tests for _retrieve_normal_context function."""
    
    @patch('backend.api.handlers.rag_retrieval_handler.is_historical_question')
    @patch('backend.api.handlers.rag_retrieval_handler.enhance_query_for_retrieval')
    def test_enhances_query_for_historical(self, mock_enhance, mock_is_historical):
        """Test that function enhances query for historical questions."""
        chat_request = ChatRequest(message="What happened in 1954?", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_is_historical.return_value = True
        mock_enhance.return_value = "What happened in 1954? Geneva Conference"
        
        mock_rag_retrieval.retrieve_context.return_value = {
            "knowledge_docs": [],
            "conversation_docs": [],
            "total_context_docs": 0
        }
        
        result = _retrieve_normal_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False,
            is_technical_question=False
        )
        
        assert result is not None
        mock_enhance.assert_called_once()
    
    @patch('backend.api.handlers.rag_retrieval_handler._log_rag_retrieval_decision')
    def test_logs_decision_when_logger_provided(self, mock_log):
        """Test that function logs decision when decision_logger is provided."""
        chat_request = ChatRequest(message="Test", use_rag=True)
        mock_rag_retrieval = Mock(spec=RAGRetrieval)
        mock_rag_retrieval.retrieve_context.return_value = {
            "knowledge_docs": [],
            "conversation_docs": [],
            "total_context_docs": 0
        }
        mock_decision_logger = Mock()
        
        _retrieve_normal_context(
            chat_request,
            mock_rag_retrieval,
            exclude_types=[],
            is_philosophical=False,
            is_technical_question=False,
            decision_logger=mock_decision_logger
        )
        
        mock_log.assert_called_once()


class TestLogRagRetrievalDecision:
    """Tests for _log_rag_retrieval_decision function."""
    
    def test_logs_decision_correctly(self):
        """Test that function logs decision correctly."""
        mock_decision_logger = Mock()
        context = {
            "total_context_docs": 5,
            "knowledge_docs": [
                {"metadata": {"source": "RSS", "type": "news"}},
                {"metadata": {"source": "RSS", "type": "news"}}
            ]
        }
        
        _log_rag_retrieval_decision(
            mock_decision_logger,
            context,
            "test query",
            "Test reasoning",
            similarity_threshold=0.1,
            prioritize_foundational=True,
            exclude_types=["technical"]
        )
        
        mock_decision_logger.log_decision.assert_called_once()
        call_args = mock_decision_logger.log_decision.call_args
        assert call_args[1]["agent_type"] == AgentType.RAG_AGENT
        assert call_args[1]["decision_type"] == DecisionType.RETRIEVAL_DECISION

