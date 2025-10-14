"""
Test Subprocess Decode Safety
============================

Tests for safe subprocess output decoding in monitor.
"""

from unittest.mock import Mock

from stillme_core.utils.io_safe import safe_decode


class TestSubprocessDecode:
    """Test subprocess output decoding safety"""

    def test_safe_decode_utf8(self):
        """Test safe decode with UTF-8"""
        text = "Hello, World! 🌍"
        data = text.encode("utf-8")
        result = safe_decode(data)
        assert result == text

    def test_safe_decode_cp1252(self):
        """Test safe decode with CP1252"""
        text = "Hello, World!"
        data = text.encode("cp1252")
        result = safe_decode(data)
        assert result == text

    def test_safe_decode_corrupted(self):
        """Test safe decode with corrupted data"""
        # Create corrupted data
        data = b"Hello, World! \xff\xfe\x00\x01"
        result = safe_decode(data)
        # Should not crash and return some string
        assert isinstance(result, str)
        assert len(result) > 0

    def test_safe_decode_empty(self):
        """Test safe decode with empty data"""
        data = b""
        result = safe_decode(data)
        assert result == ""

    def test_safe_decode_null_bytes(self):
        """Test safe decode with null bytes"""
        data = b"Hello\x00World\x00"
        result = safe_decode(data)
        assert isinstance(result, str)
        assert "Hello" in result

    def test_safe_decode_unicode_edge_cases(self):
        """Test safe decode with Unicode edge cases"""
        test_cases = [
            "Simple ASCII",
            "Unicode: 你好世界",
            "Emoji: 🚀🌟💻",
            "Mixed: Hello 世界 🌍",
            "Special chars: àáâãäåæçèéêë",
            "Math symbols: ∑∏∫√∞",
            "Currency: €£¥$",
            "Arrows: ←→↑↓",
        ]

        for text in test_cases:
            data = text.encode("utf-8")
            result = safe_decode(data)
            assert result == text

    def test_safe_decode_fallback_behavior(self):
        """Test safe decode fallback behavior"""
        # Create data that will fail with UTF-8 but work with latin-1
        data = b"Hello, World! \x80\x81\x82"
        result = safe_decode(data)
        # Should not crash
        assert isinstance(result, str)
        assert len(result) > 0

    def test_safe_decode_replace_behavior(self):
        """Test safe decode with replace behavior"""
        # Create data that will fail with all encodings
        data = b"Hello, World! \xff\xfe\xfd\xfc"
        result = safe_decode(data)
        # Should not crash and use replace
        assert isinstance(result, str)
        assert "Hello, World!" in result

    def test_monitor_subprocess_safety(self):
        """Test monitor subprocess safety"""
        # Mock subprocess result with corrupted output
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b"Hello, World! \xff\xfe\x00\x01"
        mock_result.stderr = b"Error: \xff\xfe\x00\x01"

        # Test that safe_decode handles this
        stdout_text = safe_decode(mock_result.stdout)
        stderr_text = safe_decode(mock_result.stderr)

        assert isinstance(stdout_text, str)
        assert isinstance(stderr_text, str)
        assert "Hello, World!" in stdout_text
        assert "Error:" in stderr_text

    def test_monitor_json_parsing_safety(self):
        """Test monitor JSON parsing safety"""
        import json

        # Test with corrupted JSON
        corrupted_json = b'{"key": "value", "corrupted": "\xff\xfe"}'
        text = safe_decode(corrupted_json)

        # Should not crash when parsing
        try:
            data = json.loads(text)
            # If it parses, should have expected structure
            assert "key" in data
        except json.JSONDecodeError:
            # Expected for corrupted JSON
            pass

    def test_monitor_line_parsing_safety(self):
        """Test monitor line parsing safety"""
        # Test with corrupted line data
        corrupted_lines = b"file1.py:10:5: F821 undefined name\nfile2.py:20:15: W293 \xff\xfe\x00\x01\n"
        text = safe_decode(corrupted_lines)

        # Should not crash when splitting lines
        lines = text.split("\n")
        assert len(lines) >= 2
        assert "file1.py:10:5: F821" in lines[0]
        assert "file2.py:20:15: W293" in lines[1]

    def test_monitor_continuation_under_failure(self):
        """Test monitor continuation under decode failure"""
        # Test that monitor can continue even with decode failures
        test_cases = [
            b"Normal output",
            b"Output with \xff\xfe\x00\x01",
            b"Mixed: Hello \xff World",
            b"All corrupted: \xff\xfe\xfd\xfc",
        ]

        for data in test_cases:
            result = safe_decode(data)
            # Should always return a string
            assert isinstance(result, str)
            # Should not be empty unless input was empty
            if data:
                assert len(result) > 0

    def test_safe_decode_performance(self):
        """Test safe decode performance"""
        import time

        # Create large data
        large_data = b"Hello, World! " * 10000

        # Test performance
        start_time = time.time()
        result = safe_decode(large_data)
        end_time = time.time()

        # Should complete quickly
        duration = end_time - start_time
        assert duration < 1.0  # Should complete within 1 second

        # Should produce correct result
        assert isinstance(result, str)
        assert "Hello, World!" in result

    def test_safe_decode_memory_usage(self):
        """Test safe decode memory usage"""
        # Create data that would cause memory issues if not handled properly
        data = b"Test data " * 1000

        # Multiple decodes should not cause memory leaks
        for _i in range(100):
            result = safe_decode(data)
            assert isinstance(result, str)
            assert "Test data" in result

    def test_safe_decode_deterministic(self):
        """Test safe decode deterministic behavior"""
        data = b"Hello, World! \xff\xfe\x00\x01"

        # Multiple calls should produce same result
        result1 = safe_decode(data)
        result2 = safe_decode(data)
        result3 = safe_decode(data)

        assert result1 == result2 == result3