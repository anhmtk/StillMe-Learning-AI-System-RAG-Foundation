# tests/test_smart_gpt_api_manager_v1.py
import pytest
from modules.smart_gpt_api_manager_v1 import SmartGPTAPIManager

def test_class_exists():
    """Kiểm tra class SmartGPTAPIManager tồn tại."""
    manager = SmartGPTAPIManager(model_preferences=["deepseek-coder"])
    assert isinstance(manager, SmartGPTAPIManager)
    assert hasattr(manager, "call_api")
    assert hasattr(manager, "choose_model")

def test_api_call_simulation():
    """Kiểm tra chức năng simulate call."""
    manager = SmartGPTAPIManager(model_preferences=["mock"])
    response = manager.simulate_call("Test prompt")
    assert "Mock response" in response
    assert "Test prompt" in response

def test_choose_model_logic():
    """Kiểm tra logic chọn model."""
    manager = SmartGPTAPIManager(model_preferences=["deepseek-coder", "gpt-4o"])
    
    # Test prompt dài → chọn DeepSeek
    long_prompt = "x" * 4000
    assert manager.choose_model(long_prompt) == "deepseek-coder"
    
    # Test prompt sáng tạo → chọn GPT-4o
    creative_prompt = "Hãy viết một bài thơ về AI"
    assert manager.choose_model(creative_prompt) == "gpt-4o"
    
    # Test fallback
    manager_no_prefs = SmartGPTAPIManager(model_preferences=[])
    assert manager_no_prefs.choose_model("test") == "gpt-3.5-turbo"

def test_usage_analysis():
    """Kiểm tra thống kê sử dụng."""
    manager = SmartGPTAPIManager(model_preferences=["mock"])
    manager.call_api("Test 1")
    manager.call_api("Test 2")
    stats = manager.analyze_usage()
    assert stats["mock"]["total_calls"] == 2