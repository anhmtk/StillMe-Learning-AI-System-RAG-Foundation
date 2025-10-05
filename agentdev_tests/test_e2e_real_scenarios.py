#!/usr/bin/env python3
"""
End-to-End tests for AgentDev with real scenarios
Tests real code generation, file operations, and validation
"""

import os
import shutil
import subprocess
import tempfile

import pytest

# Import AgentDev modules
from agent_dev.core.agentdev import AgentDev
from agent_dev.fixtures.mock_llm import MockLLMProvider


class TestAgentDevE2E:
    """End-to-End tests for AgentDev"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agentdev = AgentDev()
        self.mock_llm = MockLLMProvider(seed=42)

        # Create test project structure
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.e2e
    def test_fix_calculator_bugs(self):
        """Test fixing bugs in calculator application"""
        # Create calculator with bugs (from dataset)
        calculator_file = os.path.join(self.test_project, "calculator.py")
        with open(calculator_file, "w") as f:
            f.write("""
def add(a, b):
    return a + b + 1  # BUG: off-by-one error

def divide(a, b):
    if b == 0:
        return float('inf')  # BUG: should raise ValueError
    return a / b

def factorial(n):
    if n < 0:
        return -1  # BUG: should raise ValueError
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
""")

        # Test file
        test_file = os.path.join(self.test_project, "test_calculator.py")
        with open(test_file, "w") as f:
            f.write("""
import unittest
from calculator import add, divide, factorial

class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(5, 3), 8)  # This will fail
    
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(10, 0)  # This will fail
    
    def test_factorial_negative(self):
        with self.assertRaises(ValueError):
            factorial(-5)  # This will fail

if __name__ == "__main__":
    unittest.main()
""")

        # Run AgentDev to fix bugs
        task = "Fix the bugs in the calculator functions"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify fixes were applied
        with open(calculator_file) as f:
            fixed_code = f.read()

        # Should fix off-by-one error
        assert "return a + b" in fixed_code  # Fixed version
        assert "return a + b + 1" not in fixed_code  # Buggy version removed

        # Should add proper error handling
        assert "raise ValueError" in fixed_code

        # Run tests to verify fixes
        test_result = subprocess.run(
            ["python", test_file], cwd=self.test_project, capture_output=True, text=True
        )

        # Tests should pass after fixes
        assert test_result.returncode == 0

    @pytest.mark.e2e
    def test_optimize_data_processor(self):
        """Test optimizing data processor performance"""
        # Create inefficient data processor
        processor_file = os.path.join(self.test_project, "data_processor.py")
        with open(processor_file, "w") as f:
            f.write("""
def process_data(data):
    # BUG: O(n²) complexity
    processed = []
    for i, item in enumerate(data):
        for j, other_item in enumerate(data):
            if i != j and item.get('id') == other_item.get('id'):
                item['duplicate'] = True
        processed.append(item)
    return processed

def power(base, exponent):
    # BUG: Inefficient implementation
    result = 1
    for _ in range(int(exponent)):
        result *= base
    return result
""")

        # Run AgentDev to optimize
        task = "Optimize the performance of the data processor"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify optimizations were applied
        with open(processor_file) as f:
            optimized_code = f.read()

        # Should use efficient algorithms
        assert (
            "set(" in optimized_code or "dict(" in optimized_code
        )  # Efficient data structures
        assert "**" in optimized_code  # Efficient power operation

        # Should remove inefficient nested loops
        assert (
            "for i, item in enumerate(data):" not in optimized_code
            or "for j, other_item in enumerate(data):" not in optimized_code
        )

    @pytest.mark.e2e
    def test_add_security_features(self):
        """Test adding security features to application"""
        # Create insecure application
        app_file = os.path.join(self.test_project, "app.py")
        with open(app_file, "w") as f:
            f.write("""
import os
import subprocess

def process_user_input(user_input):
    # BUG: No input validation
    return user_input

def execute_command(command):
    # BUG: Command injection vulnerability
    return subprocess.run(command, shell=True, capture_output=True)

def read_file(filename):
    # BUG: Path traversal vulnerability
    with open(filename, 'r') as f:
        return f.read()
""")

        # Run AgentDev to add security
        task = "Add security features and fix vulnerabilities"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify security features were added
        with open(app_file) as f:
            secured_code = f.read()

        # Should add input validation
        assert "validate" in secured_code.lower() or "sanitize" in secured_code.lower()

        # Should add path validation
        assert "os.path" in secured_code or "pathlib" in secured_code

        # Should add command validation
        assert (
            "shell=False" in secured_code or "validate_command" in secured_code.lower()
        )

    @pytest.mark.e2e
    def test_refactor_legacy_code(self):
        """Test refactoring legacy code"""
        # Create legacy code
        legacy_file = os.path.join(self.test_project, "legacy.py")
        with open(legacy_file, "w") as f:
            f.write("""
# Legacy code with issues
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
        else:
            result.append(0)
    return result

def calculate_average(numbers):
    total = 0
    count = 0
    for num in numbers:
        total += num
        count += 1
    return total / count if count > 0 else 0
""")

        # Run AgentDev to refactor
        task = "Refactor the legacy code to use modern Python practices"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify refactoring was applied
        with open(legacy_file) as f:
            refactored_code = f.read()

        # Should use modern Python features
        assert (
            "list comprehension" in refactored_code.lower()
            or "[" in refactored_code
            and "for" in refactored_code
        )

        # Should add type hints
        assert (
            "def process_data(data: List[int]) -> List[int]:" in refactored_code
            or "typing" in refactored_code
        )

        # Should use built-in functions
        assert "sum(" in refactored_code or "len(" in refactored_code

    @pytest.mark.e2e
    def test_create_test_suite(self):
        """Test creating comprehensive test suite"""
        # Create application without tests
        app_file = os.path.join(self.test_project, "app.py")
        with open(app_file, "w") as f:
            f.write("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")

        # Run AgentDev to create tests
        task = "Create a comprehensive test suite for the application"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify test files were created
        test_files = [f for f in os.listdir(self.test_project) if f.startswith("test_")]
        assert len(test_files) > 0

        # Check test content
        for test_file in test_files:
            test_path = os.path.join(self.test_project, test_file)
            with open(test_path) as f:
                test_content = f.read()

            # Should contain proper test structure
            assert "import unittest" in test_content or "import pytest" in test_content
            assert "def test_" in test_content or "def test" in test_content
            assert "assert" in test_content

        # Run tests to verify they work
        for test_file in test_files:
            test_path = os.path.join(self.test_project, test_file)
            test_result = subprocess.run(
                ["python", "-m", "unittest", test_path],
                cwd=self.test_project,
                capture_output=True,
                text=True,
            )

            # Tests should pass
            assert test_result.returncode == 0

    @pytest.mark.e2e
    def test_merge_conflict_resolution(self):
        """Test resolving merge conflicts"""
        # Create conflicting files
        file1 = os.path.join(self.test_project, "file1.py")
        file2 = os.path.join(self.test_project, "file2.py")

        with open(file1, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
""")

        with open(file2, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b + 1  # Different implementation

def calculate_product(a, b):
    return a * b * 2  # Different implementation
""")

        # Run AgentDev to resolve conflicts
        task = "Resolve the conflicts between the two files"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify conflicts were resolved
        # Should create a merged version or provide resolution strategy
        assert "conflict_resolution" in result or "merged_file" in result

    @pytest.mark.e2e
    def test_performance_optimization(self):
        """Test performance optimization"""
        # Create slow application
        slow_app = os.path.join(self.test_project, "slow_app.py")
        with open(slow_app, "w") as f:
            f.write("""
import time

def slow_function(n):
    # BUG: Inefficient algorithm
    result = 0
    for i in range(n):
        for j in range(n):
            result += i * j
    return result

def fibonacci(n):
    # BUG: Inefficient recursive implementation
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""")

        # Run AgentDev to optimize
        task = "Optimize the performance of the slow application"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify optimizations were applied
        with open(slow_app) as f:
            optimized_code = f.read()

        # Should use efficient algorithms
        assert (
            "memoization" in optimized_code.lower() or "cache" in optimized_code.lower()
        )
        assert "O(n)" in optimized_code or "linear" in optimized_code.lower()

    @pytest.mark.e2e
    def test_error_handling_improvement(self):
        """Test improving error handling"""
        # Create application with poor error handling
        error_app = os.path.join(self.test_project, "error_app.py")
        with open(error_app, "w") as f:
            f.write("""
def divide(a, b):
    return a / b  # BUG: No error handling

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()  # BUG: No error handling

def process_data(data):
    result = []
    for item in data:
        result.append(item['value'])  # BUG: No error handling
    return result
""")

        # Run AgentDev to improve error handling
        task = "Add proper error handling to the application"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify error handling was added
        with open(error_app) as f:
            improved_code = f.read()

        # Should add try-except blocks
        assert "try:" in improved_code
        assert "except" in improved_code

        # Should add specific error handling
        assert (
            "ValueError" in improved_code
            or "FileNotFoundError" in improved_code
            or "KeyError" in improved_code
        )

    @pytest.mark.e2e
    def test_documentation_generation(self):
        """Test generating documentation"""
        # Create application without documentation
        app_file = os.path.join(self.test_project, "app.py")
        with open(app_file, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
""")

        # Run AgentDev to generate documentation
        task = "Generate comprehensive documentation for the application"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify documentation was created
        doc_files = [
            f
            for f in os.listdir(self.test_project)
            if f.endswith((".md", ".rst", ".txt"))
        ]
        assert len(doc_files) > 0

        # Check documentation content
        for doc_file in doc_files:
            doc_path = os.path.join(self.test_project, doc_file)
            with open(doc_path) as f:
                doc_content = f.read()

            # Should contain function documentation
            assert "calculate_sum" in doc_content
            assert "calculate_product" in doc_content
            assert "process_data" in doc_content

    @pytest.mark.e2e
    def test_complete_application_creation(self):
        """Test creating a complete application from scratch"""
        # Run AgentDev to create complete application
        task = "Create a complete web API with authentication, data processing, and error handling"
        result = self.agentdev.execute_task(
            task, project_path=self.test_project, mode="senior"
        )

        assert result is not None
        assert result.get("success", False)

        # Verify application files were created
        app_files = os.listdir(self.test_project)
        assert len(app_files) > 0

        # Should create main application file
        main_files = [f for f in app_files if f.endswith(".py") and "main" in f.lower()]
        assert len(main_files) > 0

        # Should create requirements file
        req_files = [f for f in app_files if f.endswith(".txt") and "req" in f.lower()]
        assert len(req_files) > 0

        # Should create test files
        test_files = [f for f in app_files if f.startswith("test_")]
        assert len(test_files) > 0

        # Should create documentation
        doc_files = [f for f in app_files if f.endswith((".md", ".rst"))]
        assert len(doc_files) > 0


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
