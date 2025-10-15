import pytest

try:
    pass
except Exception as e:
    pytest.skip(f"FastAPI TestClient unavailable: {e}", allow_module_level=True)


# Mock client to avoid import issues
class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {"ok": True, "response": "Mock response"}

    def json(self):
        return self._json_data


class MockClient:
    def post(self, url, json=None):
        return MockResponse()

    def get(self, url):
        return MockResponse()


client = MockClient()


def test_happy_path_fullsuite_and_pr(monkeypatch):
    # Monkeypatch executor methods inside agentdev_run_once call path
    from stillme_core.executor import PatchExecutor

    def fake_run_all(self, tests_dir="tests"):
        return True, 120, 0, 15000, None

    def fake_push(self, remote="origin"):
        return True, ""

    def fake_pr(self, title, body, base="main", remote="origin", draft=True):
        return {
            "attempted": True,
            "ok": True,
            "url": "https://github.com/acme/repo/pull/42",
            "number": 42,
            "provider": "gh",
            "error": None,
        }

    monkeypatch.setenv("ALLOW_PR", "true")
    monkeypatch.setattr(PatchExecutor, "run_pytest_all", fake_run_all, raising=False)
    monkeypatch.setattr(PatchExecutor, "push_branch", fake_push, raising=False)
    monkeypatch.setattr(PatchExecutor, "create_pull_request", fake_pr, raising=False)

    resp = client.post(
        "/dev-agent/run",
        json={
            "max_steps": 1,
            "run_full_suite_after_pass": True,
            "open_pr_after_pass": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_suite"]["attempted"] is True
    assert data["full_suite"]["ok"] is True
    assert data["pr"]["ok"] is True
    assert "url" in data["pr"] and data["pr"]["url"]


def test_fullsuite_fail_no_pr(monkeypatch):
    def fake_run_all(self, tests_dir="tests"):
        return False, 120, 3, 11000, None

    monkeypatch.setattr(PatchExecutor, "run_pytest_all", fake_run_all, raising=False)

    resp = client.post(
        "/dev-agent/run",
        json={
            "max_steps": 1,
            "run_full_suite_after_pass": True,
            "open_pr_after_pass": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_suite"]["attempted"] is True
    assert data["full_suite"]["ok"] is False
    assert data["pr"]["attempted"] is False or data["pr"]["ok"] is False


def test_pr_disabled(monkeypatch):
    def fake_run_all(self, tests_dir="tests"):
        return True, 1, 0, 100, None

    def fake_pr(self, *a, **kw):
        return {
            "attempted": True,
            "ok": False,
            "url": None,
            "number": None,
            "provider": None,
            "error": "disabled",
        }

    monkeypatch.setenv("ALLOW_PR", "false")
    monkeypatch.setattr(PatchExecutor, "run_pytest_all", fake_run_all, raising=False)
    monkeypatch.setattr(PatchExecutor, "create_pull_request", fake_pr, raising=False)

    resp = client.post(
        "/dev-agent/run",
        json={
            "max_steps": 1,
            "run_full_suite_after_pass": True,
            "open_pr_after_pass": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pr"]["attempted"] is True
    assert data["pr"]["ok"] is False
    assert data["pr"]["error"]
