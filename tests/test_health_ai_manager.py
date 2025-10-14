# tests/test_health_ai_manager.py
from stillme_core.ai_manager import health, set_mode


def test_health_llama3():
    set_mode("fast")  # -> llama3:8b
    info = health()
    assert isinstance(info, dict)
    assert info.get("ollama_up") is True
    assert info.get("model_present") is True
    assert info.get("tiny_generate_ok") is True