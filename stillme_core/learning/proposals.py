"""
📚 StillMe IPC Learning Proposals System
=======================================

Hệ thống đề xuất học tập với Human-in-the-Loop approval.
Bảo vệ quyền riêng tư và kiểm soát hoàn toàn quá trình học tập.

Tính năng:
- Learning proposals generation
- Content analysis và risk assessment
- Human approval workflow
- Security và privacy protection
- Audit logging

Author: StillMe IPC (Intelligent Personal Companion)
Version: 1.0.0
Date: 2025-09-28
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ProposalStatus(Enum):
    """Trạng thái đề xuất học tập"""
    PENDING = "pending"           # Chờ phê duyệt
    APPROVED = "approved"         # Đã phê duyệt
    REJECTED = "rejected"         # Đã từ chối
    LEARNING = "learning"         # Đang học
    COMPLETED = "completed"       # Hoàn thành
    FAILED = "failed"            # Thất bại

class LearningPriority(Enum):
    """Mức độ ưu tiên học tập"""
    LOW = "low"                   # Thấp
    MEDIUM = "medium"             # Trung bình
    HIGH = "high"                 # Cao
    CRITICAL = "critical"         # Quan trọng

class ContentSource(Enum):
    """Nguồn nội dung học tập"""
    RSS = "rss"                   # RSS feeds
    EXPERIENCE = "experience"     # Kinh nghiệm cá nhân
    MANUAL = "manual"             # Nhập thủ công
    API = "api"                   # API calls
    COMMUNITY = "community"       # Đóng góp cộng đồng

@dataclass
class LearningProposal:
    """Đề xuất học tập"""
    id: str
    title: str
    description: str
    content: str
    source: ContentSource
    priority: LearningPriority
    estimated_duration: int  # minutes
    learning_objectives: List[str]
    prerequisites: List[str]
    expected_outcomes: List[str]
    risk_assessment: Dict[str, Any]
    quality_score: float  # 0.0 - 1.0
    created_at: datetime
    created_by: str  # "system" hoặc user_id
    status: ProposalStatus
    approval_required: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['source'] = self.source.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningProposal':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['source'] = ContentSource(data['source'])
        data['priority'] = LearningPriority(data['priority'])
        data['status'] = ProposalStatus(data['status'])
        return cls(**data)

class LearningProposalsManager:
    """Quản lý đề xuất học tập"""
    
    def __init__(self, db_path: str = "data/learning/proposals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    source TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    estimated_duration INTEGER,
                    learning_objectives TEXT,  -- JSON array
                    prerequisites TEXT,        -- JSON array
                    expected_outcomes TEXT,     -- JSON array
                    risk_assessment TEXT,       -- JSON object
                    quality_score REAL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approval_required BOOLEAN,
                    metadata TEXT,             -- JSON object
                    approved_at TEXT,
                    approved_by TEXT,
                    rejected_at TEXT,
                    rejected_by TEXT,
                    rejection_reason TEXT,
                    learning_started_at TEXT,
                    learning_completed_at TEXT,
                    learning_failed_at TEXT,
                    failure_reason TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposal_approvals (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    approver_id TEXT NOT NULL,
                    decision TEXT NOT NULL,  -- 'approved' or 'rejected'
                    reason TEXT,
                    approved_at TEXT NOT NULL,
                    FOREIGN KEY (proposal_id) REFERENCES proposals (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposal_learning_sessions (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    metrics TEXT,  -- JSON object
                    FOREIGN KEY (proposal_id) REFERENCES proposals (id)
                )
            """)
    
    def create_proposal(self, proposal: LearningProposal) -> str:
        """Tạo đề xuất học tập mới"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO proposals (
                        id, title, description, content, source, priority,
                        estimated_duration, learning_objectives, prerequisites,
                        expected_outcomes, risk_assessment, quality_score,
                        created_at, created_by, status, approval_required, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal.id, proposal.title, proposal.description,
                    proposal.content, proposal.source.value, proposal.priority.value,
                    proposal.estimated_duration, json.dumps(proposal.learning_objectives),
                    json.dumps(proposal.prerequisites), json.dumps(proposal.expected_outcomes),
                    json.dumps(proposal.risk_assessment), proposal.quality_score,
                    proposal.created_at.isoformat(), proposal.created_by,
                    proposal.status.value, proposal.approval_required,
                    json.dumps(proposal.metadata)
                ))
                
            logger.info(f"Created learning proposal: {proposal.id}")
            return proposal.id
            
        except Exception as e:
            logger.error(f"Failed to create proposal: {e}")
            raise
    
    def get_proposal(self, proposal_id: str) -> Optional[LearningProposal]:
        """Lấy đề xuất theo ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM proposals WHERE id = ?
                """, (proposal_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                data = dict(zip(columns, row))
                
                # Parse JSON fields
                data['learning_objectives'] = json.loads(data['learning_objectives'])
                data['prerequisites'] = json.loads(data['prerequisites'])
                data['expected_outcomes'] = json.loads(data['expected_outcomes'])
                data['risk_assessment'] = json.loads(data['risk_assessment'])
                data['metadata'] = json.loads(data['metadata'])
                
                return LearningProposal.from_dict(data)
                
        except Exception as e:
            logger.error(f"Failed to get proposal {proposal_id}: {e}")
            return None
    
    def get_pending_proposals(self, limit: int = 20) -> List[LearningProposal]:
        """Lấy danh sách đề xuất chờ phê duyệt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM proposals 
                    WHERE status = 'pending' 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                proposals = []
                for row in cursor.fetchall():
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    data['learning_objectives'] = json.loads(data['learning_objectives'])
                    data['prerequisites'] = json.loads(data['prerequisites'])
                    data['expected_outcomes'] = json.loads(data['expected_outcomes'])
                    data['risk_assessment'] = json.loads(data['risk_assessment'])
                    data['metadata'] = json.loads(data['metadata'])
                    
                    proposals.append(LearningProposal.from_dict(data))
                
                return proposals
                
        except Exception as e:
            logger.error(f"Failed to get pending proposals: {e}")
            return []
    
    def approve_proposal(self, proposal_id: str, approver_id: str, reason: str = "") -> bool:
        """Phê duyệt đề xuất"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update proposal status
                conn.execute("""
                    UPDATE proposals 
                    SET status = 'approved', approved_at = ?, approved_by = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), approver_id, proposal_id))
                
                # Add approval record
                approval_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO proposal_approvals (
                        id, proposal_id, approver_id, decision, reason, approved_at
                    ) VALUES (?, ?, ?, 'approved', ?, ?)
                """, (approval_id, proposal_id, approver_id, reason, datetime.now().isoformat()))
                
                logger.info(f"Approved proposal: {proposal_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to approve proposal {proposal_id}: {e}")
            return False
    
    def reject_proposal(self, proposal_id: str, approver_id: str, reason: str) -> bool:
        """Từ chối đề xuất"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update proposal status
                conn.execute("""
                    UPDATE proposals 
                    SET status = 'rejected', rejected_at = ?, rejected_by = ?, rejection_reason = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), approver_id, reason, proposal_id))
                
                # Add approval record
                approval_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO proposal_approvals (
                        id, proposal_id, approver_id, decision, reason, approved_at
                    ) VALUES (?, ?, ?, 'rejected', ?, ?)
                """, (approval_id, proposal_id, approver_id, reason, datetime.now().isoformat()))
                
                logger.info(f"Rejected proposal: {proposal_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to reject proposal {proposal_id}: {e}")
            return False
    
    def start_learning(self, proposal_id: str, session_id: str) -> bool:
        """Bắt đầu học tập"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update proposal status
                conn.execute("""
                    UPDATE proposals 
                    SET status = 'learning', learning_started_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), proposal_id))
                
                # Add learning session record
                learning_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO proposal_learning_sessions (
                        id, proposal_id, session_id, started_at, status
                    ) VALUES (?, ?, ?, ?, 'learning')
                """, (learning_id, proposal_id, session_id, datetime.now().isoformat()))
                
                logger.info(f"Started learning for proposal: {proposal_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start learning for proposal {proposal_id}: {e}")
            return False
    
    def complete_learning(self, proposal_id: str, session_id: str, metrics: Dict[str, Any]) -> bool:
        """Hoàn thành học tập"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update proposal status
                conn.execute("""
                    UPDATE proposals 
                    SET status = 'completed', learning_completed_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), proposal_id))
                
                # Update learning session
                conn.execute("""
                    UPDATE proposal_learning_sessions 
                    SET status = 'completed', completed_at = ?, metrics = ?
                    WHERE proposal_id = ? AND session_id = ?
                """, (datetime.now().isoformat(), json.dumps(metrics), proposal_id, session_id))
                
                logger.info(f"Completed learning for proposal: {proposal_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to complete learning for proposal {proposal_id}: {e}")
            return False
    
    def get_proposal_stats(self) -> Dict[str, Any]:
        """Lấy thống kê đề xuất"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(quality_score) as avg_quality,
                        AVG(estimated_duration) as avg_duration
                    FROM proposals 
                    GROUP BY status
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    status, count, avg_quality, avg_duration = row
                    stats[status] = {
                        'count': count,
                        'avg_quality': avg_quality or 0,
                        'avg_duration': avg_duration or 0
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get proposal stats: {e}")
            return {}

def get_proposals_manager() -> LearningProposalsManager:
    """Get proposals manager instance"""
    return LearningProposalsManager()

def create_sample_proposal() -> LearningProposal:
    """Tạo đề xuất mẫu"""
    return LearningProposal(
        id=str(uuid.uuid4()),
        title="Học về Machine Learning với Python",
        description="Nghiên cứu các thuật toán machine learning cơ bản và ứng dụng thực tế",
        content="Machine Learning là một lĩnh vực của AI...",
        source=ContentSource.MANUAL,
        priority=LearningPriority.HIGH,
        estimated_duration=120,  # 2 hours
        learning_objectives=[
            "Hiểu các thuật toán ML cơ bản",
            "Thực hành với Python và scikit-learn",
            "Áp dụng vào dự án thực tế"
        ],
        prerequisites=[
            "Kiến thức Python cơ bản",
            "Hiểu toán học cơ bản"
        ],
        expected_outcomes=[
            "Có thể implement các thuật toán ML",
            "Hiểu được cách chọn model phù hợp",
            "Có thể đánh giá performance của model"
        ],
        risk_assessment={
            "complexity": "medium",
            "time_required": "high",
            "prerequisites": "low",
            "practical_value": "high"
        },
        quality_score=0.85,
        created_at=datetime.now(),
        created_by="system",
        status=ProposalStatus.PENDING,
        approval_required=True,
        metadata={
            "tags": ["machine_learning", "python", "ai"],
            "difficulty": "intermediate",
            "category": "technical"
        }
    )
