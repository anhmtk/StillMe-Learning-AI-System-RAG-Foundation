# tests/test_smart_gpt_api_manager_v1.py
from stillme_core.modules.api_provider_manager import UnifiedAPIManager


def test_class_exists():
    """Kiểm tra class UnifiedAPIManager tồn tại."""
    manager = UnifiedAPIManager(model_preferences=["deepseek-chat"])
    assert isinstance(manager, UnifiedAPIManager)
    assert hasattr(manager, "call_api")
    assert hasattr(manager, "choose_model")


def test_api_call_simulation():
    """Kiểm tra chức năng simulate call."""
    manager = UnifiedAPIManager(model_preferences=["mock"])
    response = manager.simulate_call("Test prompt")
    assert "Mock response" in response
    assert "Test prompt" in response


def test_choose_model_logic():
    """Kiểm tra logic chọn model."""
    manager = UnifiedAPIManager(model_preferences=["deepseek-coder", "gpt-4o"])

    # Test prompt dài → chọn DeepSeek
    long_prompt = "x" * 4000
    assert manager.choose_model(long_prompt) == "deepseek-coder"

    # Test prompt sáng tạo → chọn GPT-4o
    creative_prompt = "Hãy viết một bài thơ về AI"
    assert manager.choose_model(creative_prompt) == "gpt-4o"

    # Test fallback
    manager_no_prefs = UnifiedAPIManager(model_preferences=[])
    assert manager_no_prefs.choose_model("test") == "gpt-3.5-turbo"


def test_translation_basic():
    """Test basic translation functionality"""
    import pytest

    try:
        manager = UnifiedAPIManager()

        # Test same language (no translation needed)
        result = manager.translate("Hello", "en", "en")
        assert result["text"] == "Hello"
        assert result["engine"] == "none"
        assert result["confidence"] == 1.0

        # Test empty text
        result = manager.translate("", "en", "vi")
        assert result["text"] == ""
        assert result["engine"] == "none"
        assert result["confidence"] == 1.0

    except ImportError:
        pytest.skip("transformers not available")


def test_translation_code_preservation():
    """Test that code blocks and URLs are preserved during translation"""

    try:
        manager = UnifiedAPIManager()

        # Test code block masking
        text_with_code = "Here's Python code: ```python\nprint('hello')\n``` and a URL: https://example.com"
        masked, code_blocks, urls = manager._mask_code_and_urls(text_with_code)

        assert "CODE_BLOCK_PLACEHOLDER" in masked
        assert "URL_PLACEHOLDER" in masked
        assert len(code_blocks) == 1
        assert len(urls) == 1
        assert "print('hello')" in code_blocks[0]
        assert "https://example.com" in urls[0]

        # Test unmasking
        restored = manager._unmask_code_and_urls(masked, code_blocks, urls)
        assert "print('hello')" in restored
        assert "https://example.com" in restored

    except ImportError:
        pytest.skip("transformers not available")


def test_translation_confidence_evaluation():
    """Test translation confidence evaluation"""

    try:
        manager = UnifiedAPIManager()

        # Test high confidence (good length ratio)
        confidence = manager._evaluate_translation_confidence(
            "Hello", "Xin chào", "en", "vi"
        )
        assert confidence > 0.5

        # Test low confidence (bad length ratio)
        confidence = manager._evaluate_translation_confidence("Hello", "Hi", "en", "vi")
        assert confidence < 0.5

        # Test same text (should be low confidence for different languages)
        confidence = manager._evaluate_translation_confidence(
            "Hello", "Hello", "en", "vi"
        )
        assert confidence == 0.2

    except ImportError:
        pytest.skip("transformers not available")


def test_usage_analysis():
    """Kiểm tra thống kê sử dụng."""
    manager = UnifiedAPIManager(model_preferences=["mock"])

    # Gọi simulate_call để test
    response1 = manager.simulate_call("Test 1")
    response2 = manager.simulate_call("Test 2")

    # Kiểm tra response
    assert "Mock response" in response1
    assert "Mock response" in response2

    # Kiểm tra usage stats (có thể rỗng vì simulate_call không log)
    stats = manager.analyze_usage()
    assert isinstance(stats, dict)