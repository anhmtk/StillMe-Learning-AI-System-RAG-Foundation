"""
Community Voting System
=======================

Hệ thống voting của cộng đồng cho learning proposals.
Khi đạt đủ vote (50-70), proposal sẽ tự động được approve.

Author: StillMe AI Framework
Version: 2.0.0
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VoteType(Enum):
    """Loại vote"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class CommunityRole(Enum):
    """Vai trò trong cộng đồng"""
    MEMBER = "member"
    CONTRIBUTOR = "contributor"
    MODERATOR = "moderator"
    ADMIN = "admin"


@dataclass
class CommunityVote:
    """Vote của cộng đồng"""
    id: str
    proposal_id: str
    user_id: str
    vote_type: VoteType
    created_at: datetime
    reason: Optional[str] = None


@dataclass
class CommunityProposal:
    """Proposal từ cộng đồng"""
    id: str
    title: str
    description: str
    content: str
    created_by: str
    created_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    total_votes: int = 0
    vote_threshold: int = 50  # Số vote cần để auto-approve
    status: str = "pending"  # pending, approved, rejected
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class CommunityVotingSystem:
    """Hệ thống voting của cộng đồng"""
    
    def __init__(self, db_path: str = "data/learning/community_voting.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Khởi tạo database"""
        with sqlite3.connect(self.db_path) as conn:
            # Community proposals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS community_proposals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    total_votes INTEGER DEFAULT 0,
                    vote_threshold INTEGER DEFAULT 50,
                    status TEXT DEFAULT 'pending',
                    approved_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Community votes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS community_votes (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reason TEXT,
                    FOREIGN KEY (proposal_id) REFERENCES community_proposals (id)
                )
            """)
            
            # Community users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS community_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'member',
                    created_at TEXT NOT NULL,
                    total_votes INTEGER DEFAULT 0,
                    reputation INTEGER DEFAULT 0
                )
            """)
    
    def create_proposal(self, title: str, description: str, content: str, 
                       created_by: str, vote_threshold: int = 50) -> str:
        """Tạo proposal mới từ cộng đồng"""
        proposal_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO community_proposals (
                    id, title, description, content, created_by, created_at,
                    vote_threshold, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id, title, description, content, created_by,
                datetime.now().isoformat(), vote_threshold,
                json.dumps({"source": "community", "auto_approve": True})
            ))
        
        logger.info(f"Created community proposal: {proposal_id}")
        return proposal_id
    
    def vote_proposal(self, proposal_id: str, user_id: str, 
                     vote_type: VoteType, reason: str = None) -> bool:
        """Vote cho proposal"""
        try:
            vote_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if user already voted
                existing = conn.execute("""
                    SELECT id FROM community_votes 
                    WHERE proposal_id = ? AND user_id = ?
                """, (proposal_id, user_id)).fetchone()
                
                if existing:
                    # Update existing vote
                    conn.execute("""
                        UPDATE community_votes 
                        SET vote_type = ?, reason = ?, created_at = ?
                        WHERE proposal_id = ? AND user_id = ?
                    """, (vote_type.value, reason, datetime.now().isoformat(), 
                          proposal_id, user_id))
                else:
                    # Create new vote
                    conn.execute("""
                        INSERT INTO community_votes (
                            id, proposal_id, user_id, vote_type, created_at, reason
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (vote_id, proposal_id, user_id, vote_type.value,
                          datetime.now().isoformat(), reason))
                
                # Update vote counts
                self._update_vote_counts(conn, proposal_id)
                
                # Check if threshold reached
                self._check_auto_approval(conn, proposal_id)
            
            logger.info(f"User {user_id} voted {vote_type.value} on proposal {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to vote on proposal {proposal_id}: {e}")
            return False
    
    def _update_vote_counts(self, conn: sqlite3.Connection, proposal_id: str):
        """Cập nhật số lượng vote"""
        # Count votes
        upvotes = conn.execute("""
            SELECT COUNT(*) FROM community_votes 
            WHERE proposal_id = ? AND vote_type = 'up'
        """, (proposal_id,)).fetchone()[0]
        
        downvotes = conn.execute("""
            SELECT COUNT(*) FROM community_votes 
            WHERE proposal_id = ? AND vote_type = 'down'
        """, (proposal_id,)).fetchone()[0]
        
        total_votes = upvotes + downvotes
        
        # Update proposal
        conn.execute("""
            UPDATE community_proposals 
            SET upvotes = ?, downvotes = ?, total_votes = ?
            WHERE id = ?
        """, (upvotes, downvotes, total_votes, proposal_id))
    
    def _check_auto_approval(self, conn: sqlite3.Connection, proposal_id: str):
        """Kiểm tra và tự động approve nếu đủ vote"""
        proposal = conn.execute("""
            SELECT upvotes, vote_threshold, status FROM community_proposals 
            WHERE id = ?
        """, (proposal_id,)).fetchone()
        
        if proposal and proposal[0] >= proposal[1] and proposal[2] == "pending":
            # Auto approve
            conn.execute("""
                UPDATE community_proposals 
                SET status = 'approved', approved_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), proposal_id))
            
            logger.info(f"Auto-approved community proposal {proposal_id} with {proposal[0]} votes")
            
            # TODO: Send notification to admin and community
            # TODO: Convert to learning proposal
    
    def get_proposal(self, proposal_id: str) -> Optional[CommunityProposal]:
        """Lấy thông tin proposal"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT id, title, description, content, created_by, created_at,
                       upvotes, downvotes, total_votes, vote_threshold, status,
                       approved_at, metadata
                FROM community_proposals WHERE id = ?
            """, (proposal_id,)).fetchone()
            
            if row:
                return CommunityProposal(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    content=row[3],
                    created_by=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    upvotes=row[6],
                    downvotes=row[7],
                    total_votes=row[8],
                    vote_threshold=row[9],
                    status=row[10],
                    approved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    metadata=json.loads(row[12]) if row[12] else {}
                )
        return None
    
    def get_pending_proposals(self, limit: int = 20) -> List[CommunityProposal]:
        """Lấy danh sách proposals đang chờ vote"""
        proposals = []
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, title, description, content, created_by, created_at,
                       upvotes, downvotes, total_votes, vote_threshold, status,
                       approved_at, metadata
                FROM community_proposals 
                WHERE status = 'pending'
                ORDER BY total_votes DESC, created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            for row in rows:
                proposals.append(CommunityProposal(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    content=row[3],
                    created_by=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    upvotes=row[6],
                    downvotes=row[7],
                    total_votes=row[8],
                    vote_threshold=row[9],
                    status=row[10],
                    approved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    metadata=json.loads(row[12]) if row[12] else {}
                ))
        
        return proposals
    
    def get_approved_proposals(self, limit: int = 20) -> List[CommunityProposal]:
        """Lấy danh sách proposals đã được approve"""
        proposals = []
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, title, description, content, created_by, created_at,
                       upvotes, downvotes, total_votes, vote_threshold, status,
                       approved_at, metadata
                FROM community_proposals 
                WHERE status = 'approved'
                ORDER BY approved_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            for row in rows:
                proposals.append(CommunityProposal(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    content=row[3],
                    created_by=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    upvotes=row[6],
                    downvotes=row[7],
                    total_votes=row[8],
                    vote_threshold=row[9],
                    status=row[10],
                    approved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    metadata=json.loads(row[12]) if row[12] else {}
                ))
        
        return proposals
    
    def get_voting_stats(self) -> Dict[str, Any]:
        """Lấy thống kê voting"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Total proposals
            stats["total_proposals"] = conn.execute("""
                SELECT COUNT(*) FROM community_proposals
            """).fetchone()[0]
            
            # Pending proposals
            stats["pending_proposals"] = conn.execute("""
                SELECT COUNT(*) FROM community_proposals WHERE status = 'pending'
            """).fetchone()[0]
            
            # Approved proposals
            stats["approved_proposals"] = conn.execute("""
                SELECT COUNT(*) FROM community_proposals WHERE status = 'approved'
            """).fetchone()[0]
            
            # Total votes
            stats["total_votes"] = conn.execute("""
                SELECT COUNT(*) FROM community_votes
            """).fetchone()[0]
            
            # Active voters
            stats["active_voters"] = conn.execute("""
                SELECT COUNT(DISTINCT user_id) FROM community_votes
            """).fetchone()[0]
            
        return stats
