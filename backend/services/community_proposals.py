"""
Community Proposals Service
Manages community proposals for learning sources and content
"""

import sqlite3
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# SQLite Configuration
SQLITE_TIMEOUT = 10.0
MAX_RETRIES = 5
RETRY_DELAY_BASE = 0.1

# Voting thresholds
MIN_VOTES_TO_LEARN = 10  # Minimum votes required for a proposal to be learned
VOTE_COOLDOWN_HOURS = 24  # Cooldown period between votes from same user


class CommunityProposals:
    """Manages community proposals and voting"""
    
    def __init__(self, db_path: str = "data/community_proposals.db"):
        """
        Initialize community proposals service
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("Community Proposals service initialized")
    
    def _get_connection(self):
        """Get SQLite connection with timeout configuration"""
        conn = sqlite3.connect(self.db_path, timeout=SQLITE_TIMEOUT)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Proposals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    proposal_type TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    description TEXT,
                    proposer_id TEXT,
                    status TEXT DEFAULT 'pending',
                    votes_for INTEGER DEFAULT 0,
                    votes_against INTEGER DEFAULT 0,
                    total_votes INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    learned_at TEXT,
                    learning_cycle_id TEXT
                )
            """)
            
            # Votes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id),
                    UNIQUE(proposal_id, user_id)
                )
            """)
            
            # Learning queue table (tracks what's been learned and what's pending)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_queue (
                    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT,
                    content_title TEXT,
                    content_source TEXT,
                    status TEXT DEFAULT 'pending',
                    votes_received INTEGER DEFAULT 0,
                    votes_needed INTEGER DEFAULT 10,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    learned_at TEXT,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(proposal_id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposal_status 
                ON proposals(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposal_votes 
                ON proposals(total_votes DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_vote_user 
                ON votes(user_id, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status 
                ON learning_queue(status, priority DESC)
            """)
            
            conn.commit()
            logger.info("Community proposals database initialized")
        finally:
            conn.close()
    
    def create_proposal(
        self,
        proposal_type: str,
        source_url: str,
        description: str,
        proposer_id: Optional[str] = None
    ) -> str:
        """
        Create a new community proposal
        
        Args:
            proposal_type: Type of proposal (RSS Feed, Article, etc.)
            source_url: URL of the source
            description: Description of why this source is valuable
            proposer_id: Optional user identifier
            
        Returns:
            proposal_id: Unique ID for the proposal
        """
        proposal_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO proposals (
                    proposal_id, proposal_type, source_url, description,
                    proposer_id, status, votes_for, votes_against, total_votes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                proposal_type,
                source_url,
                description,
                proposer_id,
                "pending",
                0,
                0,
                0
            ))
            conn.commit()
            logger.info(f"Created proposal: {proposal_id}")
            return proposal_id
        finally:
            conn.close()
    
    def vote_on_proposal(
        self,
        proposal_id: str,
        user_id: str,
        vote_type: str  # "for" or "against"
    ) -> Dict[str, Any]:
        """
        Vote on a proposal
        
        Args:
            proposal_id: Proposal ID
            user_id: User identifier
            vote_type: "for" or "against"
            
        Returns:
            Dict with vote result and updated proposal stats
        """
        if vote_type not in ["for", "against"]:
            raise ValueError("vote_type must be 'for' or 'against'")
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if user already voted (within cooldown)
            cooldown_time = (datetime.now() - timedelta(hours=VOTE_COOLDOWN_HOURS)).isoformat()
            cursor.execute("""
                SELECT vote_id, vote_type, created_at
                FROM votes
                WHERE proposal_id = ? AND user_id = ? AND created_at > ?
            """, (proposal_id, user_id, cooldown_time))
            
            existing_vote = cursor.fetchone()
            if existing_vote:
                # User already voted, update vote
                old_vote_type = existing_vote[1]
                cursor.execute("""
                    UPDATE votes
                    SET vote_type = ?, created_at = ?
                    WHERE proposal_id = ? AND user_id = ?
                """, (vote_type, datetime.now().isoformat(), proposal_id, user_id))
                
                # Update proposal vote counts
                if old_vote_type == "for":
                    cursor.execute("""
                        UPDATE proposals
                        SET votes_for = votes_for - 1, total_votes = total_votes - 1
                        WHERE proposal_id = ?
                    """, (proposal_id,))
                else:
                    cursor.execute("""
                        UPDATE proposals
                        SET votes_against = votes_against - 1, total_votes = total_votes - 1
                        WHERE proposal_id = ?
                    """, (proposal_id,))
            else:
                # New vote
                cursor.execute("""
                    INSERT INTO votes (proposal_id, user_id, vote_type)
                    VALUES (?, ?, ?)
                """, (proposal_id, user_id, vote_type))
            
            # Update proposal vote counts
            if vote_type == "for":
                cursor.execute("""
                    UPDATE proposals
                    SET votes_for = votes_for + 1, total_votes = total_votes + 1,
                        updated_at = ?
                    WHERE proposal_id = ?
                """, (datetime.now().isoformat(), proposal_id))
            else:
                cursor.execute("""
                    UPDATE proposals
                    SET votes_against = votes_against + 1, total_votes = total_votes + 1,
                        updated_at = ?
                    WHERE proposal_id = ?
                """, (datetime.now().isoformat(), proposal_id))
            
            # Get updated proposal stats
            cursor.execute("""
                SELECT votes_for, votes_against, total_votes, status
                FROM proposals
                WHERE proposal_id = ?
            """, (proposal_id,))
            
            result = cursor.fetchone()
            votes_for, votes_against, total_votes, status = result
            
            # Check if proposal reached threshold
            votes_needed = max(0, MIN_VOTES_TO_LEARN - votes_for)
            if votes_for >= MIN_VOTES_TO_LEARN and status == "pending":
                cursor.execute("""
                    UPDATE proposals
                    SET status = 'approved'
                    WHERE proposal_id = ?
                """, (proposal_id,))
                status = "approved"
            
            conn.commit()
            
            return {
                "proposal_id": proposal_id,
                "votes_for": votes_for,
                "votes_against": votes_against,
                "total_votes": total_votes,
                "votes_needed": votes_needed,
                "status": status,
                "message": f"Vote recorded! {votes_for}/{MIN_VOTES_TO_LEARN} votes. {votes_needed} more needed." if votes_needed > 0 else "Proposal approved! Will be learned in next cycle."
            }
        finally:
            conn.close()
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal by ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT proposal_id, proposal_type, source_url, description,
                       proposer_id, status, votes_for, votes_against, total_votes,
                       created_at, updated_at, learned_at
                FROM proposals
                WHERE proposal_id = ?
            """, (proposal_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            votes_needed = max(0, MIN_VOTES_TO_LEARN - row[6])
            
            return {
                "proposal_id": row[0],
                "proposal_type": row[1],
                "source_url": row[2],
                "description": row[3],
                "proposer_id": row[4],
                "status": row[5],
                "votes_for": row[6],
                "votes_against": row[7],
                "total_votes": row[8],
                "votes_needed": votes_needed,
                "created_at": row[9],
                "updated_at": row[10],
                "learned_at": row[11]
            }
        finally:
            conn.close()
    
    def get_pending_proposals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get pending proposals sorted by votes"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT proposal_id, proposal_type, source_url, description,
                       votes_for, votes_against, total_votes, created_at
                FROM proposals
                WHERE status = 'pending'
                ORDER BY votes_for DESC, total_votes DESC, created_at DESC
                LIMIT ?
            """, (limit,))
            
            proposals = []
            for row in cursor.fetchall():
                votes_needed = max(0, MIN_VOTES_TO_LEARN - row[4])
                proposals.append({
                    "proposal_id": row[0],
                    "proposal_type": row[1],
                    "source_url": row[2],
                    "description": row[3],
                    "votes_for": row[4],
                    "votes_against": row[5],
                    "total_votes": row[6],
                    "votes_needed": votes_needed,
                    "created_at": row[7]
                })
            
            return proposals
        finally:
            conn.close()
    
    def get_learning_queue(self) -> Dict[str, Any]:
        """
        Get learning queue: what's been learned and what's pending
        
        Returns:
            Dict with 'learned' and 'pending' lists
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Get recently learned (last 10)
            cursor.execute("""
                SELECT proposal_id, content_title, content_source, learned_at
                FROM learning_queue
                WHERE status = 'learned'
                ORDER BY learned_at DESC
                LIMIT 10
            """)
            
            learned = []
            for row in cursor.fetchall():
                learned.append({
                    "proposal_id": row[0],
                    "title": row[1],
                    "source": row[2],
                    "learned_at": row[3]
                })
            
            # Get pending (top 10 by priority/votes)
            cursor.execute("""
                SELECT proposal_id, content_title, content_source,
                       votes_received, votes_needed, priority
                FROM learning_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, votes_received DESC
                LIMIT 10
            """)
            
            pending = []
            for row in cursor.fetchall():
                pending.append({
                    "proposal_id": row[0],
                    "title": row[1],
                    "source": row[2],
                    "votes_received": row[3],
                    "votes_needed": row[4],
                    "priority": row[5]
                })
            
            return {
                "learned": learned,
                "pending": pending
            }
        finally:
            conn.close()
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """
        Get daily voting statistics
        
        Returns:
            Dict with daily stats
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            
            # Votes today
            cursor.execute("""
                SELECT COUNT(*) FROM votes
                WHERE DATE(created_at) = ?
            """, (today,))
            votes_today = cursor.fetchone()[0]
            
            # Proposals created today
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE DATE(created_at) = ?
            """, (today,))
            proposals_today = cursor.fetchone()[0]
            
            # Proposals approved today
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE status = 'approved' AND DATE(updated_at) = ?
            """, (today,))
            approved_today = cursor.fetchone()[0]
            
            # Total pending proposals
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE status = 'pending'
            """)
            pending_total = cursor.fetchone()[0]
            
            # Total votes needed across all pending
            cursor.execute("""
                SELECT SUM(?) - SUM(votes_for) FROM proposals
                WHERE status = 'pending'
            """, (MIN_VOTES_TO_LEARN,))
            total_votes_needed = cursor.fetchone()[0] or 0
            
            return {
                "votes_today": votes_today,
                "proposals_today": proposals_today,
                "approved_today": approved_today,
                "pending_total": pending_total,
                "total_votes_needed": max(0, total_votes_needed)
            }
        finally:
            conn.close()


def get_community_proposals():
    """Get community proposals service (singleton pattern)"""
    import backend.api.main as main_module
    if not hasattr(main_module, 'community_proposals'):
        main_module.community_proposals = CommunityProposals()
    return main_module.community_proposals

