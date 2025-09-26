"""
Action Sandbox (skeleton)

Responsible for idempotency, dry-run execution, and side-effect guarding.
Phase 1: dry-run only, no side-effects performed.
"""

from __future__ import annotations

from typing import Any, Dict


class ActionSandbox:
    def __init__(self, *, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action safely. Phase 1: return dry-run acknowledgement.
        """
        return {
            "ok": True,
            "dry_run": self.dry_run,
            "action": action,
            "payload": payload,
        }


