"""
Chat History Service for StillMe
Persistent chat history storage using SQLite
"""

import sqlite3
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# SQLite Configuration for Concurrency
SQLITE_TIMEOUT = 10.0  # Timeout in seconds for database operations
MAX_RETRIES = 5  # Maximum number of retries for database operations
RETRY_DELAY_BASE = 0.1  # Base delay in seconds (exponential backoff)


class ChatHistory:
    """Manages persistent chat history storage"""
    
    def __init__(self, db_path: str = "data/chat_history.db"):
        """
        Initialize chat history service
        
        Args:
            db_path: Path to SQLite database for chat history
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("Chat History service initialized")
    
    def _get_connection(self):
        """Get SQLite connection with timeout configuration"""
        conn = sqlite3.connect(self.db_path, timeout=SQLITE_TIMEOUT)
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """
        Execute database operation with retry logic for concurrency
        
        Args:
            operation: Function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result of operation
        """
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(f"Database locked, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    last_exception = e
                else:
                    raise
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
        
        if last_exception:
            raise last_exception
    
    def _init_database(self):
        """Initialize chat history database schema"""
        def _create_tables():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                # Chat history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        user_message TEXT NOT NULL,
                        assistant_response TEXT NOT NULL,
                        confidence_score REAL,
                        validation_passed BOOLEAN,
                        response_length INTEGER,
                        context_docs_count INTEGER,
                        latency REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_id 
                    ON chat_history(session_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON chat_history(timestamp)
                """)
                
                conn.commit()
                logger.info("Chat history database initialized")
            finally:
                conn.close()
        
        self._execute_with_retry(_create_tables)
    
    def save_message(
        self,
        user_message: str,
        assistant_response: str,
        session_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        validation_passed: Optional[bool] = None,
        response_length: Optional[int] = None,
        context_docs_count: Optional[int] = None,
        latency: Optional[float] = None,
        update_existing: bool = False
    ) -> int:
        """
        Save a chat message to database
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            session_id: Optional session ID
            confidence_score: Optional confidence score
            validation_passed: Optional validation status
            response_length: Optional response length
            context_docs_count: Optional context docs count
            latency: Optional latency
            update_existing: If True, update the last message with empty assistant_response
        
        Returns:
            Message ID
        """
        def _insert():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                # If update_existing is True, try to update the last message with empty assistant_response
                if update_existing and assistant_response:
                    cursor.execute("""
                        SELECT id FROM chat_history
                        WHERE session_id = ? AND assistant_response = ''
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (session_id,))
                    row = cursor.fetchone()
                    if row:
                        message_id = row[0]
                        cursor.execute("""
                            UPDATE chat_history
                            SET assistant_response = ?,
                                confidence_score = ?,
                                validation_passed = ?,
                                response_length = ?,
                                context_docs_count = ?,
                                latency = ?
                            WHERE id = ?
                        """, (
                            assistant_response,
                            confidence_score,
                            validation_passed,
                            response_length,
                            context_docs_count,
                            latency,
                            message_id
                        ))
                        conn.commit()
                        logger.debug(f"Chat message updated: ID={message_id}")
                        return message_id
                
                # Otherwise, insert new message
                cursor.execute("""
                    INSERT INTO chat_history (
                        session_id, user_message, assistant_response,
                        confidence_score, validation_passed,
                        response_length, context_docs_count, latency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_message,
                    assistant_response,
                    confidence_score,
                    validation_passed,
                    response_length,
                    context_docs_count,
                    latency
                ))
                conn.commit()
                message_id = cursor.lastrowid
                logger.debug(f"Chat message saved: ID={message_id}")
                return message_id
            finally:
                conn.close()
        
        return self._execute_with_retry(_insert)
    
    def get_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get chat history from database
        
        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of messages to return
            offset: Offset for pagination
        
        Returns:
            List of chat messages
        """
        def _select():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                if session_id:
                    cursor.execute("""
                        SELECT 
                            id, session_id, user_message, assistant_response,
                            confidence_score, validation_passed,
                            response_length, context_docs_count, latency,
                            timestamp
                        FROM chat_history
                        WHERE session_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (session_id, limit, offset))
                else:
                    cursor.execute("""
                        SELECT 
                            id, session_id, user_message, assistant_response,
                            confidence_score, validation_passed,
                            response_length, context_docs_count, latency,
                            timestamp
                        FROM chat_history
                        ORDER BY timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (limit, offset))
                
                rows = cursor.fetchall()
                
                # Convert to list of dicts
                messages = []
                for row in rows:
                    messages.append({
                        "id": row[0],
                        "session_id": row[1],
                        "user_message": row[2],
                        "assistant_response": row[3],
                        "confidence_score": row[4],
                        "validation_passed": bool(row[5]) if row[5] is not None else None,
                        "response_length": row[6],
                        "context_docs_count": row[7],
                        "latency": row[8],
                        "timestamp": row[9]
                    })
                
                # Reverse to get chronological order (oldest first)
                messages.reverse()
                return messages
            finally:
                conn.close()
        
        return self._execute_with_retry(_select)
    
    def delete_history(
        self,
        session_id: Optional[str] = None,
        message_id: Optional[int] = None
    ) -> int:
        """
        Delete chat history
        
        Args:
            session_id: Delete all messages for this session
            message_id: Delete specific message by ID
        
        Returns:
            Number of deleted messages
        """
        def _delete():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                if message_id:
                    cursor.execute("DELETE FROM chat_history WHERE id = ?", (message_id,))
                elif session_id:
                    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
                else:
                    # Delete all (use with caution)
                    cursor.execute("DELETE FROM chat_history")
                
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Deleted {deleted_count} chat messages")
                return deleted_count
            finally:
                conn.close()
        
        return self._execute_with_retry(_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get chat history statistics
        
        Returns:
            Dictionary with statistics
        """
        def _stats():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                
                # Total messages
                cursor.execute("SELECT COUNT(*) FROM chat_history")
                total_messages = cursor.fetchone()[0]
                
                # Total sessions
                cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history WHERE session_id IS NOT NULL")
                total_sessions = cursor.fetchone()[0]
                
                # Average confidence
                cursor.execute("SELECT AVG(confidence_score) FROM chat_history WHERE confidence_score IS NOT NULL")
                avg_confidence = cursor.fetchone()[0]
                
                # Average validation pass rate
                cursor.execute("""
                    SELECT 
                        CAST(SUM(CASE WHEN validation_passed = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)
                    FROM chat_history
                    WHERE validation_passed IS NOT NULL
                """)
                validation_pass_rate = cursor.fetchone()[0]
                
                return {
                    "total_messages": total_messages,
                    "total_sessions": total_sessions,
                    "avg_confidence": avg_confidence if avg_confidence else 0.0,
                    "validation_pass_rate": validation_pass_rate if validation_pass_rate else 0.0
                }
            finally:
                conn.close()
        
        return self._execute_with_retry(_stats)

