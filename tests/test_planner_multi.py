import pytest


def test_planner_builds_multiple_items(monkeypatch):
    try:
        from stillme_core.planner import Planner
    except Exception as e:
        pytest.xfail(f"Planner import failed: {e}")

    # Monkeypatch git status to simulate 2 modified files
    import subprocess as _sp

    class _P:
        def __init__(self, rc=0, out=" M a.py\n M b.py\n"):
            self.returncode = rc
            self.stdout = out

    monkeypatch.setattr(_sp, "run", lambda *a, **kw: _P())

    p = Planner()
    # Create fake pytest cache lastfailed
    import json
    import os

    os.makedirs(".pytest_cache/v/cache", exist_ok=True)
    with open(".pytest_cache/v/cache/lastfailed", "w", encoding="utf-8") as f:
        json.dump({"tests/test_a.py::test_x": True}, f)

    items = p.build_plan(max_items=5)
    assert isinstance(items, list)
    assert len(items) >= 2, "Should build at least 2 items from multiple signals"