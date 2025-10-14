from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path.home() / ".stillme" / "state.json"
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_flag(key: str, default=False):
    return _load().get(key, default)


def set_flag(key: str, value: bool):
    data = _load()
    data[key] = bool(value)
    _save(data)