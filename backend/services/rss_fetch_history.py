"""
RSS Fetch History Service for StillMe
Tracks all RSS fetch operations with detailed status for transparency
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class RSSFetchHistory:
    """Tracks RSS fetch history with detailed status for transparency"""
    
    def __init__(self, db_path: str = "data/rss_fetch_history.db"):
        """
        Initialize RSS fetch history tracker
        
        Args:
            db_path: Path to SQLite database for fetch history
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("RSS Fetch History system initialized")
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # RSS fetch items table - tracks each item fetched
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_fetch_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    link TEXT,
                    summary TEXT,
                    fetch_timestamp TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    status_reason TEXT,
                    vector_id TEXT,
                    added_to_rag_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # RSS fetch cycles table - tracks each learning cycle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_fetch_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER NOT NULL,
                    entries_fetched INTEGER DEFAULT 0,
                    entries_added INTEGER DEFAULT 0,
                    entries_filtered INTEGER DEFAULT 0,
                    entries_duplicate INTEGER DEFAULT 0,
                    entries_low_score INTEGER DEFAULT 0,
                    entries_ethical_filtered INTEGER DEFAULT 0,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cycle_id ON rss_fetch_items(cycle_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON rss_fetch_items(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fetch_timestamp ON rss_fetch_items(fetch_timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info("RSS fetch history database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_fetch_cycle(self, cycle_number: int) -> int:
        """Create a new fetch cycle and return cycle_id
        
        Args:
            cycle_number: The cycle number from scheduler
            
        Returns:
            int: Cycle ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO rss_fetch_cycles 
                (cycle_number, started_at) 
                VALUES (?, ?)
            """, (cycle_number, datetime.now().isoformat()))
            
            cycle_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created fetch cycle {cycle_id} for cycle number {cycle_number}")
            return cycle_id
            
        except Exception as e:
            logger.error(f"Failed to create fetch cycle: {e}")
            raise
    
    def add_fetch_item(
        self,
        cycle_id: int,
        title: str,
        source_url: str,
        link: str,
        summary: str,
        status: str,
        status_reason: Optional[str] = None,
        vector_id: Optional[str] = None,
        added_to_rag_at: Optional[str] = None
    ) -> int:
        """Add a fetched item with status
        
        Args:
            cycle_id: ID of the fetch cycle
            title: Item title
            source_url: RSS feed URL
            link: Item link
            summary: Item summary/description
            status: Status (Added to RAG, Filtered: Duplicate, Filtered: Low Score, Filtered: Ethical/Bias Flag)
            status_reason: Optional reason for status
            vector_id: Vector ID if added to RAG
            added_to_rag_at: Timestamp when added to RAG
            
        Returns:
            int: Item ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO rss_fetch_items 
                (cycle_id, title, source_url, link, summary, fetch_timestamp, 
                 status, status_reason, vector_id, added_to_rag_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cycle_id,
                title,
                source_url,
                link,
                summary,
                datetime.now().isoformat(),
                status,
                status_reason,
                vector_id,
                added_to_rag_at
            ))
            
            item_id = cursor.lastrowid
            
            # Update cycle statistics
            self._update_cycle_stats(cycle_id, status)
            
            conn.commit()
            conn.close()
            
            return item_id
            
        except Exception as e:
            logger.error(f"Failed to add fetch item: {e}")
            raise
    
    def _update_cycle_stats(self, cycle_id: int, status: str):
        """Update cycle statistics based on item status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current stats
            cursor.execute("""
                SELECT entries_fetched, entries_added, entries_filtered,
                       entries_duplicate, entries_low_score, entries_ethical_filtered
                FROM rss_fetch_cycles WHERE id = ?
            """, (cycle_id,))
            
            row = cursor.fetchone()
            if not row:
                return
            
            (fetched, added, filtered, duplicate, low_score, ethical) = row
            
            # Update based on status
            if status == "Added to RAG":
                added += 1
            elif status == "Filtered: Duplicate":
                duplicate += 1
                filtered += 1
            elif status == "Filtered: Low Score":
                low_score += 1
                filtered += 1
            elif status == "Filtered: Ethical/Bias Flag":
                ethical += 1
                filtered += 1
            
            fetched += 1
            
            cursor.execute("""
                UPDATE rss_fetch_cycles
                SET entries_fetched = ?,
                    entries_added = ?,
                    entries_filtered = ?,
                    entries_duplicate = ?,
                    entries_low_score = ?,
                    entries_ethical_filtered = ?
                WHERE id = ?
            """, (fetched, added, filtered, duplicate, low_score, ethical, cycle_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update cycle stats: {e}")
    
    def complete_fetch_cycle(self, cycle_id: int):
        """Mark a fetch cycle as completed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rss_fetch_cycles
                SET completed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), cycle_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to complete fetch cycle: {e}")
    
    def get_latest_fetch_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest fetch items from the most recent successful cycle
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of fetch items with all details
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the latest completed cycle
            cursor.execute("""
                SELECT id FROM rss_fetch_cycles
                WHERE completed_at IS NOT NULL
                ORDER BY completed_at DESC
                LIMIT 1
            """)
            
            cycle_row = cursor.fetchone()
            if not cycle_row:
                # If no completed cycle, get the latest cycle
                cursor.execute("""
                    SELECT id FROM rss_fetch_cycles
                    ORDER BY started_at DESC
                    LIMIT 1
                """)
                cycle_row = cursor.fetchone()
            
            if not cycle_row:
                return []
            
            cycle_id = cycle_row[0]
            
            # Get all items from this cycle
            cursor.execute("""
                SELECT id, title, source_url, link, summary, fetch_timestamp,
                       status, status_reason, vector_id, added_to_rag_at
                FROM rss_fetch_items
                WHERE cycle_id = ?
                ORDER BY fetch_timestamp DESC
                LIMIT ?
            """, (cycle_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            items = []
            for row in rows:
                items.append({
                    "id": row[0],
                    "title": row[1],
                    "source_url": row[2],
                    "link": row[3],
                    "summary": row[4],
                    "fetch_timestamp": row[5],
                    "status": row[6],
                    "status_reason": row[7],
                    "vector_id": row[8],
                    "added_to_rag_at": row[9]
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get latest fetch items: {e}")
            return []
    
    def get_all_fetch_items(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all fetch items (for debugging/admin)
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of all fetch items
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, cycle_id, title, source_url, link, summary, fetch_timestamp,
                       status, status_reason, vector_id, added_to_rag_at
                FROM rss_fetch_items
                ORDER BY fetch_timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            items = []
            for row in rows:
                items.append({
                    "id": row[0],
                    "cycle_id": row[1],
                    "title": row[2],
                    "source_url": row[3],
                    "link": row[4],
                    "summary": row[5],
                    "fetch_timestamp": row[6],
                    "status": row[7],
                    "status_reason": row[8],
                    "vector_id": row[9],
                    "added_to_rag_at": row[10]
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get all fetch items: {e}")
            return []

