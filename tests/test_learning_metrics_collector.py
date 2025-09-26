#!/usr/bin/env python3
"""
Test suite for Learning Metrics Collector
=========================================

Tests for objective validation of learning effectiveness.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from stillme_core.learning.learning_metrics_collector import (
    LearningMetricsCollector,
    ErrorType,
    SafetyViolationType
)

class TestLearningMetricsCollector:
    """Test suite for LearningMetricsCollector"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def metrics_collector(self, temp_dir):
        """Create metrics collector with temporary directory"""
        with patch('stillme_core.learning.learning_metrics_collector.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            collector = LearningMetricsCollector()
            return collector
    
    @pytest.fixture
    def mock_benchmark_data(self):
        """Create mock benchmark data"""
        return [
            {
                "test_id": "test_1",
                "input": "def broken_function(\n    return 'hello'",
                "expected_output": "def broken_function():\n    return 'hello'",
                "error_type": "syntax",
                "difficulty": "easy"
            },
            {
                "test_id": "test_2",
                "input": "def calculate_sum(a, b):\n    return a - b",
                "expected_output": "def calculate_sum(a, b):\n    return a + b",
                "error_type": "logic",
                "difficulty": "medium"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_validate_learning_effectiveness(self, metrics_collector, mock_benchmark_data):
        """Test learning effectiveness validation"""
        # Mock benchmark data loading
        with patch.object(metrics_collector, '_load_benchmark_dataset', return_value=mock_benchmark_data):
            before_state = {"accuracy": 0.7, "speed": 0.8}
            after_state = {"accuracy": 0.85, "speed": 0.9}
            
            result = await metrics_collector.validate_learning_effectiveness(
                learning_session_id="test_session",
                before_state=before_state,
                after_state=after_state
            )
            
            assert result.session_id == "test_session"
            assert result.total_tests == 2
            assert result.passed_tests >= 0
            assert result.failed_tests >= 0
            assert result.success_rate >= 0.0
            assert result.success_rate <= 1.0
    
    @pytest.mark.asyncio
    async def test_load_benchmark_dataset(self, metrics_collector):
        """Test loading benchmark dataset"""
        # Test with non-existent file (should create mock)
        result = await metrics_collector._load_benchmark_dataset()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("test_id" in item for item in result)
    
    @pytest.mark.asyncio
    async def test_run_benchmark_test(self, metrics_collector):
        """Test running a single benchmark test"""
        test_case = {
            "test_id": "test_1",
            "input": "test input",
            "expected_output": "test output",
            "error_type": "syntax",
            "difficulty": "easy"
        }
        
        before_state = {"accuracy": 0.7}
        after_state = {"accuracy": 0.8}
        
        result = await metrics_collector._run_benchmark_test(
            test_case, before_state, after_state
        )
        
        assert result.test_id == "test_1"
        assert result.accuracy_before >= 0.0
        assert result.accuracy_after >= 0.0
        assert result.accuracy_delta == result.accuracy_after - result.accuracy_before
        assert result.error_types is not None
        assert result.safety_violations is not None
    
    def test_measure_accuracy(self, metrics_collector):
        """Test accuracy measurement"""
        test_case = {"difficulty": "easy"}
        state = {"accuracy": 0.8}
        
        accuracy = metrics_collector._measure_accuracy(test_case, state)
        
        assert 0.0 <= accuracy <= 1.0
    
    def test_detect_error_types(self, metrics_collector):
        """Test error type detection"""
        test_case = {"error_type": "syntax"}
        state = {"errors": []}
        
        error_types = metrics_collector._detect_error_types(test_case, state)
        
        assert "syntax" in error_types
        assert error_types["syntax"] == 1
    
    def test_detect_safety_violations(self, metrics_collector):
        """Test safety violation detection"""
        test_case = {"input": "harmful content"}
        state = {"safety": True}
        
        violations = metrics_collector._detect_safety_violations(test_case, state)
        
        assert isinstance(violations, dict)
    
    @pytest.mark.asyncio
    async def test_save_validation_results(self, metrics_collector):
        """Test saving validation results"""
        from stillme_core.learning.learning_metrics_collector import LearningValidationMetrics, BenchmarkResult
        
        # Create mock validation metrics
        benchmark_results = [
            BenchmarkResult(
                test_id="test_1",
                accuracy_before=0.7,
                accuracy_after=0.8,
                accuracy_delta=0.1,
                error_types={"syntax": 1},
                safety_violations={},
                execution_time=0.1,
                timestamp="2025-01-27T00:00:00Z"
            )
        ]
        
        metrics = LearningValidationMetrics(
            session_id="test_session",
            timestamp="2025-01-27T00:00:00Z",
            benchmark_results=benchmark_results,
            overall_accuracy_delta=0.1,
            error_distribution={"syntax": 1},
            safety_violation_rate=0.0,
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            success_rate=1.0
        )
        
        await metrics_collector._save_validation_results(metrics)
        
        # Check if file was created
        artifacts_file = metrics_collector.artifacts_path / "self_learning_validation.json"
        assert artifacts_file.exists()
    
    @pytest.mark.asyncio
    async def test_log_validation_to_transparency(self, metrics_collector):
        """Test logging to transparency logger"""
        from stillme_core.learning.learning_metrics_collector import LearningValidationMetrics, BenchmarkResult
        
        # Mock transparency logger
        with patch.object(metrics_collector.transparency_logger, 'log_decision', new_callable=AsyncMock):
            benchmark_results = [
                BenchmarkResult(
                    test_id="test_1",
                    accuracy_before=0.7,
                    accuracy_after=0.8,
                    accuracy_delta=0.1,
                    error_types={"syntax": 1},
                    safety_violations={},
                    execution_time=0.1,
                    timestamp="2025-01-27T00:00:00Z"
                )
            ]
            
            metrics = LearningValidationMetrics(
                session_id="test_session",
                timestamp="2025-01-27T00:00:00Z",
                benchmark_results=benchmark_results,
                overall_accuracy_delta=0.1,
                error_distribution={"syntax": 1},
                safety_violation_rate=0.0,
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                success_rate=1.0
            )
            
            await metrics_collector._log_validation_to_transparency(metrics)
            
            # Verify transparency logger was called
            metrics_collector.transparency_logger.log_decision.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_safety_thresholds(self, metrics_collector):
        """Test safety threshold checking"""
        from stillme_core.learning.learning_metrics_collector import LearningValidationMetrics, BenchmarkResult
        
        # Create metrics that exceed safety thresholds
        benchmark_results = [
            BenchmarkResult(
                test_id="test_1",
                accuracy_before=0.7,
                accuracy_after=0.8,
                accuracy_delta=0.1,
                error_types={"syntax": 1},
                safety_violations={"content_violation": 1},
                execution_time=0.1,
                timestamp="2025-01-27T00:00:00Z"
            )
        ]
        
        metrics = LearningValidationMetrics(
            session_id="test_session",
            timestamp="2025-01-27T00:00:00Z",
            benchmark_results=benchmark_results,
            overall_accuracy_delta=0.1,
            error_distribution={"syntax": 1},
            safety_violation_rate=1.0,  # High violation rate
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            success_rate=1.0
        )
        
        await metrics_collector._check_safety_thresholds(metrics)
        
        # Should log warning about safety threshold violations
    
    def test_get_validation_history(self, metrics_collector):
        """Test getting validation history"""
        # Initially empty
        history = metrics_collector.get_validation_history()
        assert len(history) == 0
        
        # Add some mock history
        from stillme_core.learning.learning_metrics_collector import LearningValidationMetrics, BenchmarkResult
        
        benchmark_results = [
            BenchmarkResult(
                test_id="test_1",
                accuracy_before=0.7,
                accuracy_after=0.8,
                accuracy_delta=0.1,
                error_types={"syntax": 1},
                safety_violations={},
                execution_time=0.1,
                timestamp="2025-01-27T00:00:00Z"
            )
        ]
        
        metrics = LearningValidationMetrics(
            session_id="test_session",
            timestamp="2025-01-27T00:00:00Z",
            benchmark_results=benchmark_results,
            overall_accuracy_delta=0.1,
            error_distribution={"syntax": 1},
            safety_violation_rate=0.0,
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            success_rate=1.0
        )
        
        metrics_collector.validation_history.append(metrics)
        
        history = metrics_collector.get_validation_history()
        assert len(history) == 1
        assert history[0].session_id == "test_session"
    
    def test_get_learning_trends(self, metrics_collector):
        """Test getting learning trends"""
        # Test with insufficient data
        trends = metrics_collector.get_learning_trends()
        assert trends["trend"] == "insufficient_data"
        
        # Add mock history for trend analysis
        from stillme_core.learning.learning_metrics_collector import LearningValidationMetrics, BenchmarkResult
        
        for i in range(5):
            benchmark_results = [
                BenchmarkResult(
                    test_id=f"test_{i}",
                    accuracy_before=0.7,
                    accuracy_after=0.8 + i * 0.01,  # Improving trend
                    accuracy_delta=0.1 + i * 0.01,
                    error_types={"syntax": 1},
                    safety_violations={},
                    execution_time=0.1,
                    timestamp="2025-01-27T00:00:00Z"
                )
            ]
            
            metrics = LearningValidationMetrics(
                session_id=f"test_session_{i}",
                timestamp="2025-01-27T00:00:00Z",
                benchmark_results=benchmark_results,
                overall_accuracy_delta=0.1 + i * 0.01,
                error_distribution={"syntax": 1},
                safety_violation_rate=0.0,
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                success_rate=1.0
            )
            
            metrics_collector.validation_history.append(metrics)
        
        trends = metrics_collector.get_learning_trends()
        assert "success_trend" in trends
        assert "accuracy_trend" in trends
        assert "average_success_rate" in trends
        assert "average_accuracy_delta" in trends
