import inspect
import logging
import sys
import time

from fastapi import FastAPI, HTTPException  # type: ignore
from framework import StillMeFramework  # type: ignore
from pydantic import BaseModel  # type: ignore

try:
    from stillme_core.safety_guard import (  # type: ignore
        apply_policies,  # type: ignore
        redact_output,  # type: ignore
        safe_reply,  # type: ignore
    )
except ImportError:
    # Fallback for environments without safety_guard
    class Decision:
        def __init__(self):
            self.blocked = False
            self.category = "safe"
            self.reason = "no_guard"
            self.redactions = []

    def apply_policies(prompt):
        return Decision()

    def safe_reply(category, locale, context=None):
        return "Safe response generated"

    def redact_output(text):
        return text


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


class InferenceRequest(BaseModel):
    prompt: str
    locale: str = "vi"
    safety_mode: str = "maximum"


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
