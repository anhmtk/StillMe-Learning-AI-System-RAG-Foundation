# tests/test_agentdev_loop.py
# Mục tiêu: kiểm tra vòng lặp AgentDev ở mức đơn vị (unit)
# - Planner trả về 1 PlanItem
# - Executor áp dụng patch + chạy test
# - BugMemory ghi nhận khi fail
# - Ghi log JSONL ra logs/agentdev/...
#
# Test này là "skeleton": nếu agent_dev chưa có hàm target,
# nó sẽ xfail với lý do rõ ràng để team biết cần implement gì.

from __future__ import annotations
import json
from pathlib import Path
import datetime as dt
import pytest

try:
    # PlanItem dataclass tối thiểu đã được Cursor tạo trước đó
    from stillme_core.plan_types import PlanItem
except Exception as e:
    pytest.skip(f"Thiếu stillme_core.plan_types.PlanItem: {e}", allow_module_level=True)

@pytest.fixture
def sample_plan_item() -> PlanItem:
    # Điều chỉnh field theo dataclass thực tế của anh
    return PlanItem(
        id="P-001",
        title="Fix failing test in xyz",
        diff_hint="--- a/foo.py\n+++ b/foo.py\n@@ ...",
        tests_to_run=["tests/test_foo.py::test_bar"],
        risk="low",
        deps=[]
    )

class FakePlanner:
    def __init__(self, items):
        self._items = items

    def build_plan(self):
        # Cursor nên map test này vào planner.build_plan()
        return self._items

class FakeExecutor:
    def __init__(self, will_pass=True):
        self.will_pass = will_pass
        self.calls = 0

    def apply_patch_and_test(self, plan_item: PlanItem):
        # Cursor nên map test này vào executor.apply_patch_and_test()
        self.calls += 1
        return {"ok": self.will_pass, "tests_ran": plan_item.tests_to_run or []}

class FakeBugMemory:
    def __init__(self):
        self.records = []

    def record(self, *, file: str, test_name: str | None, message: str, fingerprint: str | None = None):
        # Cursor nên map test này vào bug_memory.record(...)
        self.records.append({"file": file, "test_name": test_name, "message": message, "fp": fingerprint})

@pytest.mark.parametrize("executor_ok", [True, False])
def test_agentdev_run_once(tmp_path: Path, sample_plan_item: PlanItem, executor_ok: bool, monkeypatch):
    """
    Kỳ vọng:
    - Khi executor_ok=True: vòng lặp trả True, tạo log JSONL.
    - Khi executor_ok=False: vòng lặp vẫn kết thúc, BugMemory.record được gọi >=1, tạo log JSONL.
    """
    # Import trễ để tránh ImportError sớm
    try:
        import agent_dev  # module chính
    except Exception as e:
        pytest.xfail(f"Chưa có module agent_dev hoặc lỗi import: {e}")

    # Chuẩn bị giả lập Planner/Executor/BugMemory
    planner = FakePlanner([sample_plan_item])
    executor = FakeExecutor(will_pass=executor_ok)
    bug_memory = FakeBugMemory()

    # Thư mục log cho test
    log_dir = tmp_path / "logs" / "agentdev"
    log_dir.mkdir(parents=True, exist_ok=True)

    # AgentDev nên cung cấp 1 hàm chạy 1 bước, ví dụ: agentdev_run_once(...)
    run_fn = getattr(agent_dev, "agentdev_run_once", None)
    if run_fn is None:
        pytest.xfail("Thiếu hàm agentdev_run_once(planner, executor, bug_memory, log_dir: Path) trong agent_dev.py")

    result = run_fn(planner=planner, executor=executor, bug_memory=bug_memory, log_dir=log_dir)

    # Hỗ trợ cả kiểu bool (cũ) lẫn dict (mới)
    if isinstance(result, dict):
        ok = result.get("ok")
    # sanity check cho schema mới
        assert "branch" in result
        assert isinstance(result.get("refined"), bool)
        assert isinstance(result.get("duration_ms", 0), int)
    else:
        ok = result  # bool cũ

    # Luôn có JSONL log
    jsonl_files = list(log_dir.glob("*.jsonl"))
    assert jsonl_files, "AgentDev should write JSONL logs"

    if executor_ok:
        assert ok is True, "Khi executor pass, agentdev_run_once nên trả ok=True"
        assert len(bug_memory.records) == 0, "Không nên ghi BugMemory khi pass"
    else:
        assert ok in (False, None), "Khi executor fail, nên trả ok=False/None"
        assert len(bug_memory.records) >= 1, "Phải ghi ít nhất 1 bản ghi BugMemory khi fail"


    # Kiểm tra log JSONL được tạo
    # Gợi ý đặt tên file theo ngày, ví dụ YYYYMMDD.jsonl
    today = dt.datetime.now().strftime("%Y%m%d")
    candidates = list((log_dir).glob(f"{today}.jsonl"))
    assert candidates, "Chưa tạo file log JSONL trong logs/agentdev"
    # Kiểm tra ít nhất 1 dòng JSON hợp lệ
    with candidates[0].open("r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        assert first_line, "File log rỗng"
        json.loads(first_line)  # hợp lệ JSON là đạt

def test_agentdev_refine_on_fail(tmp_path: Path, sample_plan_item: PlanItem):
    """
    (Tùy chọn) Skeleton kiểm tra "refine 1 lần" khi fail.
    Test này để Cursor thấy yêu cầu refine và có thể bổ sung sau.
    """
    pytest.xfail("TODO: Viết khi agent_dev hỗ trợ cơ chế refine-on-fail (lặp lại 1 lần).")
