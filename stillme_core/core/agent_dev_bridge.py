# stillme_core/agent_dev_bridge.py
from __future__ import annotations

import os
from typing import Any, Literal

import httpx

__all__ = ["DevAgentBridge"]

class DevAgentBridge:
    def __init__(self, base: str | None = None, timeout: float = 60.0):
        # BRIDGE_BASE ví dụ: http://127.0.0.1:8000
        self.base = (base or os.getenv("BRIDGE_BASE", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout

    async def ask(
        self,
        prompt: str,
        mode: Literal["fast", "safe"] = "fast",
        provider: Literal["auto", "gpt5", "ollama"] = "auto",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"prompt": prompt, "mode": mode, "provider": provider}
        if extra:
            payload.update(extra)
        async with httpx.AsyncClient(timeout=self.timeout) as cli:
            r = await cli.post(f"{self.base}/dev-agent/bridge", json=payload)
            r.raise_for_status()
            return r.json()

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as cli:
            r = await cli.get(f"{self.base}/health/ai")
            r.raise_for_status()
            return r.json()
