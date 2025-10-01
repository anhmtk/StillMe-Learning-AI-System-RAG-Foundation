# tests/test_ai_manager_extended.py
import re

from stillme_core import controller, dev_agent, health, set_mode, warmup


def _ok_health():
    info = health()
    assert info.get("ollama_up") is True
    assert info.get("model_present") is True
    assert info.get("tiny_generate_ok") is True


def test_mode_switch_and_health_all():
    # fast -> llama3:8b
    assert "[MODEL]" in set_mode("fast")
    warmup()
    _ok_health()

    # code -> deepseek-coder:6.7b
    assert "[MODEL]" in set_mode("code")
    warmup()
    _ok_health()

    # think -> gpt-oss:20b
    assert "[MODEL]" in set_mode("think")
    warmup()
    _ok_health()


def test_fast_text_only_sanity():
    set_mode("fast")
    warmup()
    # ràng buộc câu trả lời cực ngắn, dễ pass
    out = dev_agent(
        "Reply with 'ok' only (lowercase). No punctuation, no spaces.", mode="fast"
    )
    assert out.strip().lower() == "ok"


def test_code_mode_python_exec_digits_only():
    set_mode("code")
    warmup()
    # dev_agent(mode='code') dùng run_python_via_model → controller chạy sandbox
    out = dev_agent("Compute 13*7 and print only the number.", mode="code")
    assert re.fullmatch(r"\d+", out.strip()) is not None
    assert out.strip() == "91"


def test_think_pipeline_ok():
    set_mode("think")
    warmup()
    # kiểm tra OI stream + fallback hoạt động (không treo, có text)
    res = controller().run_prompt_debug("In one short bullet, say hi.")
    assert res["status"] == "ok"
    assert isinstance(res.get("text"), str) and len(res["text"].strip()) > 0
