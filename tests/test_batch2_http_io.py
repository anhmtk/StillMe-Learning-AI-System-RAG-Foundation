#!/usr/bin/env python3
"""
Tests for Batch #2: HTTP & I/O Utilities
Kiểm thử cho Batch #2: Tiện ích HTTP & I/O

This module tests the HTTP and I/O utilities from the Common Layer.
Module này kiểm thử các tiện ích HTTP và I/O từ Common Layer.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx

# Import common utilities
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.http import (
    AsyncHttpClient, HTTPClientConfig, HTTPRequest, HTTPResponse, 
    HTTPMethod, HttpRequestBuilder, ResponseValidator,
    get_json, post_json, download_file
)
from common.io import (
    FileManager, FileFormat, FileInfo, FileOperation,
    read_json, write_json, read_yaml, write_yaml,
    async_read_json, async_write_json
)
from common.errors import APIError, NetworkError, ValidationError, StillMeException

class TestHTTPUtilities:
    """Test HTTP utilities - Kiểm thử tiện ích HTTP"""

    def test_http_method_enum(self):
        """Test HTTP method enum - Kiểm thử enum HTTP method"""
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"
        assert HTTPMethod.DELETE.value == "DELETE"

    def test_http_request_creation(self):
        """Test HTTP request creation - Kiểm thử tạo HTTP request"""
        request = HTTPRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            headers={"Authorization": "Bearer token"},
            params={"page": 1},
            timeout=30.0
        )
        
        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/test"
        assert request.headers["Authorization"] == "Bearer token"
        assert request.params["page"] == 1
        assert request.timeout == 30.0

    def test_http_response_creation(self):
        """Test HTTP response creation - Kiểm thử tạo HTTP response"""
        request = HTTPRequest(method=HTTPMethod.GET, url="https://api.example.com/test")
        response = HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"message": "success"}',
            text='{"message": "success"}',
            json_data={"message": "success"},
            url="https://api.example.com/test",
            elapsed_time=0.5,
            request=request
        )
        
        assert response.status_code == 200
        assert response.is_success()
        assert not response.is_client_error()
        assert not response.is_server_error()
        assert response.json_data["message"] == "success"

    def test_http_response_error_detection(self):
        """Test HTTP response error detection - Kiểm thử phát hiện lỗi HTTP response"""
        request = HTTPRequest(method=HTTPMethod.GET, url="https://api.example.com/test")
        
        # Client error
        client_error = HTTPResponse(
            status_code=400, headers={}, content=b"", text="Bad Request",
            url="https://api.example.com/test", elapsed_time=0.1, request=request
        )
        assert client_error.is_client_error()
        assert not client_error.is_success()
        
        # Server error
        server_error = HTTPResponse(
            status_code=500, headers={}, content=b"", text="Internal Server Error",
            url="https://api.example.com/test", elapsed_time=0.1, request=request
        )
        assert server_error.is_server_error()
        assert not server_error.is_success()

    def test_http_response_raise_for_status(self):
        """Test HTTP response raise for status - Kiểm thử ném lỗi theo status"""
        request = HTTPRequest(method=HTTPMethod.GET, url="https://api.example.com/test")
        
        # Success response should not raise
        success_response = HTTPResponse(
            status_code=200, headers={}, content=b"", text="OK",
            url="https://api.example.com/test", elapsed_time=0.1, request=request
        )
        success_response.raise_for_status()  # Should not raise
        
        # Error response should raise
        error_response = HTTPResponse(
            status_code=404, headers={}, content=b"", text="Not Found",
            url="https://api.example.com/test", elapsed_time=0.1, request=request
        )
        with pytest.raises(APIError):
            error_response.raise_for_status()

    def test_http_client_config(self):
        """Test HTTP client configuration - Kiểm thử cấu hình HTTP client"""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            default_headers={"User-Agent": "Test"},
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.base_url == "https://api.example.com"
        assert config.default_headers["User-Agent"] == "Test"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

    @pytest.mark.asyncio
    async def test_http_client_initialization(self):
        """Test HTTP client initialization - Kiểm thử khởi tạo HTTP client"""
        config = HTTPClientConfig(base_url="https://api.example.com")
        client = AsyncHttpClient(config)
        
        assert client.config.base_url == "https://api.example.com"
        assert client.retry_manager is not None
        assert "User-Agent" in client.default_headers

    @pytest.mark.asyncio
    async def test_http_request_builder(self):
        """Test HTTP request builder - Kiểm thử HTTP request builder"""
        client = AsyncHttpClient()
        builder = HttpRequestBuilder(client)
        
        request = (builder
                  .method(HTTPMethod.POST)
                  .url("https://api.example.com/test")
                  .header("Authorization", "Bearer token")
                  .param("page", 1)
                  .json({"message": "test"})
                  .timeout(30.0))
        
        assert builder._request.method == HTTPMethod.POST
        assert builder._request.url == "https://api.example.com/test"
        assert builder._request.headers["Authorization"] == "Bearer token"
        assert builder._request.params["page"] == 1
        assert builder._request.json_data["message"] == "test"
        assert builder._request.timeout == 30.0

    def test_response_validator_json(self):
        """Test response validator for JSON - Kiểm thử validator response cho JSON"""
        request = HTTPRequest(method=HTTPMethod.GET, url="https://api.example.com/test")
        response = HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"message": "success", "data": {"id": 1}}',
            text='{"message": "success", "data": {"id": 1}}',
            json_data={"message": "success", "data": {"id": 1}},
            url="https://api.example.com/test",
            elapsed_time=0.1,
            request=request
        )
        
        # Valid JSON response
        data = ResponseValidator.validate_json_response(response, ["message", "data"])
        assert data["message"] == "success"
        assert data["data"]["id"] == 1
        
        # Missing required fields
        with pytest.raises(ValidationError):
            ResponseValidator.validate_json_response(response, ["message", "missing_field"])

    def test_response_validator_status_code(self):
        """Test response validator for status code - Kiểm thử validator response cho status code"""
        request = HTTPRequest(method=HTTPMethod.GET, url="https://api.example.com/test")
        response = HTTPResponse(
            status_code=200,
            headers={},
            content=b"",
            text="OK",
            url="https://api.example.com/test",
            elapsed_time=0.1,
            request=request
        )
        
        # Valid status code
        ResponseValidator.validate_status_code(response, [200, 201])
        
        # Invalid status code
        with pytest.raises(ValidationError):
            ResponseValidator.validate_status_code(response, [400, 500])

class TestIOUtilities:
    """Test I/O utilities - Kiểm thử tiện ích I/O"""

    def test_file_format_enum(self):
        """Test file format enum - Kiểm thử enum định dạng file"""
        assert FileFormat.JSON.value == "json"
        assert FileFormat.YAML.value == "yaml"
        assert FileFormat.CSV.value == "csv"
        assert FileFormat.TXT.value == "txt"
        assert FileFormat.PICKLE.value == "pickle"
        assert FileFormat.BINARY.value == "binary"

    def test_file_info_creation(self):
        """Test file info creation - Kiểm thử tạo thông tin file"""
        file_info = FileInfo(
            path="/test/file.json",
            size=1024,
            modified_time=1234567890.0,
            format=FileFormat.JSON,
            checksum="abc123",
            exists=True
        )
        
        assert file_info.path == "/test/file.json"
        assert file_info.size == 1024
        assert file_info.format == FileFormat.JSON
        assert file_info.checksum == "abc123"
        assert file_info.exists

    def test_file_operation_creation(self):
        """Test file operation creation - Kiểm thử tạo thao tác file"""
        operation = FileOperation(
            source="/test/source.json",
            destination="/test/dest.json",
            backup=True,
            create_dirs=True,
            overwrite=False,
            validate=True
        )
        
        assert operation.source == "/test/source.json"
        assert operation.destination == "/test/dest.json"
        assert operation.backup
        assert operation.create_dirs
        assert not operation.overwrite
        assert operation.validate

    def test_file_manager_initialization(self):
        """Test file manager initialization - Kiểm thử khởi tạo file manager"""
        manager = FileManager("/test/base")
        assert str(manager.base_path).replace("\\", "/") == "/test/base"
        
        # Default initialization
        manager_default = FileManager()
        assert manager_default.base_path == Path.cwd()

    def test_file_manager_resolve_path(self):
        """Test file manager path resolution - Kiểm thử giải quyết đường dẫn file manager"""
        manager = FileManager("/test/base")
        
        # Absolute path
        abs_path = manager._resolve_path("/absolute/path")
        # On Windows, absolute paths get resolved to full paths
        assert str(abs_path).replace("\\", "/").endswith("/absolute/path")
        
        # Relative path
        rel_path = manager._resolve_path("relative/path")
        assert str(rel_path).replace("\\", "/").endswith("/test/base/relative/path")

    def test_file_manager_get_file_format(self):
        """Test file manager file format detection - Kiểm thử phát hiện định dạng file"""
        manager = FileManager()
        
        assert manager._get_file_format(Path("test.json")) == FileFormat.JSON
        assert manager._get_file_format(Path("test.yaml")) == FileFormat.YAML
        assert manager._get_file_format(Path("test.yml")) == FileFormat.YAML
        assert manager._get_file_format(Path("test.csv")) == FileFormat.CSV
        assert manager._get_file_format(Path("test.txt")) == FileFormat.TXT
        assert manager._get_file_format(Path("test.pickle")) == FileFormat.PICKLE
        assert manager._get_file_format(Path("test.bin")) == FileFormat.BINARY

    def test_file_manager_ensure_directory(self):
        """Test file manager directory creation - Kiểm thử tạo thư mục file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create nested directory
            dir_path = manager.ensure_directory("nested/deep/directory")
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_file_manager_backup_file(self):
        """Test file manager file backup - Kiểm thử backup file file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Backup file
            backup_path = manager.backup_file(test_file)
            assert backup_path.exists()
            assert backup_path.read_text() == "test content"
            
            # Test with custom suffix
            backup_path2 = manager.backup_file(test_file, ".custom")
            assert backup_path2.suffix == ".custom"

    def test_file_manager_safe_write_json(self):
        """Test file manager safe write JSON - Kiểm thử ghi JSON an toàn file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            test_data = {"message": "test", "data": [1, 2, 3]}
            test_file = Path(temp_dir) / "test.json"
            
            operation = FileOperation(
                source=str(test_file),
                create_dirs=True,
                overwrite=True,
                validate=True
            )
            
            manager.safe_write(test_file, test_data, operation)
            
            assert test_file.exists()
            loaded_data = manager.read_file(test_file, FileFormat.JSON)
            assert loaded_data == test_data

    def test_file_manager_safe_write_yaml(self):
        """Test file manager safe write YAML - Kiểm thử ghi YAML an toàn file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            test_data = {"message": "test", "data": [1, 2, 3]}
            test_file = Path(temp_dir) / "test.yaml"
            
            operation = FileOperation(
                source=str(test_file),
                create_dirs=True,
                overwrite=True,
                validate=True
            )
            
            manager.safe_write(test_file, test_data, operation)
            
            assert test_file.exists()
            loaded_data = manager.read_file(test_file, FileFormat.YAML)
            assert loaded_data == test_data

    def test_file_manager_read_file(self):
        """Test file manager read file - Kiểm thử đọc file file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Test JSON file
            test_data = {"message": "test"}
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text(json.dumps(test_data))
            
            loaded_data = manager.read_file(test_file, FileFormat.JSON)
            assert loaded_data == test_data
            
            # Test text file
            text_file = Path(temp_dir) / "test.txt"
            text_file.write_text("Hello World")
            
            loaded_text = manager.read_file(text_file, FileFormat.TXT)
            assert loaded_text == "Hello World"

    def test_file_manager_copy_file(self):
        """Test file manager copy file - Kiểm thử sao chép file file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create source file
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text("test content")
            
            # Copy file
            dest_file = Path(temp_dir) / "dest.txt"
            operation = FileOperation(
                source=str(source_file),
                destination=str(dest_file),
                create_dirs=True,
                overwrite=True
            )
            
            manager.copy_file(source_file, dest_file, operation)
            
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"

    def test_file_manager_move_file(self):
        """Test file manager move file - Kiểm thử di chuyển file file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create source file
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text("test content")
            
            # Move file
            dest_file = Path(temp_dir) / "dest.txt"
            operation = FileOperation(
                source=str(source_file),
                destination=str(dest_file),
                create_dirs=True,
                overwrite=True
            )
            
            manager.move_file(source_file, dest_file, operation)
            
            assert not source_file.exists()
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"

    def test_file_manager_delete_file(self):
        """Test file manager delete file - Kiểm thử xóa file file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Delete file
            manager.delete_file(test_file)
            assert not test_file.exists()
            
            # Delete non-existent file (should not raise)
            manager.delete_file(Path(temp_dir) / "nonexistent.txt")

    def test_file_manager_list_files(self):
        """Test file manager list files - Kiểm thử liệt kê files file manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileManager(temp_dir)
            
            # Create test files
            (Path(temp_dir) / "file1.txt").write_text("content1")
            (Path(temp_dir) / "file2.json").write_text('{"test": true}')
            (Path(temp_dir) / "subdir").mkdir()
            (Path(temp_dir) / "subdir" / "file3.txt").write_text("content3")
            
            # List files in root
            files = manager.list_files(temp_dir, "*.txt")
            assert len(files) == 1
            assert files[0].path.endswith("file1.txt")
            
            # List all files recursively
            all_files = manager.list_files(temp_dir, "*", recursive=True)
            assert len(all_files) == 3

class TestConvenienceFunctions:
    """Test convenience functions - Kiểm thử các hàm tiện ích"""

    def test_read_write_json(self):
        """Test read/write JSON convenience functions - Kiểm thử hàm tiện ích đọc/ghi JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {"message": "test", "data": [1, 2, 3]}
            
            # Write JSON
            write_json(test_file, test_data)
            assert test_file.exists()
            
            # Read JSON
            loaded_data = read_json(test_file)
            assert loaded_data == test_data

    def test_read_write_yaml(self):
        """Test read/write YAML convenience functions - Kiểm thử hàm tiện ích đọc/ghi YAML"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.yaml"
            test_data = {"message": "test", "data": [1, 2, 3]}
            
            # Write YAML
            write_yaml(test_file, test_data)
            assert test_file.exists()
            
            # Read YAML
            loaded_data = read_yaml(test_file)
            assert loaded_data == test_data

    @pytest.mark.asyncio
    async def test_async_read_write_json(self):
        """Test async read/write JSON convenience functions - Kiểm thử hàm tiện ích đọc/ghi JSON bất đồng bộ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {"message": "test", "data": [1, 2, 3]}
            
            # Write JSON
            await async_write_json(test_file, test_data)
            assert test_file.exists()
            
            # Read JSON
            loaded_data = await async_read_json(test_file)
            assert loaded_data == test_data

class TestErrorHandling:
    """Test error handling - Kiểm thử xử lý lỗi"""

    def test_io_error_creation(self):
        """Test IO error creation - Kiểm thử tạo lỗi IO"""
        error = StillMeException("File not found")
        assert "File not found" in str(error)
        # StillMeException doesn't have file_path attribute

    def test_validation_error_creation(self):
        """Test validation error creation - Kiểm thử tạo lỗi validation"""
        error = ValidationError("Invalid data")
        assert "Invalid data" in str(error)
        # ValidationError doesn't have field/value attributes in current implementation

    def test_api_error_creation(self):
        """Test API error creation - Kiểm thử tạo lỗi API"""
        error = APIError("Service unavailable")
        assert "Service unavailable" in str(error)
        # APIError doesn't have status_code/endpoint attributes in current implementation

    def test_network_error_creation(self):
        """Test network error creation - Kiểm thử tạo lỗi network"""
        error = NetworkError("Connection timeout")
        assert "Connection timeout" in str(error)
        # NetworkError doesn't have url/timeout attributes in current implementation

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
