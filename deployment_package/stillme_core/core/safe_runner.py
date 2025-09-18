# stillme_core/safe_runner.py
from __future__ import annotations

import asyncio
from typing import Callable


class SafeRunner:
    """
    Stub: chạy code/test trong sandbox (Docker/Firejail/pytest).
    Ở đây mô phỏng: validate kết quả bằng callback test_fn.
    """

    def __init__(self, test_fn: Callable[[str], bool] | None = None):
        self.test_fn = test_fn or (lambda _: True)

    async def run_safe(self, plan_or_code: str) -> dict:
        # TODO: thực sự sandbox + pytest ở phiên bản đầy đủ
        await asyncio.sleep(0)  # yield
        ok = self.test_fn(plan_or_code)
        return {"ok": ok, "artifacts": {"log": "safe-run simulated"}}
