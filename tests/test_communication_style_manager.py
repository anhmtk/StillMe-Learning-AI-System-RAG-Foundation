"""
Unit tests for CommunicationStyleManager module
===============================================
Tests the communication optimization functionality.
"""

import pytest

from stillme_core.modules.communication_style_manager import CommunicationStyleManager


class TestCommunicationStyleManager:
    """Test cases for CommunicationStyleManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = CommunicationStyleManager()

    def test_ask_first_rule_file_missing(self):
        """Test Rule 1: Replace verbose response with concise question for missing file info."""
        raw_response = "Tất nhiên rồi, tôi rất sẵn lòng giúp bạn sửa lỗi trong file code. Để làm được điều đó, tôi sẽ cần bạn cung cấp một số thông tin. Đầu tiên là đường dẫn chính xác đến file đó. Thứ hai là mô tả về lỗi bạn đang gặp phải. Và cuối cùng là..."

        result = self.manager.optimize_response(raw_response)

        assert result == "Bạn cho mình xin **đường dẫn đến file** nhé."
        assert len(result) < len(raw_response)

    def test_ask_first_rule_error_missing(self):
        """Test Rule 1: Replace verbose response with concise question for missing error info."""
        raw_response = "Tôi rất vui được giúp đỡ bạn debug code. Để có thể hỗ trợ tốt nhất, tôi cần bạn cung cấp mô tả chi tiết về lỗi bạn đang gặp phải. Bạn có thể chia sẻ thông tin về lỗi đó không?"

        result = self.manager.optimize_response(raw_response)

        assert result == "Bạn cho mình xin **mô tả lỗi** cụ thể nhé."
        assert len(result) < len(raw_response)

    def test_concise_rule_remove_fillers(self):
        """Test Rule 2: Remove unnecessary filler phrases."""
        raw_response = "Tất nhiên rồi, cảm ơn bạn đã hỏi. Tôi rất sẵn lòng giúp đỡ bạn. Đây là một câu hỏi rất thú vị. Python là một ngôn ngữ lập trình mạnh mẽ."

        result = self.manager.optimize_response(raw_response)

        assert "Tất nhiên rồi" not in result
        assert "cảm ơn bạn đã hỏi" not in result
        assert "tôi rất sẵn lòng" not in result
        assert "Python là một ngôn ngữ lập trình mạnh mẽ" in result
        assert len(result) < len(raw_response)

    def test_quick_confirmation_rule(self):
        """Test Rule 3: Ensure responses go straight to the point."""
        raw_response = "Để trả lời câu hỏi của bạn một cách chính xác và đầy đủ, tôi sẽ giải thích chi tiết. Câu trả lời là Python là ngôn ngữ lập trình phổ biến."

        result = self.manager.optimize_response(raw_response)

        # Should extract the core answer
        assert "Python là ngôn ngữ lập trình phổ biến" in result
        assert len(result) < len(raw_response)

    def test_good_response_unchanged(self):
        """Test that already good responses remain unchanged."""
        good_response = (
            "Python là ngôn ngữ lập trình phổ biến. Bạn muốn học về phần nào?"
        )

        result = self.manager.optimize_response(good_response)

        assert result == good_response

    def test_empty_response(self):
        """Test handling of empty or None responses."""
        assert self.manager.optimize_response("") == ""
        assert self.manager.optimize_response(None) is None
        assert self.manager.optimize_response("   ") == "   "

    def test_optimization_stats(self):
        """Test optimization statistics calculation."""
        original = (
            "Tất nhiên rồi, tôi rất sẵn lòng giúp đỡ bạn. Python là ngôn ngữ lập trình."
        )
        optimized = "Python là ngôn ngữ lập trình."

        stats = self.manager.get_optimization_stats(original, optimized)

        assert stats["original_length"] == len(original)
        assert stats["optimized_length"] == len(optimized)
        assert stats["reduction_percentage"] > 0
        assert stats["was_optimized"]

    def test_complex_verbose_response(self):
        """Test optimization of complex verbose response."""
        raw_response = """Tất nhiên rồi, tôi rất sẵn lòng giúp đỡ bạn. Cảm ơn bạn đã hỏi câu hỏi này.
        Để trả lời câu hỏi của bạn một cách chính xác và đầy đủ, tôi sẽ cần bạn cung cấp một số thông tin.
        Đầu tiên là tên file bạn đang gặp vấn đề. Thứ hai là mô tả chi tiết về lỗi.
        Và cuối cùng là thông tin về môi trường bạn đang sử dụng."""

        result = self.manager.optimize_response(raw_response)

        # Should be significantly shorter and more direct
        assert len(result) < len(raw_response) * 0.5
        assert "**" in result  # Should contain formatted question
        assert any(
            keyword in result.lower() for keyword in ["file", "lỗi", "thông tin"]
        )

    def test_mixed_language_response(self):
        """Test optimization of mixed Vietnamese-English response."""
        raw_response = "Tất nhiên rồi, I'm very happy to help you. Để làm được điều đó, I need some information. Please provide the file path and error description."

        result = self.manager.optimize_response(raw_response)

        # Should be optimized regardless of language mix
        assert len(result) < len(raw_response)
        assert "Tất nhiên rồi" not in result
        assert "I'm very happy" not in result


if __name__ == "__main__":
    pytest.main([__file__])
