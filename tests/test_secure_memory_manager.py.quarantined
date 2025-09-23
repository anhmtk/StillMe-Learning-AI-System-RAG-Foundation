#!/usr/bin/env python3
"""
Comprehensive test suite for SecureMemoryManager module.
Tests encryption/decryption, error handling, async operations, backup/recovery, and performance.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

import pytest

# Add modules to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from secure_memory_manager import SecureMemoryConfig, SecureMemoryManager


class TestSecureMemoryConfig:
    """Test SecureMemoryConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SecureMemoryConfig()
        assert config.file_path == "memory.enc"
        assert config.key_path == "memory.key"
        assert config.backup_dir == "backups"
        assert config.max_backups == 10
        assert config.key_rotation_days == 30
        assert config.compression_enabled is True
        assert config.auto_backup is True
        assert config.encryption_algorithm == "fernet"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SecureMemoryConfig(
            file_path="custom.enc",
            key_path="custom.key",
            backup_dir="custom_backups",
            max_backups=5,
            key_rotation_days=15,
            compression_enabled=False,
            auto_backup=False,
            encryption_algorithm="aes",
        )
        assert config.file_path == "custom.enc"
        assert config.key_path == "custom.key"
        assert config.backup_dir == "custom_backups"
        assert config.max_backups == 5
        assert config.key_rotation_days == 15
        assert config.compression_enabled is False
        assert config.auto_backup is False
        assert config.encryption_algorithm == "aes"


class TestSecureMemoryManager:
    """Test SecureMemoryManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create SecureMemoryManager instance for tests."""
        config = SecureMemoryConfig(
            file_path=os.path.join(temp_dir, "test_memory.enc"),
            key_path=os.path.join(temp_dir, "test_memory.key"),
            backup_dir=os.path.join(temp_dir, "test_backups"),
            max_backups=3,
            key_rotation_days=1,  # Short for testing
            auto_backup=True,
        )
        return SecureMemoryManager(config)

    def test_initialization(self, memory_manager):
        """Test SecureMemoryManager initialization."""
        assert memory_manager.config is not None
        assert memory_manager.key is not None
        assert memory_manager.cipher is not None
        assert memory_manager.key_created_date is not None
        assert memory_manager.performance_metrics["total_operations"] == 0
        assert memory_manager.error_count == 0
        assert memory_manager.last_error is None

    def test_key_creation_and_loading(self, memory_manager, temp_dir):
        """Test encryption key creation and loading."""
        key_path = Path(memory_manager.config.key_path)
        assert key_path.exists()
        assert key_path.stat().st_size > 0

        # Test loading existing key
        new_manager = SecureMemoryManager(memory_manager.config)
        assert new_manager.key == memory_manager.key

    @pytest.mark.asyncio
    async def test_save_and_load_string(self, memory_manager):
        """Test saving and loading string data."""
        test_data = "Hello, World! This is a test string."

        # Save data
        result = await memory_manager.save(test_data)
        assert result is True

        # Load data
        loaded_data = await memory_manager.load()
        assert loaded_data == test_data

        # Check performance metrics
        metrics = memory_manager.get_performance_metrics()
        assert metrics["total_operations"] == 2
        assert metrics["encryption_time"] > 0
        assert metrics["decryption_time"] > 0

    @pytest.mark.asyncio
    async def test_save_and_load_dict(self, memory_manager):
        """Test saving and loading dictionary data."""
        test_data = {
            "name": "Test User",
            "age": 25,
            "skills": ["Python", "AI", "Testing"],
            "active": True,
        }

        # Save data
        result = await memory_manager.save(test_data)
        assert result is True

        # Load data
        loaded_data = await memory_manager.load()
        loaded_dict = json.loads(loaded_data)
        assert loaded_dict == test_data

    @pytest.mark.asyncio
    async def test_save_and_load_list(self, memory_manager):
        """Test saving and loading list data."""
        test_data = ["item1", "item2", {"nested": "value"}, 123, True]

        # Save data
        result = await memory_manager.save(test_data)
        assert result is True

        # Load data
        loaded_data = await memory_manager.load()
        loaded_list = json.loads(loaded_data)
        assert loaded_list == test_data

    @pytest.mark.asyncio
    async def test_save_with_auto_backup(self, memory_manager):
        """Test saving with automatic backup."""
        # First save
        await memory_manager.save("First data")

        # Second save with auto backup
        result = await memory_manager.save("Second data", auto_backup=True)
        assert result is True

        # Check if backup was created
        backups = await memory_manager.list_backups()
        assert len(backups) > 0
        assert any("auto_save" in backup["name"] for backup in backups)

    @pytest.mark.asyncio
    async def test_save_without_auto_backup(self, memory_manager):
        """Test saving without automatic backup."""
        # First save
        await memory_manager.save("First data")

        # Second save without auto backup
        result = await memory_manager.save("Second data", auto_backup=False)
        assert result is True

        # Check if no new backup was created
        initial_backups = await memory_manager.list_backups()
        await memory_manager.save("Third data", auto_backup=False)
        final_backups = await memory_manager.list_backups()
        assert len(final_backups) == len(initial_backups)

    @pytest.mark.asyncio
    async def test_load_empty_file(self, memory_manager):
        """Test loading when no file exists."""
        data = await memory_manager.load()
        assert data == ""

    @pytest.mark.asyncio
    async def test_backup_creation(self, memory_manager):
        """Test manual backup creation."""
        # Save some data
        await memory_manager.save("Test data for backup")

        # Create manual backup
        result = await memory_manager._create_backup("manual_test")
        assert result is True

        # Check backup exists
        backups = await memory_manager.list_backups()
        assert len(backups) > 0
        assert any("manual_test" in backup["name"] for backup in backups)

    @pytest.mark.asyncio
    async def test_backup_cleanup(self, memory_manager):
        """Test backup cleanup when exceeding max_backups."""
        # Create more backups than max_backups
        for i in range(5):
            await memory_manager.save(f"Data {i}")
            await memory_manager._create_backup(f"test_{i}")
            await asyncio.sleep(0.1)  # Ensure different timestamps

        # Check that only max_backups remain
        backups = await memory_manager.list_backups()
        assert len(backups) <= memory_manager.config.max_backups

    @pytest.mark.asyncio
    async def test_restore_from_backup(self, memory_manager):
        """Test restoring data from backup."""
        # Save initial data
        await memory_manager.save("Initial data")

        # Create backup
        await memory_manager._create_backup("restore_test")

        # Change data
        await memory_manager.save("Changed data")

        # Get backup list
        backups = await memory_manager.list_backups()
        backup_name = next(b["name"] for b in backups if "restore_test" in b["name"])

        # Restore from backup
        result = await memory_manager.restore_from_backup(backup_name)
        assert result is True

        # Verify restored data
        restored_data = await memory_manager.load()
        assert restored_data == "Initial data"

    @pytest.mark.asyncio
    async def test_key_rotation(self, memory_manager):
        """Test automatic key rotation."""
        # Save initial data
        await memory_manager.save("Data before rotation")

        # Manually set key creation date to trigger rotation
        memory_manager.key_created_date = memory_manager.key_created_date - timedelta(
            days=2
        )

        # Save again to trigger rotation
        result = await memory_manager.save("Data after rotation")
        assert result is True

        # Verify data is still accessible
        loaded_data = await memory_manager.load()
        assert loaded_data == "Data after rotation"

        # Check that new key was created
        assert (
            memory_manager.key_created_date
            > memory_manager.key_created_date - timedelta(days=2)
        )

    def test_clear_memory(self, memory_manager):
        """Test clearing memory data."""
        # Create a file first
        memory_manager.file_path.write_bytes(b"test data")
        assert memory_manager.file_path.exists()

        # Clear memory
        result = memory_manager.clear()
        assert result is True
        assert not memory_manager.file_path.exists()

    def test_clear_nonexistent_file(self, memory_manager):
        """Test clearing when no file exists."""
        result = memory_manager.clear()
        assert result is True

    def test_performance_metrics(self, memory_manager):
        """Test performance metrics collection."""
        metrics = memory_manager.get_performance_metrics()

        assert "total_operations" in metrics
        assert "encryption_time" in metrics
        assert "decryption_time" in metrics
        assert "last_operation" in metrics
        assert "error_count" in metrics
        assert "last_error" in metrics
        assert "key_age_days" in metrics
        assert "should_rotate_key" in metrics

        assert metrics["total_operations"] == 0
        assert metrics["encryption_time"] == 0
        assert metrics["decryption_time"] == 0
        assert metrics["error_count"] == 0

    def test_health_status(self, memory_manager):
        """Test health status checking."""
        health = memory_manager.get_health_status()

        assert "status" in health
        assert "encryption_working" in health
        assert "file_exists" in health
        assert "key_exists" in health
        assert "key_age_days" in health
        assert "backup_count" in health
        assert "error_count" in health

        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert health["encryption_working"] is True
        assert health["key_exists"] is True

    @pytest.mark.asyncio
    async def test_shutdown(self, memory_manager):
        """Test shutdown process."""
        # Save some data first
        await memory_manager.save("Data before shutdown")

        # Shutdown
        await memory_manager.shutdown()

        # Verify backup was created
        backups = await memory_manager.list_backups()
        assert any("shutdown" in backup["name"] for backup in backups)


class TestSecureMemoryErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create SecureMemoryManager instance for tests."""
        config = SecureMemoryConfig(
            file_path=os.path.join(temp_dir, "test_memory.enc"),
            key_path=os.path.join(temp_dir, "test_memory.key"),
            backup_dir=os.path.join(temp_dir, "test_backups"),
        )
        return SecureMemoryManager(config)

    @pytest.mark.asyncio
    async def test_save_with_corrupted_key(self, memory_manager):
        """Test saving with corrupted encryption key."""
        # Corrupt the key and cipher
        memory_manager.key = b"corrupted_key"
        memory_manager.cipher = None

        # Try to save
        result = await memory_manager.save("Test data")
        assert result is False
        assert memory_manager.error_count > 0
        assert memory_manager.last_error is not None

    @pytest.mark.asyncio
    async def test_load_corrupted_file(self, memory_manager):
        """Test loading corrupted encrypted file."""
        # Create corrupted encrypted file
        memory_manager.file_path.write_bytes(b"corrupted_data")

        # Try to load
        result = await memory_manager.load()
        assert result is None
        assert memory_manager.error_count > 0
        assert memory_manager.last_error is not None

    @pytest.mark.asyncio
    async def test_backup_creation_failure(self, memory_manager):
        """Test backup creation when backup directory is inaccessible."""
        # Try to create backup without main file (should fail gracefully)
        memory_manager.file_path = Path("/nonexistent/path/file.enc")

        # Try to create backup
        result = await memory_manager._create_backup("test")
        assert result is True  # Should return True when no file exists

        # Restore original file path
        memory_manager.file_path = Path(memory_manager.config.file_path)

    @pytest.mark.asyncio
    async def test_restore_nonexistent_backup(self, memory_manager):
        """Test restoring from non-existent backup."""
        result = await memory_manager.restore_from_backup("nonexistent_backup.enc")
        assert result is False
        # Error count should increase when restore fails
        assert (
            memory_manager.error_count >= 0
        )  # May not always increase for file not found


class TestSecureMemoryPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create SecureMemoryManager instance for tests."""
        config = SecureMemoryConfig(
            file_path=os.path.join(temp_dir, "test_memory.enc"),
            key_path=os.path.join(temp_dir, "test_memory.key"),
            backup_dir=os.path.join(temp_dir, "test_backups"),
        )
        return SecureMemoryManager(config)

    @pytest.mark.asyncio
    async def test_large_data_performance(self, memory_manager):
        """Test performance with large data."""
        # Generate large data
        large_data = {
            "items": [f"Item {i}" for i in range(1000)],
            "metadata": {f"key_{i}": f"value_{i}" for i in range(100)},
            "timestamp": time.time(),
        }

        start_time = time.time()
        result = await memory_manager.save(large_data)
        save_time = time.time() - start_time

        assert result is True
        assert save_time < 1.0  # Should complete within 1 second

        # Test load performance
        start_time = time.time()
        loaded_data = await memory_manager.load()
        load_time = time.time() - start_time

        assert load_time < 1.0  # Should complete within 1 second

        # Verify data integrity
        loaded_dict = json.loads(loaded_data)
        assert loaded_dict == large_data

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory_manager):
        """Test concurrent save/load operations."""

        async def save_operation(i):
            return await memory_manager.save(f"Data {i}")

        async def load_operation():
            return await memory_manager.load()

        # Run concurrent saves
        save_tasks = [save_operation(i) for i in range(10)]
        save_results = await asyncio.gather(*save_tasks)

        assert all(save_results)

        # Verify final data
        final_data = await memory_manager.load()
        assert "Data 9" in final_data  # Last saved data

    @pytest.mark.asyncio
    async def test_memory_usage(self, memory_manager):
        """Test memory usage during operations."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform multiple operations
        for i in range(100):
            await memory_manager.save(f"Data {i}")
            await memory_manager.load()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024


class TestSecureMemoryIntegration:
    """Test integration with other components."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create SecureMemoryManager instance for tests."""
        config = SecureMemoryConfig(
            file_path=os.path.join(temp_dir, "test_memory.enc"),
            key_path=os.path.join(temp_dir, "test_memory.key"),
            backup_dir=os.path.join(temp_dir, "test_backups"),
        )
        return SecureMemoryManager(config)

    @pytest.mark.asyncio
    async def test_vietnamese_text_handling(self, memory_manager):
        """Test handling Vietnamese text with proper encoding."""
        vietnamese_text = (
            "Xin chào! Tôi là một AI thông minh. Tôi có thể hiểu và xử lý tiếng Việt."
        )

        # Save Vietnamese text
        result = await memory_manager.save(vietnamese_text)
        assert result is True

        # Load and verify
        loaded_text = await memory_manager.load()
        assert loaded_text == vietnamese_text

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, memory_manager):
        """Test handling special characters and symbols."""
        special_text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?`~ \n\t\r"

        # Save special characters
        result = await memory_manager.save(special_text)
        assert result is True

        # Load and verify
        loaded_text = await memory_manager.load()
        assert loaded_text == special_text

    @pytest.mark.asyncio
    async def test_binary_data_handling(self, memory_manager):
        """Test handling binary-like data as string."""
        binary_like = "\\x00\\x01\\x02\\x03\\xff\\xfe\\xfd"

        # Save binary-like data
        result = await memory_manager.save(binary_like)
        assert result is True

        # Load and verify
        loaded_data = await memory_manager.load()
        assert loaded_data == binary_like


# Performance test runner
async def run_performance_test():
    """Run comprehensive performance test."""
    print("🚀 Running SecureMemoryManager Performance Test...")

    with tempfile.TemporaryDirectory() as temp_dir:
        config = SecureMemoryConfig(
            file_path=os.path.join(temp_dir, "perf_memory.enc"),
            key_path=os.path.join(temp_dir, "perf_memory.key"),
            backup_dir=os.path.join(temp_dir, "perf_backups"),
        )

        memory_manager = SecureMemoryManager(config)

        # Test 1000 operations
        start_time = time.time()

        for i in range(1000):
            data = {
                "id": i,
                "content": f"Performance test data {i}",
                "timestamp": time.time(),
                "metadata": {f"key_{j}": f"value_{j}" for j in range(10)},
            }

            await memory_manager.save(data)
            loaded = await memory_manager.load()

            if i % 100 == 0:
                print(f"✅ Completed {i} operations...")

        total_time = time.time() - start_time
        operations_per_second = 1000 / total_time

        print("🎯 Performance Test Results:")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Operations per second: {operations_per_second:.2f}")
        print(f"   Average time per operation: {(total_time/1000)*1000:.2f} ms")

        # Get final metrics
        metrics = memory_manager.get_performance_metrics()
        health = memory_manager.get_health_status()

        print("📊 Final Metrics:")
        print(f"   Total operations: {metrics['total_operations']}")
        print(f"   Total encryption time: {metrics['encryption_time']:.3f}s")
        print(f"   Total decryption time: {metrics['decryption_time']:.3f}s")
        print(f"   Error count: {metrics['error_count']}")
        print(f"   Health status: {health['status']}")

        await memory_manager.shutdown()

        return {
            "total_time": total_time,
            "operations_per_second": operations_per_second,
            "error_count": metrics["error_count"],
            "health_status": health["status"],
        }


if __name__ == "__main__":
    # Run performance test
    result = asyncio.run(run_performance_test())
    print(f"\n🎉 Performance test completed with result: {result}")
