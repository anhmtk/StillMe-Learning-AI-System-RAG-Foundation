# oi_adapter/interpreter_controller.py
from __future__ import annotations

import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from interpreter import interpreter as oi  # pyright: ignore[reportMissingImports]

from stillme_core.config import OLLAMA_HOST  # lấy host từ config

# Mặc định vẫn để 20b, nhưng có thể gọi set_model('llama3:8b') để debug nhanh
MODEL_NAME = "gpt-oss:20b"
FULL_MODEL_ID = f"ollama/{MODEL_NAME}"  # yêu cầu OI gọi qua liteLLM/ollama
AVAILABLE = {"gpt-oss:20b", "llama3:8b", "deepseek-coder:6.7b"}

logger = logging.getLogger("OI-Controller")


class OpenInterpreterController:
    def __init__(
        self,
        model: str = MODEL_NAME,
        provider: str = "ollama",
        context_window: Optional[int] = 8000,
        max_tokens: Optional[int] = 1024,
        auto_run: bool = True,
        execute: bool = True,
    ):
        self.ollama_host = OLLAMA_HOST
        # lưu model hiện hành
        self.model = model

        # cấu hình OI dùng Ollama
        oi.llm.library = provider
        oi.llm.model = f"ollama/{self.model}"
        if hasattr(oi.llm, "api_base"):
            oi.llm.api_base = self.ollama_host
        if hasattr(oi, "api_base"):
            oi.api_base = self.ollama_host

        try:
            if context_window:
                oi.context_window = context_window
            if max_tokens:
                oi.max_tokens = max_tokens
        except Exception:
            pass

        oi.auto_run = auto_run
        oi.execute = execute
        oi.system_message = (
            "You are the StillMe DevOps agent. "
            "Read files you are given, propose fixes, execute tests if provided, "
            "and print concise results."
        )

        # --- đảm bảo OI dùng đúng Python + thư mục làm việc an toàn
        try:
            if hasattr(oi, "python_path"):
                oi.python_path = sys.executable  # ví dụ: ...\envs\oi311\python.exe
        except Exception:
            pass

        self._work_dir: Path = Path.cwd() / ".oi_sandbox"
        self._work_dir.mkdir(parents=True, exist_ok=True)
        try:
            if hasattr(oi, "working_directory"):
                oi.working_directory = str(self._work_dir)
            elif hasattr(oi, "work_dir"):
                oi.work_dir = str(self._work_dir)
        except Exception:
            pass

        self._oi = oi

    # ---------------------------------------------------------------------
    def _ensure_work_dir(self):
        if not hasattr(self, "_work_dir") or self._work_dir is None:
            self._work_dir = Path.cwd() / ".oi_sandbox"
        self._work_dir.mkdir(parents=True, exist_ok=True)

    # ---- helpers ---------------------------------------------------------
    def _norm_piece(self, piece: Any) -> str:
        if piece is None:
            return ""
        if isinstance(piece, dict):
            for k in ("content", "message", "text"):
                v = piece.get(k)
                if isinstance(v, str) and v.strip():
                    return v
            delta = piece.get("delta") or piece.get("data") or {}
            if isinstance(delta, dict):
                for k in ("content", "text"):
                    v = delta.get(k)
                    if isinstance(v, str) and v.strip():
                        return v
            return ""
        s = str(piece)
        return s if s.strip() else ""

    # ---- model control ---------------------------------------------------
    def set_model(self, name: str) -> str:
        """Đổi model động: 'gpt-oss:20b' | 'llama3:8b' | 'deepseek-coder:6.7b'"""
        if name not in AVAILABLE:
            return f"[MODEL_ERROR] '{name}' not in {sorted(AVAILABLE)}"
        self.model = name
        try:
            self._oi.llm.model = f"ollama/{name}"
        except Exception:
            pass
        return f"[MODEL] set to {name}"

    # ---- OI chat ---------------------------------------------------------
    def run_prompt(self, prompt: str) -> str:
        out: List[str] = []
        for chunk in self._oi.chat(prompt, stream=True):
            text = self._norm_piece(chunk)
            if text:
                out.append(text)
        return "\n".join(out).strip()

    def _say_exact(self, text: str) -> str:
        p = (
            "Your only job: print exactly the following string with no extra characters:\n\n"
            f"{text}\n"
            "Do not add quotes, prefixes, suffixes, or explanations."
        )
        return self.run_prompt(p)

    # ---- Ollama REST helpers --------------------------------------------
    def _ollama_direct(self, prompt: str, *, model: Optional[str] = None) -> str:
        base = (self.ollama_host or OLLAMA_HOST).rstrip("/")
        for _ in range(6):
            try:
                r = requests.get(f"{base}/api/version", timeout=5)
                if r.ok:
                    break
            except Exception:
                time.sleep(5)
        else:
            raise RuntimeError("Ollama service not responding at /api/version")

        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
        }
        r = requests.post(f"{base}/api/generate", json=payload, timeout=(30, 600))
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()

    def _ollama_generate(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        timeout: int = 60,
        host: Optional[str] = None,
    ) -> Dict[str, Any]:
        base = (host or self.ollama_host or OLLAMA_HOST).rstrip("/")
        url = f"{base}/api/generate"
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        try:
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            text = data.get("response") or data.get("message") or ""
            return {
                "ok": True,
                "text": (text or "").strip(),
                "raw": data,
                "error": None,
            }
        except requests.exceptions.Timeout:
            return {
                "ok": False,
                "text": "",
                "raw": None,
                "error": f"Timeout after {timeout}s",
            }
        except Exception as e:
            return {"ok": False, "text": "", "raw": None, "error": str(e)}

    # ---- public quick checks --------------------------------------------
    def test_integration(self) -> str:
        expected = "I am OpenInterpreter inside StillMe."
        out = (self._say_exact(expected) or "").replace("\u200b", "").strip()
        if out == expected:
            return expected
        fb = (
            self._ollama_direct(
                "Reply with exactly the next line, and nothing else:\n"
                f"{expected}\n"
                "No quotes. No explanations. No extra whitespace."
            )
            or ""
        ).strip()
        if fb == expected:
            return f"{expected}  (via fallback: Ollama REST; OI silent)"
        return f"[Mismatch] OI:{out!r} | Ollama:{fb!r}"

    # ---- health & warmup -------------------------------------------------
    def health(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Kiểm tra Ollama + model + generate siêu ngắn (tự warmup khi cần)."""
        model = model or self.model
        base = OLLAMA_HOST.rstrip("/")
        info: Dict[str, Any] = {"model": model}

        # 1) Ollama up?
        try:
            v = requests.get(f"{base}/api/version", timeout=5)
            info["ollama_up"] = v.ok
            info["ollama_version"] = v.json().get("version") if v.ok else None
        except Exception as e:
            info["ollama_up"] = False
            info["error"] = f"version_err: {e}"
            return info

        # 2) Model present?
        try:
            tags = requests.get(f"{base}/api/tags", timeout=5)
            names = (
                [m.get("name") for m in tags.json().get("models", [])]
                if tags.ok
                else []
            )
            info["model_present"] = model in names
        except Exception:
            info["model_present"] = None

        # 3) Tiny generate (giới hạn token, nhiệt độ thấp)
        tiny_opts = {"temperature": 0.0, "num_predict": 8}
        tiny = self._ollama_generate(
            prompt=".", model=model, options=tiny_opts, timeout=8
        )
        if tiny["ok"]:
            info["tiny_generate_ok"] = True
            return info

        # 4) Nếu timeout → warmup + retry (timeout dài hơn)
        if "Timeout" in (tiny["error"] or ""):
            _ = self.warmup(model=model, tries=2, delay=1.5)  # hâm nóng nhanh
            tiny2 = self._ollama_generate(
                prompt="ok", model=model, options=tiny_opts, timeout=30
            )
            info["tiny_generate_ok"] = tiny2["ok"]
            if not tiny2["ok"]:
                info["tiny_generate_error"] = tiny2["error"]
            return info

        # 5) Lỗi khác
        info["tiny_generate_ok"] = False
        info["tiny_generate_error"] = tiny["error"]
        return info

    def warmup(
        self, model: Optional[str] = None, tries: int = 3, delay: float = 2.0
    ) -> Dict[str, Any]:
        """Gọi vài prompt ngắn để nạp model vào RAM, giảm ReadTimeout lần đầu."""
        model = model or self.model
        t0 = time.time()
        last_err = None
        for i in range(tries):
            res = self._ollama_generate(
                prompt="Warmup. Reply 'ok'.",
                model=model,
                stream=False,
                timeout=20,
                host=OLLAMA_HOST,
            )
            if res["ok"]:
                return {
                    "ok": True,
                    "elapsed": round(time.time() - t0, 2),
                    "model": model,
                }
            last_err = res["error"]
            time.sleep(delay)
        return {
            "ok": False,
            "elapsed": round(time.time() - t0, 2),
            "model": model,
            "error": last_err,
        }

    # ---- text-only fast path --------------------------------------------
    def run_text_only(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
        timeout: int = 60,
    ) -> str:
        options = {"temperature": temperature, "num_predict": max_tokens}
        res = self._ollama_generate(
            prompt=prompt,
            model=model or self.model,
            options=options,
            stream=False,
            timeout=timeout,
        )
        if not res["ok"]:
            return f"[TEXT_ONLY_ERROR] {res['error']}"
        return res["text"]

    # ---- Controller-side Python executor (fallback) ----------------------
    _PY_BLOCK_RE = re.compile(r"```python\s*(.*?)```", re.DOTALL | re.IGNORECASE)

    def _extract_python_block(self, text: str) -> str:
        m = self._PY_BLOCK_RE.search(text or "")
        return (m.group(1) if m else "").strip()

    def _run_python_subprocess(self, code: str, timeout: int = 30) -> Dict[str, str]:
        self._ensure_work_dir()
        if not code.strip():
            return {"stdout": "", "stderr": "Empty code", "ok": False}
        script_path = self._work_dir / "snippet.py"
        script_path.write_text(code, encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(self._work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = "", "Timeout running Python code"
        ok = (proc.returncode == 0) and not err.strip()
        return {"stdout": out, "stderr": err, "ok": ok}

    def run_python_via_model(self, task_prompt: str, *, timeout: int = 30) -> str:
        self._ensure_work_dir()
        instr = (
            "Write ONLY one Python code block that prints the final answer.\n"
            "No explanations. No extra text. Use:\n"
            "```python\nprint(<result>)\n```"
        )
        response_text = self.run_prompt(f"{task_prompt}\n\n{instr}")
        code = self._extract_python_block(response_text)
        if not code:
            response_text = self.run_text_only(f"{task_prompt}\n\n{instr}")
            code = self._extract_python_block(response_text)
        if not code:
            return "[PY_EXEC_ERROR] Model did not return a Python code block."
        res = self._run_python_subprocess(code, timeout=timeout)
        return (
            res["stdout"].strip()
            if res["ok"]
            else f"[PY_EXEC_ERROR] {res['stderr'].strip()}"
        )

    # ---- run_prompt với debug + soft-timeout + fallback ------------------
    def run_prompt_debug(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        total_timeout: int = 75,
        step_sleep: float = 0.25,
        max_tokens: int = 512,
        temperature: float = 0.2,
        force_text_only_fallback: bool = False,
    ) -> Dict[str, Any]:
        debug_log: List[str] = []
        t0 = time.time()
        used_fallback = False
        model = model or self.model

        def log(msg: str):
            debug_log.append(msg)
            try:
                logger.info(msg)
            except Exception:
                pass

        log(f"[run_prompt_debug] start; model={model}")
        log(f"[run_prompt_debug] prompt={prompt!r}")

        if force_text_only_fallback:
            log("[run_prompt_debug] force_text_only_fallback=True → run_text_only()")
            text = self.run_text_only(
                prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=total_timeout,
            )
            status = "ok" if not text.startswith("[TEXT_ONLY_ERROR]") else "error"
            return {
                "status": status,
                "text": text,
                "log": debug_log,
                "used_fallback": True,
                "elapsed": round(time.time() - t0, 2),
            }

        # Preflight: ping Ollama
        ping = self._ollama_generate(prompt=".", model=model, stream=False, timeout=5)
        if not ping["ok"]:
            log(
                f"[run_prompt_debug] preflight failed: {ping['error']} → fallback text_only"
            )
            used_fallback = True

        if not used_fallback:
            try:
                log("[run_prompt_debug] initializing OI stream ...")
                out_chunks: List[str] = []
                last_yield = time.time()
                for chunk in self._oi.chat(prompt, stream=True):
                    text = self._norm_piece(chunk)
                    if text:
                        out_chunks.append(text)
                        last_yield = time.time()
                    if time.time() - t0 > total_timeout:
                        raise TimeoutError("Soft timeout waiting OI output")
                    if time.time() - last_yield > 5 and not out_chunks:
                        raise TimeoutError("OI silent (no first token within 5s)")
                text_from_oi = "".join(out_chunks).strip()
                if text_from_oi:
                    log("[run_prompt_debug] got text from OI.")
                    return {
                        "status": "ok",
                        "text": text_from_oi,
                        "log": debug_log,
                        "used_fallback": False,
                        "elapsed": round(time.time() - t0, 2),
                    }
                else:
                    log("[run_prompt_debug] OI returned empty → fallback")
                    used_fallback = True
            except TimeoutError as te:
                log(f"[run_prompt_debug] TIMEOUT in OI: {te} → fallback text_only")
                used_fallback = True
            except Exception as e:
                log(f"[run_prompt_debug] ERROR in OI: {e} → fallback text_only")
                used_fallback = True

        # Fallback qua REST (non-stream)
        remain = max(5, total_timeout - int(time.time() - t0))
        text = self.run_text_only(
            prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=remain,
        )
        status = "ok" if not text.startswith("[TEXT_ONLY_ERROR]") else "error"
        log(
            f"[run_prompt_debug] fallback done; status={status}; elapsed={round(time.time()-t0,2)}s"
        )
        return {
            "status": status,
            "text": text,
            "log": debug_log,
            "used_fallback": True,
            "elapsed": round(time.time() - t0, 2),
        }

    # ---- Convenience: luôn trả về CHỈ CHỮ SỐ ----------------------------
    def run_compute_number(self, task_prompt: str, *, timeout: int = 40) -> str:
        """
        Chuỗi fallback: OI → text-only → trích số.
        Đảm bảo output là chuỗi số (vd '1073'). Nếu thất bại trả [NUM_ERROR].
        """
        # 1) thử OI (debug + fallback)
        res = self.run_prompt_debug(
            f"{task_prompt}\nAnswer with ONLY digits, no words.", total_timeout=timeout
        )
        txt = (res.get("text") or "").strip()
        m = re.search(r"\b\d+\b", txt)
        if m:
            return m.group(0)

        # 2) thử controller-python (cho tác vụ tính dễ)
        out = self.run_python_via_model(task_prompt)
        if out.isdigit():
            return out

        # 3) text-only ràng buộc
        txt2 = self.run_text_only(
            f"{task_prompt}\nAnswer with ONLY digits, no words.", timeout=timeout
        )
        m2 = re.search(r"\b\d+\b", txt2 or "")
        return m2.group(0) if m2 else f"[NUM_ERROR] {txt2[:120]}"
