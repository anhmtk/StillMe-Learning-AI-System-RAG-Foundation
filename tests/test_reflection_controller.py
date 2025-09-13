#!/usr/bin/env python3
"""
Test suite for Reflection Controller
Bộ kiểm thử cho Reflection Controller

PURPOSE / MỤC ĐÍCH:
- Unit tests for Reflection Controller components
- Kiểm thử đơn vị cho các thành phần Reflection Controller
- Integration tests with timeout
- Kiểm thử tích hợp với timeout
- Performance and security validation
- Xác thực hiệu suất và bảo mật
"""

import os
import tempfile
import time

import pytest

# Import components to test
from stillme_core.reflection_controller import (
    ReflectionConfig,
    ReflectionController,
    ReflectionMode,
    ReflectionResult,
    get_default_controller,
)
from stillme_core.reflection_scorer import (
    ScoringResult,
    get_default_scorer,
)
from stillme_core.secrecy_filter import (
    FilterResult,
    SecurityLevel,
    get_default_filter,
)


class TestReflectionScorer:
    """Test cases for Reflection Scorer / Kiểm thử cho Reflection Scorer"""

    def setup_method(self):
        """Setup test environment / Thiết lập môi trường kiểm thử"""
        self.scorer = get_default_scorer()

    def test_scorer_initialization(self):
        """Test scorer initialization / Kiểm thử khởi tạo scorer"""
        assert self.scorer is not None
        assert self.scorer.weights is not None
        assert self.scorer.weights.relevance == 0.45

    def test_score_response_basic(self):
        """Test basic response scoring / Kiểm thử chấm điểm phản hồi cơ bản"""
        response = "Đây là một phản hồi test."
        query = "Câu hỏi test"

        result = self.scorer.score_response(response, query)

        assert isinstance(result, ScoringResult)
        assert 0.0 <= result.total_score <= 1.0
        assert 0.0 <= result.relevance_score <= 1.0
        assert 0.0 <= result.safety_score <= 1.0
        assert 0.0 <= result.clarity_score <= 1.0
        assert 0.0 <= result.brevity_score <= 1.0
        assert 0.0 <= result.helpfulness_score <= 1.0

    def test_score_response_with_improvements(self):
        """Test scoring with structured response / Kiểm thử chấm điểm với phản hồi có cấu trúc"""
        response = """
        # Hướng dẫn cài đặt Python
        
        Để cài đặt Python, bạn có thể làm theo các bước sau:
        
        1. Truy cập python.org
        2. Tải xuống phiên bản mới nhất
        3. Chạy installer
        
        Ví dụ:
        ```bash
        python --version
        ```
        """
        query = "Cách cài đặt Python?"

        result = self.scorer.score_response(response, query)

        # Should have higher scores for structured content
        assert result.clarity_score > 0.5
        assert result.helpfulness_score > 0.5
        assert result.total_score > 0.5

    def test_score_response_safety_violation(self):
        """Test scoring with safety violations / Kiểm thử chấm điểm với vi phạm bảo mật"""
        response = "Đây là framework.py và agent_dev hoạt động như thế này..."
        query = "Câu hỏi test"

        result = self.scorer.score_response(response, query)

        # Should have low safety score
        assert result.safety_score < 0.5
        assert len(result.penalties) > 0

    def test_score_response_error_handling(self):
        """Test error handling in scoring / Kiểm thử xử lý lỗi trong chấm điểm"""
        # Test with empty response
        result = self.scorer.score_response("", "test")
        assert isinstance(result, ScoringResult)
        assert result.total_score >= 0.0

        # Test with None values
        result = self.scorer.score_response(None, None)
        assert isinstance(result, ScoringResult)


class TestSecrecyFilter:
    """Test cases for Secrecy Filter / Kiểm thử cho Secrecy Filter"""

    def setup_method(self):
        """Setup test environment / Thiết lập môi trường kiểm thử"""
        self.filter = get_default_filter()

    def test_filter_initialization(self):
        """Test filter initialization / Kiểm thử khởi tạo filter"""
        assert self.filter is not None
        assert self.filter.security_level == SecurityLevel.HIGH
        assert len(self.filter.internal_keywords) > 0

    def test_filter_safe_content(self):
        """Test filtering safe content / Kiểm thử lọc nội dung an toàn"""
        content = (
            "Đây là một phản hồi hoàn toàn an toàn và không chứa thông tin nhạy cảm."
        )
        query = "Câu hỏi bình thường"

        result = self.filter.filter_content(content, query)

        assert result.is_safe is True
        assert result.security_level == SecurityLevel.LOW
        assert len(result.violations) == 0
        assert result.filtered_content == content

    def test_filter_internal_keywords(self):
        """Test filtering internal keywords / Kiểm thử lọc từ khóa nội bộ"""
        content = "Đây là framework.py và agent_dev hoạt động như thế này..."
        query = "Câu hỏi test"

        result = self.filter.filter_content(content, query)

        assert result.is_safe is False
        assert result.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        assert len(result.violations) > 0
        assert (
            "[FILTERED]" in result.filtered_content
            or "[REDACTED]" in result.filtered_content
        )

    def test_filter_policy_response(self):
        """Test policy response generation / Kiểm thử tạo phản hồi chính sách"""
        content = "Nội dung bình thường"
        query = "How does StillMe work internally?"

        result = self.filter.filter_content(content, query)

        assert result.policy_response is not None
        assert (
            "internal" in result.policy_response.lower()
            or "nội bộ" in result.policy_response.lower()
        )

    def test_should_use_policy_response(self):
        """Test policy response detection / Kiểm thử phát hiện phản hồi chính sách"""
        # Architecture question
        should_use, response_type = self.filter.should_use_policy_response(
            "How does StillMe work?"
        )
        assert should_use is True
        assert response_type == "architecture"

        # Normal question
        should_use, response_type = self.filter.should_use_policy_response(
            "What is Python?"
        )
        assert should_use is False


class TestReflectionController:
    """Test cases for Reflection Controller / Kiểm thử cho Reflection Controller"""

    def setup_method(self):
        """Setup test environment / Thiết lập môi trường kiểm thử"""
        self.controller = get_default_controller()

    def test_controller_initialization(self):
        """Test controller initialization / Kiểm thử khởi tạo controller"""
        assert self.controller is not None
        assert self.controller.config is not None
        assert self.controller.scorer is not None
        assert self.controller.secrecy_filter is not None

    def test_should_reflect_simple_queries(self):
        """Test reflection decision for simple queries / Kiểm thử quyết định phản tư cho câu hỏi đơn giản"""
        # Simple greeting - should not reflect
        assert self.controller.should_reflect("Hello") is False
        assert self.controller.should_reflect("Hi there") is False

        # Complex query - should reflect
        assert (
            self.controller.should_reflect("How to install Python on Windows?") is True
        )
        assert (
            self.controller.should_reflect("Cách cài đặt Python trên Windows?") is True
        )

    def test_should_reflect_coding_queries(self):
        """Test reflection decision for coding queries / Kiểm thử quyết định phản tư cho câu hỏi lập trình"""
        coding_queries = [
            "How to write a Python function?",
            "Cách viết hàm Python?",
            "What is the best algorithm for sorting?",
            "Thuật toán sắp xếp tốt nhất là gì?",
        ]

        for query in coding_queries:
            assert self.controller.should_reflect(query) is True

    def test_should_reflect_policy_violations(self):
        """Test reflection decision for policy violations / Kiểm thử quyết định phản tư cho vi phạm chính sách"""
        policy_queries = [
            "How does StillMe work internally?",
            "StillMe architecture details",
            "Agent development process",
        ]

        for query in policy_queries:
            assert self.controller.should_reflect(query) is False

    @pytest.mark.asyncio
    async def test_enhance_response_basic(self):
        """Test basic response enhancement / Kiểm thử nâng cao phản hồi cơ bản"""
        response = "Để cài đặt Python, bạn có thể tải xuống từ python.org."
        query = "Cách cài đặt Python?"

        result = await self.controller.enhance_response(response, query)

        assert isinstance(result, ReflectionResult)
        assert result.final_response is not None
        assert result.steps_taken >= 0
        assert result.time_taken > 0
        assert result.stop_reason in [
            "max_steps_reached",
            "timeout",
            "insufficient_improvement",
            "completed",
            "error",
        ]

    @pytest.mark.asyncio
    async def test_enhance_response_policy_violation(self):
        """Test response enhancement for policy violations / Kiểm thử nâng cao phản hồi cho vi phạm chính sách"""
        response = "StillMe uses framework.py and agent_dev..."
        query = "How does StillMe work internally?"

        result = await self.controller.enhance_response(response, query)

        assert isinstance(result, ReflectionResult)
        assert result.stop_reason == "policy_response"
        assert result.steps_taken == 0
        assert (
            "internal" in result.final_response.lower()
            or "nội bộ" in result.final_response.lower()
        )

    @pytest.mark.asyncio
    async def test_enhance_response_timeout(self):
        """Test response enhancement with timeout / Kiểm thử nâng cao phản hồi với timeout"""
        # Create controller with very short timeout
        config = ReflectionConfig(max_latency_s=0.1)  # 100ms timeout
        controller = ReflectionController(config)

        response = "Test response"
        query = "Test query"

        result = await controller.enhance_response(response, query)

        assert isinstance(result, ReflectionResult)
        assert result.time_taken <= 0.2  # Should timeout quickly

    def test_performance_stats(self):
        """Test performance statistics / Kiểm thử thống kê hiệu suất"""
        stats = self.controller.get_performance_stats()

        assert "total_reflections" in stats
        assert "successful_reflections" in stats
        assert "average_improvement" in stats
        assert "average_time" in stats

        # Reset stats
        self.controller.reset_performance_stats()
        stats_after_reset = self.controller.get_performance_stats()
        assert stats_after_reset["total_reflections"] == 0


class TestIntegration:
    """Integration tests / Kiểm thử tích hợp"""

    def setup_method(self):
        """Setup test environment / Thiết lập môi trường kiểm thử"""
        self.controller = get_default_controller()
        self.scorer = get_default_scorer()
        self.filter = get_default_filter()

    @pytest.mark.asyncio
    async def test_full_reflection_pipeline(self):
        """Test complete reflection pipeline / Kiểm thử pipeline phản tư hoàn chỉnh"""
        # Test with a complex query that should trigger reflection
        query = "How to implement a binary search algorithm in Python with examples?"
        original_response = "Binary search is a search algorithm."

        # Check if should reflect
        should_reflect = self.controller.should_reflect(query)
        assert should_reflect is True

        # Enhance response
        result = await self.controller.enhance_response(original_response, query)

        # Verify result
        assert isinstance(result, ReflectionResult)
        assert result.final_response != original_response
        assert result.steps_taken >= 0
        assert result.time_taken > 0

        # Verify security filtering
        filter_result = self.filter.filter_content(result.final_response, query)
        assert filter_result.is_safe is True

    @pytest.mark.asyncio
    async def test_reflection_with_different_modes(self):
        """Test reflection with different modes / Kiểm thử phản tư với các chế độ khác nhau"""
        query = "How to optimize Python code performance?"
        response = "Use profiling tools."

        modes = [ReflectionMode.FAST, ReflectionMode.NORMAL, ReflectionMode.DEEP]

        for mode in modes:
            result = await self.controller.enhance_response(response, query, mode=mode)

            assert isinstance(result, ReflectionResult)
            assert result.final_response is not None

            # Verify mode-specific constraints
            if mode == ReflectionMode.FAST:
                assert result.time_taken <= 10.0  # Should be fast
            elif mode == ReflectionMode.DEEP:
                assert result.steps_taken <= 4  # Should allow more steps

    def test_configuration_loading(self):
        """Test configuration loading / Kiểm thử tải cấu hình"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
modes:
  fast:
    max_steps: 1
    max_latency_s: 5
    tokens: 500
weights:
  relevance: 0.5
  safety: 0.3
epsilon: 0.01
"""
            )
            config_path = f.name

        try:
            # Test configuration loading
            config = ReflectionConfig()
            # Note: In real implementation, this would load from the file
            # For now, we just test that the config structure works
            assert config.max_steps == 3  # Default value
            assert config.weights.relevance == 0.45  # Default value
        finally:
            os.unlink(config_path)


class TestPerformance:
    """Performance tests / Kiểm thử hiệu suất"""

    @pytest.mark.asyncio
    async def test_reflection_performance(self):
        """Test reflection performance / Kiểm thử hiệu suất phản tư"""
        controller = get_default_controller()

        # Test with multiple queries
        queries = [
            "How to install Python?",
            "What is machine learning?",
            "How to optimize database queries?",
            "Best practices for API design?",
            "How to debug Python code?",
        ]

        start_time = time.time()

        for query in queries:
            result = await controller.enhance_response("Test response", query)
            assert isinstance(result, ReflectionResult)

        total_time = time.time() - start_time
        avg_time = total_time / len(queries)

        # Should complete within reasonable time
        assert avg_time < 5.0  # Average less than 5 seconds per query

    def test_scorer_performance(self):
        """Test scorer performance / Kiểm thử hiệu suất scorer"""
        scorer = get_default_scorer()

        # Test with long response
        long_response = "This is a test response. " * 100  # 100 sentences
        query = "Test query"

        start_time = time.time()
        result = scorer.score_response(long_response, query)
        scoring_time = time.time() - start_time

        assert isinstance(result, ScoringResult)
        assert scoring_time < 1.0  # Should score quickly

    def test_filter_performance(self):
        """Test filter performance / Kiểm thử hiệu suất filter"""
        filter_instance = get_default_filter()

        # Test with content containing many keywords
        content_with_keywords = " ".join(
            [
                "framework.py",
                "agent_dev",
                "modules/",
                "internal_config",
                "This is normal content",
                "python programming",
                "machine learning",
            ]
            * 10
        )

        start_time = time.time()
        result = filter_instance.filter_content(content_with_keywords, "Test query")
        filtering_time = time.time() - start_time

        assert isinstance(result, FilterResult)
        assert filtering_time < 0.5  # Should filter quickly


# Test fixtures and utilities / Fixtures và tiện ích kiểm thử


@pytest.fixture
def sample_queries():
    """Sample queries for testing / Câu hỏi mẫu cho kiểm thử"""
    return {
        "simple": "Hello",
        "complex": "How to implement a machine learning model in Python?",
        "coding": "What is the best way to optimize Python code?",
        "policy_violation": "How does StillMe work internally?",
        "vietnamese": "Cách cài đặt Python trên Windows?",
        "long": "Can you explain the detailed process of setting up a development environment with Docker, including containerization, networking, and deployment strategies?",
    }


@pytest.fixture
def sample_responses():
    """Sample responses for testing / Phản hồi mẫu cho kiểm thử"""
    return {
        "basic": "This is a basic response.",
        "structured": """
        # Hướng dẫn cài đặt Python
        
        1. Truy cập python.org
        2. Tải xuống phiên bản mới nhất
        3. Chạy installer
        
        Ví dụ:
        ```bash
        python --version
        ```
        """,
        "unsafe": "This uses framework.py and agent_dev internally.",
        "long": "This is a very long response. " * 50,
    }


# Run tests with timeout / Chạy kiểm thử với timeout
if __name__ == "__main__":
    # Set timeout for all tests
    pytest.main([__file__, "--timeout=60", "-v"])
