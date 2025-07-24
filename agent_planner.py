import json
import logging
from pathlib import Path
from typing import Dict, List

# ---------------- CONFIG ----------------
PLANNER_MEMORY = Path("planner_memory.json")

logger = logging.getLogger("PlannerAgent")

class PlannerAgent:
    """
    Planner Agent: Chia nhỏ yêu cầu lớn thành task cụ thể.
    Dùng cho AgentDev như một "kiến trúc sư".
    """

    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict:
        """Load planner memory từ file JSON."""
        if PLANNER_MEMORY.exists():
            try:
                with open(PLANNER_MEMORY, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi load memory: {e}")
        return {"tasks": []}

    def _save_memory(self):
        """Lưu memory xuống file."""
        try:
            with open(PLANNER_MEMORY, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Lỗi save memory: {e}")

    def plan_project(self, project_desc: str) -> List[str]:
        """
        Phân tích yêu cầu project và chia thành task cụ thể.
        Ví dụ: "Xây web AI phân tích bệnh cây trồng"
        """
        logger.info(f"📋 Đang lập kế hoạch cho: {project_desc}")
        # Mô phỏng logic chia task
        tasks = [
            f"Phân tích yêu cầu: {project_desc}",
            "Tạo cấu trúc project (folders, modules)",
            "Viết module backend (API, database)",
            "Viết module AI (DeepSeek local + GPT-4o)",
            "Tạo frontend (React hoặc Next.js)",
            "Viết test tự động cho backend & AI",
            "Chạy thử và fix bug",
            "Tối ưu code và log performance"
        ]
        self.memory["tasks"].append({
            "project": project_desc,
            "tasks": tasks
        })
        self._save_memory()
        return tasks

    def get_all_projects(self) -> List[Dict]:
        """Lấy toàn bộ project đã lập kế hoạch."""
        return self.memory.get("tasks", [])
