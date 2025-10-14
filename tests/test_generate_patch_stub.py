from stillme_core.ai_manager import AIManager
from stillme_core.plan_types import PlanItem


def test_generate_patch_returns_string(monkeypatch):
    ai = AIManager()
    item = PlanItem(id="1", title="Demo", diff_hint="", target="a.py")
    # Force LOCAL_HTTP to avoid OpenAI dependency in test
    monkeypatch.setenv("PATCH_PROVIDER", "LOCAL_HTTP")
    monkeypatch.setenv("LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:9/invalid")
    diff = ai.generate_patch(item, context="")
    assert isinstance(diff, str)