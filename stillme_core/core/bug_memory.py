import hashlib
import json
import time
from pathlib import Path
from typing import Any


class BugMemory:
    def __init__(self, storage: str = "bug_memory.jsonl"):
        self.path = Path(storage)

    @staticmethod
    def fingerprint(file: str, line: int | None, message: str) -> str:
        base = f"{file}:{line or 0}:{message}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def exists(self, fp: str) -> bool:
        if not self.path.exists():
            return False
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("fingerprint") == fp:
                        return True
                except Exception:
                    continue
        return False

    def find_similar(self, fingerprint: str) -> list[dict]:
        """Return records sharing same fingerprint."""
        results = []
        if not self.path.exists():
            return results
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("fingerprint") == fingerprint:
                        results.append(obj)
                except Exception:
                    continue
        return results

    def stats_by_file(self) -> dict:
        """Return {file: count} aggregated from memory."""
        stats: dict[str, int] = {}
        if not self.path.exists():
            return stats
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    file = obj.get("file") or ""
                    if file:
                        stats[file] = stats.get(file, 0) + 1
                except Exception:
                    continue
        return stats

    def record(
        self,
        file: str,
        test_name: str | None = None,
        message: str = "",
        line: int | None = None,
    ) -> None:
        """
        Record a bug/failure in memory.

        Args:
            file: File path where the issue occurred
            test_name: Name of the test that failed (optional)
            message: Error message or description
            line: Line number where issue occurred (optional)
        """
        fingerprint = self.fingerprint(file, line, message)

        # Check if this exact issue was already recorded
        if self.exists(fingerprint):
            return

        record = {
            "timestamp": json.dumps(
                {"$date": {"$numberLong": str(int(time.time() * 1000))}}
            ),
            "file": file,
            "test_name": test_name,
            "message": message,
            "line": line,
            "fingerprint": fingerprint,
        }

        self.append(record)