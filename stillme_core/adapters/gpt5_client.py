# adapters/gpt5_client.py
from __future__ import annotations

import os
from typing import Any, Literal

import httpx


class GPT5Client:
    """
    OpenAI-compatible thin client (chat.completions).
    Chỉ dùng các field tối thiểu để tránh lệ thuộc SDK.
    """

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_base = (api_base or os.getenv("GPT5_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("GPT5_API_KEY", "")
        if not self.api_base:
            raise ValueError("GPT5_API_BASE is not set")
        if not self.api_key:
            raise ValueError("GPT5_API_KEY is not set")
        self.timeout = timeout
        self._chat_url = f"{self.api_base}/chat/completions"

    async def generate(
        self,
        prompt: str,
        mode: Literal["fast", "safe"] = "fast",
        system: str | None = None,
        temperature: float = 0.2,
        extra: dict[str, Any] | None = None,
    ) -> str:
        model = (
            os.getenv("GPT5_MODEL_FAST")
            if mode == "fast"
            else os.getenv("GPT5_MODEL_SAFE")
        )
        if not model:
            raise ValueError(f"Missing model env for mode={mode}")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False,
        }
        if extra:
            body.update(extra)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(self._chat_url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            # OpenAI-compatible shape
            return data["choices"][0]["message"]["content"]

    async def health(self) -> bool:
        try:
            text = await self.generate(prompt="ping", mode="fast", temperature=0.0)
            return isinstance(text, str) and len(text) > 0
        except Exception:
            return False