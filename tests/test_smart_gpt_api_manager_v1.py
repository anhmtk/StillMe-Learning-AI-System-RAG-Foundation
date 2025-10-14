# tests/test_smart_gpt_api_manager_v1.py
from stillme_core.modules.api_provider_manager import UnifiedAPIManager


def test_class_exists():
    """Kiểm tra class UnifiedAPIManager tồn tại."""
    manager = UnifiedAPIManager(model_preferences=["deepseek-coder"])
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