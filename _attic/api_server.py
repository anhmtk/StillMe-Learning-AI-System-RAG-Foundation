import inspect
import logging
import sys
import time
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import StillMeFramework from correct path
try:
    from stillme_core.framework import StillMeFramework as _StillMeFramework

    StillMeFramework = _StillMeFramework
except ImportError:
    # Fallback if framework not available
    class StillMeFramework:
        def __init__(self):
            pass


try:
    from stillme_core.safety_guard import (
        apply_policies,
        redact_output,
        safe_reply,
    )
except ImportError:
    # Fallback for environments without safety_guard
    class Decision:
        def __init__(self):
            self.blocked = False
            self.category = "safe"
            self.reason = "no_guard"
            self.redactions = []

    def apply_policies(content: str, policies=None):
        return Decision()

    def redact_output(output: str, sensitive_patterns=None):
        return output

    def safe_reply(content: str, context=None):
        return "Safe response generated"


app = FastAPI()
log = logging.getLogger("api")

# UTF-8 logging

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers.clear()
root.addHandler(handler)

sm = StillMeFramework()
# Framework tự động khởi tạo modules trong __init__


class AgentMode(str, Enum):
    """AgentDev mode enumeration"""

    FAST = "fast"
    SAFE = "safe"
    CODE = "code"
    REAL = "real"


class InferenceRequest(BaseModel):
    prompt: str
    locale: str = "vi"
    safety_mode: str = "maximum"


class DevAgentRequest(BaseModel):
    prompt: str
    mode: AgentMode = AgentMode.FAST
    params: dict[str, Any] | None = None


class DevAgentResponse(BaseModel):
    ok: bool
    mode: AgentMode
    output: str
    latency_ms: float
    error: str | None = None


def _call_framework(prompt: str, locale: str, safety: str):
    candidates = ["generate", "respond", "infer", "chat", "process_input", "process"]
    for name in candidates:
        fn = getattr(sm, name, None)
        if callable(fn):
            sig = inspect.signature(fn)
            kwargs = {}
            for p in sig.parameters.values():
                if p.name in ("prompt", "text"):
                    kwargs[p.name] = prompt
                elif p.name == "locale":
                    kwargs["locale"] = locale
                elif p.name in ("safety", "safety_mode"):
                    kwargs[p.name] = safety
            return fn(**kwargs)
    raise HTTPException(status_code=500, detail="No suitable framework method found")


def _normalize(result):
    blocked = bool(
        getattr(result, "blocked", False)
        if hasattr(result, "blocked")
        else result.get("blocked", False)
    )
    text = str(
        getattr(result, "text", "")
        if hasattr(result, "text")
        else result.get("text", "")
    )
    reason = (
        getattr(result, "reason", None)
        if hasattr(result, "reason")
        else result.get("reason")
    )
    return blocked, text, reason


@app.get("/health/ai")
def health_ai():
    count_fn = getattr(sm, "count_modules", None)
    count = count_fn() if callable(count_fn) else None
    return {"ok": True, "modules": count, "status": "ready"}


def _inference_common(req: InferenceRequest):
    t0 = time.perf_counter()

    # Apply safety guard before processing
    decision = apply_policies(req.prompt)

    if decision.blocked:
        # Blocked content - return safe response
        safe_text = safe_reply(decision.category, req.locale)
        return {
            "blocked": True,
            "text": safe_text,
            "reason": decision.reason,
            "latency_ms": (time.perf_counter() - t0) * 1000.0,
        }

    # Not blocked - process through framework
    res = _call_framework(req.prompt, req.locale, req.safety_mode)
    blocked, text, reason = _normalize(res)

    # Sanitize output and apply redactions
    if decision.redactions:
        text = redact_output(text)

    return {
        "blocked": blocked,
        "text": text,
        "reason": reason,
        "latency_ms": (time.perf_counter() - t0) * 1000.0,
    }


@app.post("/inference")
def inference(req: InferenceRequest):
    return _inference_common(req)


@app.post("/process")
def process(req: InferenceRequest):
    return _inference_common(req)


@app.post("/dev-agent", response_model=DevAgentResponse)
def dev_agent(req: DevAgentRequest):
    """AgentDev endpoint with proper mode handling"""
    t0 = time.perf_counter()

    try:
        # Import AgentDev functionality
        try:
            from stillme_core.core.ai_manager import dev_agent as dev_agent_func

            result = dev_agent_func(
                req.prompt, mode=req.mode.value, **(req.params or {})
            )
        except ImportError:
            # Fallback if AgentDev not available
            result = (
                f"AgentDev not available. Prompt: {req.prompt}, Mode: {req.mode.value}"
            )

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DevAgentResponse(
            ok=True, mode=req.mode, output=str(result), latency_ms=latency_ms
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return DevAgentResponse(
            ok=False, mode=req.mode, output="", latency_ms=latency_ms, error=str(e)
        )


@app.post("/dev-agent/bridge", response_model=DevAgentResponse)
def dev_agent_bridge(req: DevAgentRequest):
    """AgentDev bridge endpoint for internal communication"""
    return dev_agent(req)
