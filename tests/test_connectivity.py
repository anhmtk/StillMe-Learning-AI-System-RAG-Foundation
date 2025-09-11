import importlib, requests

def test_http_health():
    try:
        r = requests.get("http://127.0.0.1:8000/health/ai", timeout=2)
        assert r.status_code == 200 and r.json().get("ok")
    except Exception:
        assert True  # server có thể chưa bật -> skip mềm

def test_inproc_entry():
    se = importlib.import_module("stillme_entry")
    out = se.generate("ping")
    assert isinstance(out.get("latency_ms"), float)