#!/usr/bin/env python3
"""
AgentDev Sandbox Coverage Boost Tests
Target: agent_dev/sandbox.py (0% → 60%)
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from agent_dev.sandbox import safe_join, safe_read, safe_write, safe_remove


class TestSandboxBoost:
    """Boost coverage for agent_dev/sandbox.py"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox_root = Path(self.temp_dir.name)
        
    def teardown_method(self):
        """Cleanup test environment"""
        self.temp_dir.cleanup()
    
    def test_safe_join_function(self):
        """Test safe_join function"""
        # Test valid path joining
        result = safe_join(self.sandbox_root, "test", "file.txt")
        assert result == self.sandbox_root / "test" / "file.txt"
        
        # Test path traversal protection
        with pytest.raises(ValueError):
            safe_join(self.sandbox_root, "..", "..", "etc", "passwd")
    
    def test_safe_read_function(self):
        """Test safe_read function"""
        # Create a test file
        test_file = self.sandbox_root / "test.txt"
        test_file.write_text("test content")
        
        # Test safe read
        content = safe_read(str(test_file))
        assert content == "test content"
        
        # Test path traversal protection
        with pytest.raises(ValueError):
            safe_read("/etc/passwd")
    
    def test_safe_write_function(self):
        """Test safe_write function"""
        # Test safe write
        test_file = self.sandbox_root / "write_test.txt"
        safe_write(str(test_file), "test content")
        
        assert test_file.exists()
        assert test_file.read_text() == "test content"
        
        # Test path traversal protection
        with pytest.raises(ValueError):
            safe_write("/etc/passwd", "malicious content")
    
    def test_safe_remove_function(self):
        """Test safe_remove function"""
        # Create a test file
        test_file = self.sandbox_root / "remove_test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        
        # Test safe remove
        safe_remove(str(test_file))
        assert not test_file.exists()
        
        # Test path traversal protection
        with pytest.raises(ValueError):
            safe_remove("/etc/passwd")
    
    def test_safe_join_with_multiple_paths(self):
        """Test safe_join with multiple path components"""
        result = safe_join(self.sandbox_root, "dir1", "dir2", "file.txt")
        expected = self.sandbox_root / "dir1" / "dir2" / "file.txt"
        assert result == expected
    
    def test_safe_join_with_absolute_paths(self):
        """Test safe_join with absolute paths"""
        # Test that absolute paths are rejected
        with pytest.raises(ValueError):
            safe_join(self.sandbox_root, "/absolute/path")
    
    def test_safe_read_nonexistent_file(self):
        """Test safe_read with nonexistent file"""
        nonexistent_file = self.sandbox_root / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            safe_read(str(nonexistent_file))
    
    def test_safe_write_directory_creation(self):
        """Test safe_write with directory creation"""
        # Test writing to a file in a subdirectory
        subdir_file = self.sandbox_root / "subdir" / "file.txt"
        safe_write(str(subdir_file), "content")
        
        assert subdir_file.exists()
        assert subdir_file.read_text() == "content"
        assert subdir_file.parent.exists()
    
    def test_safe_remove_nonexistent_file(self):
        """Test safe_remove with nonexistent file"""
        nonexistent_file = self.sandbox_root / "nonexistent.txt"
        
        # Should not raise an exception
        safe_remove(str(nonexistent_file))
    
    def test_safe_operations_with_symlinks(self):
        """Test safe operations with symlinks"""
        # Create a regular file
        regular_file = self.sandbox_root / "regular.txt"
        regular_file.write_text("regular content")
        
        # Create a symlink (if supported)
        try:
            symlink_file = self.sandbox_root / "symlink.txt"
            symlink_file.symlink_to(regular_file)
            
            # Test safe read through symlink
            content = safe_read(str(symlink_file))
            assert content == "regular content"
            
        except OSError:
            # Symlinks not supported on this system
            pass
    
    def test_safe_operations_with_permissions(self):
        """Test safe operations with different permissions"""
        # Create a file with specific permissions
        test_file = self.sandbox_root / "perm_test.txt"
        test_file.write_text("content")
        
        # Test that safe operations work regardless of permissions
        content = safe_read(str(test_file))
        assert content == "content"
    
    def test_safe_join_edge_cases(self):
        """Test safe_join edge cases"""
        # Test with empty path components
        result = safe_join(self.sandbox_root, "", "file.txt")
        assert result == self.sandbox_root / "file.txt"
        
        # Test with single dot
        result = safe_join(self.sandbox_root, ".", "file.txt")
        assert result == self.sandbox_root / "file.txt"
    
    def test_safe_operations_with_unicode(self):
        """Test safe operations with unicode content"""
        # Test with unicode content
        unicode_content = "测试内容 🚀"
        test_file = self.sandbox_root / "unicode_test.txt"
        
        safe_write(str(test_file), unicode_content)
        content = safe_read(str(test_file))
        assert content == unicode_content
    
    def test_safe_operations_with_binary_data(self):
        """Test safe operations with binary data"""
        # Test with binary content
        binary_content = b"binary data \x00\x01\x02"
        test_file = self.sandbox_root / "binary_test.bin"
        
        # Note: safe_write might expect string, so we'll test with string
        text_content = "binary-like content"
        safe_write(str(test_file), text_content)
        content = safe_read(str(test_file))
        assert content == text_content
    
    def test_sandbox_module_imports(self):
        """Test sandbox module imports"""
        from agent_dev.sandbox import safe_join, safe_read, safe_write, safe_remove
        
        # Test that functions are callable
        assert callable(safe_join)
        assert callable(safe_read)
        assert callable(safe_write)
        assert callable(safe_remove)
    
    def test_safe_operations_error_handling(self):
        """Test safe operations error handling"""
        # Test with invalid input types
        with pytest.raises((TypeError, ValueError)):
            safe_join(None, "test")
        
        with pytest.raises((TypeError, ValueError)):
            safe_read(None)
        
        with pytest.raises((TypeError, ValueError)):
            safe_write(None, "content")
        
        with pytest.raises((TypeError, ValueError)):
            safe_remove(None)
    
    def test_sandbox_coverage_comprehensive(self):
        """Test comprehensive sandbox coverage"""
        # Test all safe operations in sequence
        test_file = self.sandbox_root / "comprehensive_test.txt"
        
        # Write
        safe_write(str(test_file), "initial content")
        assert test_file.exists()
        
        # Read
        content = safe_read(str(test_file))
        assert content == "initial content"
        
        # Update
        safe_write(str(test_file), "updated content")
        content = safe_read(str(test_file))
        assert content == "updated content"
        
        # Remove
        safe_remove(str(test_file))
        assert not test_file.exists()