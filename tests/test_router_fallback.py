import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_stub_mode_env(monkeypatch):
    """Test that STILLME_ROUTER_MODE=stub forces stub mode."""
    monkeypatch.setenv("STILLME_ROUTER_MODE", "stub")
    from stillme_core.router_loader import load_router

    r = load_router()
    m = r.choose_model("write code example")
    assert isinstance(m, str) and len(m) > 0
    assert "deepseek-coder" in m  # Should choose code model


def test_auto_falls_back_when_pro_absent(monkeypatch):
    """Test that auto-detection falls back to stub when Pro is not available."""
    monkeypatch.delenv("STILLME_ROUTER_MODE", raising=False)
    # Ensure private module not present
    sys.modules.pop("stillme_private", None)
    sys.modules.pop("stillme_private.plugin", None)

    r = load_router()
    m = r.choose_model("hello")
    assert isinstance(m, str) and len(m) > 0
    assert "llama3" in m  # Should choose default model


def test_force_pro_but_missing(monkeypatch, capsys):
    """Test that forcing pro mode falls back to stub when Pro is not available."""
    monkeypatch.setenv("STILLME_ROUTER_MODE", "pro")
    sys.modules.pop("stillme_private", None)

    r = load_router()  # should fall back to Stub
    m = r.choose_model("hello")
    assert isinstance(m, str) and len(m) > 0
    assert "llama3" in m  # Should fall back to default model


def test_stub_router_heuristics():
    """Test that StubRouter chooses appropriate models for different prompt types."""
    from plugins.private_stub.plugin import StubRouter

    router = StubRouter()

    # Code prompts
    assert "deepseek-coder" in router.choose_model("write a function")
    assert "deepseek-coder" in router.choose_model("```python\nprint('hello')\n```")

    # Image prompts
    assert "llava" in router.choose_model("describe this image")
    assert "llava" in router.choose_model("what's in this photo")

    # Math prompts
    assert "deepseek-math" in router.choose_model("solve this equation")
    assert "deepseek-math" in router.choose_model("calculate statistics")

    # Default prompts
    assert "llama3" in router.choose_model("hello world")
    assert "llama3" in router.choose_model("tell me a story")


def test_empty_prompt():
    """Test handling of empty or None prompts."""

    router = StubRouter()

    assert "llama3" in router.choose_model("")
    assert "llama3" in router.choose_model(None)