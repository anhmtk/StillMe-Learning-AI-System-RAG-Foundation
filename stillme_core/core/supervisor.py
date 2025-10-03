"""
Daily Supervisor for StillMe
Collects signals, proposes lessons, and creates knowledge packs
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("Supervisor")


@dataclass
class LessonProposal:
    """A proposed lesson for the system"""

    id: str
    title: str
    guideline: str
    examples: list[str]
    safety_notes: str
    success_criteria: str
    created_at: str
    source: str


@dataclass
class KnowledgePack:
    """A knowledge pack containing approved lessons"""

    id: str
    version: str
    created_at: str
    lessons: list[LessonProposal]
    summary: str


class DailySupervisor:
    """
    Daily supervisor that collects signals and proposes lessons
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.lesson_proposals_dir = self.repo_root / "lesson_proposals"
        self.knowledge_packs_dir = self.repo_root / "knowledge_packs"
        self.logs_dir = self.repo_root / "logs"

        # Ensure directories exist
        self.lesson_proposals_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_packs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def collect_signals(self) -> dict[str, Any]:
        """Collect signals from logs and memory"""
        signals = {
            "timestamp": datetime.now().isoformat(),
            "agentdev_logs": [],
            "memory_usage": {},
            "error_patterns": [],
            "performance_metrics": {},
        }

        # Collect AgentDev logs
        agentdev_log_file = self.logs_dir / "agentdev.jsonl"
        if agentdev_log_file.exists():
            try:
                with open(agentdev_log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    # Get last 10 entries
                    for line in lines[-10:]:
                        try:
                            log_entry = json.loads(line.strip())
                            signals["agentdev_logs"].append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.warning(f"Failed to read AgentDev logs: {e}")

        # Collect memory usage (if available)
        try:
            from .sul import get_sul

            sul = get_sul()
            memory_analysis = sul.get_dependencies("layered_memory_v1")
            signals["memory_usage"] = {
                "risk_score": memory_analysis.get("risk_score", 0.0),
                "test_files": memory_analysis.get("test_files", []),
            }
        except Exception as e:
            logger.warning(f"Failed to collect memory signals: {e}")

        # Analyze error patterns from logs
        error_patterns = []
        for log_entry in signals["agentdev_logs"]:
            if not log_entry.get("ok", True):
                error_patterns.append(
                    {
                        "action": log_entry.get("action", "unknown"),
                        "error": log_entry.get("stdout_tail", ""),
                        "timestamp": log_entry.get("timestamp", ""),
                    }
                )
        signals["error_patterns"] = error_patterns

        return signals

    def propose_lessons(self, signals: dict[str, Any]) -> list[LessonProposal]:
        """Generate lesson proposals based on collected signals"""
        proposals = []

        # Lesson 1: Memory Module Stability
        if signals.get("memory_usage", {}).get("risk_score", 0) > 0.5:
            proposals.append(
                LessonProposal(
                    id="memory_stability_001",
                    title="Memory Module Stability Best Practices",
                    guideline="Always test memory operations in isolation before integration. Use proper async handling and error recovery.",
                    examples=[
                        "Test encryption/decryption separately",
                        "Handle async operations with proper event loop checks",
                        "Implement fallback mechanisms for failed operations",
                    ],
                    safety_notes="Memory operations are critical - always have backup and recovery mechanisms",
                    success_criteria="All memory tests pass with 100% success rate",
                    created_at=datetime.now().isoformat(),
                    source="memory_analysis",
                )
            )

        # Lesson 2: Error Handling Patterns
        error_patterns = signals.get("error_patterns", [])
        if error_patterns:
            proposals.append(
                LessonProposal(
                    id="error_handling_001",
                    title="Robust Error Handling in AgentDev",
                    guideline="Implement comprehensive error handling with proper logging and recovery mechanisms.",
                    examples=[
                        "Use try-catch blocks around critical operations",
                        "Log errors with sufficient context",
                        "Provide fallback behaviors for common failures",
                    ],
                    safety_notes="Never let unhandled exceptions crash the system",
                    success_criteria="Zero unhandled exceptions in production logs",
                    created_at=datetime.now().isoformat(),
                    source="error_analysis",
                )
            )

        # Lesson 3: Test Coverage
        if len(signals.get("agentdev_logs", [])) > 0:
            proposals.append(
                LessonProposal(
                    id="test_coverage_001",
                    title="Comprehensive Test Coverage",
                    guideline="Maintain high test coverage for all critical components, especially memory and async operations.",
                    examples=[
                        "Write unit tests for all public methods",
                        "Include integration tests for complex workflows",
                        "Test edge cases and error conditions",
                    ],
                    safety_notes="Tests should cover both happy path and failure scenarios",
                    success_criteria="Test coverage > 90% for critical modules",
                    created_at=datetime.now().isoformat(),
                    source="test_analysis",
                )
            )

        return proposals

    def save_lesson_proposals(self, proposals: list[LessonProposal]) -> str:
        """Save lesson proposals to file"""
        today = datetime.now().strftime("%Y%m%d")
        proposals_file = self.lesson_proposals_dir / f"{today}.json"

        proposals_data = {
            "date": today,
            "proposals": [asdict(proposal) for proposal in proposals],
            "count": len(proposals),
        }

        with open(proposals_file, "w", encoding="utf-8") as f:
            json.dump(proposals_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(proposals)} lesson proposals to {proposals_file}")
        return str(proposals_file)

    def approve_lessons(self, proposal_ids: list[str]) -> KnowledgePack:
        """Create knowledge pack from approved lesson proposals"""
        today = datetime.now().strftime("%Y%m%d")
        proposals_file = self.lesson_proposals_dir / f"{today}.json"

        if not proposals_file.exists():
            raise FileNotFoundError(f"No proposals found for {today}")

        with open(proposals_file, encoding="utf-8") as f:
            proposals_data = json.load(f)

        # Filter approved proposals
        all_proposals = [LessonProposal(**p) for p in proposals_data["proposals"]]
        approved_proposals = [p for p in all_proposals if p.id in proposal_ids]

        if not approved_proposals:
            raise ValueError("No approved proposals found")

        # Create knowledge pack
        pack_id = f"pack_{today}_{len(approved_proposals)}"
        knowledge_pack = KnowledgePack(
            id=pack_id,
            version="1.0",
            created_at=datetime.now().isoformat(),
            lessons=approved_proposals,
            summary=f"Knowledge pack containing {len(approved_proposals)} approved lessons",
        )

        # Save knowledge pack
        pack_file = self.knowledge_packs_dir / f"{pack_id}.json"
        with open(pack_file, "w", encoding="utf-8") as f:
            json.dump(asdict(knowledge_pack), f, ensure_ascii=False, indent=2)

        logger.info(
            f"Created knowledge pack {pack_id} with {len(approved_proposals)} lessons"
        )
        return knowledge_pack

    def get_current_proposals(self) -> list[LessonProposal]:
        """Get today's lesson proposals"""
        today = datetime.now().strftime("%Y%m%d")
        proposals_file = self.lesson_proposals_dir / f"{today}.json"

        if not proposals_file.exists():
            return []

        with open(proposals_file, encoding="utf-8") as f:
            proposals_data = json.load(f)

        return [LessonProposal(**p) for p in proposals_data["proposals"]]

    def get_latest_knowledge_pack(self) -> KnowledgePack | None:
        """Get the latest knowledge pack"""
        if not self.knowledge_packs_dir.exists():
            return None

        pack_files = list(self.knowledge_packs_dir.glob("pack_*.json"))
        if not pack_files:
            return None

        # Get the most recent pack
        latest_pack = max(pack_files, key=lambda p: p.stat().st_mtime)

        with open(latest_pack, encoding="utf-8") as f:
            pack_data = json.load(f)

        # Convert lessons back to LessonProposal objects
        lessons = [LessonProposal(**lesson) for lesson in pack_data.get("lessons", [])]

        return KnowledgePack(
            id=pack_data["id"],
            version=pack_data["version"],
            created_at=pack_data["created_at"],
            lessons=lessons,
            summary=pack_data["summary"],
        )


# Global supervisor instance
_supervisor_instance: DailySupervisor | None = None


def get_supervisor() -> DailySupervisor:
    """Get global supervisor instance"""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = DailySupervisor()
    return _supervisor_instance
