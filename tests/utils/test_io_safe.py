"""
Test Safe I/O Operations
========================

Tests for the safe file reading utilities.
"""

import tempfile
from pathlib import Path

from stillme_core.utils.io_safe import is_text_file, safe_read_lines, safe_read_text


class TestSafeIO:
    """Test cases for safe I/O operations"""

    def test_safe_read_text_utf8(self):
        """Test reading UTF-8 file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Hello, World! 🌍")
            temp_path = Path(f.name)

        try:
            content = safe_read_text(temp_path)
            assert content == "Hello, World! 🌍"
        finally:
            temp_path.unlink()

    def test_safe_read_text_cp1252(self):
        """Test reading CP1252 file"""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="cp1252", delete=False
        ) as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            content = safe_read_text(temp_path)
            assert content == "Hello, World!"
        finally:
            temp_path.unlink()

    def test_safe_read_text_with_encoding(self):
        """Test reading with specific encoding"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            content = safe_read_text(temp_path, encoding="utf-8")
            assert content == "Test content"
        finally:
            temp_path.unlink()

    def test_safe_read_text_corrupted_encoding(self):
        """Test reading file with corrupted encoding"""
        # Create file with mixed encoding
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            # Write UTF-8 content but with some invalid bytes
            f.write(b"Hello, World! \xff\xfe")
            temp_path = Path(f.name)

        try:
            content = safe_read_text(temp_path)
            # Should not crash and should return some content
            assert isinstance(content, str)
            assert len(content) > 0
        finally:
            temp_path.unlink()

    def test_safe_read_text_nonexistent_file(self):
        """Test reading non-existent file"""
        temp_path = Path("/non/existent/file.txt")
        content = safe_read_text(temp_path)
        assert content == ""

    def test_safe_read_lines(self):
        """Test reading file as lines"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3")
            temp_path = Path(f.name)

        try:
            lines = safe_read_lines(temp_path)
            assert lines == ["Line 1", "Line 2", "Line 3"]
        finally:
            temp_path.unlink()

    def test_safe_read_lines_empty_file(self):
        """Test reading empty file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            lines = safe_read_lines(temp_path)
            assert lines == []  # Empty file should return empty list
        finally:
            temp_path.unlink()

    def test_is_text_file_text(self):
        """Test detecting text file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("This is a text file")
            temp_path = Path(f.name)

        try:
            assert is_text_file(temp_path) is True
        finally:
            temp_path.unlink()

    def test_is_text_file_binary(self):
        """Test detecting binary file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            # Write binary data with null bytes
            f.write(b"Binary data\x00\x01\x02\x03")
            temp_path = Path(f.name)

        try:
            assert is_text_file(temp_path) is False
        finally:
            temp_path.unlink()

    def test_is_text_file_nonexistent(self):
        """Test detecting non-existent file"""
        temp_path = Path("/non/existent/file.txt")
        assert is_text_file(temp_path) is False

    def test_safe_read_text_unicode_edge_cases(self):
        """Test Unicode edge cases"""
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

        for test_content in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False
            ) as f:
                f.write(test_content)
                temp_path = Path(f.name)

            try:
                content = safe_read_text(temp_path)
                assert content == test_content
            finally:
                temp_path.unlink()

    def test_safe_read_text_large_file(self):
        """Test reading large file"""
        # Create a large file (1MB)
        large_content = "A" * 1024 * 1024

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(large_content)
            temp_path = Path(f.name)

        try:
            content = safe_read_text(temp_path)
            assert len(content) == len(large_content)
            assert content == large_content
        finally:
            temp_path.unlink()
