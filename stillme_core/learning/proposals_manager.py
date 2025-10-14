"""
StillMe IPC Learning Proposals Manager
=====================================

Manager for learning proposals with database operations.
"""

from typing import TYPE_CHECKING
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ProposalsManager:
    """Manager for learning proposals"""

    def __init__(self, db_path: str = "data/learning/proposals.db") -> None:
        """Initialize proposals manager"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema"""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    learning_objectives TEXT NOT NULL,
                    prerequisites TEXT NOT NULL,
                    expected_outcomes TEXT NOT NULL,
                    estimated_duration INTEGER NOT NULL,
                    quality_score REAL NOT NULL,
                    source TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    created_by TEXT DEFAULT 'system',
                    approved_at TEXT,
                    approved_by TEXT,
                    rejected_at TEXT,
                    rejected_by TEXT,
                    rejection_reason TEXT,
                    session_id TEXT,
                    learning_started_at TEXT,
                    learning_completed_at TEXT,
                    learning_progress REAL DEFAULT 0,
                    current_objective INTEGER DEFAULT 0,
                    learning_notes TEXT,
                    last_updated TEXT,
                    final_progress REAL
                )
            """)

    def create_proposal(self, **kwargs) -> "LearningProposal":
        """Create a new learning proposal"""
        proposal_id = str(uuid.uuid4())

        # Create proposal data
        proposal_data = {
            "id": proposal_id,
            "title": kwargs.get("title", ""),
            "description": kwargs.get("description", ""),
            "learning_objectives": json.dumps(kwargs.get("learning_objectives", [])),
            "prerequisites": json.dumps(kwargs.get("prerequisites", [])),
            "expected_outcomes": json.dumps(kwargs.get("expected_outcomes", [])),
            "estimated_duration": kwargs.get("estimated_duration", 60),
            "quality_score": kwargs.get("quality_score", 0.8),
            "source": kwargs.get("source", "manual"),
            "priority": kwargs.get("priority", "medium"),
            "risk_assessment": json.dumps(kwargs.get("risk_assessment", {})),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        # Save to database

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO proposals (
                    id, title, description, learning_objectives, prerequisites,
                    expected_outcomes, estimated_duration, quality_score, source,
                    priority, risk_assessment, status, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                tuple(proposal_data.values()) + ("system",),
            )

        logger.info(f"Created learning proposal: {proposal_id}")

        # Create LearningProposal object
        return LearningProposal(
            id=proposal_id,
            title=proposal_data["title"],
            description=proposal_data["description"],
            learning_objectives=kwargs.get("learning_objectives", []),
            prerequisites=kwargs.get("prerequisites", []),
            expected_outcomes=kwargs.get("expected_outcomes", []),
            estimated_duration=proposal_data["estimated_duration"],
            quality_score=proposal_data["quality_score"],
            source=kwargs.get("source", "manual"),
            priority=kwargs.get("priority", "medium"),
            risk_assessment=kwargs.get("risk_assessment", {}),
            status="pending",
            created_at=datetime.now(),
        )

    def get_all_proposals(self) -> list["LearningProposal"]:
        """Get all proposals"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM proposals
                ORDER BY created_at DESC
            """)

            rows = cursor.fetchall()
            proposals = []

            for row in rows:
                # Handle None values safely
                learning_objectives = row[7] if row[7] else "[]"
                prerequisites = row[8] if row[8] else "[]"
                expected_outcomes = row[9] if row[9] else "[]"
                risk_assessment = row[10] if row[10] else "{}"

                try:
                    proposal = LearningProposal(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        learning_objectives=json.loads(learning_objectives),
                        prerequisites=json.loads(prerequisites),
                        expected_outcomes=json.loads(expected_outcomes),
                        estimated_duration=row[6],
                        quality_score=row[11],
                        source=row[4],
                        priority=row[5],
                        risk_assessment=json.loads(risk_assessment),
                        status=row[14],
                        created_at=datetime.fromisoformat(row[12]),
                    )
                    proposals.append(proposal)
                except Exception as e:
                    print(f"Error parsing proposal {row[0]}: {e}")
                    continue

            return proposals

    def get_pending_proposals(self, limit: int = 10) -> list["LearningProposal"]:
        """Get pending proposals"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM proposals
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            proposals = []

            for row in rows:
                # Handle None values safely
                learning_objectives = (
                    row[7] if row[7] else "[]"
                )  # Fixed: learning_objectives is at index 7
                prerequisites = (
                    row[8] if row[8] else "[]"
                )  # Fixed: prerequisites is at index 8
                expected_outcomes = (
                    row[9] if row[9] else "[]"
                )  # Fixed: expected_outcomes is at index 9
                risk_assessment = (
                    row[10] if row[10] else "{}"
                )  # risk_assessment is at index 10

                try:
                    proposal = LearningProposal(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        learning_objectives=json.loads(learning_objectives),
                        prerequisites=json.loads(prerequisites),
                        expected_outcomes=json.loads(expected_outcomes),
                        estimated_duration=row[6],
                        quality_score=row[11],  # Fixed: quality_score is at index 11
                        source=row[4],  # Fixed: source is at index 4
                        priority=row[5],  # Fixed: priority is at index 5
                        risk_assessment=json.loads(risk_assessment),
                        status=row[14],  # Fixed: status is at index 14
                        created_at=datetime.fromisoformat(row[12]),
                    )
                    proposals.append(proposal)
                except Exception as e:
                    print(f"Error parsing proposal {row[0]}: {e}")
                    # Create a simple proposal with basic data
                    try:
                        simple_proposal = LearningProposal(
                            id=row[0],
                            title=row[1] or "Untitled Proposal",
                            description=row[2] or "No description",
                            learning_objectives=[],
                            prerequisites=[],
                            expected_outcomes=[],
                            estimated_duration=row[6] or 60,
                            quality_score=row[7] or 0.5,
                            source=row[8] or "unknown",
                            priority=row[9] or "medium",
                            risk_assessment={},
                            status=row[11] or "pending",
                            created_at=datetime.fromisoformat(row[12])
                            if row[12]
                            else datetime.now(),
                        )
                        proposals.append(simple_proposal)
                    except Exception as e2:
                        print(f"Error creating simple proposal {row[0]}: {e2}")
                        continue

            return proposals

    def approve_proposal(self, proposal_id: str, approved_by: str) -> bool:
        """Approve a proposal"""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE proposals
                SET status = 'approved', approved_at = ?, approved_by = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), approved_by, proposal_id),
            )

        logger.info(f"Approved proposal: {proposal_id}")
        return True

    def update_proposal_status(self, proposal_id: str, status: str) -> bool:
        """Update proposal status"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE proposals SET status = ? WHERE id = ?",
                    (status, proposal_id),
                )
            logger.info(f"Updated proposal {proposal_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update proposal status: {e}")
            return False

    def update_proposal(self, proposal_id: str, updates: dict) -> bool:
        """Update proposal with new data"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic UPDATE query
                set_clauses = []
                values = []

                for key, value in updates.items():
                    if key in [
                        "learning_progress",
                        "current_objective",
                        "learning_notes",
                        "session_id",
                        "learning_started_at",
                        "learning_completed_at",
                        "last_updated",
                        "final_progress",
                    ]:
                        set_clauses.append(f"{key} = ?")
                        if isinstance(value, (list, dict)):
                            values.append(json.dumps(value))
                        else:
                            values.append(value)

                if set_clauses:
                    values.append(proposal_id)
                    query = (
                        f"UPDATE proposals SET {', '.join(set_clauses)} WHERE id = ?"
                    )
                    conn.execute(query, values)

            logger.info(f"Updated proposal {proposal_id} with {len(updates)} fields")
            return True
        except Exception as e:
            logger.error(f"Failed to update proposal: {e}")
            return False

    def get_proposal(self, proposal_id: str) -> None:
        """Get a specific proposal by ID"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
                )
                row = cursor.fetchone()

                if row:
                    # Parse the proposal data
                    return LearningProposal(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        learning_objectives=json.loads(row[3]) if row[3] else [],
                        prerequisites=json.loads(row[4]) if row[4] else [],
                        expected_outcomes=json.loads(row[5]) if row[5] else [],
                        estimated_duration=row[6],
                        quality_score=row[7],
                        source=row[8],
                        priority=row[9],
                        risk_assessment=json.loads(row[10]) if row[10] else {},
                        status=row[11],
                        created_at=datetime.fromisoformat(row[12])
                        if row[12]
                        else datetime.now(),
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get proposal {proposal_id}: {e}")
            return None

    def reject_proposal(
        self, proposal_id: str, rejected_by: str, reason: str = ""
    ) -> bool:
        """Reject a proposal"""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE proposals
                SET status = 'rejected', rejected_at = ?, rejected_by = ?, rejection_reason = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), rejected_by, reason, proposal_id),
            )

        logger.info(f"Rejected proposal: {proposal_id}")
        return True


class LearningProposal:
    """Learning proposal data class"""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", "")
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.learning_objectives = kwargs.get("learning_objectives", [])
        self.prerequisites = kwargs.get("prerequisites", [])
        self.expected_outcomes = kwargs.get("expected_outcomes", [])
        self.estimated_duration = kwargs.get("estimated_duration", 60)
        self.quality_score = kwargs.get("quality_score", 0.8)
        self.source = kwargs.get("source", "manual")
        self.priority = kwargs.get("priority", "medium")
        self.risk_assessment = kwargs.get("risk_assessment", {})
        self.status = kwargs.get("status", "pending")
        self.created_at = kwargs.get("created_at", datetime.now())