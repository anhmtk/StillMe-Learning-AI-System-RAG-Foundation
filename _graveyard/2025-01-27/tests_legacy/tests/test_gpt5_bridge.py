# tests/test_gpt5_bridge.py
import os

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


# üîí √âp AnyIO ch·ªâ ch·∫°y backend asyncio (tr√°nh trio)
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def test_app():
    os.environ["ALLOW_GPT5"] = "false"  # √©p fallback sang Ollama
    from api_server import app

    return app


# Helper: ch·∫°y app v·ªõi lifespan + t·∫Øt keep-warm ƒë·ªÉ kh·ªèi r√≤ task
@pytest.fixture
async def app_with_lifespan(monkeypatch, test_app: FastAPI):
    import api_server as srv

    # t·∫Øt v√≤ng keep-warm (tr√°nh task ch·∫°y n·ªÅn)
    async def _noop_keepwarm():
        return None

    monkeypatch.setattr(srv, "_keep_warm_task", _noop_keepwarm, raising=True)

    async with LifespanManager(test_app):
        yield test_app


@pytest.mark.anyio
async def test_bridge_fast_fallback_ollama(monkeypatch, app_with_lifespan: FastAPI):
    from api_server import ollama_client

    async def fake_generate(prompt: str, mode="fast"):
        return f"[ollama-{mode}] {prompt}"

    monkeypatch.setattr(ollama_client, "generate", fake_generate)

    transport = ASGITransport(app=app_with_lifespan)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/dev-agent/bridge",
            json={"prompt": "hello", "mode": "fast", "provider": "auto"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "ollama"
        assert data["mode"] == "fast"
        assert data["content"].startswith("[ollama-fast]")


@pytest.mark.anyio
async def test_bridge_safe_runs_saferunner(monkeypatch, app_with_lifespan: FastAPI):
    from api_server import ollama_client, safe_runner

    async def fake_generate(prompt: str, mode="safe"):
        return "SOME_PLAN_OR_CODE"

    monkeypatch.setattr(ollama_client, "generate", fake_generate)

    async def fake_run_safe(plan: str):
        return {"ok": True}

    monkeypatch.setattr(safe_runner, "run_safe", fake_run_safe)

    transport = ASGITransport(app=app_with_lifespan)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/dev-agent/bridge",
            json={"prompt": "do safe thing", "mode": "safe", "provider": "auto"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["safe_passed"] is True


@pytest.mark.anyio
async def test_health_ai_endpoint(monkeypatch, app_with_lifespan: FastAPI):
    from api_server import ollama_client

    async def fake_health():
        return True

    monkeypatch.setattr(ollama_client, "health", fake_health)

    transport = ASGITransport(app=app_with_lifespan)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health/ai")
        assert r.status_code == 200
        data = r.json()
        assert "ollama" in data and data["ollama"]["ok"] is True
