"""
Habit Store - Opt-in habit learning with privacy and decay
"""
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

@dataclass
class HabitEntry:
    """Single habit entry with metadata"""
    cue_hash: str  # Hashed cue for privacy
    action: str
    confidence: float  # 0.0-1.0
    frequency: int  # How many times observed
    first_seen: float  # Unix timestamp
    last_seen: float  # Unix timestamp
    decay_factor: float = 1.0  # Current decay (0.0-1.0)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class HabitStats:
    """Statistics for habit store"""
    total_habits: int = 0
    active_habits: int = 0  # Non-decayed habits
    total_observations: int = 0
    avg_confidence: float = 0.0
    oldest_habit_days: float = 0.0
    newest_habit_days: float = 0.0

class HabitStore:
    """
    Habit Store with opt-in privacy, quorum requirements, and decay
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Privacy settings
        self.privacy_enabled = self.config.get("privacy", {}).get("enabled", True)
        self.habits_opt_in = self.config.get("privacy", {}).get("habits_opt_in", False)  # Default: opt-out
        self.ttl_days = self.config.get("privacy", {}).get("ttl_days", 90)  # 90 days retention
        self.hash_cues = self.config.get("privacy", {}).get("hash_cues", True)
        
        # Quorum settings
        self.quorum_threshold = self.config.get("quorum", {}).get("threshold", 3)  # Min 3 observations
        self.quorum_window_days = self.config.get("quorum", {}).get("window_days", 7)  # Within 7 days
        
        # Decay settings
        self.decay_half_life_days = self.config.get("decay", {}).get("half_life_days", 30)  # 30 days half-life
        self.decay_min_threshold = self.config.get("decay", {}).get("min_threshold", 0.1)  # Remove below 0.1
        
        # Storage
        self.habits: Dict[str, HabitEntry] = {}  # cue_hash -> HabitEntry
        self.observations: Dict[str, List[float]] = {}  # cue_hash -> [timestamps]
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = HabitStats()
        self._update_stats()
        
        logger.info(f"HabitStore initialized: opt_in={self.habits_opt_in}, ttl={self.ttl_days}d, quorum={self.quorum_threshold}")
    
    def is_enabled(self) -> bool:
        """Check if habit learning is enabled (opt-in)"""
        return self.habits_opt_in
    
    def _hash_cue(self, cue: str) -> str:
        """Hash cue for privacy (if enabled)"""
        if not self.hash_cues:
            return cue
        return hashlib.sha256(cue.encode('utf-8')).hexdigest()[:16]  # 16 chars for readability
    
    def _is_quorum_met(self, cue_hash: str) -> bool:
        """Check if quorum is met for a cue"""
        if cue_hash not in self.observations:
            return False
        
        now = time.time()
        window_start = now - (self.quorum_window_days * 24 * 3600)
        
        # Count observations within window
        recent_observations = [ts for ts in self.observations[cue_hash] if ts >= window_start]
        return len(recent_observations) >= self.quorum_threshold
    
    def _calculate_decay(self, habit: HabitEntry) -> float:
        """Calculate current decay factor based on time since last seen"""
        if habit.frequency == 0:
            return 0.0
        
        days_since_last = (time.time() - habit.last_seen) / (24 * 3600)
        if days_since_last <= 0:
            return 1.0
        
        # Exponential decay: decay_factor = 0.5^(days / half_life)
        decay_factor = 0.5 ** (days_since_last / self.decay_half_life_days)
        return max(decay_factor, 0.0)
    
    def _cleanup_expired(self):
        """Remove expired habits and observations"""
        now = time.time()
        cutoff_time = now - (self.ttl_days * 24 * 3600)
        
        # Remove expired habits
        expired_habits = []
        for cue_hash, habit in self.habits.items():
            if habit.last_seen < cutoff_time or habit.decay_factor < self.decay_min_threshold:
                expired_habits.append(cue_hash)
        
        for cue_hash in expired_habits:
            del self.habits[cue_hash]
            if cue_hash in self.observations:
                del self.observations[cue_hash]
        
        # Clean up old observations
        for cue_hash in list(self.observations.keys()):
            self.observations[cue_hash] = [ts for ts in self.observations[cue_hash] if ts >= cutoff_time]
            if not self.observations[cue_hash]:
                del self.observations[cue_hash]
        
        if expired_habits:
            logger.info(f"Cleaned up {len(expired_habits)} expired habits")
    
    def cleanup_expired(self):
        """Public method to trigger cleanup (for testing)"""
        self._cleanup_expired()
    
    def observe_cue(self, cue: str, action: str, confidence: float = 1.0, 
                   user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> bool:
        """
        Observe a cue-action pair. Returns True if habit was created/updated.
        """
        if not self.is_enabled():
            return False
        
        with self.lock:
            cue_hash = self._hash_cue(cue)
            now = time.time()
            
        # Check if quorum is met (before adding the new observation)
        if not self._is_quorum_met(cue_hash):
            # Record observation but don't create habit yet
            if cue_hash not in self.observations:
                self.observations[cue_hash] = []
            self.observations[cue_hash].append(now)
            
            # Check again after adding observation
            if not self._is_quorum_met(cue_hash):
                logger.debug(f"Quorum not met for cue_hash {cue_hash[:8]}... (need {self.quorum_threshold} in {self.quorum_window_days}d)")
                return False
        else:
            # Record observation
            if cue_hash not in self.observations:
                self.observations[cue_hash] = []
            self.observations[cue_hash].append(now)
        
        # Create or update habit
        if cue_hash in self.habits:
            # Update existing habit
            habit = self.habits[cue_hash]
            habit.frequency += 1
            habit.last_seen = now
            habit.confidence = max(habit.confidence, confidence)  # Keep highest confidence
            habit.action = action  # Update action to latest
            habit.metadata.update({
                "last_action": action,
                "last_confidence": confidence,
                "last_user": user_id,
                "last_tenant": tenant_id
            })
        else:
            # Create new habit
            habit = HabitEntry(
                cue_hash=cue_hash,
                action=action,
                confidence=confidence,
                frequency=1,
                first_seen=now,
                last_seen=now,
                decay_factor=1.0,
                metadata={
                    "first_action": action,
                    "first_confidence": confidence,
                    "first_user": user_id,
                    "first_tenant": tenant_id,
                    "last_action": action,
                    "last_confidence": confidence,
                    "last_user": user_id,
                    "last_tenant": tenant_id
                }
            )
            self.habits[cue_hash] = habit
        
        # Update decay
        habit.decay_factor = self._calculate_decay(habit)
        
        # Cleanup expired entries
        self._cleanup_expired()
        self._update_stats()
        
        logger.info(f"Habit {'updated' if cue_hash in self.habits else 'created'}: {cue_hash[:8]}... -> {action} (conf={confidence:.2f}, freq={habit.frequency})")
        return True
    
    def get_habit_score(self, cue: str) -> Tuple[float, Optional[str]]:
        """
        Get habit score for a cue. Returns (score, action) or (0.0, None).
        """
        if not self.is_enabled():
            return 0.0, None
        
        with self.lock:
            cue_hash = self._hash_cue(cue)
            
            if cue_hash not in self.habits:
                return 0.0, None
            
            habit = self.habits[cue_hash]
            
            # Update decay
            habit.decay_factor = self._calculate_decay(habit)
            
            # Calculate score: confidence * decay_factor * frequency_bonus
            frequency_bonus = min(1.0, habit.frequency / 10.0)  # Cap at 10 observations
            score = habit.confidence * habit.decay_factor * frequency_bonus
            
            # Remove if too decayed
            if habit.decay_factor < self.decay_min_threshold:
                del self.habits[cue_hash]
                if cue_hash in self.observations:
                    del self.observations[cue_hash]
                self._update_stats()
                return 0.0, None
            
            return score, habit.action
    
    def get_all_habits(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all habits (for export/debugging)"""
        if not self.is_enabled():
            return []
        
        with self.lock:
            habits = []
            for habit in self.habits.values():
                # Filter by user/tenant if specified
                if user_id and habit.metadata.get("last_user") != user_id:
                    continue
                if tenant_id and habit.metadata.get("last_tenant") != tenant_id:
                    continue
                
                habit_dict = asdict(habit)
                habit_dict["days_since_last"] = (time.time() - habit.last_seen) / (24 * 3600)
                habits.append(habit_dict)
            
            return sorted(habits, key=lambda h: h["confidence"] * h["decay_factor"], reverse=True)
    
    def delete_habits(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> int:
        """Delete habits for a user/tenant (for privacy compliance)"""
        if not self.is_enabled():
            return 0
        
        with self.lock:
            deleted_count = 0
            to_delete = []
            
            for cue_hash, habit in self.habits.items():
                if user_id and habit.metadata.get("last_user") != user_id:
                    continue
                if tenant_id and habit.metadata.get("last_tenant") != tenant_id:
                    continue
                
                to_delete.append(cue_hash)
            
            for cue_hash in to_delete:
                del self.habits[cue_hash]
                if cue_hash in self.observations:
                    del self.observations[cue_hash]
                deleted_count += 1
            
            self._update_stats()
            logger.info(f"Deleted {deleted_count} habits for user={user_id}, tenant={tenant_id}")
            return deleted_count
    
    def export_habits(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Export habits data (for GDPR compliance)"""
        if not self.is_enabled():
            return {"habits": [], "metadata": {"export_time": time.time(), "opt_in": False}}
        
        with self.lock:
            habits = self.get_all_habits(user_id, tenant_id)
            return {
                "habits": habits,
                "metadata": {
                    "export_time": time.time(),
                    "opt_in": self.habits_opt_in,
                    "total_habits": len(habits),
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "privacy_settings": {
                        "hash_cues": self.hash_cues,
                        "ttl_days": self.ttl_days,
                        "quorum_threshold": self.quorum_threshold,
                        "quorum_window_days": self.quorum_window_days,
                        "decay_half_life_days": self.decay_half_life_days
                    }
                }
            }
    
    def _update_stats(self):
        """Update internal statistics"""
        now = time.time()
        
        self.stats.total_habits = len(self.habits)
        self.stats.active_habits = sum(1 for h in self.habits.values() if h.decay_factor >= self.decay_min_threshold)
        self.stats.total_observations = sum(len(obs) for obs in self.observations.values())
        
        if self.habits:
            confidences = [h.confidence for h in self.habits.values()]
            self.stats.avg_confidence = sum(confidences) / len(confidences)
            
            ages = [(now - h.first_seen) / (24 * 3600) for h in self.habits.values()]
            self.stats.oldest_habit_days = max(ages) if ages else 0.0
            self.stats.newest_habit_days = min(ages) if ages else 0.0
        else:
            self.stats.avg_confidence = 0.0
            self.stats.oldest_habit_days = 0.0
            self.stats.newest_habit_days = 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self.lock:
            self._update_stats()
            return asdict(self.stats)
    
    def reset(self):
        """Reset all habits (for testing)"""
        with self.lock:
            self.habits.clear()
            self.observations.clear()
            self._update_stats()
            logger.info("HabitStore reset")
