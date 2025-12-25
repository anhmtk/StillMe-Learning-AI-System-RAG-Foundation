"""Unit tests for validation_handler.py module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from backend.api.handlers.validation_handler import (
    handle_validation_with_fallback,
    _add_transparency_disclaimer_before_validation,
    _get_adaptive_thresholds,
    _build_validation_chain,
    _run_step_validation,
    _run_consistency_check
)
from backend.api.models import ChatRequest


class TestAddTransparencyDisclaimerBeforeValidation:
    """Tests for _add_transparency_disclaimer_before_validation function."""
    
    def test_adds_disclaimer_when_no_context_and_not_philosophical(self):
        """Test that disclaimer is added when no context and not philosophical."""
        raw_response = "This is a test response."
        ctx_docs = []
        is_philosophical = False
        detected_lang = "en"
        
        result = _add_transparency_disclaimer_before_validation(
            raw_response, ctx_docs, is_philosophical, detected_lang
        )
        
        assert "Note: This answer is based on general knowledge" in result
        assert raw_response in result
    
    def test_adds_vietnamese_disclaimer(self):
        """Test that Vietnamese disclaimer is added for Vietnamese language."""
        raw_response = "Đây là câu trả lời."
        ctx_docs = []
        is_philosophical = False
        detected_lang = "vi"
        
        result = _add_transparency_disclaimer_before_validation(
            raw_response, ctx_docs, is_philosophical, detected_lang
        )
        
        assert "Lưu ý: Câu trả lời này dựa trên kiến thức chung" in result
    
    def test_does_not_add_disclaimer_when_has_context(self):
        """Test that disclaimer is not added when context exists."""
        raw_response = "This is a test response."
        ctx_docs = ["Some context document"]
        is_philosophical = False
        detected_lang = "en"
        
        result = _add_transparency_disclaimer_before_validation(
            raw_response, ctx_docs, is_philosophical, detected_lang
        )
        
        assert result == raw_response
        assert "Note:" not in result
    
    def test_does_not_add_disclaimer_for_philosophical(self):
        """Test that disclaimer is not added for philosophical questions."""
        raw_response = "This is a philosophical response."
        ctx_docs = []
        is_philosophical = True
        detected_lang = "en"
        
        result = _add_transparency_disclaimer_before_validation(
            raw_response, ctx_docs, is_philosophical, detected_lang
        )
        
        assert result == raw_response
        assert "Note:" not in result
    
    def test_does_not_add_disclaimer_when_already_has_transparency(self):
        """Test that disclaimer is not added when response already has transparency indicators."""
        raw_response = "This is based on general knowledge from training data."
        ctx_docs = []
        is_philosophical = False
        detected_lang = "en"
        
        result = _add_transparency_disclaimer_before_validation(
            raw_response, ctx_docs, is_philosophical, detected_lang
        )
        
        assert result == raw_response
        # Should not duplicate disclaimer
        assert result.count("Note:") == 0


class TestGetAdaptiveThresholds:
    """Tests for _get_adaptive_thresholds function."""
    
    @patch('backend.services.self_distilled_learning.get_self_distilled_learning')
    @patch('backend.api.handlers.validation_handler.get_chat_config')
    def test_returns_adaptive_thresholds(self, mock_config, mock_sdl):
        """Test that function returns adaptive thresholds from SDL."""
        mock_sdl_instance = MagicMock()
        mock_sdl.return_value = mock_sdl_instance
        mock_sdl_instance.get_adaptive_threshold.side_effect = [0.3, 0.4]
        
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT = 0.25
        mock_config_instance.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT = 0.35
        
        chat_request = Mock()
        chat_request.message = "What is the answer?"
        
        citation_overlap, evidence_threshold = _get_adaptive_thresholds(
            is_philosophical=False,
            ctx_docs=["doc1"],
            context={"context_quality": "high", "avg_similarity_score": 0.8},
            chat_request=chat_request
        )
        
        assert citation_overlap == 0.3
        assert evidence_threshold == 0.4
        assert mock_sdl_instance.get_adaptive_threshold.call_count == 2
    
    @patch('backend.services.self_distilled_learning.get_self_distilled_learning')
    @patch('backend.api.handlers.validation_handler.get_chat_config')
    def test_falls_back_to_defaults_on_error(self, mock_config, mock_sdl):
        """Test that function falls back to defaults when SDL fails."""
        mock_sdl.side_effect = Exception("SDL not available")
        
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT = 0.25
        mock_config_instance.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT = 0.35
        
        chat_request = Mock()
        chat_request.message = "What is the answer?"
        
        citation_overlap, evidence_threshold = _get_adaptive_thresholds(
            is_philosophical=False,
            ctx_docs=[],
            context={},
            chat_request=chat_request
        )
        
        assert citation_overlap == 0.25
        assert evidence_threshold == 0.35
    
    @patch('backend.services.self_distilled_learning.get_self_distilled_learning')
    @patch('backend.api.handlers.validation_handler.get_chat_config')
    def test_detects_technical_questions(self, mock_config, mock_sdl):
        """Test that function detects technical questions."""
        mock_sdl_instance = MagicMock()
        mock_sdl.return_value = mock_sdl_instance
        mock_sdl_instance.get_adaptive_threshold.return_value = 0.3
        
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT = 0.25
        mock_config_instance.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT = 0.35
        
        chat_request = Mock()
        chat_request.message = "How does this code function work?"
        
        _get_adaptive_thresholds(
            is_philosophical=False,
            ctx_docs=[],
            context={},
            chat_request=chat_request
        )
        
        # Check that threshold_context includes is_technical=True
        call_args = mock_sdl_instance.get_adaptive_threshold.call_args_list[0]
        threshold_context = call_args[1]['context']
        assert threshold_context['is_technical'] is True


class TestBuildValidationChain:
    """Tests for _build_validation_chain function."""
    
    @patch('backend.api.handlers.validation_handler.get_chat_config')
    def test_builds_chain_with_critical_validators(self, mock_config):
        """Test that function builds chain with critical validators."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.validation.MIN_SOURCES_FOR_CONSENSUS = 2
        mock_config_instance.timeouts.SOURCE_CONSENSUS = 5.0
        
        chain, validators = _build_validation_chain(
            detected_lang="en",
            is_philosophical=False,
            ctx_docs=["doc1", "doc2"],
            adaptive_citation_overlap=0.3,
            adaptive_evidence_threshold=0.4,
            context={"context_quality": "high"}
        )
        
        assert chain is not None
        assert len(validators) > 0
    
    @patch('backend.api.handlers.validation_handler.get_chat_config')
    def test_adds_philosophical_validator_for_philosophical_questions(self, mock_config):
        """Test that function adds PhilosophicalDepthValidator for philosophical questions."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.validation.MIN_SOURCES_FOR_CONSENSUS = 2
        mock_config_instance.timeouts.SOURCE_CONSENSUS = 5.0
        
        chain, validators = _build_validation_chain(
            detected_lang="en",
            is_philosophical=True,
            ctx_docs=[],
            adaptive_citation_overlap=0.3,
            adaptive_evidence_threshold=0.4,
            context={}
        )
        
        validator_names = [type(v).__name__ for v in validators]
        assert "PhilosophicalDepthValidator" in validator_names


class TestRunStepValidation:
    """Tests for _run_step_validation function."""
    
    @patch.dict('os.environ', {'ENABLE_STEP_LEVEL_VALIDATION': 'true', 'STEP_VALIDATION_MIN_STEPS': '2', 'STEP_CONFIDENCE_THRESHOLD': '0.5'})
    @patch('backend.validators.step_detector.StepDetector')
    @patch('backend.validators.step_validator.StepValidator')
    def test_runs_step_validation_when_enabled(self, mock_step_validator, mock_step_detector):
        """Test that step validation runs when enabled."""
        mock_detector_instance = MagicMock()
        mock_step_detector.return_value = mock_detector_instance
        mock_detector_instance.is_multi_step.return_value = True
        
        mock_step = MagicMock()
        mock_step.step_number = 1
        mock_detector_instance.detect_steps.return_value = [mock_step, MagicMock()]
        
        mock_validator_instance = MagicMock()
        mock_step_validator.return_value = mock_validator_instance
        
        mock_result = MagicMock()
        mock_result.confidence = 0.8
        mock_result.passed = True
        mock_result.issues = []
        mock_result.step = mock_step
        mock_validator_instance.validate_all_steps.return_value = [mock_result, mock_result]
        
        result = _run_step_validation(
            raw_response="Step 1: Do this. Step 2: Do that.",
            ctx_docs=["doc1"],
            context={},
            adaptive_citation_overlap=0.3,
            adaptive_evidence_threshold=0.4,
            processing_steps=[]
        )
        
        assert result is not None
        assert result["is_multi_step"] is True
        assert result["total_steps"] == 2
    
    @patch.dict('os.environ', {'ENABLE_STEP_LEVEL_VALIDATION': 'false'})
    def test_skips_step_validation_when_disabled(self):
        """Test that step validation is skipped when disabled."""
        result = _run_step_validation(
            raw_response="Step 1: Do this.",
            ctx_docs=[],
            context={},
            adaptive_citation_overlap=0.3,
            adaptive_evidence_threshold=0.4,
            processing_steps=[]
        )
        
        assert result is None
    
    @patch.dict('os.environ', {'ENABLE_STEP_LEVEL_VALIDATION': 'true', 'STEP_VALIDATION_MIN_STEPS': '2'})
    @patch('backend.validators.step_detector.StepDetector')
    def test_skips_when_not_multi_step(self, mock_step_detector):
        """Test that step validation is skipped when response is not multi-step."""
        mock_detector_instance = MagicMock()
        mock_step_detector.return_value = mock_detector_instance
        mock_detector_instance.is_multi_step.return_value = False
        
        result = _run_step_validation(
            raw_response="This is a single step response.",
            ctx_docs=[],
            context={},
            adaptive_citation_overlap=0.3,
            adaptive_evidence_threshold=0.4,
            processing_steps=[]
        )
        
        assert result is None


class TestRunConsistencyCheck:
    """Tests for _run_consistency_check function."""
    
    @patch.dict('os.environ', {'ENABLE_CONSISTENCY_CHECKS': 'true'})
    @patch('backend.validators.consistency_checker.ConsistencyChecker')
    def test_runs_consistency_check_when_enabled(self, mock_checker_class):
        """Test that consistency check runs when enabled."""
        mock_checker_instance = MagicMock()
        mock_checker_class.return_value = mock_checker_instance
        
        mock_claim1 = MagicMock()
        mock_claim2 = MagicMock()
        mock_checker_instance.extract_claims.return_value = [mock_claim1, mock_claim2]
        mock_checker_instance.check_pairwise_consistency.return_value = {
            "claim_0_vs_claim_1": "CONSISTENT"
        }
        mock_checker_instance.check_kb_consistency.return_value = "CONSISTENT"
        
        result = _run_consistency_check(
            raw_response="Claim 1. Claim 2.",
            ctx_docs=["doc1"],
            processing_steps=[]
        )
        
        assert result is not None
        assert result["total_claims"] == 2
        assert result["has_issues"] is False
    
    @patch.dict('os.environ', {'ENABLE_CONSISTENCY_CHECKS': 'false'})
    def test_skips_consistency_check_when_disabled(self):
        """Test that consistency check is skipped when disabled."""
        result = _run_consistency_check(
            raw_response="Some response.",
            ctx_docs=[],
            processing_steps=[]
        )
        
        assert result is None
    
    @patch.dict('os.environ', {'ENABLE_CONSISTENCY_CHECKS': 'true'})
    @patch('backend.validators.consistency_checker.ConsistencyChecker')
    def test_detects_contradictions(self, mock_checker_class):
        """Test that function detects contradictions."""
        mock_checker_instance = MagicMock()
        mock_checker_class.return_value = mock_checker_instance
        
        mock_claim1 = MagicMock()
        mock_claim2 = MagicMock()
        mock_checker_instance.extract_claims.return_value = [mock_claim1, mock_claim2]
        mock_checker_instance.check_pairwise_consistency.return_value = {
            "claim_0_vs_claim_1": "CONTRADICTION"
        }
        mock_checker_instance.check_kb_consistency.return_value = "CONSISTENT"
        
        result = _run_consistency_check(
            raw_response="Claim 1 contradicts claim 2.",
            ctx_docs=["doc1"],
            processing_steps=[]
        )
        
        assert result is not None
        assert result["has_issues"] is True
        assert len(result["contradictions"]) > 0


class TestHandleValidationWithFallback:
    """Tests for handle_validation_with_fallback function."""
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.validation_handler._build_validation_chain')
    @patch('backend.api.handlers.validation_handler._run_step_validation')
    @patch('backend.api.handlers.validation_handler._run_consistency_check')
    @patch('backend.api.handlers.validation_handler._get_adaptive_thresholds')
    @patch('backend.api.handlers.validation_handler._add_transparency_disclaimer_before_validation')
    async def test_handles_validation_successfully(
        self,
        mock_add_disclaimer,
        mock_get_thresholds,
        mock_consistency,
        mock_step_validation,
        mock_build_chain
    ):
        """Test that function handles validation successfully."""
        # Setup mocks
        mock_add_disclaimer.return_value = "Test response"
        mock_get_thresholds.return_value = (0.3, 0.4)
        
        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.reasons = []
        mock_validation_result.patched_answer = None
        
        mock_chain = MagicMock()
        mock_validators = []
        mock_chain.run.return_value = mock_validation_result
        mock_build_chain.return_value = (mock_chain, mock_validators)
        
        mock_step_validation.return_value = None
        mock_consistency.return_value = None
        
        # Setup context
        context = {
            "knowledge_docs": [{"content": "doc1"}],
            "conversation_docs": [],
            "context_quality": "high",
            "avg_similarity_score": 0.8
        }
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.llm_provider = None
        
        processing_steps = []
        timing_logs = {}
        
        response, validation_info, confidence_score, used_fallback, step_info, consistency_info, ctx_docs = await handle_validation_with_fallback(
            raw_response="Test response",
            context=context,
            detected_lang="en",
            is_philosophical=False,
            is_religion_roleplay=False,
            chat_request=chat_request,
            enhanced_prompt="Test prompt",
            context_text="Test context",
            citation_instruction="Cite sources",
            num_knowledge=1,
            processing_steps=processing_steps,
            timing_logs=timing_logs,
            is_origin_query=False,
            is_stillme_query=False
        )
        
        assert response is not None
        assert validation_info is not None
        assert validation_info["passed"] is True
        assert used_fallback is False
        assert step_info is None
        assert consistency_info is None
        assert len(ctx_docs) == 1
    
    @pytest.mark.asyncio
    @patch('backend.api.handlers.validation_handler._build_validation_chain')
    @patch('backend.api.handlers.validation_handler._get_adaptive_thresholds')
    @patch('backend.api.handlers.validation_handler._add_transparency_disclaimer_before_validation')
    @patch('backend.api.handlers.validation_handler.FallbackHandler')
    async def test_handles_validation_failure_with_fallback(
        self,
        mock_fallback_handler,
        mock_add_disclaimer,
        mock_get_thresholds,
        mock_build_chain
    ):
        """Test that function handles validation failure with fallback."""
        # Setup mocks
        mock_add_disclaimer.return_value = "Test response"
        mock_get_thresholds.return_value = (0.3, 0.4)
        
        mock_validation_result = MagicMock()
        mock_validation_result.passed = False
        mock_validation_result.reasons = ["missing_citation"]
        mock_validation_result.patched_answer = None
        
        mock_chain = MagicMock()
        mock_chain.run.return_value = mock_validation_result
        mock_build_chain.return_value = mock_chain
        
        mock_fallback_instance = MagicMock()
        mock_fallback_handler.return_value = mock_fallback_instance
        mock_fallback_instance.get_fallback_answer.return_value = "Fallback response"
        
        context = {
            "knowledge_docs": [{"content": "doc1"}],
            "conversation_docs": [],
            "context_quality": "high"
        }
        
        chat_request = Mock()
        chat_request.message = "Test question"
        chat_request.llm_provider = None
        
        processing_steps = []
        timing_logs = {}
        
        response, validation_info, confidence_score, used_fallback, step_info, consistency_info, ctx_docs = await handle_validation_with_fallback(
            raw_response="Test response",
            context=context,
            detected_lang="en",
            is_philosophical=False,
            is_religion_roleplay=False,
            chat_request=chat_request,
            enhanced_prompt="Test prompt",
            context_text="Test context",
            citation_instruction="Cite sources",
            num_knowledge=1,
            processing_steps=processing_steps,
            timing_logs=timing_logs
        )
        
        assert response is not None
        assert validation_info is not None
        assert validation_info["passed"] is False

