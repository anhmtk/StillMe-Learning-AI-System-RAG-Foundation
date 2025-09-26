#!/usr/bin/env python3
"""
StillMe Learning Rollback System
================================

Version control and rollback mechanism for learning updates.
Allows reverting learning changes to previous states.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import json
import logging
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LearningUpdateType(Enum):
    """Types of learning updates"""
    KNOWLEDGE_BASE_UPDATE = "knowledge_base_update"
    PATTERN_LEARNING = "pattern_learning"
    BEHAVIOR_ADJUSTMENT = "behavior_adjustment"
    SKILL_ACQUISITION = "skill_acquisition"
    PREFERENCE_UPDATE = "preference_update"

class RollbackStatus(Enum):
    """Status of rollback operations"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_NEEDED = "not_needed"

@dataclass
class LearningSnapshot:
    """Snapshot of learning state at a point in time"""
    version_id: str
    timestamp: str
    update_type: str
    description: str
    state_hash: str
    changes: Dict[str, Any]
    dependencies: List[str]
    rollback_data: Dict[str, Any]

@dataclass
class RollbackResult:
    """Result of a rollback operation"""
    version_id: str
    status: str
    timestamp: str
    changes_reverted: List[str]
    errors: List[str]
    rollback_duration: float

class LearningRollback:
    """
    Version control and rollback system for learning updates.
    
    Features:
    - Version control: Every learning update gets a version ID
    - Rollback capability: Revert to any previous version
    - Dependency tracking: Handle dependent changes
    - Safety checks: Validate rollback safety
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        
        # Storage
        self.snapshots: Dict[str, LearningSnapshot] = {}
        self.rollback_history: List[RollbackResult] = []
        self.current_version: Optional[str] = None
        
        # Configuration
        self.artifacts_path = Path("artifacts")
        self.artifacts_path.mkdir(exist_ok=True)
        self.snapshots_path = self.artifacts_path / "learning_snapshots.json"
        
        # Safety settings
        self.max_rollback_depth = 10  # Maximum versions to rollback
        self.rollback_timeout = 300   # 5 minutes timeout for rollback
        
        # Load existing snapshots
        self._load_snapshots()
        
        self.logger.info("✅ LearningRollback system initialized")
    
    async def create_snapshot(
        self,
        update_type: LearningUpdateType,
        description: str,
        changes: Dict[str, Any],
        dependencies: Optional[List[str]] = None
    ) -> LearningSnapshot:
        """
        Create a snapshot of current learning state.
        
        Args:
            update_type: Type of learning update
            description: Human-readable description
            changes: Dictionary of changes made
            dependencies: List of dependent version IDs
            
        Returns:
            LearningSnapshot with version ID and state hash
        """
        # Generate version ID
        version_id = self._generate_version_id()
        
        # Create state hash
        state_hash = self._calculate_state_hash(changes)
        
        # Prepare rollback data
        rollback_data = await self._prepare_rollback_data(changes)
        
        # Create snapshot
        snapshot = LearningSnapshot(
            version_id=version_id,
            timestamp=datetime.now().isoformat(),
            update_type=update_type.value,
            description=description,
            state_hash=state_hash,
            changes=changes,
            dependencies=dependencies or [],
            rollback_data=rollback_data
        )
        
        # Store snapshot
        self.snapshots[version_id] = snapshot
        self.current_version = version_id
        
        # Save to persistent storage
        await self._save_snapshots()
        
        self.logger.info(f"📸 Created learning snapshot {version_id}: {description}")
        
        return snapshot
    
    async def rollback_to_version(
        self,
        target_version_id: str,
        force: bool = False
    ) -> RollbackResult:
        """
        Rollback learning state to a specific version.
        
        Args:
            target_version_id: Version ID to rollback to
            force: Force rollback even if dependencies exist
            
        Returns:
            RollbackResult with operation status
        """
        start_time = datetime.now()
        
        if target_version_id not in self.snapshots:
            return RollbackResult(
                version_id=target_version_id,
                status=RollbackStatus.FAILED.value,
                timestamp=datetime.now().isoformat(),
                changes_reverted=[],
                errors=[f"Version {target_version_id} not found"],
                rollback_duration=0.0
            )
        
        # Check if rollback is needed
        if self.current_version == target_version_id:
            return RollbackResult(
                version_id=target_version_id,
                status=RollbackStatus.NOT_NEEDED.value,
                timestamp=datetime.now().isoformat(),
                changes_reverted=[],
                errors=[],
                rollback_duration=0.0
            )
        
        # Validate rollback safety
        if not force:
            safety_check = await self._validate_rollback_safety(target_version_id)
            if not safety_check["safe"]:
                return RollbackResult(
                    version_id=target_version_id,
                    status=RollbackStatus.FAILED.value,
                    timestamp=datetime.now().isoformat(),
                    changes_reverted=[],
                    errors=safety_check["errors"],
                    rollback_duration=0.0
                )
        
        # Perform rollback
        try:
            changes_reverted = await self._execute_rollback(target_version_id)
            
            # Update current version
            self.current_version = target_version_id
            
            # Record rollback
            rollback_duration = (datetime.now() - start_time).total_seconds()
            result = RollbackResult(
                version_id=target_version_id,
                status=RollbackStatus.SUCCESS.value,
                timestamp=datetime.now().isoformat(),
                changes_reverted=changes_reverted,
                errors=[],
                rollback_duration=rollback_duration
            )
            
            self.rollback_history.append(result)
            await self._save_snapshots()
            
            self.logger.info(f"⏪ Rollback to version {target_version_id} completed successfully")
            
            return result
            
        except Exception as e:
            rollback_duration = (datetime.now() - start_time).total_seconds()
            result = RollbackResult(
                version_id=target_version_id,
                status=RollbackStatus.FAILED.value,
                timestamp=datetime.now().isoformat(),
                changes_reverted=[],
                errors=[str(e)],
                rollback_duration=rollback_duration
            )
            
            self.rollback_history.append(result)
            self.logger.error(f"❌ Rollback to version {target_version_id} failed: {e}")
            
            return result
    
    async def get_rollback_candidates(self) -> List[Dict[str, Any]]:
        """Get list of versions that can be rolled back to"""
        candidates = []
        
        for version_id, snapshot in self.snapshots.items():
            # Check if version is rollback-able
            can_rollback = await self._can_rollback_to_version(version_id)
            
            candidates.append({
                "version_id": version_id,
                "timestamp": snapshot.timestamp,
                "description": snapshot.description,
                "update_type": snapshot.update_type,
                "can_rollback": can_rollback,
                "dependencies": snapshot.dependencies
            })
        
        # Sort by timestamp (newest first)
        candidates.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return candidates
    
    async def get_version_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get version history with rollback information"""
        history = []
        
        for version_id, snapshot in list(self.snapshots.items())[-limit:]:
            history.append({
                "version_id": version_id,
                "timestamp": snapshot.timestamp,
                "description": snapshot.description,
                "update_type": snapshot.update_type,
                "state_hash": snapshot.state_hash,
                "is_current": version_id == self.current_version
            })
        
        return history
    
    def _generate_version_id(self) -> str:
        """Generate unique version ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        return f"v{timestamp}_{random_suffix}"
    
    def _calculate_state_hash(self, changes: Dict[str, Any]) -> str:
        """Calculate hash of current state"""
        state_string = json.dumps(changes, sort_keys=True)
        return hashlib.sha256(state_string.encode()).hexdigest()[:16]
    
    async def _prepare_rollback_data(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data needed for rollback"""
        rollback_data = {}
        
        # For each change, store the previous state
        for key, new_value in changes.items():
            # In a real implementation, this would capture the previous state
            # For now, we'll simulate this
            rollback_data[key] = {
                "previous_value": f"previous_{key}",
                "change_type": "update",
                "revert_function": f"revert_{key}"
            }
        
        return rollback_data
    
    async def _validate_rollback_safety(self, target_version_id: str) -> Dict[str, Any]:
        """Validate that rollback is safe to perform"""
        errors = []
        
        # Check if target version exists
        if target_version_id not in self.snapshots:
            errors.append(f"Target version {target_version_id} not found")
            return {"safe": False, "errors": errors}
        
        # Check for dependent versions
        target_snapshot = self.snapshots[target_version_id]
        dependent_versions = [
            vid for vid, snapshot in self.snapshots.items()
            if target_version_id in snapshot.dependencies
        ]
        
        if dependent_versions:
            errors.append(f"Cannot rollback: {len(dependent_versions)} dependent versions exist")
            return {"safe": False, "errors": errors}
        
        # Check rollback depth
        if self.current_version:
            current_index = list(self.snapshots.keys()).index(self.current_version)
            target_index = list(self.snapshots.keys()).index(target_version_id)
            rollback_depth = current_index - target_index
            
            if rollback_depth > self.max_rollback_depth:
                errors.append(f"Rollback depth {rollback_depth} exceeds maximum {self.max_rollback_depth}")
                return {"safe": False, "errors": errors}
        
        return {"safe": True, "errors": []}
    
    async def _can_rollback_to_version(self, version_id: str) -> bool:
        """Check if a version can be rolled back to"""
        safety_check = await self._validate_rollback_safety(version_id)
        return safety_check["safe"]
    
    async def _execute_rollback(self, target_version_id: str) -> List[str]:
        """Execute the actual rollback operation"""
        changes_reverted = []
        
        # Get target snapshot
        target_snapshot = self.snapshots[target_version_id]
        
        # Revert each change
        for key, rollback_info in target_snapshot.rollback_data.items():
            try:
                # In a real implementation, this would call the actual revert function
                # For now, we'll simulate the rollback
                revert_function = rollback_info.get("revert_function", f"revert_{key}")
                previous_value = rollback_info.get("previous_value")
                
                # Simulate rollback
                self.logger.info(f"🔄 Reverting {key} to {previous_value}")
                changes_reverted.append(key)
                
            except Exception as e:
                self.logger.error(f"Failed to revert {key}: {e}")
        
        return changes_reverted
    
    async def _save_snapshots(self):
        """Save snapshots to persistent storage"""
        data = {
            "snapshots": {vid: asdict(snapshot) for vid, snapshot in self.snapshots.items()},
            "current_version": self.current_version,
            "rollback_history": [asdict(result) for result in self.rollback_history],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.snapshots_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"💾 Snapshots saved to {self.snapshots_path}")
    
    def _load_snapshots(self):
        """Load snapshots from persistent storage"""
        if not self.snapshots_path.exists():
            self.logger.info("No existing snapshots found")
            return
        
        try:
            with open(self.snapshots_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load snapshots
            for vid, snapshot_data in data.get("snapshots", {}).items():
                snapshot = LearningSnapshot(**snapshot_data)
                self.snapshots[vid] = snapshot
            
            # Load current version
            self.current_version = data.get("current_version")
            
            # Load rollback history
            for result_data in data.get("rollback_history", []):
                result = RollbackResult(**result_data)
                self.rollback_history.append(result)
            
            self.logger.info(f"📂 Loaded {len(self.snapshots)} snapshots")
            
        except Exception as e:
            self.logger.error(f"Failed to load snapshots: {e}")
    
    def get_current_version(self) -> Optional[str]:
        """Get current version ID"""
        return self.current_version
    
    def get_snapshot_count(self) -> int:
        """Get total number of snapshots"""
        return len(self.snapshots)
    
    def get_rollback_count(self) -> int:
        """Get total number of rollbacks performed"""
        return len(self.rollback_history)
