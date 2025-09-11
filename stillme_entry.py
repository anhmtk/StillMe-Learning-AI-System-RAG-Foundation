# stillme_entry.py  — PATCH v5 (fallback cứng sang template)

import time
from framework import StillMeFramework
try:
    from stillme_core.safety_guard import apply_policies, safe_reply, detect_locale, redact_output  # type: ignore
except ImportError:
    # Fallback for environments without safety_guard
    class Decision:
        def __init__(self):
            self.blocked = False
            self.category = 'safe'
            self.reason = 'no_guard'
            self.intent_scores = {}
            self.privacy_intent = False
            self.model_spec_intent = False
            self.jailbreak_intent = False
            self.redactions = []
    
    def apply_policies(prompt):
        return Decision()
    
    def safe_reply(category, locale, context=None):
        return "Safe response generated"
    
    def detect_locale(prompt):
        return "vi"
    
    def redact_output(text):
        return text

_sm = None

def _ensure_boot():
    global _sm
    if _sm is None:
        _sm = StillMeFramework()
        # Framework tự động khởi tạo modules trong __init__
    return _sm

def _try_methods(framework, prompt, locale, safety_mode):
    """Thử các method của framework để xử lý prompt"""
    # Thử theo danh sách tên hàm có thể tồn tại
    for name in ("process", "generate", "handle", "infer", "respond", "chat"):
        fn = getattr(framework, name, None)
        if callable(fn):
            try:
                # Thử với các tham số khác nhau
                sig = fn.__code__.co_varnames if hasattr(fn, '__code__') else []
                if "prompt" in sig:
                    out = fn(prompt=prompt)
                elif "text" in sig:
                    out = fn(text=prompt)
                else:
                    out = fn(prompt)
                
                # Chấp nhận các dạng phổ biến
                if isinstance(out, dict) and (out.get("text") or out.get("output")):
                    return out.get("text") or out.get("output")
                if isinstance(out, str) and out.strip():
                    return out
            except Exception:
                continue
    # Không có method phù hợp / output rỗng
    raise AttributeError("no_suitable_method")

def generate(prompt: str, locale: str = "vi", safety_mode: str = "maximum"):
    t0 = time.perf_counter()

    # Detect effective locale
    locale_eff = detect_locale(prompt)

    # Apply safety guard before processing
    decision = apply_policies(prompt)

    if decision.blocked:
        # Blocked content - return intelligent safe response with context
        context = {
            "intent_scores": getattr(decision, 'intent_scores', {}),
            "privacy_intent": getattr(decision, 'privacy_intent', False),
            "model_spec_intent": getattr(decision, 'model_spec_intent', False),
            "jailbreak_intent": getattr(decision, 'jailbreak_intent', False)
        }
        safe_text = safe_reply(decision.category, locale_eff, context)
        return {
            "blocked": True,
            "text": safe_text,
            "reason": decision.reason,
            "latency_ms": (time.perf_counter() - t0)*1000.0
        }

    # Not blocked - try framework first
    sm = _ensure_boot()
    try:
        # Thử gọi framework methods
        model_text = _try_methods(sm, prompt, locale, safety_mode)
        if model_text and model_text.strip():
            # Framework trả lời thành công
            out = model_text
            reason = "model_ok"
        else:
            # Framework trả lời rỗng - fallback to intelligent template
            context = {
                "intent_scores": getattr(decision, 'intent_scores', {}),
                "privacy_intent": getattr(decision, 'privacy_intent', False),
                "model_spec_intent": getattr(decision, 'model_spec_intent', False),
                "jailbreak_intent": getattr(decision, 'jailbreak_intent', False)
            }
            out = safe_reply(decision.category, locale_eff, context)
            reason = "fallback_template"
    except Exception:
        # Framework lỗi - fallback to intelligent template
        context = {
            "intent_scores": getattr(decision, 'intent_scores', {}),
            "privacy_intent": getattr(decision, 'privacy_intent', False),
            "model_spec_intent": getattr(decision, 'model_spec_intent', False),
            "jailbreak_intent": getattr(decision, 'jailbreak_intent', False)
        }
        out = safe_reply(decision.category, locale_eff, context)
        reason = "fallback_template"

    # Sanitize output and apply redactions
    if decision.redactions:
        out = redact_output(out)

    return {
        "blocked": False, 
        "text": out, 
        "reason": reason, 
        "latency_ms": (time.perf_counter() - t0)*1000.0
    }
