"""Decision Engine for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DecisionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW = "review"
    EXECUTED = "executed"


class DecisionType(Enum):
    LEARNING = "learning"
    SECURITY = "security"
    ETHICS = "ethics"
    PERFORMANCE = "performance"
    QUALITY = "quality"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Decision:
    """Decision record"""

    decision_id: str
    decision_type: DecisionType
    status: DecisionStatus
    risk_level: RiskLevel
    description: str
    timestamp: datetime
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DecisionEngine:
    """Decision engine for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.decisions: list[Decision] = []
        self.logger.info("✅ DecisionEngine initialized")

    def make_decision(
        self,
        decision_type: DecisionType,
        description: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata: dict[str, Any] = None,
    ) -> Decision:
        """Make a decision"""
        try:
            decision_id = f"decision_{len(self.decisions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            decision = Decision(
                decision_id=decision_id,
                decision_type=decision_type,
                status=DecisionStatus.PENDING,
                risk_level=risk_level,
                description=description,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            self.decisions.append(decision)
            self.logger.info(f"🤔 Decision made: {decision_type.value} - {description}")
            return decision

        except Exception as e:
            self.logger.error(f"❌ Failed to make decision: {e}")
            raise

    def update_decision_status(self, decision_id: str, status: DecisionStatus) -> bool:
        """Update decision status"""
        try:
            for decision in self.decisions:
                if decision.decision_id == decision_id:
                    decision.status = status
                    self.logger.info(
                        f"📝 Decision status updated: {decision_id} -> {status.value}"
                    )
                    return True

            self.logger.warning(f"⚠️ Decision not found: {decision_id}")
            return False

        except Exception as e:
            self.logger.error(f"❌ Failed to update decision status: {e}")
            return False

    def get_decisions_by_type(self, decision_type: DecisionType) -> list[Decision]:
        """Get decisions by type"""
        return [d for d in self.decisions if d.decision_type == decision_type]

    def get_decisions_by_status(self, status: DecisionStatus) -> list[Decision]:
        """Get decisions by status"""
        return [d for d in self.decisions if d.status == status]

    def get_decision_summary(self) -> dict[str, Any]:
        """Get decision summary"""
        try:
            total_decisions = len(self.decisions)

            decisions_by_type = {}
            decisions_by_status = {}
            decisions_by_risk = {}

            for decision in self.decisions:
                # By type
                type_key = decision.decision_type.value
                decisions_by_type[type_key] = decisions_by_type.get(type_key, 0) + 1

                # By status
                status_key = decision.status.value
                decisions_by_status[status_key] = (
                    decisions_by_status.get(status_key, 0) + 1
                )

                # By risk
                risk_key = decision.risk_level.value
                decisions_by_risk[risk_key] = decisions_by_risk.get(risk_key, 0) + 1

            return {
                "total_decisions": total_decisions,
                "decisions_by_type": decisions_by_type,
                "decisions_by_status": decisions_by_status,
                "decisions_by_risk": decisions_by_risk,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get decision summary: {e}")
            return {"error": str(e)}

    def clear_decisions(self):
        """Clear all decisions"""
        self.decisions.clear()
        self.logger.info("🧹 All decisions cleared")
