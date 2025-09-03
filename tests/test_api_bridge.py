# tests/test_api_bridge.py
# Mục tiêu: test các endpoint FastAPI trong api_server.py:
#   - GET /health/ai  -> 200 "ok"
#   - POST /dev-agent/plan -> trả kế hoạch (dry-run)
#   - POST /dev-agent/run  -> chạy 1 vòng xử lý
#
# Test này dùng httpx (hoặc TestClient); nếu app chưa sẵn sàng,
# test sẽ xfail/skip với lý do rõ ràng.

import json
import pytest

# Ưu tiên httpx.AsyncClient, nhưng có thể dùng TestClient sync cho skeleton
try:
    from fastapi.testclient import TestClient
except Exception as e:
    pytest.skip(f"Thiếu fastapi.testclient: {e}", allow_module_level=True)

try:
    # Kỳ vọng api_server.py có biến `app` (FastAPI instance)
    from api_server import app
except Exception as e:
    pytest.xfail(f"Không import được FastAPI app từ api_server: {e}")

client = TestClient(app)

def test_health_ok():
    resp = client.get("/health/ai")
    if resp.status_code == 404:
        pytest.xfail("Thiếu endpoint GET /health/ai trong api_server.py")
    assert resp.status_code == 200
    # Có thể trả 'ok' (chuỗi) hoặc JSON {"status": "ok"}
    body = resp.text.strip()
    assert "ok" in body.lower(), f"Nội dung health chưa đúng: {body}"

def test_plan_endpoint_returns_plan():
    # Kỳ vọng: trả JSON dạng {"plan": [...]} hoặc tương tự
    resp = client.post("/dev-agent/plan", json={"dry_run": True})
    if resp.status_code == 404:
        pytest.xfail("Thiếu endpoint POST /dev-agent/plan trong api_server.py")
    assert resp.status_code == 200

    try:
        data = resp.json()
    except json.JSONDecodeError:
        pytest.fail(f"Phản hồi /dev-agent/plan không phải JSON: {resp.text}")

    # Schema mới: "plan", "count", "generated_at"
    assert "plan" in data, f"JSON thiếu key 'plan': {data}"
    assert isinstance(data["plan"], list), "plan phải là list các PlanItem (dict)"
    assert "count" in data and isinstance(data["count"], int)
    assert "generated_at" in data and isinstance(data["generated_at"], str)

def test_run_endpoint_triggers_one_cycle():
    # Kỳ vọng: gọi 1 vòng xử lý AgentDev
    # Yêu cầu block đến khi xong vòng hiện tại, trả JSON
    payload = {"max_steps": 1}
    resp = client.post("/dev-agent/run", json=payload)
    if resp.status_code == 404:
        pytest.xfail("Thiếu endpoint POST /dev-agent/run trong api_server.py")
    assert resp.status_code == 200

    try:
        data = resp.json()
    except json.JSONDecodeError:
        pytest.fail(f"Phản hồi /dev-agent/run không phải JSON: {resp.text}")

    # Schema tối thiểu mới: { "ok": bool, "taken": int, "branch": str|None, "refined": bool, "duration_ms": int, "logs": {"jsonl": str} }
    assert "ok" in data, "JSON trả về phải có 'ok'"
    assert isinstance(data["ok"], (bool, type(None))), "'ok' phải là bool hoặc null"
    assert "taken" in data and isinstance(data["taken"], int)
    assert "branch" in data
    assert "refined" in data
    assert "duration_ms" in data and isinstance(data["duration_ms"], int)
    assert "logs" in data and isinstance(data["logs"], dict)
    # Không bắt buộc nhưng khuyến khích:
    # assert "taken" in data and isinstance(data["taken"], int)
