# stillme_core/executor.py

"""
executor.py - Thực thi các bước trong kế hoạch AI tạo ra
Đọc JSON plan từ planner → thực hiện từng bước → log kết quả
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("StillmeCore-Executor")

class PlanExecutor:
    def __init__(self, plan: Dict[str, Any]):
        self.plan = plan
        self.module_name = plan.get("module_name", "unknown_module")
        self.steps = plan.get("steps", [])

    def execute(self) -> None:
        logger.info(f"🚀 Bắt đầu thực thi kế hoạch cho module: {self.module_name}")
        for step in self.steps:
            try:
                step_id = step.get("step_id", "unknown_step")
                action = step.get("action", "")
                reasoning = step.get("reasoning", "")
                logger.info(f"🔧 Thực thi bước {step_id}: {action}")
                self._perform_action(action, step_id)
                logger.info(f"✅ Hoàn thành bước {step_id}: {reasoning}")
            except Exception as e:
                logger.error(f"❌ Lỗi tại bước {step_id}: {e}")

    def _perform_action(self, action: str, step_id: str) -> None:
        """
        Đây là chỗ để định nghĩa hành động thật.
        Ví dụ: tạo file, ghi nội dung, sửa dòng code, v.v.
        Bản demo này chỉ ghi log – A có thể mở rộng dần.
        """
        simulated_file = Path(f"output/{self.module_name}_{step_id}.txt")
        simulated_file.parent.mkdir(parents=True, exist_ok=True)
        simulated_file.write_text(f"Simulated action: {action}\n")
