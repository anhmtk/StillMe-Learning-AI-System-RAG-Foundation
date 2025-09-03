# stillme_core/ai_manager.py
"""
AI Manager – lớp mỏng điều phối giữa StillMe và Dev Agent Bridge.
Các chế độ:
- fast  : text-only (REST nhanh)  -> bridge mode="fast" (mặc định llama3:8b)
- think : suy luận sâu (text)     -> bridge mode="safe" (mặc định gpt-oss:20b hoặc cấu hình .env)
- code  : model sinh code + sandbox -> giữ nguyên OpenInterpreterController
"""

from __future__ import annotations
from typing import Optional, Dict, Any

import asyncio
from .config_defaults import try_load_dotenv, DEFAULT_MODE
from .plan_types import PlanItem
import os
import json
import httpx
from pathlib import Path

# 1) Bridge (Dev Agent)
from stillme_core.provider_router import ask  # async def ask(...)

# 2) Code path (giữ như cũ)
from oi_adapter.interpreter_controller import OpenInterpreterController as C

# =======================
# Singleton controller cho nhánh "code"
# =======================
_CTL: Optional[C] = None

def controller() -> C:
    global _CTL
    if _CTL is None:
        _CTL = C()
    return _CTL

# =======================
# Tiện ích mapping mode
# =======================
_TEXT_MODE_MAP = {
    "fast": "fast",
    "think": "safe",
}

# Load .env if available
try_load_dotenv()

# =======================
# Public API cũ (giữ tương thích)
# =======================
def set_mode(mode: str) -> str:
    """
    (Giữ để tương thích) – Trước đây set model trực tiếp.
    Hiện tại: với text-mode, model do Bridge quyết định theo .env; với code-mode vẫn dùng controller.
    """
    if mode == "code":
        ctl = controller()
        try:
            return ctl.set_model("deepseek-coder:6.7b")
        except Exception:
            return "[AIManager] controller: set_model('deepseek-coder:6.7b') failed or not required"
    return "[AIManager] text-mode uses Dev Agent Bridge; no local set_model needed."

def warmup(model: Optional[str] = None) -> Dict[str, Any]:
    """Warmup cho nhánh code (tuỳ controller)."""
    try:
        return controller().warmup(model=model)
    except Exception:
        return {"ok": False, "msg": "warmup not supported for controller or failed"}

def health(model: Optional[str] = None) -> Dict[str, Any]:
    """Health-check nhanh cho nhánh code (controller)."""
    try:
        return controller().health(model=model)
    except Exception:
        return {"ok": False, "msg": "health not supported for controller or failed"}
# --- add to stillme_core/ai_manager.py ---

def _gpt5_ping() -> Dict[str, Any]:
    """
    Ping thật GPT-5 bằng một chat mini 'ping' → 'pong'.
    Trả: {"enabled": bool, "ok": bool, "error": "...?"}
    """
    enabled = os.getenv("ALLOW_GPT5", "true").lower() == "true"
    base_url = os.getenv("GPT5_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("GPT5_MODEL_FAST", "gpt-5-mini")
    out: Dict[str, Any] = {"enabled": enabled, "ok": False}

    if not enabled:
        return out
    if not api_key:
        out["error"] = "missing OPENAI_API_KEY"
        return out

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        # LƯU Ý: đừng set temperature=0 vì một số model không cho override
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
        )
        _ = r.choices[0].message.content or ""
        out["ok"] = True
        return out
    except Exception as e:
        out["error"] = str(e)[:300]
        return out


def _ollama_ping() -> Dict[str, Any]:
    """
    Ping nhanh Ollama bằng /api/tags.
    Trả: {"ok": bool, "error": "...?"}
    """
    url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{url}/api/tags", timeout=2)
        r.raise_for_status()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

# =======================
# Bridge helpers (đÃ SỬA: tránh tạo coroutine khi loop đang chạy)
# =======================
def _bridge_sync_ask(prompt: str, mode: str = "fast", **params: Any) -> str:
    """
    Helper ĐỒNG BỘ gọi bridge.
    - Nếu KHÔNG có event loop đang chạy: dùng asyncio.run(ask(...))
    - Nếu ĐANG có event loop: KHÔNG tạo coroutine -> raise RuntimeError để caller chọn đường async
    """
    # Quan trọng: kiểm tra loop trước, tránh tạo coroutine bị bỏ rơi
    try:
        asyncio.get_running_loop()  # có loop -> báo lên
        raise RuntimeError("event loop is running")
    except RuntimeError as no_loop:
        # Không có loop đang chạy -> an toàn để run
        if str(no_loop) != "event loop is running":
            return asyncio.run(ask(prompt, mode=mode, **params))
        # Có loop -> rơi xuống except phía dưới
        pass
    # Có loop đang chạy -> báo cho caller dùng async API
    raise RuntimeError("Event loop is running; use aget_ai_response()")

async def _bridge_async_ask(prompt: str, mode: str = "fast", **params: Any) -> str:
    return await ask(prompt, mode=mode, **params)

# =======================
# Router tác vụ “dev_agent”
# =======================
def dev_agent(task: str, mode: str = DEFAULT_MODE, **params: Any) -> str:
    """
    Router tác vụ:
      - fast  : text-only -> bridge mode="fast"
      - think : text-only -> bridge mode="safe"
      - code  : deepseek-coder:6.7b + python sandbox
    """
    mode_lower = (mode or "fast").lower()

    if mode_lower == "code":
        ctl = controller()
        try:
            ctl.set_model("deepseek-coder:6.7b")
        except Exception:
            pass
        try:
            return ctl.run_python_via_model(task)
        except Exception as e:
            return f"[AIManager][code] error: {e}"

    bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
    try:
        return _bridge_sync_ask(task, mode=bridge_mode, **params)
    except RuntimeError as re:
        # Không cố gọi async từ đây để tránh warning; trả hướng dẫn rõ ràng
        return f"[AIManager][{bridge_mode}] cannot run sync in running loop; use aget_ai_response(). Detail: {re}"
    except Exception as e:
        # Fallback sang fast (nếu safe lỗi)
        try:
            return _bridge_sync_ask(task, mode="fast", **params)
        except Exception:
            return f"[AIManager][{bridge_mode}] error: {e}"

def compute_number(task: str) -> str:
    """Đảm bảo trả về CHỈ CHỮ SỐ cho các phép tính đơn giản (nhánh controller)."""
    ctl = controller()
    try:
        ctl.set_model("llama3:8b")
    except Exception:
        pass
    try:
        warmup()
    except Exception:
        pass
    try:
        return ctl.run_compute_number(task)
    except Exception as e:
        return f"[AIManager][compute_number] error: {e}"

# =========================
# NEW: Lớp AIManager (wrapper)
# =========================
class AIManager:
    """
    Lớp bọc mỏng quanh các hàm module-level để tương thích import từ các module khác
    (ví dụ: stillme_core.planner). Dùng Bridge cho text-mode; giữ controller cho code-mode.
    """

    # ====== API đang có ======
    def set_mode(self, mode: str) -> str:
        return set_mode(mode)

    def warmup(self, model: Optional[str] = None) -> Dict[str, Any]:
        return warmup(model)

    def health(self, model: Optional[str] = None) -> Dict[str, Any]:
        return health(model)

    def dev_agent(self, task: str, mode: str = "fast", **params: Any) -> str:
        return dev_agent(task, mode, **params)

    def compute_number(self, task: str) -> str:
        return compute_number(task)

    # ====== API Planner kỳ vọng ======
    def get_ai_response(self, prompt: str, mode: str = "fast", **params: Any) -> str:
        """
        BẢN SYNC: dùng khi KHÔNG ở trong event loop (ví dụ test/unit sync).
        Nếu đang ở trong event loop, hàm này trả message hướng dẫn dùng async.
        """
        mode_lower = (mode or "fast").lower()
        if mode_lower == "code":
            return dev_agent(prompt, "code", **params)

        bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
        try:
            return _bridge_sync_ask(prompt, mode=bridge_mode, **params)
        except RuntimeError as re:
            # Không tạo coroutine ở đây -> không còn "coroutine was never awaited"
            return f"[AIManager][{bridge_mode}] cannot run sync in running loop; use aget_ai_response(). Detail: {re}"
        except Exception:
            try:
                return _bridge_sync_ask(prompt, mode="fast", **params)
            except Exception:
                return ""

    async def aget_ai_response(self, prompt: str, mode: str = "fast", **params: Any) -> str:
        """BẢN ASYNC: dùng trong FastAPI handler / async context."""
        mode_lower = (mode or "fast").lower()
        if mode_lower == "code":
            # Nếu thực sự cần gọi controller sync trong async context, cân nhắc chạy bằng thread executor
            return dev_agent(prompt, "code", **params)

        bridge_mode = _TEXT_MODE_MAP.get(mode_lower, "fast")
        try:
            return await _bridge_async_ask(prompt, mode=bridge_mode, **params)
        except Exception:
            try:
                return await _bridge_async_ask(prompt, mode="fast", **params)
            except Exception:
                return ""

    def get_ai_response_json(self, prompt: str, mode: str = "fast") -> Dict[str, Any]:
        """Một số chỗ cần JSON; parse mềm."""
        txt = self.get_ai_response(prompt, mode)
        try:
            return json.loads(txt)
        except Exception:
            return {}
    def health_providers(self) -> Dict[str, Any]:
        """
        Trả health chi tiết cho các provider dùng ở dự án.
        """
        return {
            "gpt5": _gpt5_ping(),
            "ollama": _ollama_ping(),
        }
    # ====== NEW: generate unified diff patch ======
    def generate_patch(self, plan_item: PlanItem, context: str = "") -> str:
        """
        Generate unified diff via provider. Providers:
        - OPENAI (default, env OPENAI_API_KEY)
        - LOCAL_HTTP (OpenAI-compatible endpoint via env LOCAL_MODEL_ENDPOINT)
        Returns a string that starts with '--- a/..' and '+++ b/..'.
        """
        provider = os.getenv("PATCH_PROVIDER", "OPENAI").upper()
        model = os.getenv("PATCH_MODEL", "gpt-4o-mini")
        system = (
            "You are a senior software engineer. Return ONLY a unified diff patch."
            " It must include file headers (--- a/... +++ b/...) and valid hunks."
        )
        # Build lightweight file context if not provided
        if not context:
            context = self._build_file_context(plan_item)

        user = {
            "instruction": "Generate a minimal patch to implement the plan item.",
            "plan_item": plan_item.to_dict(),
            "diff_hint": plan_item.diff_hint or "",
            "file_context": context,
            "tests_to_run": plan_item.tests_to_run,
            "constraints": [
                "Output must be plain text unified diff",
                "No markdown code fences",
                "Keep patch minimal and safe",
            ],
        }

        if provider == "LOCAL_HTTP":
            endpoint = os.getenv("LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:8000/v1/chat/completions")
            try:
                r = httpx.post(
                    endpoint,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": json.dumps(user)},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
                txt = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._ensure_unified_diff(txt)
            except Exception:
                return ""

        # Default: OPENAI
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
            if not openai.api_key:
                return ""
            resp = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(user)},
                ],
                temperature=0.2,
            )
            txt = resp.choices[0].message.content or ""
            return self._ensure_unified_diff(txt)
        except Exception:
            return ""

    @staticmethod
    def _ensure_unified_diff(text: str) -> str:
        t = (text or "").strip()
        # Strip markdown fences if present
        if t.startswith("```") and t.endswith("```"):
            t = t.strip("`").strip()
            if t.lower().startswith("json") or t.lower().startswith("diff"):
                t = t.split("\n", 1)[1] if "\n" in t else t
        if "--- a/" in t and "+++ b/" in t:
            return t
        return ""

    @staticmethod
    def _build_file_context(item: PlanItem, max_lines: int = 80) -> str:
        """Read up to N lines of the target file as context for patch synthesis."""
        path = (item.target or "").strip()
        if not path:
            return ""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return ""
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
            head = lines[:max_lines]
            tail = lines[-max_lines:] if len(lines) > max_lines else []
            snippet = "\n".join(head + (["\n..."] if tail and head != lines else []) + tail)
            return f"FILE: {path}\n{snippet}"
        except Exception:
            return ""
