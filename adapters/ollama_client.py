# adapters/ollama_client.py
from __future__ import annotations
import os
import httpx
from typing import Literal, Optional
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Optional, Dict, Any, List

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env", override=True, encoding="utf-8")
class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        # dùng Timeout chi tiết thay vì float
        self.timeout = httpx.Timeout(connect=10.0, read=600.0, write=60.0, pool=60.0)

    async def generate(
        self,
        prompt: str,
        mode: str = "fast",
        *,
        max_tokens: Optional[int] = None,      # map -> options.num_predict
        temperature: Optional[float] = None,   # map -> options.temperature
        top_p: Optional[float] = None,         # map -> options.top_p
        stop: Optional[List[str]] = None,      # map -> options.stop
        system_prompt: Optional[str] = None,   # map -> system
    ) -> str:
        model = os.getenv("OLLAMA_MODEL_FAST") if mode == "fast" else os.getenv("OLLAMA_MODEL_SAFE")
        if not model:
            raise ValueError(f"Missing OLLAMA model for mode={mode}")

        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        # map tham số -> options
        options: Dict[str, Any] = {}
        if max_tokens is not None:
            options["num_predict"] = int(max_tokens)
        if temperature is not None:
            options["temperature"] = float(temperature)
        if top_p is not None:
            options["top_p"] = float(top_p)
        if stop:
            options["stop"] = stop
        if options:
            payload["options"] = options

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("response", "")
                if not text and isinstance(data, dict):
                    message_obj = data.get("message")        # đổi tên
                    if isinstance(message_obj, dict):
                        text = message_obj.get("content", "")  # đổi tên
                if not text:
                    text = str(data)
                return text       
        except httpx.HTTPStatusError as e:
            err_text = e.response.text if e.response is not None else str(e)
            raise RuntimeError(f"HTTP {e.response.status_code}: {err_text}") from e

        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}") from e
    async def health(self) -> bool:
        """
        Check if Ollama server is alive.
        Stub để Pylance không báo lỗi. Thực tế có thể gọi API /health.
        """
        try:
            # nếu đã có method nào tương tự (vd. ping), gọi lại ở đây
            return True
        except Exception:
            return False