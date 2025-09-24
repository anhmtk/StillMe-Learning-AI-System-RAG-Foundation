"""
Test suite for Multi-Modal Clarification - Phase 3

Tests for VisualClarifier, CodeClarifier, TextClarifier, and MultiModalClarifier
"""

import pytest
import base64
import io
from PIL import Image
from stillme_core.modules.multi_modal_clarification import (
    VisualClarifier, CodeClarifier, TextClarifier, MultiModalClarifier,
    MultiModalResult
)

class TestVisualClarifier:
    """Test VisualClarifier functionality"""
    
    @pytest.fixture
    def visual_clarifier(self):
        """Create a VisualClarifier instance for testing"""
        config = {
            "max_image_size_mb": 10,
            "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
            "image_analysis": "stub"
        }
        return VisualClarifier(config)
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Create a sample image for testing"""
        # Create a simple 100x100 red image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_visual_clarifier_initialization(self, visual_clarifier):
        """Test VisualClarifier initialization"""
        assert visual_clarifier is not None
        assert visual_clarifier.max_size_mb == 10
        assert "png" in visual_clarifier.supported_formats
        assert visual_clarifier.analysis_mode == "stub"
    
    def test_image_validation_valid(self, visual_clarifier, sample_image_bytes):
        """Test image validation with valid image"""
        validation = visual_clarifier._validate_image(sample_image_bytes)
        assert validation["valid"] is True
        assert validation["format"] == "png"
        assert validation["size"] == (100, 100)
        assert validation["size_mb"] < 1.0
    
    def test_image_validation_too_large(self, visual_clarifier):
        """Test image validation with oversized image"""
        # Create a large image (simulate)
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        validation = visual_clarifier._validate_image(large_data)
        assert validation["valid"] is False
        assert "too large" in validation["error"]
    
    def test_image_validation_invalid_format(self, visual_clarifier):
        """Test image validation with invalid format"""
        invalid_data = b"not an image"
        validation = visual_clarifier._validate_image(invalid_data)
        assert validation["valid"] is False
        assert "Invalid image data" in validation["error"]
    
    def test_stub_analysis_wide_image(self, visual_clarifier):
        """Test stub analysis for wide image"""
        metadata = {"size": (200, 50), "format": "png", "size_mb": 0.1}
        result = visual_clarifier._stub_analysis(metadata)
        
        assert "diagram" in result["question"].lower() or "chart" in result["question"].lower()
        assert len(result["options"]) > 0
        assert result["confidence"] > 0.5
        assert "diagram" in result["detected_objects"]
    
    def test_stub_analysis_tall_image(self, visual_clarifier):
        """Test stub analysis for tall image"""
        metadata = {"size": (50, 200), "format": "png", "size_mb": 0.1}
        result = visual_clarifier._stub_analysis(metadata)
        
        assert "document" in result["question"].lower() or "code" in result["question"].lower()
        assert len(result["options"]) > 0
        assert result["confidence"] > 0.5
        assert "document" in result["detected_objects"]
    
    def test_analyze_valid_image(self, visual_clarifier, sample_image_bytes):
        """Test full analysis with valid image"""
        result = visual_clarifier.analyze(sample_image_bytes)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "image"
        assert result.question is not None
        assert len(result.options) > 0
        assert result.confidence > 0.5
        assert result.domain == "visual"
        assert result.metadata is not None
    
    def test_analyze_invalid_image(self, visual_clarifier):
        """Test analysis with invalid image"""
        result = visual_clarifier.analyze(b"invalid image data")
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "image"
        assert "validation failed" in result.question.lower()
        assert result.confidence > 0.5

class TestCodeClarifier:
    """Test CodeClarifier functionality"""
    
    @pytest.fixture
    def code_clarifier(self):
        """Create a CodeClarifier instance for testing"""
        config = {
            "code_analysis": "ast",
            "code_languages": ["python", "javascript", "typescript", "java", "cpp", "go", "rust"]
        }
        return CodeClarifier(config)
    
    def test_code_clarifier_initialization(self, code_clarifier):
        """Test CodeClarifier initialization"""
        assert code_clarifier is not None
        assert code_clarifier.analysis_mode == "ast"
        assert "python" in code_clarifier.supported_languages
    
    def test_detect_language_python(self, code_clarifier):
        """Test Python language detection"""
        python_code = "def hello_world():\n    print('Hello, World!')"
        language = code_clarifier._detect_language(python_code)
        assert language == "python"
    
    def test_detect_language_javascript(self, code_clarifier):
        """Test JavaScript language detection"""
        js_code = "function helloWorld() {\n    console.log('Hello, World!');\n}"
        language = code_clarifier._detect_language(js_code)
        assert language == "javascript"
    
    def test_detect_language_typescript(self, code_clarifier):
        """Test TypeScript language detection"""
        ts_code = "interface User {\n    name: string;\n    age: number;\n}"
        language = code_clarifier._detect_language(ts_code)
        assert language == "typescript"
    
    def test_detect_language_unknown(self, code_clarifier):
        """Test unknown language detection"""
        unknown_code = "some random text without clear language indicators"
        language = code_clarifier._detect_language(unknown_code)
        assert language == "unknown"
    
    def test_analyze_python_ast_valid(self, code_clarifier):
        """Test Python AST analysis with valid code"""
        python_code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.result = 0
"""
        analysis = code_clarifier._analyze_python_ast(python_code)
        
        assert analysis["valid"] is True
        assert len(analysis["functions"]) == 1
        assert len(analysis["classes"]) == 1
        assert analysis["functions"][0]["name"] == "calculate_sum"
        assert analysis["classes"][0]["name"] == "Calculator"
    
    def test_analyze_python_ast_syntax_error(self, code_clarifier):
        """Test Python AST analysis with syntax error"""
        invalid_code = "def invalid_syntax(\n    return 42"
        analysis = code_clarifier._analyze_python_ast(invalid_code)
        
        assert analysis["valid"] is False
        assert "Syntax error" in analysis["error"]
    
    def test_generate_code_question_single_function(self, code_clarifier):
        """Test question generation for single function"""
        analysis = {
            "valid": True,
            "functions": [{"name": "calculate_sum", "args": ["a", "b"], "line": 1}],
            "classes": []
        }
        result = code_clarifier._generate_code_question(analysis, "python")
        
        assert "calculate_sum" in result["question"]
        assert len(result["options"]) > 0
        assert result["confidence"] > 0.5
        assert "Review the function" in result["suggestions"]
    
    def test_generate_code_question_multiple_functions(self, code_clarifier):
        """Test question generation for multiple functions"""
        analysis = {
            "valid": True,
            "functions": [
                {"name": "func1", "args": [], "line": 1},
                {"name": "func2", "args": [], "line": 5}
            ],
            "classes": []
        }
        result = code_clarifier._generate_code_question(analysis, "python")
        
        assert "2 functions" in result["question"]
        assert len(result["options"]) >= 2
        assert result["confidence"] > 0.5
    
    def test_generate_code_question_syntax_error(self, code_clarifier):
        """Test question generation for syntax error"""
        analysis = {
            "valid": False,
            "error": "Syntax error: invalid syntax"
        }
        result = code_clarifier._generate_code_question(analysis, "python")
        
        assert "syntax error" in result["question"].lower()
        assert "Fix syntax error" in result["options"]
        assert result["confidence"] > 0.8
    
    def test_analyze_python_code(self, code_clarifier):
        """Test full analysis with Python code"""
        python_code = "def hello():\n    print('Hello')"
        result = code_clarifier.analyze(python_code)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "code"
        assert result.domain == "code"
        assert "hello" in result.question
        assert result.confidence > 0.5
        assert result.metadata["language"] == "python"
    
    def test_analyze_javascript_code(self, code_clarifier):
        """Test full analysis with JavaScript code"""
        js_code = "function greet(name) {\n    return `Hello, ${name}!`;\n}"
        result = code_clarifier.analyze(js_code)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "code"
        assert result.domain == "code"
        assert result.metadata["language"] == "javascript"

class TestTextClarifier:
    """Test TextClarifier functionality"""
    
    @pytest.fixture
    def text_clarifier(self):
        """Create a TextClarifier instance for testing"""
        config = {"text_analysis": "enhanced"}
        return TextClarifier(config, context_aware_clarifier=None)
    
    def test_text_clarifier_initialization(self, text_clarifier):
        """Test TextClarifier initialization"""
        assert text_clarifier is not None
        assert text_clarifier.analysis_mode == "enhanced"
    
    def test_enhanced_text_analysis_web_domain(self, text_clarifier):
        """Test enhanced text analysis for web domain"""
        text = "I want to build a website with React and Node.js"
        analysis = text_clarifier._enhanced_text_analysis(text)
        
        assert "web" in analysis["domains"]
        assert "create" in analysis["intents"]
        assert analysis["has_technical_terms"] is True
    
    def test_enhanced_text_analysis_data_domain(self, text_clarifier):
        """Test enhanced text analysis for data domain"""
        text = "I need to analyze CSV data and create visualizations"
        analysis = text_clarifier._enhanced_text_analysis(text)
        
        assert "data" in analysis["domains"]
        assert "create" in analysis["intents"]
        assert analysis["has_technical_terms"] is True
    
    def test_enhanced_text_analysis_multiple_domains(self, text_clarifier):
        """Test enhanced text analysis with multiple domains"""
        text = "I want to optimize my web application performance and add security features"
        analysis = text_clarifier._enhanced_text_analysis(text)
        
        assert "web" in analysis["domains"]
        assert "performance" in analysis["domains"]
        assert "security" in analysis["domains"]
        assert "optimize" in analysis["intents"]
    
    def test_analyze_web_text(self, text_clarifier):
        """Test full analysis with web-related text"""
        text = "Build a web application"
        result = text_clarifier.analyze(text)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "text"
        assert result.domain == "web"
        assert result.question is not None
        assert len(result.options) > 0
    
    def test_analyze_generic_text(self, text_clarifier):
        """Test full analysis with generic text"""
        text = "Help me with something"
        result = text_clarifier.analyze(text)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert result.input_type == "text"
        assert result.domain == "generic"
        assert "more details" in result.question.lower()

class TestMultiModalClarifier:
    """Test MultiModalClarifier functionality"""
    
    @pytest.fixture
    def multi_modal_clarifier(self):
        """Create a MultiModalClarifier instance for testing"""
        config = {
            "enabled": True,
            "max_image_size_mb": 10,
            "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
            "image_analysis": "stub",
            "code_analysis": "ast",
            "text_analysis": "enhanced"
        }
        return MultiModalClarifier(config, context_aware_clarifier=None)
    
    def test_multi_modal_clarifier_initialization(self, multi_modal_clarifier):
        """Test MultiModalClarifier initialization"""
        assert multi_modal_clarifier is not None
        assert multi_modal_clarifier.enabled is True
        assert multi_modal_clarifier.visual_clarifier is not None
        assert multi_modal_clarifier.code_clarifier is not None
        assert multi_modal_clarifier.text_clarifier is not None
    
    def test_detect_input_type_text(self, multi_modal_clarifier):
        """Test input type detection for text"""
        text = "Hello, how are you?"
        input_type = multi_modal_clarifier._detect_input_type(text)
        assert input_type == "text"
    
    def test_detect_input_type_code(self, multi_modal_clarifier):
        """Test input type detection for code"""
        code = "def hello():\n    print('Hello')"
        input_type = multi_modal_clarifier._detect_input_type(code)
        assert input_type == "code"
    
    def test_detect_input_type_mixed(self, multi_modal_clarifier):
        """Test input type detection for mixed content"""
        mixed = "Here's some code:\n```python\ndef hello():\n    print('Hello')\n```\nAnd here's an image: image.png"
        input_type = multi_modal_clarifier._detect_input_type(mixed)
        assert input_type == "mixed"
    
    def test_extract_code_blocks(self, multi_modal_clarifier):
        """Test code block extraction"""
        content = "Here's some code:\n```python\ndef hello():\n    print('Hello')\n```\nAnd more: def world(): pass"
        code_blocks = multi_modal_clarifier._extract_code_blocks(content)
        
        assert len(code_blocks) >= 1
        assert "def hello():" in code_blocks[0]
    
    def test_analyze_text_input(self, multi_modal_clarifier):
        """Test analysis with text input"""
        text = "I want to build a web application"
        result = multi_modal_clarifier.analyze(text)
        
        assert isinstance(result, MultiModalResult)
        assert result.input_type == "text"
        assert result.needs_clarification is True
    
    def test_analyze_code_input(self, multi_modal_clarifier):
        """Test analysis with code input"""
        code = "def calculate(x, y):\n    return x + y"
        result = multi_modal_clarifier.analyze(code)
        
        assert isinstance(result, MultiModalResult)
        assert result.input_type == "code"
        assert result.needs_clarification is True
        assert "calculate" in result.question
    
    def test_analyze_mixed_input(self, multi_modal_clarifier):
        """Test analysis with mixed input"""
        mixed = "Here's my code:\n```python\ndef hello():\n    print('Hello')\n```\nAnd an image: test.png"
        result = multi_modal_clarifier.analyze(mixed)
        
        assert isinstance(result, MultiModalResult)
        assert result.input_type == "mixed"
        assert result.needs_clarification is True
        assert "both code and images" in result.question.lower()
        assert result.metadata["mixed_content"] is True
    
    def test_analyze_disabled(self, multi_modal_clarifier):
        """Test analysis when disabled"""
        multi_modal_clarifier.enabled = False
        result = multi_modal_clarifier.analyze("test input")
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is False
        assert result.reasoning == "Multi-modal clarification disabled"
    
    def test_analyze_error_handling(self, multi_modal_clarifier):
        """Test error handling in analysis"""
        # This should not crash
        result = multi_modal_clarifier.analyze(None)
        
        assert isinstance(result, MultiModalResult)
        assert result.needs_clarification is True
        assert "error" in result.reasoning.lower()

class TestMultiModalIntegration:
    """Integration tests for multi-modal clarification"""
    
    @pytest.fixture
    def full_clarifier(self):
        """Create a full MultiModalClarifier with all components"""
        config = {
            "enabled": True,
            "max_image_size_mb": 10,
            "supported_image_formats": ["png", "jpg"],
            "image_analysis": "stub",
            "code_analysis": "ast",
            "text_analysis": "enhanced",
            "code_languages": ["python", "javascript"]
        }
        return MultiModalClarifier(config)
    
    def test_full_workflow_text(self, full_clarifier):
        """Test complete workflow with text input"""
        context = {
            "user_id": "test_user",
            "conversation_history": [],
            "project_context": {"files": ["app.py"], "extensions": [".py"]}
        }
        
        result = full_clarifier.analyze("Build a web application", context)
        
        assert result.needs_clarification is True
        assert result.input_type == "text"
        assert result.domain == "web"
        assert result.question is not None
        assert len(result.options) > 0
    
    def test_full_workflow_code(self, full_clarifier):
        """Test complete workflow with code input"""
        context = {
            "user_id": "test_user",
            "conversation_history": [],
            "project_context": {"files": ["main.py"], "extensions": [".py"]}
        }
        
        code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
        result = full_clarifier.analyze(code, context)
        
        assert result.needs_clarification is True
        assert result.input_type == "code"
        assert result.domain == "code"
        assert "process_data" in result.question
        assert result.metadata["language"] == "python"
    
    def test_performance_large_input(self, full_clarifier):
        """Test performance with large input"""
        large_code = "def func():\n    pass\n" * 1000  # 1000 functions
        
        import time
        start_time = time.time()
        result = full_clarifier.analyze(large_code)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0  # 5 seconds max
        assert result.needs_clarification is True
        assert result.input_type == "code"
