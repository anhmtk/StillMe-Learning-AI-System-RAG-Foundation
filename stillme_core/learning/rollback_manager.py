"""
Learning Rollback Manager v2 with Safe Sandbox
Advanced version control and rollback system for learning updates.
"""

import json
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class RollbackReason(Enum):
    """Reasons for rollback"""
    ETHICS_VIOLATION = "ethics_violation"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ISSUE = "security_issue"
    USER_REQUEST = "user_request"
    AUTOMATIC_SAFETY = "automatic_safety"

class SandboxStatus(Enum):
    """Sandbox execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class LearningSnapshot:
    """Snapshot of learning state at a specific point"""
    version_id: str
    timestamp: str
    model_state: Dict[str, Any]
    learning_data: Dict[str, Any]
    performance_metrics: Dict[str, float]
    ethics_scores: Dict[str, float]
    safety_metrics: Dict[str, float]
    checksum: str
    description: str

@dataclass
class SandboxResult:
    """Result of sandbox execution"""
    sandbox_id: str
    status: SandboxStatus
    execution_time: float
    performance_delta: float
    ethics_score: float
    safety_score: float
    errors: List[str]
    warnings: List[str]
    rollback_required: bool
    rollback_reason: Optional[RollbackReason]

class RollbackManager:
    """
    Advanced rollback manager with safe sandbox execution
    """
    
    def __init__(self, snapshots_dir: str = "snapshots", sandbox_dir: str = "sandbox"):
        self.snapshots_dir = Path(snapshots_dir)
        self.sandbox_dir = Path(sandbox_dir)
        self.snapshots_dir.mkdir(exist_ok=True)
        self.sandbox_dir.mkdir(exist_ok=True)
        
        # Load existing snapshots
        self.snapshots = self._load_snapshots()
        logger.info(f"Loaded {len(self.snapshots)} existing snapshots")
    
    def _load_snapshots(self) -> Dict[str, LearningSnapshot]:
        """Load existing snapshots from disk"""
        snapshots = {}
        
        if not self.snapshots_dir.exists():
            return snapshots
        
        for snapshot_file in self.snapshots_dir.glob("*.json"):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshot = LearningSnapshot(**data)
                    snapshots[snapshot.version_id] = snapshot
                    logger.info(f"Loaded snapshot: {snapshot.version_id}")
            except Exception as e:
                logger.error(f"Failed to load snapshot {snapshot_file}: {e}")
        
        return snapshots
    
    async def create_snapshot(
        self,
        model_state: Dict[str, Any],
        learning_data: Dict[str, Any],
        performance_metrics: Dict[str, float],
        ethics_scores: Dict[str, float],
        safety_metrics: Dict[str, float],
        description: str = "Manual snapshot"
    ) -> str:
        """
        Create a new learning snapshot
        
        Args:
            model_state: Current model state
            learning_data: Learning data and parameters
            performance_metrics: Performance metrics
            ethics_scores: Ethics compliance scores
            safety_metrics: Safety metrics
            description: Human-readable description
            
        Returns:
            Version ID of the created snapshot
        """
        timestamp = datetime.now()
        version_id = f"v{timestamp.strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        
        # Create snapshot data
        snapshot_data = {
            "model_state": model_state,
            "learning_data": learning_data,
            "performance_metrics": performance_metrics,
            "ethics_scores": ethics_scores,
            "safety_metrics": safety_metrics
        }
        
        # Calculate checksum
        checksum = hashlib.sha256(json.dumps(snapshot_data, sort_keys=True).encode()).hexdigest()
        
        snapshot = LearningSnapshot(
            version_id=version_id,
            timestamp=timestamp.isoformat(),
            model_state=model_state,
            learning_data=learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            checksum=checksum,
            description=description
        )
        
        # Save snapshot
        await self._save_snapshot(snapshot)
        self.snapshots[version_id] = snapshot
        
        logger.info(f"Created snapshot: {version_id}")
        return version_id
    
    async def _save_snapshot(self, snapshot: LearningSnapshot):
        """Save snapshot to disk"""
        try:
            snapshot_file = self.snapshots_dir / f"{snapshot.version_id}.json"
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Snapshot saved: {snapshot_file}")
            
        except Exception as e:
            logger.error(f"Failed to save snapshot {snapshot.version_id}: {e}")
            raise
    
    async def execute_in_sandbox(
        self,
        learning_update: Dict[str, Any],
        baseline_snapshot: str,
        timeout: int = 300
    ) -> SandboxResult:
        """
        Execute learning update in safe sandbox
        
        Args:
            learning_update: Learning update to test
            baseline_snapshot: Baseline snapshot version ID
            timeout: Execution timeout in seconds
            
        Returns:
            SandboxResult with execution results
        """
        if baseline_snapshot not in self.snapshots:
            raise ValueError(f"Baseline snapshot {baseline_snapshot} not found")
        
        sandbox_id = f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sandbox_path = self.sandbox_dir / sandbox_id
        sandbox_path.mkdir(exist_ok=True)
        
        logger.info(f"Executing sandbox test: {sandbox_id}")
        
        start_time = datetime.now()
        status = SandboxStatus.RUNNING
        errors = []
        warnings = []
        
        try:
            # Simulate sandbox execution
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Evaluate performance
            performance_delta = await self._evaluate_performance(learning_update, baseline_snapshot)
            
            # Evaluate ethics
            ethics_score = await self._evaluate_ethics(learning_update)
            
            # Evaluate safety
            safety_score = await self._evaluate_safety(learning_update)
            
            # Determine if rollback is required
            rollback_required, rollback_reason = self._determine_rollback_requirement(
                performance_delta, ethics_score, safety_score
            )
            
            if rollback_required:
                status = SandboxStatus.ROLLED_BACK
                warnings.append(f"Rollback required: {rollback_reason.value}")
            else:
                status = SandboxStatus.COMPLETED
            
        except Exception as e:
            status = SandboxStatus.FAILED
            errors.append(f"Sandbox execution failed: {str(e)}")
            rollback_required = True
            rollback_reason = RollbackReason.AUTOMATIC_SAFETY
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = SandboxResult(
            sandbox_id=sandbox_id,
            status=status,
            execution_time=execution_time,
            performance_delta=performance_delta if 'performance_delta' in locals() else 0.0,
            ethics_score=ethics_score if 'ethics_score' in locals() else 0.0,
            safety_score=safety_score if 'safety_score' in locals() else 0.0,
            errors=errors,
            warnings=warnings,
            rollback_required=rollback_required,
            rollback_reason=rollback_reason
        )
        
        # Clean up sandbox
        await self._cleanup_sandbox(sandbox_path)
        
        logger.info(f"Sandbox execution completed: {status.value}")
        return result
    
    async def _evaluate_performance(self, learning_update: Dict[str, Any], baseline_snapshot: str) -> float:
        """Evaluate performance impact of learning update"""
        # Simulate performance evaluation
        baseline_metrics = self.snapshots[baseline_snapshot].performance_metrics
        baseline_score = sum(baseline_metrics.values()) / len(baseline_metrics) if baseline_metrics else 0.0
        
        # Simulate new performance (with some variation)
        import random
        performance_delta = random.uniform(-0.1, 0.2)  # -10% to +20% change
        
        return performance_delta
    
    async def _evaluate_ethics(self, learning_update: Dict[str, Any]) -> float:
        """Evaluate ethics compliance of learning update"""
        # Simulate ethics evaluation
        import random
        ethics_score = random.uniform(0.7, 1.0)  # 70-100% ethics compliance
        
        return ethics_score
    
    async def _evaluate_safety(self, learning_update: Dict[str, Any]) -> float:
        """Evaluate safety of learning update"""
        # Simulate safety evaluation
        import random
        safety_score = random.uniform(0.8, 1.0)  # 80-100% safety score
        
        return safety_score
    
    def _determine_rollback_requirement(
        self, 
        performance_delta: float, 
        ethics_score: float, 
        safety_score: float
    ) -> Tuple[bool, Optional[RollbackReason]]:
        """Determine if rollback is required based on evaluation results"""
        
        # Check ethics violation
        if ethics_score < 0.8:
            return True, RollbackReason.ETHICS_VIOLATION
        
        # Check safety issue
        if safety_score < 0.85:
            return True, RollbackReason.SECURITY_ISSUE
        
        # Check performance degradation
        if performance_delta < -0.15:  # More than 15% performance drop
            return True, RollbackReason.PERFORMANCE_DEGRADATION
        
        return False, None
    
    async def _cleanup_sandbox(self, sandbox_path: Path):
        """Clean up sandbox directory"""
        try:
            if sandbox_path.exists():
                shutil.rmtree(sandbox_path)
                logger.info(f"Sandbox cleaned up: {sandbox_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {sandbox_path}: {e}")
    
    async def rollback_to_version(
        self, 
        version_id: str, 
        reason: RollbackReason = RollbackReason.USER_REQUEST
    ) -> bool:
        """
        Rollback to a specific version
        
        Args:
            version_id: Version ID to rollback to
            reason: Reason for rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        if version_id not in self.snapshots:
            logger.error(f"Snapshot {version_id} not found for rollback")
            return False
        
        try:
            snapshot = self.snapshots[version_id]
            
            # Create rollback snapshot before applying
            rollback_snapshot_id = await self.create_snapshot(
                model_state=snapshot.model_state,
                learning_data=snapshot.learning_data,
                performance_metrics=snapshot.performance_metrics,
                ethics_scores=snapshot.ethics_scores,
                safety_metrics=snapshot.safety_metrics,
                description=f"Rollback to {version_id} - {reason.value}"
            )
            
            # Apply rollback (simulate)
            logger.info(f"Rolling back to version {version_id} (reason: {reason.value})")
            
            # In a real implementation, this would restore the actual model state
            await asyncio.sleep(0.1)  # Simulate rollback time
            
            logger.info(f"Rollback completed successfully to {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_snapshot_history(self) -> List[Dict[str, Any]]:
        """Get snapshot history"""
        history = []
        
        for snapshot in sorted(self.snapshots.values(), key=lambda x: x.timestamp):
            history.append({
                "version_id": snapshot.version_id,
                "timestamp": snapshot.timestamp,
                "description": snapshot.description,
                "performance_metrics": snapshot.performance_metrics,
                "ethics_scores": snapshot.ethics_scores,
                "safety_metrics": snapshot.safety_metrics,
                "checksum": snapshot.checksum
            })
        
        return history
    
    def get_latest_snapshot(self) -> Optional[LearningSnapshot]:
        """Get the latest snapshot"""
        if not self.snapshots:
            return None
        
        return max(self.snapshots.values(), key=lambda x: x.timestamp)
    
    def get_snapshot_by_id(self, version_id: str) -> Optional[LearningSnapshot]:
        """Get snapshot by version ID"""
        return self.snapshots.get(version_id)
    
    async def export_snapshot_data(self, version_id: str, output_path: str) -> bool:
        """Export snapshot data to file"""
        if version_id not in self.snapshots:
            logger.error(f"Snapshot {version_id} not found")
            return False
        
        try:
            snapshot = self.snapshots[version_id]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Snapshot {version_id} exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export snapshot {version_id}: {e}")
            return False
    
    def get_rollback_statistics(self) -> Dict[str, Any]:
        """Get rollback statistics"""
        if not self.snapshots:
            return {
                "total_snapshots": 0,
                "rollback_count": 0,
                "latest_version": None,
                "snapshot_health": "unknown"
            }
        
        # Count rollbacks (snapshots with "Rollback" in description)
        rollback_count = sum(1 for snapshot in self.snapshots.values() 
                           if "rollback" in snapshot.description.lower())
        
        latest_snapshot = self.get_latest_snapshot()
        
        return {
            "total_snapshots": len(self.snapshots),
            "rollback_count": rollback_count,
            "latest_version": latest_snapshot.version_id if latest_snapshot else None,
            "snapshot_health": "good" if rollback_count < len(self.snapshots) * 0.3 else "needs_attention",
            "average_ethics_score": sum(s.ethics_scores.get("overall", 0) for s in self.snapshots.values()) / len(self.snapshots),
            "average_safety_score": sum(s.safety_metrics.get("overall", 0) for s in self.snapshots.values()) / len(self.snapshots)
        }
