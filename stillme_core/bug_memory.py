"""Bug Memory System for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BugRecord:
    """Bug record in memory"""

    id: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BugMemory:
    """Bug memory system for tracking and learning from bugs"""

    def __init__(self):
        self.logger = logger
        self.bugs: dict[str, BugRecord] = {}
        self.logger.info("✅ BugMemory initialized")

    def add_bug(self, bug_id: str, description: str, severity: str = "medium") -> bool:
        """Add a new bug to memory"""
        try:
            now = datetime.now()
            bug = BugRecord(
                id=bug_id,
                description=description,
                severity=severity,
                status="open",
                created_at=now,
                updated_at=now,
            )
            self.bugs[bug_id] = bug
            self.logger.info(f"🐛 Bug added: {bug_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to add bug {bug_id}: {e}")
            return False

    def get_bug(self, bug_id: str) -> BugRecord | None:
        """Get bug by ID"""
        return self.bugs.get(bug_id)

    def update_bug_status(self, bug_id: str, status: str) -> bool:
        """Update bug status"""
        if bug_id in self.bugs:
            self.bugs[bug_id].status = status
            self.bugs[bug_id].updated_at = datetime.now()
            self.logger.info(f"🔄 Bug {bug_id} status updated to {status}")
            return True
        return False

    def get_all_bugs(self) -> list[BugRecord]:
        """Get all bugs"""
        return list(self.bugs.values())

    def get_bugs_by_severity(self, severity: str) -> list[BugRecord]:
        """Get bugs by severity"""
        return [bug for bug in self.bugs.values() if bug.severity == severity]

    def clear_bugs(self):
        """Clear all bugs"""
        self.bugs.clear()
        self.logger.info("🧹 All bugs cleared")

    def record(self, file: str, test_name: str | None, message: str) -> bool:
        """Record a bug/error for AgentDev compatibility"""
        try:
            bug_id = f"{file}_{test_name or 'unknown'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            description = (
                f"File: {file}, Test: {test_name or 'N/A'}, Message: {message[:200]}"
            )
            return self.add_bug(bug_id, description, "medium")
        except Exception as e:
            self.logger.error(f"❌ Failed to record bug: {e}")
            return False
