import hashlib
import json
from pathlib import Path
from typing import Dict, Any


class BugMemory:
    def __init__(self, storage: str = "bug_memory.jsonl"):
        self.path = Path(storage)

    @staticmethod
    def fingerprint(file: str, line: int | None, message: str) -> str:
        base = f"{file}:{line or 0}:{message}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def append(self, record: Dict[str, Any]) -> None:
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


