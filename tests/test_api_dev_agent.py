# tests/test_api_dev_agent.py
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_dev_agent_fast():
    resp = client.post("/dev-agent", json={
        "prompt": "Say hello in one sentence.",
        "mode": "fast"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mode"] == "fast"
    assert "output" in data

def test_dev_agent_safe():
    resp = client.post("/dev-agent", json={
        "prompt": "Explain how you would plan unit tests for a small Python function.",
        "mode": "safe",
        "params": {"max_tokens": 256}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mode"] == "safe"
    assert "output" in data
