"""Supervisor for StillMe Framework"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SupervisorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class LessonStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class LessonProposal:
    """Lesson proposal record"""
    proposal_id: str
    title: str
    description: str
    category: str
    difficulty: str
    estimated_duration: int  # minutes
    prerequisites: List[str]
    learning_objectives: List[str]
    status: LessonStatus
    created_by: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DailySupervisor:
    """Daily supervisor record"""
    supervisor_id: str
    date: datetime
    status: SupervisorStatus
    lessons_completed: int
    lessons_failed: int
    total_learning_time: int  # minutes
    performance_score: float
    notes: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class Supervisor:
    """Supervisor for StillMe Framework"""
    
    def __init__(self):
        self.logger = logger
        self.lesson_proposals: List[LessonProposal] = []
        self.daily_supervisors: List[DailySupervisor] = []
        self.supervisor_config = self._initialize_supervisor_config()
        self.logger.info("✅ Supervisor initialized")
    
    def _initialize_supervisor_config(self) -> Dict[str, Any]:
        """Initialize supervisor configuration"""
        return {
            "max_lessons_per_day": 10,
            "min_lesson_duration": 5,  # minutes
            "max_lesson_duration": 120,  # minutes
            "approval_required": True,
            "auto_approve_simple": False,
            "performance_threshold": 70.0,
            "learning_categories": [
                "programming",
                "security",
                "ethics",
                "performance",
                "maintenance"
            ]
        }
    
    def create_lesson_proposal(self, 
                              title: str,
                              description: str,
                              category: str,
                              difficulty: str = "medium",
                              estimated_duration: int = 30,
                              prerequisites: List[str] = None,
                              learning_objectives: List[str] = None,
                              created_by: str = "system") -> LessonProposal:
        """Create a new lesson proposal"""
        try:
            proposal_id = f"lesson_{len(self.lesson_proposals) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            proposal = LessonProposal(
                proposal_id=proposal_id,
                title=title,
                description=description,
                category=category,
                difficulty=difficulty,
                estimated_duration=estimated_duration,
                prerequisites=prerequisites or [],
                learning_objectives=learning_objectives or [],
                status=LessonStatus.PENDING,
                created_by=created_by,
                created_at=datetime.now()
            )
            
            self.lesson_proposals.append(proposal)
            self.logger.info(f"📚 Lesson proposal created: {title} (ID: {proposal_id})")
            return proposal
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create lesson proposal: {e}")
            raise
    
    def approve_lesson_proposal(self, proposal_id: str, approved_by: str) -> bool:
        """Approve a lesson proposal"""
        try:
            for proposal in self.lesson_proposals:
                if proposal.proposal_id == proposal_id:
                    proposal.status = LessonStatus.APPROVED
                    proposal.approved_by = approved_by
                    proposal.approved_at = datetime.now()
                    
                    self.logger.info(f"✅ Lesson proposal approved: {proposal.title} (ID: {proposal_id})")
                    return True
            
            self.logger.warning(f"⚠️ Lesson proposal not found: {proposal_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to approve lesson proposal: {e}")
            return False
    
    def reject_lesson_proposal(self, proposal_id: str, reason: str) -> bool:
        """Reject a lesson proposal"""
        try:
            for proposal in self.lesson_proposals:
                if proposal.proposal_id == proposal_id:
                    proposal.status = LessonStatus.REJECTED
                    proposal.metadata["rejection_reason"] = reason
                    
                    self.logger.info(f"❌ Lesson proposal rejected: {proposal.title} (ID: {proposal_id}) - {reason}")
                    return True
            
            self.logger.warning(f"⚠️ Lesson proposal not found: {proposal_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to reject lesson proposal: {e}")
            return False
    
    def get_pending_lesson_proposals(self) -> List[LessonProposal]:
        """Get pending lesson proposals"""
        return [p for p in self.lesson_proposals if p.status == LessonStatus.PENDING]
    
    def get_approved_lesson_proposals(self) -> List[LessonProposal]:
        """Get approved lesson proposals"""
        return [p for p in self.lesson_proposals if p.status == LessonStatus.APPROVED]
    
    def create_daily_supervisor(self, date: datetime = None) -> DailySupervisor:
        """Create daily supervisor record"""
        try:
            if date is None:
                date = datetime.now()
            
            supervisor_id = f"supervisor_{date.strftime('%Y%m%d')}"
            
            supervisor = DailySupervisor(
                supervisor_id=supervisor_id,
                date=date,
                status=SupervisorStatus.ACTIVE,
                lessons_completed=0,
                lessons_failed=0,
                total_learning_time=0,
                performance_score=0.0,
                notes=[]
            )
            
            self.daily_supervisors.append(supervisor)
            self.logger.info(f"📅 Daily supervisor created: {supervisor_id}")
            return supervisor
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create daily supervisor: {e}")
            raise
    
    def update_daily_supervisor(self, 
                               supervisor_id: str,
                               lessons_completed: int = None,
                               lessons_failed: int = None,
                               total_learning_time: int = None,
                               performance_score: float = None,
                               note: str = None) -> bool:
        """Update daily supervisor record"""
        try:
            for supervisor in self.daily_supervisors:
                if supervisor.supervisor_id == supervisor_id:
                    if lessons_completed is not None:
                        supervisor.lessons_completed = lessons_completed
                    if lessons_failed is not None:
                        supervisor.lessons_failed = lessons_failed
                    if total_learning_time is not None:
                        supervisor.total_learning_time = total_learning_time
                    if performance_score is not None:
                        supervisor.performance_score = performance_score
                    if note:
                        supervisor.notes.append(f"{datetime.now().isoformat()}: {note}")
                    
                    self.logger.info(f"📝 Daily supervisor updated: {supervisor_id}")
                    return True
            
            self.logger.warning(f"⚠️ Daily supervisor not found: {supervisor_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update daily supervisor: {e}")
            return False
    
    def get_daily_supervisor(self, date: datetime = None) -> Optional[DailySupervisor]:
        """Get daily supervisor for a specific date"""
        try:
            if date is None:
                date = datetime.now()
            
            supervisor_id = f"supervisor_{date.strftime('%Y%m%d')}"
            
            for supervisor in self.daily_supervisors:
                if supervisor.supervisor_id == supervisor_id:
                    return supervisor
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get daily supervisor: {e}")
            return None
    
    def get_supervisor_summary(self) -> Dict[str, Any]:
        """Get supervisor summary"""
        try:
            total_proposals = len(self.lesson_proposals)
            pending_proposals = len(self.get_pending_lesson_proposals())
            approved_proposals = len(self.get_approved_lesson_proposals())
            
            total_supervisors = len(self.daily_supervisors)
            active_supervisors = len([s for s in self.daily_supervisors if s.status == SupervisorStatus.ACTIVE])
            
            # Calculate average performance
            if self.daily_supervisors:
                avg_performance = sum(s.performance_score for s in self.daily_supervisors) / len(self.daily_supervisors)
            else:
                avg_performance = 0.0
            
            return {
                "total_lesson_proposals": total_proposals,
                "pending_proposals": pending_proposals,
                "approved_proposals": approved_proposals,
                "total_daily_supervisors": total_supervisors,
                "active_supervisors": active_supervisors,
                "average_performance": avg_performance,
                "supervisor_config": self.supervisor_config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get supervisor summary: {e}")
            return {"error": str(e)}
    
    def clear_data(self):
        """Clear all supervisor data"""
        self.lesson_proposals.clear()
        self.daily_supervisors.clear()
        self.logger.info("🧹 All supervisor data cleared")