#!/usr/bin/env python3
"""
Security tests for sandbox functionality
Tests path traversal, symlink, and other security protections
"""

import tempfile
from pathlib import Path

import pytest

from agent_dev.sandbox import (
    deny_symlink,
    is_within_root,
    mkdir_sandbox,
    safe_join,
    safe_read_file,
    safe_write_file,
)
from agent_dev.schemas import PolicyViolation


class TestSandboxSecurity:
    """Test cases for sandbox security features"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sandbox_root = self.temp_dir / "sandbox"
        self.sandbox_root.mkdir()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_path_traversal_detection(self):
        """Test that path traversal with '..' is blocked"""
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "../secret.txt")

        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "file", "..", "..", "etc", "passwd")

    def test_absolute_path_blocking(self):
        """Test that absolute paths are blocked"""
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "/etc/passwd")

        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "C:\\Windows\\System32")

    def test_home_expansion_blocking(self):
        """Test that home expansion '~' is blocked"""
        # Test with explicit '~' in path
        with pytest.raises(
            PolicyViolation, match="Path traversal or home expansion not allowed"
        ):
            mkdir_sandbox("~/malicious")

    def test_symlink_detection(self):
        """Test that symlinks are detected and blocked"""
        # Create a symlink
        target_file = self.temp_dir / "target.txt"
        target_file.write_text("secret content")

        symlink_path = self.sandbox_root / "link.txt"
        symlink_path.symlink_to(target_file)

        # Should raise PolicyViolation
        with pytest.raises(PolicyViolation, match="Symlink not allowed"):
            deny_symlink(symlink_path)

    def test_safe_join_within_root(self):
        """Test that safe_join works correctly within root"""
        # Valid paths should work
        result = safe_join(self.sandbox_root, "subdir", "file.txt")
        expected = self.sandbox_root / "subdir" / "file.txt"
        assert result == expected.resolve()

    def test_safe_join_outside_root(self):
        """Test that safe_join blocks paths outside root"""
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_join(self.sandbox_root, "..", "..", "etc")

    def test_is_within_root_validation(self):
        """Test is_within_root function"""
        # Valid cases
        assert is_within_root(self.sandbox_root / "file.txt", self.sandbox_root)
        assert is_within_root(
            self.sandbox_root / "subdir" / "file.txt", self.sandbox_root
        )

        # Invalid cases
        assert not is_within_root(self.temp_dir / "outside.txt", self.sandbox_root)
        assert not is_within_root("/etc/passwd", self.sandbox_root)

    def test_safe_write_file_traversal(self):
        """Test that safe_write_file blocks path traversal"""
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_write_file("../secret.txt", "content", self.sandbox_root)

    def test_safe_write_file_size_limit(self):
        """Test that safe_write_file enforces size limits"""
        large_content = "x" * (2 * 1024)  # 2KB content

        with pytest.raises(PolicyViolation, match="File size.*exceeds limit"):
            safe_write_file(
                "large.txt", large_content, self.sandbox_root, max_size_kb=1
            )

    def test_safe_read_file_traversal(self):
        """Test that safe_read_file blocks path traversal"""
        with pytest.raises(PolicyViolation, match="Path traversal detected"):
            safe_read_file("../secret.txt", self.sandbox_root)

    def test_safe_read_file_size_limit(self):
        """Test that safe_read_file enforces size limits"""
        # Create a large file
        large_file = self.sandbox_root / "large.txt"
        large_content = "x" * (2 * 1024)  # 2KB
        large_file.write_text(large_content)

        with pytest.raises(PolicyViolation, match="File size.*exceeds limit"):
            safe_read_file("large.txt", self.sandbox_root, max_size_kb=1)

    def test_safe_write_file_symlink_parent(self):
        """Test that safe_write_file checks for symlinks in parent directories"""
        # Create a symlink in parent directory
        symlink_dir = self.sandbox_root / "symlink_dir"
        symlink_dir.symlink_to(self.temp_dir)

        with pytest.raises(PolicyViolation, match="Path outside root directory"):
            safe_write_file("symlink_dir/file.txt", "content", self.sandbox_root)

    def test_mkdir_sandbox_traversal(self):
        """Test that mkdir_sandbox blocks path traversal"""
        with pytest.raises(
            PolicyViolation, match="Path traversal or home expansion not allowed"
        ):
            mkdir_sandbox("../malicious")

    def test_safe_operations_success(self):
        """Test that safe operations work correctly for valid paths"""
        # Test safe_write_file
        content = "Hello, World!"
        file_path = safe_write_file("test.txt", content, self.sandbox_root)
        assert file_path.exists()
        assert file_path.read_text() == content

        # Test safe_read_file
        read_content = safe_read_file("test.txt", self.sandbox_root)
        assert read_content == content

    def test_safe_operations_nested_paths(self):
        """Test that safe operations work with nested paths"""
        # Create nested directory structure
        nested_path = safe_write_file(
            "subdir/nested/file.txt", "nested content", self.sandbox_root
        )
        assert nested_path.exists()
        assert nested_path.read_text() == "nested content"

        # Read from nested path
        read_content = safe_read_file("subdir/nested/file.txt", self.sandbox_root)
        assert read_content == "nested content"

    def test_edge_case_empty_paths(self):
        """Test edge cases with empty or special paths"""
        # Empty path should work
        result = safe_join(self.sandbox_root, "")
        assert result == self.sandbox_root.resolve()

        # Single dot should work
        result = safe_join(self.sandbox_root, ".")
        assert result == self.sandbox_root.resolve()

    def test_edge_case_unicode_paths(self):
        """Test edge cases with unicode paths"""
        unicode_path = "测试/文件.txt"
        content = "Unicode content"

        file_path = safe_write_file(unicode_path, content, self.sandbox_root)
        assert file_path.exists()
        assert file_path.read_text() == content

        read_content = safe_read_file(unicode_path, self.sandbox_root)
        assert read_content == content


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi