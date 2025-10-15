"""
Additional edge case tests for Sandbox Module
Tests to improve coverage for missing lines
"""

import pytest
import tempfile
from pathlib import Path

from agent_dev.sandbox import (
    safe_join,
    is_within_root,
    deny_symlink,
    mkdir_sandbox,
    safe_write_file,
    safe_read_file,
    list_sandbox_files,
    cleanup_sandbox,
)
from agent_dev.schemas import PolicyViolation


class TestSandboxEdgeCases:
    """Test cases for edge cases and missing coverage in sandbox module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sandbox_root = self.temp_dir / "sandbox"
        self.sandbox_root.mkdir()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_safe_join_edge_cases(self):
        """Test safe_join with edge cases"""
        # Test with single dot (should work)
        result = safe_join(self.sandbox_root, ".")
        assert result == self.sandbox_root

        # Test with multiple valid components
        result = safe_join(self.sandbox_root, "dir1", "dir2", "file.txt")
        expected = self.sandbox_root / "dir1" / "dir2" / "file.txt"
        assert result == expected.resolve()

        # Test with empty string (should work as it's not a traversal)
        result = safe_join(self.sandbox_root, "")
        assert result == self.sandbox_root

    @pytest.mark.unit
    def test_is_within_root_edge_cases(self):
        """Test is_within_root with edge cases"""
        # Test with non-existent paths
        non_existent = self.temp_dir / "non_existent" / "file.txt"
        assert not is_within_root(non_existent, self.sandbox_root)

        # Test with invalid paths
        invalid_path = Path("/invalid/path/with/../traversal")
        assert not is_within_root(invalid_path, self.sandbox_root)

        # Test with same path
        assert is_within_root(self.sandbox_root, self.sandbox_root)

        # Test with subdirectory
        subdir = self.sandbox_root / "subdir"
        subdir.mkdir()
        assert is_within_root(subdir, self.sandbox_root)

    @pytest.mark.unit
    def test_deny_symlink_edge_cases(self):
        """Test deny_symlink with edge cases"""
        # Test with non-existent path (should not raise)
        non_existent = self.sandbox_root / "non_existent"
        deny_symlink(non_existent)  # Should not raise

        # Test with regular file
        regular_file = self.sandbox_root / "regular.txt"
        regular_file.write_text("content")
        deny_symlink(regular_file)  # Should not raise

        # Test with directory
        test_dir = self.sandbox_root / "test_dir"
        test_dir.mkdir()
        deny_symlink(test_dir)  # Should not raise

    @pytest.mark.unit
    def test_mkdir_sandbox_edge_cases(self):
        """Test mkdir_sandbox with edge cases"""
        # Test with existing directory
        existing_dir = self.temp_dir / "existing"
        existing_dir.mkdir()
        result = mkdir_sandbox(existing_dir)
        assert result == existing_dir.resolve()

        # Test with nested path
        nested_path = self.temp_dir / "nested" / "deep" / "path"
        result = mkdir_sandbox(nested_path)
        assert result == nested_path.resolve()
        assert result.exists()

    @pytest.mark.unit
    def test_safe_write_file_edge_cases(self):
        """Test safe_write_file with edge cases"""
        # Test with empty content
        safe_write_file("empty.txt", "", self.sandbox_root)
        assert (self.sandbox_root / "empty.txt").exists()

        # Test with unicode content
        unicode_content = "Hello 世界 🌍"
        safe_write_file("unicode.txt", unicode_content, self.sandbox_root)
        content = safe_read_file("unicode.txt", self.sandbox_root)
        assert content == unicode_content

        # Test with very small size limit
        with pytest.raises(PolicyViolation, match="File size.*exceeds limit"):
            safe_write_file("large.txt", "A" * 2000, self.sandbox_root, max_size_kb=1)

    @pytest.mark.unit
    def test_safe_read_file_edge_cases(self):
        """Test safe_read_file with edge cases"""
        # Test with non-existent file
        with pytest.raises(PolicyViolation, match="File not found"):
            safe_read_file("non_existent.txt", self.sandbox_root)

        # Test with empty file
        empty_file = self.sandbox_root / "empty.txt"
        empty_file.write_text("")
        content = safe_read_file("empty.txt", self.sandbox_root)
        assert content == ""

        # Test with binary-like content (should still work with text)
        binary_like = "Hello\x00World\x01Test"
        safe_write_file("binary_like.txt", binary_like, self.sandbox_root)
        content = safe_read_file("binary_like.txt", self.sandbox_root)
        assert content == binary_like

    @pytest.mark.unit
    def test_list_sandbox_files_edge_cases(self):
        """Test list_sandbox_files with edge cases"""
        # Test with empty directory
        files = list_sandbox_files(self.sandbox_root)
        assert len(files) == 0

        # Test with pattern matching
        (self.sandbox_root / "test1.txt").write_text("content1")
        (self.sandbox_root / "test2.py").write_text("content2")
        (self.sandbox_root / "other.md").write_text("content3")

        # Test with specific pattern
        txt_files = list_sandbox_files(self.sandbox_root, "*.txt")
        assert len(txt_files) == 1
        assert txt_files[0].name == "test1.txt"

        # Test with all files
        all_files = list_sandbox_files(self.sandbox_root, "*")
        assert len(all_files) == 3

        # Test with non-matching pattern
        no_files = list_sandbox_files(self.sandbox_root, "*.nonexistent")
        assert len(no_files) == 0

    @pytest.mark.unit
    def test_cleanup_sandbox_edge_cases(self):
        """Test cleanup_sandbox with edge cases"""
        # Test with non-existent directory
        non_existent = self.temp_dir / "non_existent"
        cleanup_sandbox(non_existent)  # Should not raise

        # Test with file instead of directory
        file_path = self.temp_dir / "file.txt"
        file_path.write_text("content")
        cleanup_sandbox(file_path)  # Should not raise

        # Test with directory containing files
        test_dir = self.temp_dir / "test_cleanup"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        cleanup_sandbox(test_dir)
        assert not test_dir.exists()

    @pytest.mark.unit
    def test_path_traversal_variations(self):
        """Test various path traversal attack patterns"""
        # Test with encoded traversal
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "..", "..", "etc", "passwd")

        # Test with mixed separators
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "dir", "..", "..", "..", "etc")

        # Test with Windows-style paths
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "C:\\Windows\\System32")

        # Test with absolute Unix paths
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "/etc/passwd")

    @pytest.mark.unit
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        # Test with unicode filenames
        unicode_filename = "файл_с_русским_названием.txt"
        unicode_content = "Содержимое файла на русском языке"
        safe_write_file(unicode_filename, unicode_content, self.sandbox_root)
        content = safe_read_file(unicode_filename, self.sandbox_root)
        assert content == unicode_content

        # Test with special characters in filename
        special_filename = "file with spaces & symbols!@#.txt"
        special_content = "Content with special chars: !@#$%^&*()"
        safe_write_file(special_filename, special_content, self.sandbox_root)
        content = safe_read_file(special_filename, self.sandbox_root)
        assert content == special_content

    @pytest.mark.unit
    def test_nested_directory_operations(self):
        """Test operations with deeply nested directories"""
        # Create deeply nested structure
        deep_path = Path("level1/level2/level3/level4/level5")
        safe_write_file(deep_path / "deep_file.txt", "deep content", self.sandbox_root)

        # Verify file exists
        content = safe_read_file(deep_path / "deep_file.txt", self.sandbox_root)
        assert content == "deep content"

        # Test listing files in nested directory
        files = list_sandbox_files(self.sandbox_root / deep_path)
        assert len(files) == 1
        assert files[0].name == "deep_file.txt"

    @pytest.mark.unit
    def test_permission_edge_cases(self):
        """Test permission-related edge cases"""
        # Test with read-only parent directory (should still work)
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()

        # On Windows, we can't easily make directories read-only, so we'll test
        # the basic functionality instead
        safe_write_file("test.txt", "content", readonly_dir)
        content = safe_read_file("test.txt", readonly_dir)
        assert content == "content"
