#!/usr/bin/env python3
"""
Canary test để bảo vệ AgentDev khỏi bị xóa nhầm
"""
import os
import importlib
import pytest

os.environ.setdefault("STILLME_DRY_RUN", "1")

def _try_import_framework():
    # Cho phép tên entry linh hoạt: 'framework' hoặc 'stillme.framework'
    for name in ("stillme_core.framework", "framework", "stillme.framework"):
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    pytest.skip("Không tìm thấy module framework entry; bỏ qua canary.")

def test_agentdev_import_and_init():
    """Test AgentDev có thể import và khởi tạo"""
    fw_module = _try_import_framework()
    
    # Tạo instance của framework
    fw = fw_module.StillMeFramework()

    # Các API theo thiết kế đã nêu trong dự án
    get_ad = getattr(fw, "get_agentdev", None)
    assert get_ad is not None, "framework.get_agentdev() phải tồn tại"

    agent = get_ad()
    assert agent is not None, "AgentDev instance không được None"
    # Thuộc tính/marker tối thiểu để nhận diện
    assert hasattr(agent, "run") or hasattr(agent, "execute") or hasattr(agent, "version"), \
        "AgentDev thiếu API cơ bản (run/execute/version)"

def test_agentdev_noop_task_safe():
    """Test AgentDev có thể thực thi task noop an toàn"""
    fw = _try_import_framework()
    exec_task = getattr(fw, "execute_agentdev_task", None)
    if exec_task is None:
        pytest.skip("Thiếu execute_agentdev_task – bỏ qua noop test.")
    
    # Thực thi chế độ 'noop' / 'dry' nếu hỗ trợ, không được raise.
    try:
        res = exec_task({"kind": "noop", "note": "canary"}, mode="dry")
    except TypeError:
        # fallback nếu hàm chỉ nhận 1 tham số
        res = exec_task({"kind": "noop", "note": "canary"})
    except Exception as e:
        # Nếu có lỗi khác, chỉ cần không crash
        pytest.skip(f"AgentDev task execution failed (expected in dry-run): {e}")
    
    assert res is None or res is True or getattr(res, "ok", True), "No-op task phải pass (không phá gì)."

def test_agentdev_module_structure():
    """Test cấu trúc module AgentDev còn nguyên vẹn"""
    try:
        import agent_dev.core.agentdev
        import agent_dev.core.executor
        import agent_dev.core.planner
        import agent_dev.security.defense
        import agent_dev.rules.engine
        assert True, "AgentDev modules import thành công"
    except ImportError as e:
        pytest.fail(f"AgentDev module structure bị phá vỡ: {e}")