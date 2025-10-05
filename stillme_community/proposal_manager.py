#!/usr/bin/env python3
"""
StillMe Community Proposal Manager
Quản lý đề xuất học tập từ cộng đồng với hệ thống voting tự động
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommunityProposalManager:
    """Quản lý đề xuất học tập từ cộng đồng"""
    
    def __init__(self, db_path: str = "data/community_proposals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Voting configuration
        self.vote_threshold = 50  # Số vote tối thiểu để approve
        self.voting_period = 7    # Số ngày voting
        self.auto_approve = True  # Tự động approve khi đạt threshold
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Khởi tạo database cho community proposals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tạo bảng proposals
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS community_proposals (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        learning_objectives TEXT NOT NULL,
                        category TEXT NOT NULL,
                        author TEXT NOT NULL,
                        source TEXT NOT NULL,
                        github_issue_url TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        upvotes INTEGER DEFAULT 0,
                        downvotes INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        voting_ends_at TIMESTAMP,
                        approved_at TIMESTAMP,
                        learning_session_id TEXT
                    )
                """)
                
                # Tạo bảng votes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proposal_votes (
                        id TEXT PRIMARY KEY,
                        proposal_id TEXT NOT NULL,
                        voter_id TEXT NOT NULL,
                        vote_type TEXT NOT NULL CHECK (vote_type IN ('up', 'down')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (proposal_id) REFERENCES community_proposals (id),
                        UNIQUE(proposal_id, voter_id)
                    )
                """)
                
                # Tạo bảng contributors
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS community_contributors (
                        username TEXT PRIMARY KEY,
                        proposals_count INTEGER DEFAULT 0,
                        votes_received INTEGER DEFAULT 0,
                        total_votes_given INTEGER DEFAULT 0,
                        first_contribution TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("✅ Community database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize community database: {e}")
            raise
    
    def submit_proposal(
        self,
        title: str,
        description: str,
        learning_objectives: List[str],
        category: str,
        author: str,
        source: str = "web_dashboard",
        github_issue_url: Optional[str] = None
    ) -> str:
        """Community member submits new learning proposal"""
        try:
            proposal_id = str(uuid.uuid4())
            voting_ends_at = datetime.now() + timedelta(days=self.voting_period)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO community_proposals 
                    (id, title, description, learning_objectives, category, author, 
                     source, github_issue_url, voting_ends_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal_id,
                    title,
                    description,
                    json.dumps(learning_objectives),
                    category,
                    author,
                    source,
                    github_issue_url,
                    voting_ends_at
                ))
                
                # Update contributor stats
                self._update_contributor_stats(author, "proposal_submitted")
                
                conn.commit()
                
            logger.info(f"✅ New proposal submitted: {title} by {author}")
            return proposal_id
            
        except Exception as e:
            logger.error(f"❌ Failed to submit proposal: {e}")
            raise
    
    def vote_proposal(self, proposal_id: str, voter_id: str, vote_type: str) -> bool:
        """Community votes on proposals (upvote/downvote)"""
        try:
            if vote_type not in ['up', 'down']:
                raise ValueError("Vote type must be 'up' or 'down'")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user already voted
                cursor.execute("""
                    SELECT vote_type FROM proposal_votes 
                    WHERE proposal_id = ? AND voter_id = ?
                """, (proposal_id, voter_id))
                
                existing_vote = cursor.fetchone()
                
                if existing_vote:
                    if existing_vote[0] == vote_type:
                        logger.info(f"User {voter_id} already voted {vote_type} on proposal {proposal_id}")
                        return False
                    else:
                        # Change vote
                        self._update_vote_counts(proposal_id, existing_vote[0], -1)
                        cursor.execute("""
                            UPDATE proposal_votes 
                            SET vote_type = ?, created_at = CURRENT_TIMESTAMP
                            WHERE proposal_id = ? AND voter_id = ?
                        """, (vote_type, proposal_id, voter_id))
                else:
                    # New vote
                    vote_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO proposal_votes (id, proposal_id, voter_id, vote_type)
                        VALUES (?, ?, ?, ?)
                    """, (vote_id, proposal_id, voter_id, vote_type))
                
                # Update vote counts
                self._update_vote_counts(proposal_id, vote_type, 1)
                
                # Update contributor stats
                self._update_contributor_stats(voter_id, "vote_given")
                
                conn.commit()
                
            logger.info(f"✅ Vote recorded: {voter_id} voted {vote_type} on {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record vote: {e}")
            raise
    
    def _update_vote_counts(self, proposal_id: str, vote_type: str, change: int) -> None:
        """Update vote counts for a proposal"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if vote_type == 'up':
                cursor.execute("""
                    UPDATE community_proposals 
                    SET upvotes = upvotes + ? 
                    WHERE id = ?
                """, (change, proposal_id))
            else:
                cursor.execute("""
                    UPDATE community_proposals 
                    SET downvotes = downvotes + ? 
                    WHERE id = ?
                """, (change, proposal_id))
    
    def check_approval_status(self, proposal_id: str) -> Optional[str]:
        """Auto-check if proposal reaches vote threshold"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT upvotes, downvotes, status, author
                    FROM community_proposals 
                    WHERE id = ?
                """, (proposal_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                upvotes, downvotes, status, author = result
                
                # Check if already processed
                if status != 'voting':
                    return status
                
                # Check approval criteria
                if (upvotes >= self.vote_threshold and 
                    upvotes > downvotes * 2):  # Upvotes must be at least 2x downvotes
                    
                    # Auto-approve if enabled
                    if self.auto_approve:
                        self._approve_proposal(proposal_id, author)
                        return 'approved'
                    else:
                        # Mark for manual approval
                        cursor.execute("""
                            UPDATE community_proposals 
                            SET status = 'ready_for_approval'
                            WHERE id = ?
                        """, (proposal_id,))
                        conn.commit()
                        return 'ready_for_approval'
                
                # Check if voting period expired
                cursor.execute("""
                    SELECT voting_ends_at FROM community_proposals 
                    WHERE id = ?
                """, (proposal_id,))
                
                voting_ends = cursor.fetchone()[0]
                if datetime.now() > datetime.fromisoformat(voting_ends):
                    cursor.execute("""
                        UPDATE community_proposals 
                        SET status = 'expired'
                        WHERE id = ?
                    """, (proposal_id,))
                    conn.commit()
                    return 'expired'
                
                return 'voting'
                
        except Exception as e:
            logger.error(f"❌ Failed to check approval status: {e}")
            return None
    
    def _approve_proposal(self, proposal_id: str, author: str) -> None:
        """Approve proposal and start learning"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update proposal status
                cursor.execute("""
                    UPDATE community_proposals 
                    SET status = 'approved', approved_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (proposal_id,))
                
                # Update contributor stats
                self._update_contributor_stats(author, "proposal_approved")
                
                conn.commit()
            
            logger.info(f"✅ Proposal {proposal_id} auto-approved by community!")
            
        except Exception as e:
            logger.error(f"❌ Failed to approve proposal: {e}")
            raise
    
    def _update_contributor_stats(self, username: str, action: str) -> None:
        """Update contributor statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update contributor
                cursor.execute("""
                    INSERT OR REPLACE INTO community_contributors 
                    (username, proposals_count, votes_received, total_votes_given, 
                     first_contribution, last_activity)
                    VALUES (
                        COALESCE((SELECT username FROM community_contributors WHERE username = ?), ?),
                        COALESCE((SELECT proposals_count FROM community_contributors WHERE username = ?), 0) + 
                        CASE WHEN ? = 'proposal_submitted' OR ? = 'proposal_approved' THEN 1 ELSE 0 END,
                        COALESCE((SELECT votes_received FROM community_contributors WHERE username = ?), 0) + 
                        CASE WHEN ? = 'proposal_approved' THEN 1 ELSE 0 END,
                        COALESCE((SELECT total_votes_given FROM community_contributors WHERE username = ?), 0) + 
                        CASE WHEN ? = 'vote_given' THEN 1 ELSE 0 END,
                        COALESCE((SELECT first_contribution FROM community_contributors WHERE username = ?), CURRENT_TIMESTAMP),
                        CURRENT_TIMESTAMP
                    )
                """, (username, username, username, action, action, username, action, 
                      username, action, username, username))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update contributor stats: {e}")
    
    def get_active_proposals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active proposals for voting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, description, learning_objectives, category, 
                           author, upvotes, downvotes, created_at, status
                    FROM community_proposals 
                    WHERE status = 'voting'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                proposals = []
                for row in cursor.fetchall():
                    proposals.append({
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'learning_objectives': json.loads(row[3]),
                        'category': row[4],
                        'author': row[5],
                        'upvotes': row[6],
                        'downvotes': row[7],
                        'created_at': row[8],
                        'status': row[9]
                    })
                
                return proposals
                
        except Exception as e:
            logger.error(f"❌ Failed to get active proposals: {e}")
            return []
    
    def get_contributors_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top contributors leaderboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT username, proposals_count, votes_received, total_votes_given
                    FROM community_contributors 
                    ORDER BY votes_received DESC, proposals_count DESC
                    LIMIT ?
                """, (limit,))
                
                contributors = []
                for i, row in enumerate(cursor.fetchall(), 1):
                    contributors.append({
                        'rank': i,
                        'username': row[0],
                        'proposals': row[1],
                        'votes_received': row[2],
                        'total_votes': row[3]
                    })
                
                return contributors
                
        except Exception as e:
            logger.error(f"❌ Failed to get contributors leaderboard: {e}")
            return []
    
    def get_dashboard_statistics(self) -> Dict[str, int]:
        """Get dashboard statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Active proposals
                cursor.execute("SELECT COUNT(*) FROM community_proposals WHERE status = 'voting'")
                active_proposals = cursor.fetchone()[0]
                
                # Total votes today
                cursor.execute("""
                    SELECT COUNT(*) FROM proposal_votes 
                    WHERE DATE(created_at) = DATE('now')
                """)
                votes_today = cursor.fetchone()[0]
                
                # Approved today
                cursor.execute("""
                    SELECT COUNT(*) FROM community_proposals 
                    WHERE DATE(approved_at) = DATE('now')
                """)
                approved_today = cursor.fetchone()[0]
                
                # Community members
                cursor.execute("SELECT COUNT(*) FROM community_contributors")
                community_members = cursor.fetchone()[0]
                
                return {
                    'active_proposals': active_proposals,
                    'votes_today': votes_today,
                    'approved_today': approved_today,
                    'community_members': community_members
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard statistics: {e}")
            return {
                'active_proposals': 0,
                'votes_today': 0,
                'approved_today': 0,
                'community_members': 0
            }
    
    def process_daily_voting(self) -> Dict[str, int]:
        """Process daily voting - check all proposals for approval"""
        try:
            logger.info("🔄 Processing daily community voting...")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all voting proposals
                cursor.execute("""
                    SELECT id, title, author FROM community_proposals 
                    WHERE status = 'voting'
                """)
                
                proposals = cursor.fetchall()
                processed = {'approved': 0, 'expired': 0, 'still_voting': 0}
                
                for proposal_id, title, author in proposals:
                    status = self.check_approval_status(proposal_id)
                    
                    if status == 'approved':
                        processed['approved'] += 1
                        logger.info(f"✅ Auto-approved: {title}")
                    elif status == 'expired':
                        processed['expired'] += 1
                        logger.info(f"⏰ Expired: {title}")
                    else:
                        processed['still_voting'] += 1
                
                logger.info(f"📊 Voting processed: {processed}")
                return processed
                
        except Exception as e:
            logger.error(f"❌ Failed to process daily voting: {e}")
            return {'approved': 0, 'expired': 0, 'still_voting': 0}


def main():
    """Test the Community Proposal Manager"""
    print("🎯 Testing StillMe Community Proposal Manager...")
    
    # Initialize manager
    manager = CommunityProposalManager()
    
    # Test proposal submission
    proposal_id = manager.submit_proposal(
        title="Learn Advanced Python Async Programming",
        description="StillMe should master async/await patterns and concurrent programming",
        learning_objectives=[
            "Master asyncio library fundamentals",
            "Implement async web scraping",
            "Build concurrent API clients"
        ],
        category="programming",
        author="test_user",
        source="test"
    )
    
    print(f"✅ Proposal submitted: {proposal_id}")
    
    # Test voting
    manager.vote_proposal(proposal_id, "voter1", "up")
    manager.vote_proposal(proposal_id, "voter2", "up")
    manager.vote_proposal(proposal_id, "voter3", "down")
    
    print("✅ Votes recorded")
    
    # Test statistics
    stats = manager.get_dashboard_statistics()
    print(f"📊 Dashboard stats: {stats}")
    
    # Test leaderboard
    contributors = manager.get_contributors_leaderboard()
    print(f"🏆 Top contributors: {contributors}")
    
    print("🎉 Community Proposal Manager test completed!")


if __name__ == "__main__":
    main()
