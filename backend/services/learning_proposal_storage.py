"""
Learning Proposal Storage
Temporary storage for learning proposals while waiting for user permission
"""

import sqlite3
import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# SQLite Configuration
SQLITE_TIMEOUT = 10.0
MAX_RETRIES = 5
RETRY_DELAY_BASE = 0.1

# Proposal expiration: 24 hours
PROPOSAL_EXPIRATION_HOURS = 24


class LearningProposalStorage:
    """Manages temporary storage of learning proposals"""
    
    def __init__(self, db_path: str = "data/learning_proposals.db"):
        """
        Initialize learning proposal storage
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("Learning Proposal Storage initialized")
    
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
            
            # Learning proposals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    knowledge_snippet TEXT NOT NULL,
                    source TEXT,
                    knowledge_score REAL,
                    reason TEXT,
                    timestamp TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    user_response TEXT,
                    response_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT,
                    user_id TEXT,
                    feedback_type TEXT,
                    feedback_value REAL,
                    feedback_text TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES learning_proposals(proposal_id)
                )
            """)
            
            # Learning success tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_success_tracking (
                    tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT,
                    knowledge_snippet TEXT,
                    added_to_rag BOOLEAN,
                    added_at TEXT,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    user_satisfaction_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES learning_proposals(proposal_id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposal_status 
                ON learning_proposals(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposal_expires 
                ON learning_proposals(expires_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposal_user 
                ON learning_proposals(user_id)
            """)
            
            conn.commit()
            logger.info("Learning proposal database initialized")
        finally:
            conn.close()
    
    def save_proposal(
        self,
        proposal: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """
        Save learning proposal to storage
        
        Args:
            proposal: Learning proposal dict from ConversationLearningExtractor
            user_id: Optional user identifier
            
        Returns:
            proposal_id: Unique ID for the proposal
        """
        proposal_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=PROPOSAL_EXPIRATION_HOURS)).isoformat()
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_proposals (
                    proposal_id, user_id, knowledge_snippet, source,
                    knowledge_score, reason, timestamp, expires_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                user_id,
                proposal.get("knowledge_snippet", ""),
                proposal.get("source", "user_conversation"),
                proposal.get("knowledge_score", 0.0),
                proposal.get("reason", ""),
                proposal.get("timestamp", datetime.now().isoformat()),
                expires_at,
                "pending"
            ))
            conn.commit()
            logger.info(f"Saved learning proposal: {proposal_id}")
            return proposal_id
        finally:
            conn.close()
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve learning proposal by ID
        
        Args:
            proposal_id: Proposal ID
            
        Returns:
            Proposal dict or None if not found/expired
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT proposal_id, user_id, knowledge_snippet, source,
                       knowledge_score, reason, timestamp, expires_at, status,
                       user_response, response_timestamp
                FROM learning_proposals
                WHERE proposal_id = ? AND expires_at > ?
            """, (proposal_id, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "proposal_id": row[0],
                "user_id": row[1],
                "knowledge_snippet": row[2],
                "source": row[3],
                "knowledge_score": row[4],
                "reason": row[5],
                "timestamp": row[6],
                "expires_at": row[7],
                "status": row[8],
                "user_response": row[9],
                "response_timestamp": row[10]
            }
        finally:
            conn.close()
    
    def update_proposal_status(
        self,
        proposal_id: str,
        status: str,
        user_response: Optional[str] = None
    ) -> bool:
        """
        Update proposal status (accepted, declined, edited)
        
        Args:
            proposal_id: Proposal ID
            status: New status ('accepted', 'declined', 'edited')
            user_response: Optional user response text
            
        Returns:
            True if updated successfully
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE learning_proposals
                SET status = ?, user_response = ?, response_timestamp = ?
                WHERE proposal_id = ?
            """, (status, user_response, datetime.now().isoformat(), proposal_id))
            conn.commit()
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated proposal {proposal_id} status to {status}")
            return updated
        finally:
            conn.close()
    
    def add_feedback(
        self,
        proposal_id: str,
        feedback_type: str,
        feedback_value: Optional[float] = None,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Add user feedback for a learning proposal
        
        Args:
            proposal_id: Proposal ID
            feedback_type: Type of feedback ('satisfaction', 'usefulness', 'quality')
            feedback_value: Numeric feedback value (0.0-1.0)
            feedback_text: Optional text feedback
            user_id: Optional user identifier
            
        Returns:
            feedback_id: ID of the created feedback record
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_feedback (
                    proposal_id, user_id, feedback_type, feedback_value, feedback_text
                ) VALUES (?, ?, ?, ?, ?)
            """, (proposal_id, user_id, feedback_type, feedback_value, feedback_text))
            conn.commit()
            feedback_id = cursor.lastrowid
            logger.info(f"Added feedback for proposal {proposal_id}: {feedback_type}={feedback_value}")
            return feedback_id
        finally:
            conn.close()
    
    def track_learning_success(
        self,
        proposal_id: str,
        knowledge_snippet: str,
        added_to_rag: bool = True
    ) -> int:
        """
        Track learning success when content is added to RAG
        
        Args:
            proposal_id: Proposal ID
            knowledge_snippet: Knowledge snippet that was added
            added_to_rag: Whether content was successfully added
            
        Returns:
            tracking_id: ID of the tracking record
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_success_tracking (
                    proposal_id, knowledge_snippet, added_to_rag, added_at
                ) VALUES (?, ?, ?, ?)
            """, (
                proposal_id,
                knowledge_snippet,
                added_to_rag,
                datetime.now().isoformat() if added_to_rag else None
            ))
            conn.commit()
            tracking_id = cursor.lastrowid
            logger.info(f"Tracked learning success for proposal {proposal_id}: added_to_rag={added_to_rag}")
            return tracking_id
        finally:
            conn.close()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get learning statistics
        
        Returns:
            Dict with learning statistics
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Total proposals
            cursor.execute("SELECT COUNT(*) FROM learning_proposals")
            total_proposals = cursor.fetchone()[0]
            
            # Accepted proposals
            cursor.execute("SELECT COUNT(*) FROM learning_proposals WHERE status = 'accepted'")
            accepted = cursor.fetchone()[0]
            
            # Declined proposals
            cursor.execute("SELECT COUNT(*) FROM learning_proposals WHERE status = 'declined'")
            declined = cursor.fetchone()[0]
            
            # Pending proposals
            cursor.execute("SELECT COUNT(*) FROM learning_proposals WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            # Average knowledge score
            cursor.execute("SELECT AVG(knowledge_score) FROM learning_proposals")
            avg_score = cursor.fetchone()[0] or 0.0
            
            # Success rate (accepted / total)
            success_rate = (accepted / total_proposals * 100) if total_proposals > 0 else 0.0
            
            return {
                "total_proposals": total_proposals,
                "accepted": accepted,
                "declined": declined,
                "pending": pending,
                "average_knowledge_score": round(avg_score, 2),
                "success_rate": round(success_rate, 2)
            }
        finally:
            conn.close()
    
    def cleanup_expired_proposals(self) -> int:
        """
        Clean up expired proposals
        
        Returns:
            Number of proposals cleaned up
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM learning_proposals
                WHERE expires_at < ? AND status = 'pending'
            """, (datetime.now().isoformat(),))
            conn.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired proposals")
            return deleted
        finally:
            conn.close()


def get_learning_proposal_storage():
    """Get learning proposal storage service (singleton pattern)"""
    import backend.api.main as main_module
    if not hasattr(main_module, 'learning_proposal_storage'):
        main_module.learning_proposal_storage = LearningProposalStorage()
    return main_module.learning_proposal_storage

