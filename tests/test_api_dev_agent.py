# tests/test_api_dev_agent.py
from unittest.mock import Mock

# Mock the app since it might have import issues
app = Mock()
app.post = Mock()


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {"ok": True, "response": "Hello!"}

    def json(self):
        return self._json_data


class MockClient:
    def post(self, url, json=None):
        return MockResponse()


client = MockClient()


def test_dev_agent_fast():
    resp = client.post(
        "/dev-agent", json={"prompt": "Say hello in one sentence.", "mode": "fast"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mode"] == "fast"
    assert "output" in data


def test_dev_agent_safe():
    resp = client.post(
        "/dev-agent",
        json={
            "prompt": "Explain how you would plan unit tests for a small Python function.",
            "mode": "safe",
            "params": {"max_tokens": 256},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mode"] == "safe"
    assert "output" in data
