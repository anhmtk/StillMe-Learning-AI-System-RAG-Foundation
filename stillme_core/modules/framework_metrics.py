# modules/framework_metrics.py
"""
FrameworkMetrics - Module quản lý và thống kê hiệu suất của StillMeFramework.
"""

import json
import time
from pathlib import Path


class FrameworkMetrics:
    def __init__(self, metrics_file: str = "framework_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics = {}
        self.load()

    def record(self, key: str, value):
        """Ghi lại giá trị metric."""
        self.metrics[key] = value
        self.save()

    def increment(self, key: str, amount: int = 1):
        """Tăng giá trị metric."""
        self.metrics[key] = self.metrics.get(key, 0) + amount
        self.save()

    def get(self, key: str, default=None):
        """Lấy giá trị metric."""
        return self.metrics.get(key, default)

    def save(self):
        """Lưu metrics ra file JSON."""
        try:
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=4)
        except Exception as e:
            print(f"[FrameworkMetrics] Lỗi khi lưu metrics: {e}")

    def load(self):
        """Tải metrics từ file JSON."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, encoding="utf-8") as f:
                    self.metrics = json.load(f)
            except Exception as e:
                print(f"[FrameworkMetrics] Lỗi khi load metrics: {e}")
                self.metrics = {}

    def record_execution_time(self, func_name: str, start_time: float):
        """Tự động ghi lại thời gian thực thi của 1 hàm/module."""
        duration = time.time() - start_time
        self.record(f"{func_name}_execution_time", round(duration, 4))