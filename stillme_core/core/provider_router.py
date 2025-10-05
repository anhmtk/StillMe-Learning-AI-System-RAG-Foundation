# stillme_core/provider_router.py
from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)

BRIDGE_BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8000")
ALLOWED_MODES: tuple[Literal["fast", "safe"], ...] = ("fast", "safe")


def _norm_mode(mode: str | None) -> Literal["fast", "safe"]:
    m = (mode or "fast").lower().strip()
    if m not in ALLOWED_MODES:
        logger.warning("provider_router: invalid mode '%s' → dùng 'safe'", m)
        return "safe"
    return m


class ProviderRouter:
    """
    Client router → gọi Dev Agent Bridge.
    Truyền đầy đủ system_prompt/hints xuống Bridge, để server build [{system},{user}] khi gọi model.
    """

    def __init__(self, base_url: str | None = None, timeout_s: float = 30.0):
        self.base_url = (base_url or BRIDGE_BASE).rstrip("/")
        self.timeout = httpx.Timeout(connect=5.0, read=timeout_s, write=20.0, pool=20.0)

    async def ask(
        self,
        prompt: str,
        mode: str = "fast",
        *,
        system_prompt: str | None = None,
        response_format: str | None = "json",
        force_json: bool | None = True,
        schema_hint: dict[str, Any] | None = None,
        max_tokens: int | None = 512,
        temperature: float | None = 0.3,
        top_p: float | None = 0.95,
        stop: list[str] | None = None,
        **extra: Any,
    ) -> str:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "mode": _norm_mode(mode),
            "system_prompt": system_prompt,
            "response_format": response_format,
            "force_json": force_json,
            "schema_hint": schema_hint,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": stop,
        }
        # loại None
        payload = {k: v for k, v in payload.items() if v is not None}
        if extra:
            for k, v in extra.items():
                if v is not None:
                    payload[k] = v

        logger.debug(
            "provider_router.ask payload=%s",
            json.dumps({**payload, "prompt": f"{prompt[:60]}..."}, ensure_ascii=False),
        )

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as c:
            r = await c.post("/dev-agent/bridge", json=payload)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Bridge HTTP error %s: %s", r.status_code, r.text)
                raise e

            data = r.json()
            content = data.get("content", "")
            if not isinstance(content, str):
                try:
                    content = json.dumps(content, ensure_ascii=False)
                except Exception:
                    content = str(content)
            logger.debug(
                "provider_router.ask resp provider=%s mode=%s safe=%s preview=%s",
                data.get("provider"),
                data.get("mode"),
                data.get("safe_passed"),
                (content or "")[:200].replace("\n", "\\n"),
            )
            return content

    def ask_sync(
        self,
        prompt: str,
        mode: str = "fast",
        *,
        system_prompt: str | None = None,
        response_format: str | None = "json",
        force_json: bool | None = True,
        schema_hint: dict[str, Any] | None = None,
        max_tokens: int | None = 512,
        temperature: float | None = 0.3,
        top_p: float | None = 0.95,
        stop: list[str] | None = None,
        **extra: Any,
    ) -> str:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "mode": _norm_mode(mode),
            "system_prompt": system_prompt,
            "response_format": response_format,
            "force_json": force_json,
            "schema_hint": schema_hint,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": stop,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        if extra:
            for k, v in extra.items():
                if v is not None:
                    payload[k] = v

        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as c:
            r = c.post("/dev-agent/bridge", json=payload)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Bridge HTTP error %s: %s", r.status_code, r.text)
                raise e
            data = r.json()
            content = data.get("content", "")
            if not isinstance(content, str):
                try:
                    content = json.dumps(content, ensure_ascii=False)
                except Exception:
                    content = str(content)
            logger.debug(
                "provider_router.ask_sync resp provider=%s mode=%s preview=%s",
                data.get("provider"),
                data.get("mode"),
                (content or "")[:200].replace("\n", "\\n"),
            )
            return content


# instance dùng chung
router = ProviderRouter()


# helpers
async def ask(prompt: str, mode: str = "fast", **params: Any) -> str:
    return await router.ask(prompt, mode=mode, **params)


def ask_sync(prompt: str, mode: str = "fast", **params: Any) -> str:
    return router.ask_sync(prompt, mode=mode, **params)
