"""
Knowledge Retention System for StillMe
Implements meta-learning capabilities for long-term knowledge storage
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KnowledgeRetention:
    """System for retaining and managing learned knowledge"""
    
    def __init__(self, db_path: str = "data/knowledge_retention.db"):
        """Initialize knowledge retention system
        
        Args:
            db_path: Path to SQLite database for knowledge storage
        """
        self.db_path = db_path
        self._init_database()
        logger.info("Knowledge Retention system initialized")
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Knowledge items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.0,
                    retention_score REAL DEFAULT 0.0,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Learning sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT NOT NULL,
                    content_learned TEXT NOT NULL,
                    accuracy_score REAL DEFAULT 0.0,
                    retention_improvement REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Knowledge relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES knowledge_items (id),
                    FOREIGN KEY (target_id) REFERENCES knowledge_items (id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Knowledge retention database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_knowledge(self, 
                     content: str, 
                     source: str, 
                     knowledge_type: str = "general",
                     confidence_score: float = 0.5,
                     metadata: Optional[Dict[str, Any]] = None) -> int:
        """Add new knowledge item
        
        Args:
            content: Knowledge content
            source: Source of knowledge
            knowledge_type: Type of knowledge
            confidence_score: Initial confidence (0-1)
            metadata: Additional metadata
            
        Returns:
            int: Knowledge item ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO knowledge_items 
                (content, source, knowledge_type, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                content, 
                source, 
                knowledge_type, 
                confidence_score,
                json.dumps(metadata or {})
            ))
            
            knowledge_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Added knowledge item {knowledge_id}: {content[:50]}...")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return -1
    
    def update_retention_score(self, knowledge_id: int, new_score: float) -> bool:
        """Update retention score for knowledge item
        
        Args:
            knowledge_id: ID of knowledge item
            new_score: New retention score (0-1)
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE knowledge_items 
                SET retention_score = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_score, knowledge_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated retention score for knowledge {knowledge_id}: {new_score}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update retention score: {e}")
            return False
    
    def get_retained_knowledge(self, 
                              knowledge_type: Optional[str] = None,
                              min_retention_score: float = 0.7,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get knowledge items with high retention scores
        
        Args:
            knowledge_type: Filter by knowledge type
            min_retention_score: Minimum retention score
            limit: Maximum number of items to return
            
        Returns:
            List of knowledge items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT id, content, source, knowledge_type, confidence_score, 
                       retention_score, access_count, last_accessed, metadata
                FROM knowledge_items 
                WHERE retention_score >= ?
            """
            params = [min_retention_score]
            
            if knowledge_type:
                query += " AND knowledge_type = ?"
                params.append(knowledge_type)
            
            query += " ORDER BY retention_score DESC, access_count DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            knowledge_items = []
            for row in rows:
                knowledge_items.append({
                    "id": row[0],
                    "content": row[1],
                    "source": row[2],
                    "knowledge_type": row[3],
                    "confidence_score": row[4],
                    "retention_score": row[5],
                    "access_count": row[6],
                    "last_accessed": row[7],
                    "metadata": json.loads(row[8])
                })
            
            logger.info(f"Retrieved {len(knowledge_items)} retained knowledge items")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to get retained knowledge: {e}")
            return []
    
    def record_learning_session(self, 
                               session_type: str,
                               content_learned: str,
                               accuracy_score: float,
                               retention_improvement: float = 0.0,
                               metadata: Optional[Dict[str, Any]] = None) -> int:
        """Record a learning session
        
        Args:
            session_type: Type of learning session
            content_learned: What was learned
            accuracy_score: Accuracy of learning (0-1)
            retention_improvement: Improvement in retention (0-1)
            metadata: Additional metadata
            
        Returns:
            int: Session ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_sessions 
                (session_type, content_learned, accuracy_score, retention_improvement, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_type,
                content_learned,
                accuracy_score,
                retention_improvement,
                json.dumps(metadata or {})
            ))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded learning session {session_id}: {session_type}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to record learning session: {e}")
            return -1
    
    def calculate_retention_metrics(self) -> Dict[str, Any]:
        """Calculate retention metrics
        
        Returns:
            Dict with retention statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            total_knowledge = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(retention_score) FROM knowledge_items")
            avg_retention = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_items WHERE retention_score >= 0.7")
            high_retention = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_sessions")
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy_score) FROM learning_sessions")
            avg_accuracy = cursor.fetchone()[0] or 0.0
            
            # Get recent learning trend
            cursor.execute("""
                SELECT AVG(accuracy_score) 
                FROM learning_sessions 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_accuracy = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            metrics = {
                "total_knowledge_items": total_knowledge,
                "average_retention_score": round(avg_retention, 3),
                "high_retention_items": high_retention,
                "retention_rate": round(high_retention / max(total_knowledge, 1), 3),
                "total_learning_sessions": total_sessions,
                "average_accuracy": round(avg_accuracy, 3),
                "recent_accuracy": round(recent_accuracy, 3),
                "learning_trend": "improving" if recent_accuracy > avg_accuracy else "stable"
            }
            
            logger.info(f"Calculated retention metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate retention metrics: {e}")
            return {}
    
    def cleanup_old_knowledge(self, days_threshold: int = 30, min_retention_score: float = 0.3) -> int:
        """Clean up old, low-retention knowledge
        
        Args:
            days_threshold: Remove items older than this many days
            min_retention_score: Remove items with retention below this
            
        Returns:
            int: Number of items removed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count items to be removed
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_items 
                WHERE created_at < datetime('now', '-{} days') 
                AND retention_score < ?
            """.format(days_threshold), (min_retention_score,))
            
            count = cursor.fetchone()[0]
            
            # Remove items
            cursor.execute("""
                DELETE FROM knowledge_items 
                WHERE created_at < datetime('now', '-{} days') 
                AND retention_score < ?
            """.format(days_threshold), (min_retention_score,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {count} old knowledge items")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old knowledge: {e}")
            return 0
