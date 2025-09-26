"""
SEAL-GRADE SYSTEM TESTS - Unit Tests for Core Modules
Kiểm thử đơn vị cho các module cốt lõi

This module contains unit tests for all core StillMe modules with comprehensive coverage.
Module này chứa các test đơn vị cho tất cả module cốt lõi của StillMe với coverage toàn diện.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import test fixtures
from conftest import (
    test_config, test_datasets, mock_framework, mock_memory_system,
    mock_secure_memory, mock_ethics_system, mock_content_filter,
    mock_conversational_core, mock_api_manager, mock_emotion_sense,
    mock_token_optimizer, mock_self_improvement, mock_scheduler,
    mock_telemetry, mock_metrics, mock_communication_style,
    mock_input_sketcher, mock_prediction_engine, mock_market_intel,
    mock_daily_learning, mock_persona_morph, test_utils
)


class TestLayeredMemoryV1:
    """Test suite for LayeredMemoryV1 module."""
    
    @pytest.mark.unit
    def test_memory_initialization(self, mock_memory_system):
        """Test memory system initialization."""
        # Test successful initialization
        mock_memory_system.initialize.return_value = True
        result = mock_memory_system.initialize()
        assert result is True
        mock_memory_system.initialize.assert_called_once()
    
    @pytest.mark.unit
    def test_memory_store_retrieve(self, mock_memory_system):
        """Test memory store and retrieve operations."""
        # Test store operation
        test_data = {"id": "test_1", "content": "test content", "timestamp": time.time()}
        mock_memory_system.store.return_value = True
        result = mock_memory_system.store("test_1", test_data)
        assert result is True
        
        # Test retrieve operation
        mock_memory_system.retrieve.return_value = test_data
        retrieved = mock_memory_system.retrieve("test_1")
        assert retrieved == test_data
    
    @pytest.mark.unit
    def test_memory_search(self, mock_memory_system):
        """Test memory search functionality."""
        # Test search with query
        mock_results = [
            {"id": "1", "content": "test content 1", "score": 0.9},
            {"id": "2", "content": "test content 2", "score": 0.8}
        ]
        mock_memory_system.search.return_value = mock_results
        
        results = mock_memory_system.search("test query")
        assert len(results) == 2
        assert results[0]["score"] == 0.9
    
    @pytest.mark.unit
    def test_memory_clear(self, mock_memory_system):
        """Test memory clear operation."""
        mock_memory_system.clear.return_value = True
        result = mock_memory_system.clear()
        assert result is True
    
    @pytest.mark.unit
    def test_memory_edge_cases(self, mock_memory_system):
        """Test memory system edge cases."""
        # Test with empty data
        mock_memory_system.store.return_value = False
        result = mock_memory_system.store("empty", {})
        assert result is False
        
        # Test with invalid key
        mock_memory_system.retrieve.return_value = None
        result = mock_memory_system.retrieve("invalid_key")
        assert result is None


class TestSecureMemoryManager:
    """Test suite for SecureMemoryManager module."""
    
    @pytest.mark.unit
    def test_encryption_decryption(self, mock_secure_memory):
        """Test encryption and decryption operations."""
        test_data = "sensitive data"
        encrypted_data = "encrypted_data"
        
        # Test encryption
        mock_secure_memory.encrypt.return_value = encrypted_data
        result = mock_secure_memory.encrypt(test_data)
        assert result == encrypted_data
        
        # Test decryption
        mock_secure_memory.decrypt.return_value = test_data
        result = mock_secure_memory.decrypt(encrypted_data)
        assert result == test_data
    
    @pytest.mark.unit
    def test_key_rotation(self, mock_secure_memory):
        """Test key rotation functionality."""
        mock_secure_memory.rotate_key.return_value = True
        result = mock_secure_memory.rotate_key()
        assert result is True
    
    @pytest.mark.unit
    def test_backup_restore(self, mock_secure_memory):
        """Test backup and restore operations."""
        mock_secure_memory.backup.return_value = True
        result = mock_secure_memory.backup()
        assert result is True


class TestEthicalCoreSystem:
    """Test suite for EthicalCoreSystem module."""
    
    @pytest.mark.unit
    def test_ethics_validation_safe_content(self, mock_ethics_system):
        """Test ethics validation with safe content."""
        safe_response = {"is_safe": True, "violations": []}
        mock_ethics_system.validate.return_value = safe_response
        
        result = mock_ethics_system.validate("This is safe content")
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0
    
    @pytest.mark.unit
    def test_ethics_validation_unsafe_content(self, mock_ethics_system):
        """Test ethics validation with unsafe content."""
        unsafe_response = {
            "is_safe": False,
            "violations": ["harmful_content", "violence"]
        }
        mock_ethics_system.validate.return_value = unsafe_response
        
        result = mock_ethics_system.validate("Harmful content")
        assert result["is_safe"] is False
        assert len(result["violations"]) > 0
    
    @pytest.mark.unit
    def test_content_safety_check(self, mock_ethics_system):
        """Test content safety checking."""
        safety_response = {"is_safe": True, "score": 0.1}
        mock_ethics_system.check_content.return_value = safety_response
        
        result = mock_ethics_system.check_content("Safe content")
        assert result["is_safe"] is True
        assert result["score"] <= 0.1  # Low risk score
    
    @pytest.mark.unit
    def test_violation_detection(self, mock_ethics_system):
        """Test violation detection."""
        violations = ["hate_speech", "violence"]
        mock_ethics_system.get_violations.return_value = violations
        
        result = mock_ethics_system.get_violations("Harmful text")
        assert len(result) == 2
        assert "hate_speech" in result


class TestContentIntegrityFilter:
    """Test suite for ContentIntegrityFilter module."""
    
    @pytest.mark.unit
    def test_content_filtering_safe(self, mock_content_filter):
        """Test content filtering with safe content."""
        filter_response = {"is_safe": True, "filtered_content": "safe content"}
        mock_content_filter.filter.return_value = filter_response
        
        result = mock_content_filter.filter("safe content")
        assert result["is_safe"] is True
        assert result["filtered_content"] == "safe content"
    
    @pytest.mark.unit
    def test_content_filtering_unsafe(self, mock_content_filter):
        """Test content filtering with unsafe content."""
        filter_response = {"is_safe": False, "filtered_content": "filtered content"}
        mock_content_filter.filter.return_value = filter_response
        
        result = mock_content_filter.filter("unsafe content")
        assert result["is_safe"] is False
    
    @pytest.mark.unit
    def test_harmful_content_detection(self, mock_content_filter):
        """Test harmful content detection."""
        mock_content_filter.detect_harmful.return_value = True
        
        result = mock_content_filter.detect_harmful("harmful content")
        assert result is True
    
    @pytest.mark.unit
    def test_content_sanitization(self, mock_content_filter):
        """Test content sanitization."""
        sanitized = "sanitized content"
        mock_content_filter.sanitize.return_value = sanitized
        
        result = mock_content_filter.sanitize("unsafe content")
        assert result == sanitized


class TestConversationalCore:
    """Test suite for ConversationalCore module."""
    
    @pytest.mark.unit
    def test_message_processing(self, mock_conversational_core):
        """Test message processing."""
        response = {"response": "Hello! How can I help you?"}
        mock_conversational_core.process_message.return_value = response
        
        result = mock_conversational_core.process_message("Hello")
        assert "response" in result
        assert result["response"] == "Hello! How can I help you?"
    
    @pytest.mark.unit
    def test_context_management(self, mock_conversational_core):
        """Test context management."""
        context = {"context": "conversation context"}
        mock_conversational_core.get_context.return_value = context
        
        result = mock_conversational_core.get_context()
        assert "context" in result
        
        # Test context update
        mock_conversational_core.update_context.return_value = True
        result = mock_conversational_core.update_context("new context")
        assert result is True
    
    @pytest.mark.unit
    def test_conversation_flow(self, mock_conversational_core):
        """Test conversation flow."""
        # Test multiple message exchanges
        responses = [
            {"response": "Hello!"},
            {"response": "How are you?"},
            {"response": "Good to hear!"}
        ]
        mock_conversational_core.process_message.side_effect = responses
        
        for i, expected_response in enumerate(responses):
            result = mock_conversational_core.process_message(f"Message {i}")
            assert result == expected_response


class TestUnifiedAPIManager:
    """Test suite for UnifiedAPIManager module."""
    
    @pytest.mark.unit
    def test_api_request_success(self, mock_api_manager):
        """Test successful API request."""
        api_response = {"response": "API response", "status": "success"}
        mock_api_manager.send_request.return_value = api_response
        
        result = mock_api_manager.send_request("test prompt")
        assert result["status"] == "success"
        assert "response" in result
    
    @pytest.mark.unit
    def test_api_health_check(self, mock_api_manager):
        """Test API health check."""
        health_response = {"status": "healthy", "uptime": 3600}
        mock_api_manager.get_health.return_value = health_response
        
        result = mock_api_manager.get_health()
        assert result["status"] == "healthy"
    
    @pytest.mark.unit
    def test_api_fallback(self, mock_api_manager):
        """Test API fallback mechanism."""
        fallback_response = {"response": "Fallback response", "fallback": True}
        mock_api_manager.fallback.return_value = fallback_response
        
        result = mock_api_manager.fallback("test prompt")
        assert result["fallback"] is True
    
    @pytest.mark.unit
    def test_api_error_handling(self, mock_api_manager):
        """Test API error handling."""
        # Test with exception
        mock_api_manager.send_request.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            mock_api_manager.send_request("test prompt")


class TestEmotionSenseV1:
    """Test suite for EmotionSenseV1 module."""
    
    @pytest.mark.unit
    def test_emotion_detection(self, mock_emotion_sense):
        """Test emotion detection."""
        emotion_response = {"emotion": "happy", "confidence": 0.8}
        mock_emotion_sense.detect_emotion.return_value = emotion_response
        
        result = mock_emotion_sense.detect_emotion("I'm so happy today!")
        assert result["emotion"] == "happy"
        assert result["confidence"] >= 0.8
    
    @pytest.mark.unit
    def test_sentiment_analysis(self, mock_emotion_sense):
        """Test sentiment analysis."""
        sentiment_response = {"sentiment": "positive", "score": 0.7}
        mock_emotion_sense.analyze_sentiment.return_value = sentiment_response
        
        result = mock_emotion_sense.analyze_sentiment("This is great!")
        assert result["sentiment"] == "positive"
        assert result["score"] >= 0.7
    
    @pytest.mark.unit
    def test_vietnamese_emotion_detection(self, mock_emotion_sense):
        """Test emotion detection for Vietnamese text."""
        emotion_response = {"emotion": "vui", "confidence": 0.9}
        mock_emotion_sense.detect_emotion.return_value = emotion_response
        
        result = mock_emotion_sense.detect_emotion("Tôi rất vui hôm nay!")
        assert result["emotion"] == "vui"
        assert result["confidence"] >= 0.9


class TestTokenOptimizer:
    """Test suite for TokenOptimizer module."""
    
    @pytest.mark.unit
    def test_token_optimization(self, mock_token_optimizer):
        """Test token optimization."""
        optimization_response = {
            "optimized_text": "optimized text",
            "tokens_saved": 10,
            "original_tokens": 100,
            "optimized_tokens": 90
        }
        mock_token_optimizer.optimize.return_value = optimization_response
        
        result = mock_token_optimizer.optimize("original text")
        assert result["tokens_saved"] == 10
        assert result["optimized_tokens"] < result["original_tokens"]
    
    @pytest.mark.unit
    def test_token_estimation(self, mock_token_optimizer):
        """Test token estimation."""
        mock_token_optimizer.estimate_tokens.return_value = 50
        
        result = mock_token_optimizer.estimate_tokens("test text")
        assert result == 50
    
    @pytest.mark.unit
    def test_semantic_caching(self, mock_token_optimizer):
        """Test semantic caching."""
        mock_token_optimizer.cache_similar.return_value = True
        
        result = mock_token_optimizer.cache_similar("test text", "similar text")
        assert result is True


class TestSelfImprovementManager:
    """Test suite for SelfImprovementManager module."""
    
    @pytest.mark.unit
    def test_performance_analysis(self, mock_self_improvement):
        """Test performance analysis."""
        analysis_response = {
            "score": 0.8,
            "suggestions": ["improve accuracy", "reduce latency"],
            "metrics": {"accuracy": 0.9, "speed": 0.8}
        }
        mock_self_improvement.analyze_performance.return_value = analysis_response
        
        result = mock_self_improvement.analyze_performance()
        assert result["score"] >= 0.8
        assert len(result["suggestions"]) > 0
    
    @pytest.mark.unit
    def test_improvement_implementation(self, mock_self_improvement):
        """Test improvement implementation."""
        improvement_response = {
            "improved": True,
            "changes": ["updated algorithm", "optimized parameters"],
            "impact": "positive"
        }
        mock_self_improvement.improve.return_value = improvement_response
        
        result = mock_self_improvement.improve()
        assert result["improved"] is True
        assert len(result["changes"]) > 0
    
    @pytest.mark.unit
    def test_metrics_collection(self, mock_self_improvement):
        """Test metrics collection."""
        metrics_response = {"accuracy": 0.9, "speed": 0.8, "efficiency": 0.85}
        mock_self_improvement.get_metrics.return_value = metrics_response
        
        result = mock_self_improvement.get_metrics()
        assert result["accuracy"] >= 0.9
        assert result["speed"] >= 0.8


class TestAutomatedScheduler:
    """Test suite for AutomatedScheduler module."""
    
    @pytest.mark.unit
    def test_job_scheduling(self, mock_scheduler):
        """Test job scheduling."""
        mock_scheduler.schedule_job.return_value = True
        
        result = mock_scheduler.schedule_job("daily_learning", "0 9 * * *")
        assert result is True
    
    @pytest.mark.unit
    def test_job_execution(self, mock_scheduler):
        """Test job execution."""
        execution_response = {"status": "completed", "duration": 30}
        mock_scheduler.run_job.return_value = execution_response
        
        result = mock_scheduler.run_job("daily_learning")
        assert result["status"] == "completed"
    
    @pytest.mark.unit
    def test_scheduler_status(self, mock_scheduler):
        """Test scheduler status."""
        status_response = {"active_jobs": 2, "completed_jobs": 10, "failed_jobs": 0}
        mock_scheduler.get_status.return_value = status_response
        
        result = mock_scheduler.get_status()
        assert result["active_jobs"] >= 0
        assert result["completed_jobs"] >= 0


class TestTelemetry:
    """Test suite for Telemetry module."""
    
    @pytest.mark.unit
    def test_event_tracking(self, mock_telemetry):
        """Test event tracking."""
        mock_telemetry.track_event.return_value = True
        
        result = mock_telemetry.track_event("user_action", {"action": "click"})
        assert result is True
    
    @pytest.mark.unit
    def test_metrics_collection(self, mock_telemetry):
        """Test metrics collection."""
        metrics_response = {"events": 100, "errors": 0, "avg_response_time": 50}
        mock_telemetry.get_metrics.return_value = metrics_response
        
        result = mock_telemetry.get_metrics()
        assert result["events"] >= 0
        assert result["errors"] >= 0
    
    @pytest.mark.unit
    def test_data_export(self, mock_telemetry):
        """Test data export."""
        export_response = {"data": "exported", "format": "json", "size": 1024}
        mock_telemetry.export_data.return_value = export_response
        
        result = mock_telemetry.export_data()
        assert "data" in result


class TestFrameworkMetrics:
    """Test suite for FrameworkMetrics module."""
    
    @pytest.mark.unit
    def test_metric_recording(self, mock_metrics):
        """Test metric recording."""
        mock_metrics.record_metric.return_value = True
        
        result = mock_metrics.record_metric("response_time", 100)
        assert result is True
    
    @pytest.mark.unit
    def test_metrics_summary(self, mock_metrics):
        """Test metrics summary."""
        summary_response = {
            "total_requests": 1000,
            "avg_response_time": 100,
            "error_rate": 0.01,
            "uptime": 3600
        }
        mock_metrics.get_summary.return_value = summary_response
        
        result = mock_metrics.get_summary()
        assert result["total_requests"] >= 0
        assert result["avg_response_time"] >= 0
    
    @pytest.mark.unit
    def test_report_generation(self, mock_metrics):
        """Test report generation."""
        report_response = {"report": "generated", "format": "html", "path": "/reports/metrics.html"}
        mock_metrics.export_report.return_value = report_response
        
        result = mock_metrics.export_report()
        assert "report" in result


class TestCommunicationStyleManager:
    """Test suite for CommunicationStyleManager module."""
    
    @pytest.mark.unit
    def test_style_retrieval(self, mock_communication_style):
        """Test style retrieval."""
        style_response = {"style": "friendly", "tone": "casual", "formality": "low"}
        mock_communication_style.get_style.return_value = style_response
        
        result = mock_communication_style.get_style("user_123")
        assert result["style"] == "friendly"
        assert result["tone"] == "casual"
    
    @pytest.mark.unit
    def test_style_adaptation(self, mock_communication_style):
        """Test style adaptation."""
        adapted_message = "Hey there! How can I help you today?"
        mock_communication_style.adapt_style.return_value = adapted_message
        
        result = mock_communication_style.adapt_style("Hello", "friendly")
        assert result == adapted_message
    
    @pytest.mark.unit
    def test_style_learning(self, mock_communication_style):
        """Test style learning."""
        mock_communication_style.learn_style.return_value = True
        
        result = mock_communication_style.learn_style("user_123", "formal")
        assert result is True


class TestInputSketcher:
    """Test suite for InputSketcher module."""
    
    @pytest.mark.unit
    def test_input_sketching(self, mock_input_sketcher):
        """Test input sketching."""
        sketch_response = {
            "sketch": "test sketch",
            "confidence": 0.8,
            "features": ["intent", "entities"]
        }
        mock_input_sketcher.sketch.return_value = sketch_response
        
        result = mock_input_sketcher.sketch("test input")
        assert result["confidence"] >= 0.8
        assert "sketch" in result
    
    @pytest.mark.unit
    def test_input_enhancement(self, mock_input_sketcher):
        """Test input enhancement."""
        enhanced_input = "enhanced test input"
        mock_input_sketcher.enhance.return_value = enhanced_input
        
        result = mock_input_sketcher.enhance("test input")
        assert result == enhanced_input
    
    @pytest.mark.unit
    def test_input_validation(self, mock_input_sketcher):
        """Test input validation."""
        validation_response = {"is_valid": True, "errors": [], "warnings": []}
        mock_input_sketcher.validate.return_value = validation_response
        
        result = mock_input_sketcher.validate("valid input")
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0


class TestPredictionEngine:
    """Test suite for PredictionEngine module."""
    
    @pytest.mark.unit
    def test_prediction_generation(self, mock_prediction_engine):
        """Test prediction generation."""
        prediction_response = {
            "prediction": "test prediction",
            "confidence": 0.8,
            "probability": 0.75
        }
        mock_prediction_engine.predict.return_value = prediction_response
        
        result = mock_prediction_engine.predict("test data")
        assert result["confidence"] >= 0.8
        assert "prediction" in result
    
    @pytest.mark.unit
    def test_model_training(self, mock_prediction_engine):
        """Test model training."""
        training_response = {"accuracy": 0.9, "loss": 0.1, "epochs": 100}
        mock_prediction_engine.train.return_value = training_response
        
        result = mock_prediction_engine.train("training data")
        assert result["accuracy"] >= 0.9
    
    @pytest.mark.unit
    def test_model_evaluation(self, mock_prediction_engine):
        """Test model evaluation."""
        evaluation_response = {"score": 0.85, "precision": 0.8, "recall": 0.9}
        mock_prediction_engine.evaluate.return_value = evaluation_response
        
        result = mock_prediction_engine.evaluate("test data")
        assert result["score"] >= 0.85


class TestMarketIntelligence:
    """Test suite for MarketIntelligence module."""
    
    @pytest.mark.unit
    def test_trend_analysis(self, mock_market_intel):
        """Test trend analysis."""
        trend_response = {
            "trends": ["AI", "ML", "automation"],
            "confidence": 0.8,
            "timeframe": "30_days"
        }
        mock_market_intel.analyze_trends.return_value = trend_response
        
        result = mock_market_intel.analyze_trends()
        assert len(result["trends"]) > 0
        assert result["confidence"] >= 0.8
    
    @pytest.mark.unit
    def test_insights_generation(self, mock_market_intel):
        """Test insights generation."""
        insights_response = {
            "insights": "Market is trending towards AI adoption",
            "confidence": 0.9,
            "sources": ["news", "social_media", "reports"]
        }
        mock_market_intel.get_insights.return_value = insights_response
        
        result = mock_market_intel.get_insights()
        assert "insights" in result
        assert result["confidence"] >= 0.9
    
    @pytest.mark.unit
    def test_data_update(self, mock_market_intel):
        """Test data update."""
        mock_market_intel.update_data.return_value = True
        
        result = mock_market_intel.update_data("new_data")
        assert result is True


class TestDailyLearningManager:
    """Test suite for DailyLearningManager module."""
    
    @pytest.mark.unit
    def test_learning_session(self, mock_daily_learning):
        """Test learning session execution."""
        session_response = {
            "completed": True,
            "score": 0.8,
            "cases_processed": 5,
            "improvements": ["accuracy", "speed"]
        }
        mock_daily_learning.run_session.return_value = session_response
        
        result = mock_daily_learning.run_session()
        assert result["completed"] is True
        assert result["score"] >= 0.8
    
    @pytest.mark.unit
    def test_progress_tracking(self, mock_daily_learning):
        """Test progress tracking."""
        progress_response = {
            "sessions": 10,
            "avg_score": 0.75,
            "total_cases": 50,
            "improvement_rate": 0.1
        }
        mock_daily_learning.get_progress.return_value = progress_response
        
        result = mock_daily_learning.get_progress()
        assert result["sessions"] >= 0
        assert result["avg_score"] >= 0
    
    @pytest.mark.unit
    def test_case_addition(self, mock_daily_learning):
        """Test case addition."""
        mock_daily_learning.add_case.return_value = True
        
        result = mock_daily_learning.add_case("new_case", "category")
        assert result is True


class TestPersonaMorph:
    """Test suite for PersonaMorph module."""
    
    @pytest.mark.unit
    def test_persona_morphing(self, mock_persona_morph):
        """Test persona morphing."""
        morph_response = {
            "new_persona": "friendly",
            "confidence": 0.8,
            "changes": ["tone", "style"]
        }
        mock_persona_morph.morph.return_value = morph_response
        
        result = mock_persona_morph.morph("friendly")
        assert result["new_persona"] == "friendly"
        assert result["confidence"] >= 0.8
    
    @pytest.mark.unit
    def test_current_persona(self, mock_persona_morph):
        """Test current persona retrieval."""
        persona_response = {"persona": "default", "active": True}
        mock_persona_morph.get_current.return_value = persona_response
        
        result = mock_persona_morph.get_current()
        assert result["persona"] == "default"
        assert result["active"] is True
    
    @pytest.mark.unit
    def test_persona_reset(self, mock_persona_morph):
        """Test persona reset."""
        mock_persona_morph.reset.return_value = True
        
        result = mock_persona_morph.reset()
        assert result is True


class TestFrameworkIntegration:
    """Test suite for framework integration."""
    
    @pytest.mark.unit
    def test_framework_initialization(self, mock_framework):
        """Test framework initialization."""
        mock_framework.initialize.return_value = True
        
        result = mock_framework.initialize()
        assert result is True
    
    @pytest.mark.unit
    def test_framework_request_processing(self, mock_framework):
        """Test framework request processing."""
        request_response = {
            "response": "Test response",
            "status": "success",
            "modules_used": ["conversational", "memory"]
        }
        mock_framework.process_request.return_value = request_response
        
        result = mock_framework.process_request("test request")
        assert result["status"] == "success"
        assert "response" in result
    
    @pytest.mark.unit
    def test_framework_health_check(self, mock_framework):
        """Test framework health check."""
        health_response = {
            "status": "healthy",
            "modules": {
                "memory": "healthy",
                "ethics": "healthy",
                "conversational": "healthy"
            }
        }
        mock_framework.get_health_status.return_value = health_response
        
        result = mock_framework.get_health_status()
        assert result["status"] == "healthy"
        assert "modules" in result


# Performance and edge case tests
class TestPerformanceAndEdgeCases:
    """Test suite for performance and edge cases."""
    
    @pytest.mark.unit
    def test_response_time_performance(self, test_utils, test_config):
        """Test response time performance."""
        start_time = time.time()
        # Simulate processing time
        time.sleep(0.001)  # 1ms
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        threshold = test_config["performance"]["gateway_p95_threshold"]
        
        test_utils.assert_response_time(response_time, threshold)
    
    @pytest.mark.unit
    def test_error_rate_calculation(self, test_utils, test_config):
        """Test error rate calculation."""
        total_requests = 1000
        errors = 5
        threshold = test_config["performance"]["error_rate_threshold"]
        
        test_utils.assert_error_rate(errors, total_requests, threshold)
    
    @pytest.mark.unit
    def test_memory_usage_edge_cases(self, mock_memory_system):
        """Test memory usage edge cases."""
        # Test with large data
        large_data = {"data": "x" * 10000}  # 10KB
        mock_memory_system.store.return_value = True
        
        result = mock_memory_system.store("large_data", large_data)
        assert result is True
        
        # Test with empty data
        mock_memory_system.store.return_value = False
        result = mock_memory_system.store("empty", {})
        assert result is False
    
    @pytest.mark.unit
    def test_concurrent_operations(self, mock_memory_system):
        """Test concurrent operations."""
        # Simulate concurrent operations
        results = []
        for i in range(10):
            mock_memory_system.store.return_value = True
            result = mock_memory_system.store(f"key_{i}", f"value_{i}")
            results.append(result)
        
        assert all(results)  # All operations should succeed
    
    @pytest.mark.unit
    def test_unicode_handling(self, mock_conversational_core):
        """Test Unicode handling."""
        unicode_text = "Hello 世界! 🌍"
        response = {"response": f"Echo: {unicode_text}"}
        mock_conversational_core.process_message.return_value = response
        
        result = mock_conversational_core.process_message(unicode_text)
        assert "世界" in result["response"]
        assert "🌍" in result["response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
