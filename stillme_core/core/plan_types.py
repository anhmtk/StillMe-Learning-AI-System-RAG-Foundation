from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlanItem:
    id: str
    title: str
    action: str = "edit_file"
    target: Optional[str] = None
    patch: Optional[str] = None
    diff_hint: Optional[str] = None
    tests_to_run: list[str] = field(default_factory=list)
    risk: str = "low"
    deps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "action": self.action,
            "target": self.target,
            "patch": self.patch,
            "diff_hint": self.diff_hint,
            "tests_to_run": list(self.tests_to_run),
            "risk": self.risk,
            "deps": list(self.deps),
        }

    @staticmethod
    def from_dict(d: dict) -> "PlanItem":
        return PlanItem(
            id=str(d.get("id", "1")),
            title=str(d.get("title", "Untitled")),
            action=str(d.get("action", "edit_file")),
            target=d.get("target"),
            patch=d.get("patch"),
            diff_hint=d.get("diff_hint"),
            tests_to_run=list(d.get("tests_to_run", [])),
            risk=str(d.get("risk", "low")),
            deps=list(d.get("deps", [])),
        )
