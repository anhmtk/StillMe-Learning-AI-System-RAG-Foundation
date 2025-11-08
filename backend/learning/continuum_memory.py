"""
Continuum Memory System for StillMe
Implements tiered memory architecture (L0-L3) with promotion/demotion logic
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Feature flag check
ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"

# Tier configuration
TIER_PROMOTE_THRESHOLD = float(os.getenv("TIER_PROMOTE_THRESHOLD", "0.65"))
TIER_DEMOTE_THRESHOLD = float(os.getenv("TIER_DEMOTE_THRESHOLD", "0.15"))

# Tier retention days (default values)
TIER_RETENTION_DAYS = {
    "L0": int(os.getenv("TIER_RETENTION_DAYS_L0", "2")),
    "L1": int(os.getenv("TIER_RETENTION_DAYS_L1", "21")),
    "L2": int(os.getenv("TIER_RETENTION_DAYS_L2", "180")),
    "L3": int(os.getenv("TIER_RETENTION_DAYS_L3", "9999"))
}


class ContinuumMemory:
    """Manages tiered memory system with promotion/demotion"""
    
    def __init__(self, db_path: str = "data/continuum_memory.db"):
        """Initialize Continuum Memory system
        
        Args:
            db_path: Path to SQLite database for tier metrics and audit
        """
        if not ENABLE_CONTINUUM_MEMORY:
            logger.info("Continuum Memory is disabled (ENABLE_CONTINUUM_MEMORY=false)")
            return
            
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("Continuum Memory system initialized")
    
    def _init_database(self):
        """Initialize database tables for tier metrics, audit, and forgetting metrics"""
        if not ENABLE_CONTINUUM_MEMORY:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tier metrics table - tracks surprise score, retrieval count, etc.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tier_metrics (
                    item_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL CHECK(tier IN ('L0', 'L1', 'L2', 'L3')),
                    surprise_score REAL DEFAULT 0.0,
                    retrieval_count_7d INTEGER DEFAULT 0,
                    retrieval_count_30d INTEGER DEFAULT 0,
                    validator_overlap REAL DEFAULT 0.0,
                    last_promoted_at TIMESTAMP,
                    last_demoted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tier audit table - tracks all promotion/demotion events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tier_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    from_tier TEXT,
                    to_tier TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    surprise_score REAL,
                    retrieval_count_7d INTEGER,
                    validator_overlap REAL,
                    performed_by TEXT DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Forgetting metrics table - tracks Recall@k degradation over time
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forgetting_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regression_item_id TEXT NOT NULL,
                    regression_query TEXT NOT NULL,
                    recall_at_k_before REAL,
                    recall_at_k_after REAL,
                    forgetting_delta REAL,
                    faithfulness_score REAL,
                    overlap_score REAL,
                    evaluation_timestamp TIMESTAMP NOT NULL,
                    knowledge_update_timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier_metrics_item_id ON tier_metrics(item_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier_metrics_tier ON tier_metrics(tier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier_audit_item_id ON tier_audit(item_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier_audit_created_at ON tier_audit(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_forgetting_evaluation_timestamp ON forgetting_metrics(evaluation_timestamp)")
            
            conn.commit()
            conn.close()
            logger.info("Continuum Memory database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Continuum Memory database: {e}")
            raise
    
    def calculate_surprise_score(self, 
                                 item_id: str,
                                 content: str,
                                 rarity_score: float = 0.0,
                                 novelty_score: float = 0.0,
                                 retrieval_frequency: float = 0.0,
                                 validator_overlap: float = 0.0) -> float:
        """
        Calculate surprise score for a knowledge item.
        
        Formula (normalized to 0.0-1.0):
        surprise_score = 0.3 * rarity_score + 
                        0.3 * novelty_score + 
                        0.2 * retrieval_frequency + 
                        0.2 * validator_overlap
        
        Where:
        - rarity_score: Uniqueness of keywords (0.0-1.0)
        - novelty_score: Cosine distance from centroid of existing knowledge (0.0-1.0)
        - retrieval_frequency: Normalized retrieval count in last 7 days (0.0-1.0)
        - validator_overlap: Evidence overlap from validator chain (0.0-1.0)
        
        Args:
            item_id: Knowledge item ID
            content: Content text (for keyword extraction if needed)
            rarity_score: Keyword rarity score (0.0-1.0)
            novelty_score: OOD/novelty score (0.0-1.0)
            retrieval_frequency: Normalized retrieval frequency (0.0-1.0)
            validator_overlap: Validator evidence overlap (0.0-1.0)
            
        Returns:
            Surprise score (0.0-1.0)
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return 0.0
        
        # PR-1: Mock computation (will be real in PR-2)
        # For now, return a mock value based on simple heuristics
        mock_score = min(1.0, (rarity_score * 0.3 + novelty_score * 0.3 + 
                               retrieval_frequency * 0.2 + validator_overlap * 0.2))
        
        logger.debug(f"Surprise score (mock) for {item_id}: {mock_score:.3f}")
        return mock_score
    
    def get_tier_stats(self) -> Dict[str, Any]:
        """Get statistics for each tier
        
        Returns:
            Dictionary with tier counts and metrics
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "total": 0}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count items per tier
            stats = {}
            for tier in ["L0", "L1", "L2", "L3"]:
                cursor.execute("""
                    SELECT COUNT(*) FROM tier_metrics WHERE tier = ?
                """, (tier,))
                count = cursor.fetchone()[0]
                stats[tier] = count
            
            stats["total"] = sum(stats.values())
            
            # Get promotion/demotion counts (last 7 days)
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE from_tier < to_tier) as promoted,
                    COUNT(*) FILTER (WHERE from_tier > to_tier) as demoted
                FROM tier_audit
                WHERE created_at >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            stats["promoted_7d"] = result[0] or 0
            stats["demoted_7d"] = result[1] or 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tier stats: {e}")
            return {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "total": 0, "promoted_7d": 0, "demoted_7d": 0}
    
    def get_audit_log(self, limit: int = 100, item_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log of promotion/demotion events
        
        Args:
            limit: Maximum number of records to return
            item_id: Optional filter by item_id
            
        Returns:
            List of audit records
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if item_id:
                cursor.execute("""
                    SELECT * FROM tier_audit
                    WHERE item_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (item_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM tier_audit
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            audit_log = [dict(row) for row in rows]
            
            conn.close()
            return audit_log
            
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            return []
    
    def record_forgetting_metric(self,
                                 regression_item_id: str,
                                 regression_query: str,
                                 recall_at_k_before: float,
                                 recall_at_k_after: float,
                                 faithfulness_score: Optional[float] = None,
                                 overlap_score: Optional[float] = None,
                                 knowledge_update_timestamp: Optional[datetime] = None) -> int:
        """Record forgetting metric (Recall@k degradation)
        
        Args:
            regression_item_id: ID of regression test item
            regression_query: Query used for regression test
            recall_at_k_before: Recall@k before knowledge update
            recall_at_k_after: Recall@k after knowledge update
            faithfulness_score: Optional faithfulness score
            overlap_score: Optional overlap score
            knowledge_update_timestamp: Timestamp of knowledge update
            
        Returns:
            Record ID
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return -1
        
        try:
            forgetting_delta = recall_at_k_before - recall_at_k_after
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO forgetting_metrics (
                    regression_item_id, regression_query,
                    recall_at_k_before, recall_at_k_after, forgetting_delta,
                    faithfulness_score, overlap_score,
                    evaluation_timestamp, knowledge_update_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                regression_item_id,
                regression_query,
                recall_at_k_before,
                recall_at_k_after,
                forgetting_delta,
                faithfulness_score,
                overlap_score,
                datetime.now().isoformat(),
                knowledge_update_timestamp.isoformat() if knowledge_update_timestamp else None
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded forgetting metric: Δ={forgetting_delta:.3f} for {regression_item_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Error recording forgetting metric: {e}")
            return -1
    
    def get_forgetting_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get forgetting trends over time
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of forgetting metrics with timestamps
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    evaluation_timestamp,
                    AVG(forgetting_delta) as avg_forgetting_delta,
                    AVG(recall_at_k_before) as avg_recall_before,
                    AVG(recall_at_k_after) as avg_recall_after,
                    COUNT(*) as evaluation_count
                FROM forgetting_metrics
                WHERE evaluation_timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(evaluation_timestamp)
                ORDER BY evaluation_timestamp ASC
            """, (days,))
            
            rows = cursor.fetchall()
            trends = [dict(row) for row in rows]
            
            conn.close()
            return trends
            
        except Exception as e:
            logger.error(f"Error getting forgetting trends: {e}")
            return []

