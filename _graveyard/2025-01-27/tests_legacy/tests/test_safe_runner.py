"""
Test suite for SafeRunner module

Tests the safe code execution functionality with various scenarios.
"""

import pytest

from stillme_core.core.safe_runner import SafeRunner


class TestSafeRunner:
    """Test cases for SafeRunner"""

    @pytest.fixture
    async def safe_runner(self):
        """Create SafeRunner instance for testing"""
        runner = SafeRunner()
        await runner.initialize()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    async def test_safe_code_execution(self, safe_runner):
        """Test safe code execution"""
        code = """
print("Hello, World!")
result = 2 + 2
print(f"Result: {result}")
"""
        result = await safe_runner.run_safe(code)

        assert result["ok"] is True
        assert "Hello, World!" in result["output"]
        assert "Result: 4" in result["output"]
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_dangerous_import_detection(self, safe_runner):
        """Test detection of dangerous imports"""
        code = """
import subprocess
print("This should not execute")
"""
        result = await safe_runner.run_safe(code)

        assert result["ok"] is False
        assert "Code validation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_file_system_operation_detection(self, safe_runner):
        """Test detection of file system operations"""
        code = """
with open("test.txt", "w") as f:
    f.write("This should not execute")
"""
        result = await safe_runner.run_safe(code)

        assert result["ok"] is False
        assert "File system operation detected" in result["error"]

    @pytest.mark.asyncio
    async def test_syntax_error_handling(self, safe_runner):
        """Test handling of syntax errors"""
        code = """
print("Hello"
# Missing closing parenthesis
"""
        result = await safe_runner.run_safe(code)

        assert result["ok"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, safe_runner):
        """Test handling of runtime errors"""
        code = """
x = 1 / 0  # Division by zero
"""
        result = await safe_runner.run_safe(code)

        assert result["ok"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_module_info(self, safe_runner):
        """Test module information"""
        info = safe_runner.module_info

        assert info.name == "SafeRunner"
        assert info.version == "1.0.0"
        assert "sandboxing" in info.description
        assert info.author == "StillMe AI Team"

    @pytest.mark.asyncio
    async def test_configuration(self):
        """Test configuration handling"""
        config = {
            "timeout": 10,
            "max_memory_mb": 256,
            "allowed_imports": ["math", "json"],
        }

        runner = SafeRunner(config)
        await runner.initialize()

        assert runner.timeout == 10
        assert runner.max_memory_mb == 256
        assert "math" in runner.allowed_imports

        await runner.cleanup()

    @pytest.mark.asyncio
    async def test_process_method(self, safe_runner):
        """Test process method with different input types"""
        # Test with string input
        result1 = await safe_runner.process("print('Hello from process')")
        assert result1["ok"] is True

        # Test with dict input
        result2 = await safe_runner.process({"code": "print('Hello from dict')"})
        assert result2["ok"] is True

        # Test with invalid input
        with pytest.raises(ValueError):
            await safe_runner.process({"invalid": "input"})

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure handling"""
        # This test would require mocking tempfile.mkdtemp to fail
        # For now, we'll test the normal case
        runner = SafeRunner()
        result = await runner.initialize()
        assert result is True
        await runner.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup(self, safe_runner):
        """Test cleanup functionality"""
        # Ensure runner is initialized
        assert safe_runner._temp_dir is not None

        # Cleanup should not raise exceptions
        await safe_runner.cleanup()

        # Status should be stopped
        assert safe_runner.status.value == "stopped"
