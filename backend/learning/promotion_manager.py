"""
Promotion Manager for Continuum Memory System
Handles promotion/demotion of knowledge items between tiers based on surprise score
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import os
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Feature flag check
ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"

# Promotion thresholds
TIER_PROMOTE_THRESHOLD = float(os.getenv("TIER_PROMOTE_THRESHOLD", "0.65"))
TIER_DEMOTE_THRESHOLD = float(os.getenv("TIER_DEMOTE_THRESHOLD", "0.15"))

# Hysteresis to prevent oscillation (promote threshold > demote threshold)
PROMOTE_HYSTERESIS = 0.1  # Additional buffer for promotion


class PromotionManager:
    """Manages promotion and demotion of knowledge items between tiers"""
    
    def __init__(self, db_path: str = "data/continuum_memory.db"):
        """Initialize Promotion Manager
        
        Args:
            db_path: Path to Continuum Memory SQLite database
        """
        if not ENABLE_CONTINUUM_MEMORY:
            logger.info("Promotion Manager disabled (ENABLE_CONTINUUM_MEMORY=false)")
            return
            
        self.db_path = db_path
        logger.info("Promotion Manager initialized")
    
    def calculate_rarity_score(self, content: str, existing_keywords: Optional[List[str]] = None) -> float:
        """
        Calculate rarity score based on keyword uniqueness.
        
        Extracts keywords from content and compares with existing knowledge base.
        Rare keywords (not in existing KB) get higher score.
        
        Args:
            content: Content text to analyze
            existing_keywords: List of keywords from existing knowledge (optional, will query if None)
            
        Returns:
            Rarity score (0.0-1.0)
        """
        if not content:
            return 0.0
        
        # Extract keywords (simple approach: words > 4 chars, lowercase, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        if not words:
            return 0.0
        
        # Count word frequencies
        word_counts = Counter(words)
        total_words = len(words)
        
        # If no existing keywords provided, use simple heuristic
        # (In production, would query existing knowledge base)
        if existing_keywords is None:
            # Simple heuristic: rare words (appearing once) get higher score
            rare_words = sum(1 for count in word_counts.values() if count == 1)
            rarity_score = min(1.0, rare_words / max(total_words, 1) * 2.0)  # Scale up rare words
        else:
            # Compare with existing keywords
            existing_set = set(existing_keywords)
            rare_words = sum(1 for word in word_counts.keys() if word not in existing_set)
            rarity_score = min(1.0, rare_words / max(len(word_counts), 1))
        
        return rarity_score
    
    def calculate_novelty_score(self, 
                               content_embedding: List[float],
                               centroid_embeddings: Optional[List[List[float]]] = None) -> float:
        """
        Calculate novelty score based on cosine distance from centroid of existing knowledge.
        
        Higher distance = more novel (OOD detection).
        
        Args:
            content_embedding: Embedding vector of the content
            centroid_embeddings: List of centroid embeddings from existing knowledge (optional)
            
        Returns:
            Novelty score (0.0-1.0), where 1.0 = highly novel
        """
        if not content_embedding:
            return 0.0
        
        # If no centroid provided, use simple heuristic
        # (In production, would compute centroid from existing knowledge embeddings)
        if centroid_embeddings is None or not centroid_embeddings:
            # Default: assume moderate novelty
            return 0.5
        
        try:
            import numpy as np
            
            # Compute average centroid
            centroid = np.mean(centroid_embeddings, axis=0)
            
            # Calculate cosine distance
            content_vec = np.array(content_embedding)
            centroid_vec = np.array(centroid)
            
            # Cosine similarity
            dot_product = np.dot(content_vec, centroid_vec)
            norm_content = np.linalg.norm(content_vec)
            norm_centroid = np.linalg.norm(centroid_vec)
            
            if norm_content == 0 or norm_centroid == 0:
                return 0.5
            
            cosine_similarity = dot_product / (norm_content * norm_centroid)
            
            # Convert similarity to novelty (distance = 1 - similarity)
            novelty_score = 1.0 - cosine_similarity
            
            # Normalize to 0.0-1.0
            return max(0.0, min(1.0, novelty_score))
            
        except Exception as e:
            logger.warning(f"Error calculating novelty score: {e}, using default 0.5")
            return 0.5
    
    def get_retrieval_frequency(self, item_id: str, days: int = 7) -> float:
        """
        Get normalized retrieval frequency for an item.
        
        Args:
            item_id: Knowledge item ID
            days: Number of days to look back
            
        Returns:
            Normalized retrieval frequency (0.0-1.0)
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return 0.0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get retrieval count from tier_metrics
            cursor.execute("""
                SELECT retrieval_count_7d, retrieval_count_30d
                FROM tier_metrics
                WHERE item_id = ?
            """, (item_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return 0.0
            
            retrieval_count = result[0] if days <= 7 else result[1]
            
            # Normalize: max 100 retrievals = 1.0
            normalized = min(1.0, retrieval_count / 100.0)
            return normalized
            
        except Exception as e:
            logger.warning(f"Error getting retrieval frequency: {e}")
            return 0.0
    
    def get_validator_overlap(self, item_id: str) -> float:
        """
        Get validator evidence overlap score for an item.
        
        Args:
            item_id: Knowledge item ID
            
        Returns:
            Validator overlap score (0.0-1.0)
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return 0.0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get validator_overlap from tier_metrics
            cursor.execute("""
                SELECT validator_overlap
                FROM tier_metrics
                WHERE item_id = ?
            """, (item_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] is not None:
                return float(result[0])
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error getting validator overlap: {e}")
            return 0.0
    
    def calculate_surprise_score(self,
                               item_id: str,
                               content: str,
                               content_embedding: Optional[List[float]] = None,
                               existing_keywords: Optional[List[str]] = None,
                               centroid_embeddings: Optional[List[List[float]]] = None) -> float:
        """
        Calculate real surprise score for a knowledge item.
        
        Formula (normalized to 0.0-1.0):
        surprise_score = 0.3 × rarity_score + 
                        0.3 × novelty_score + 
                        0.2 × retrieval_frequency + 
                        0.2 × validator_overlap
        
        Args:
            item_id: Knowledge item ID
            content: Content text
            content_embedding: Optional embedding vector of content
            existing_keywords: Optional list of existing keywords
            centroid_embeddings: Optional list of centroid embeddings
            
        Returns:
            Surprise score (0.0-1.0)
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return 0.0
        
        # Calculate components
        rarity_score = self.calculate_rarity_score(content, existing_keywords)
        novelty_score = self.calculate_novelty_score(content_embedding, centroid_embeddings)
        retrieval_frequency = self.get_retrieval_frequency(item_id, days=7)
        validator_overlap = self.get_validator_overlap(item_id)
        
        # Weighted sum
        surprise_score = (
            0.3 * rarity_score +
            0.3 * novelty_score +
            0.2 * retrieval_frequency +
            0.2 * validator_overlap
        )
        
        # Normalize to 0.0-1.0
        surprise_score = max(0.0, min(1.0, surprise_score))
        
        logger.debug(
            f"Surprise score for {item_id}: {surprise_score:.3f} "
            f"(rarity={rarity_score:.3f}, novelty={novelty_score:.3f}, "
            f"retrieval={retrieval_frequency:.3f}, overlap={validator_overlap:.3f})"
        )
        
        return surprise_score
    
    def promote_item(self, 
                    item_id: str,
                    from_tier: str,
                    to_tier: str,
                    reason: str,
                    surprise_score: float,
                    retrieval_count_7d: int,
                    validator_overlap: float) -> bool:
        """
        Promote an item to higher tier.
        
        Args:
            item_id: Knowledge item ID
            from_tier: Current tier (L0/L1/L2/L3)
            to_tier: Target tier (must be higher than from_tier)
            reason: Reason for promotion
            surprise_score: Current surprise score
            retrieval_count_7d: Retrieval count in last 7 days
            validator_overlap: Validator overlap score
            
        Returns:
            bool: Success status
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update tier_metrics
            cursor.execute("""
                UPDATE tier_metrics
                SET tier = ?,
                    last_promoted_at = ?,
                    updated_at = ?
                WHERE item_id = ?
            """, (to_tier, datetime.now().isoformat(), datetime.now().isoformat(), item_id))
            
            # Insert audit record
            cursor.execute("""
                INSERT INTO tier_audit (
                    item_id, from_tier, to_tier, reason,
                    surprise_score, retrieval_count_7d, validator_overlap,
                    performed_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'system', ?)
            """, (
                item_id, from_tier, to_tier, reason,
                surprise_score, retrieval_count_7d, validator_overlap,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Promoted {item_id} from {from_tier} to {to_tier}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error promoting item {item_id}: {e}")
            return False
    
    def demote_item(self,
                   item_id: str,
                   from_tier: str,
                   to_tier: str,
                   reason: str,
                   surprise_score: float,
                   retrieval_count_7d: int,
                   validator_overlap: float) -> bool:
        """
        Demote an item to lower tier.
        
        Args:
            item_id: Knowledge item ID
            from_tier: Current tier (L0/L1/L2/L3)
            to_tier: Target tier (must be lower than from_tier)
            reason: Reason for demotion
            surprise_score: Current surprise score
            retrieval_count_7d: Retrieval count in last 7 days
            validator_overlap: Validator overlap score
            
        Returns:
            bool: Success status
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update tier_metrics
            cursor.execute("""
                UPDATE tier_metrics
                SET tier = ?,
                    last_demoted_at = ?,
                    updated_at = ?
                WHERE item_id = ?
            """, (to_tier, datetime.now().isoformat(), datetime.now().isoformat(), item_id))
            
            # Insert audit record
            cursor.execute("""
                INSERT INTO tier_audit (
                    item_id, from_tier, to_tier, reason,
                    surprise_score, retrieval_count_7d, validator_overlap,
                    performed_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'system', ?)
            """, (
                item_id, from_tier, to_tier, reason,
                surprise_score, retrieval_count_7d, validator_overlap,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Demoted {item_id} from {from_tier} to {to_tier}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error demoting item {item_id}: {e}")
            return False
    
    def evaluate_and_promote(self, item_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Evaluate an item and promote if criteria met.
        
        Returns:
            Tuple of (from_tier, to_tier, reason) if promoted, None otherwise
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current tier and metrics
            cursor.execute("""
                SELECT tier, surprise_score, retrieval_count_7d, validator_overlap
                FROM tier_metrics
                WHERE item_id = ?
            """, (item_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            current_tier = result[0]
            surprise_score = result[1] or 0.0
            retrieval_count_7d = result[2] or 0
            validator_overlap = result[3] or 0.0
            
            # Promotion rules with hysteresis
            promote_threshold = TIER_PROMOTE_THRESHOLD + PROMOTE_HYSTERESIS
            
            # L0 → L1: surprise_score >= threshold AND retrieval_count increasing
            if current_tier == "L0" and surprise_score >= promote_threshold and retrieval_count_7d > 0:
                if self.promote_item(
                    item_id, "L0", "L1",
                    f"surprise_score={surprise_score:.3f} >= {promote_threshold} and retrieval_count_7d={retrieval_count_7d} > 0",
                    surprise_score, retrieval_count_7d, validator_overlap
                ):
                    return ("L0", "L1", "High surprise score and active retrieval")
            
            # L1 → L2: surprise_score >= threshold AND validator_overlap high
            elif current_tier == "L1" and surprise_score >= promote_threshold and validator_overlap >= 0.8:
                if self.promote_item(
                    item_id, "L1", "L2",
                    f"surprise_score={surprise_score:.3f} >= {promote_threshold} and validator_overlap={validator_overlap:.3f} >= 0.8",
                    surprise_score, retrieval_count_7d, validator_overlap
                ):
                    return ("L1", "L2", "High surprise score and strong validator evidence")
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating promotion for {item_id}: {e}")
            return None
    
    def evaluate_and_demote(self, item_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Evaluate an item and demote if criteria met.
        
        Returns:
            Tuple of (from_tier, to_tier, reason) if demoted, None otherwise
        """
        if not ENABLE_CONTINUUM_MEMORY:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current tier and metrics
            cursor.execute("""
                SELECT tier, surprise_score, retrieval_count_7d, validator_overlap
                FROM tier_metrics
                WHERE item_id = ?
            """, (item_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            current_tier = result[0]
            surprise_score = result[1] or 0.0
            retrieval_count_7d = result[2] or 0
            validator_overlap = result[3] or 0.0
            
            # Demotion rules
            # L2 → L1: retrieval_count == 0 OR validator_overlap low
            if current_tier == "L2" and (retrieval_count_7d == 0 or validator_overlap < 0.3):
                reason = "retrieval_count_7d=0" if retrieval_count_7d == 0 else f"validator_overlap={validator_overlap:.3f} < 0.3"
                if self.demote_item(
                    item_id, "L2", "L1", reason,
                    surprise_score, retrieval_count_7d, validator_overlap
                ):
                    return ("L2", "L1", reason)
            
            # L1 → L0: surprise_score < demote_threshold OR retrieval_count == 0
            elif current_tier == "L1" and (surprise_score < TIER_DEMOTE_THRESHOLD or retrieval_count_7d == 0):
                reason = f"surprise_score={surprise_score:.3f} < {TIER_DEMOTE_THRESHOLD}" if surprise_score < TIER_DEMOTE_THRESHOLD else "retrieval_count_7d=0"
                if self.demote_item(
                    item_id, "L1", "L0", reason,
                    surprise_score, retrieval_count_7d, validator_overlap
                ):
                    return ("L1", "L0", reason)
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating demotion for {item_id}: {e}")
            return None

