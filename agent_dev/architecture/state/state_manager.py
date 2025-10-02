#!/usr/bin/env python3
"""
StillMe AgentDev - State Manager
Enterprise-grade state management with persistence and recovery
"""

import asyncio
import json
import pickle
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import aiofiles

T = TypeVar('T')

class StateType(Enum):
    """State types for different AgentDev components"""
    TASK_STATE = "task_state"
    EXECUTION_STATE = "execution_state"
    PLAN_STATE = "plan_state"
    SECURITY_STATE = "security_state"
    WORKFLOW_STATE = "workflow_state"
    USER_SESSION = "user_session"
    SYSTEM_STATE = "system_state"

@dataclass
class StateSnapshot:
    """State snapshot for checkpointing"""
    snapshot_id: str
    state_type: StateType
    entity_id: str
    data: Dict[str, Any]
    timestamp: float
    version: int
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class StateTransition:
    """State transition record"""
    transition_id: str
    entity_id: str
    from_state: Optional[str]
    to_state: str
    timestamp: float
    reason: str
    data: Optional[Dict[str, Any]] = None

class StateManager:
    """Enterprise state manager with persistence, recovery, and versioning"""

    def __init__(self, config_path: Optional[str] = None):
        self.states: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, List[StateSnapshot]] = {}
        self.transitions: Dict[str, List[StateTransition]] = {}
        self.config = self._load_config(config_path)
        self.persistence_enabled = self.config.get('persistence', {}).get('enabled', True)
        self.state_dir = Path(self.config.get('persistence', {}).get('directory', '.agentdev/state'))
        self.max_snapshots = self.config.get('max_snapshots', 100)
        self.auto_checkpoint_interval = self.config.get('auto_checkpoint_interval', 300)  # 5 minutes
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load state manager configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/state_manager.yaml")

        if config_file.exists():
            import yaml
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                'persistence': {
                    'enabled': True,
                    'directory': '.agentdev/state',
                    'format': 'json'  # json or pickle
                },
                'max_snapshots': 100,
                'auto_checkpoint_interval': 300,
                'compression': True
            }

    def get_state(self, entity_id: str, state_type: StateType) -> Optional[Dict[str, Any]]:
        """Get current state for an entity"""
        with self.lock:
            state_key = f"{state_type.value}:{entity_id}"
            return self.states.get(state_key, {}).copy()

    def set_state(self, entity_id: str, state_type: StateType,
                 state_data: Dict[str, Any], reason: str = "manual_update") -> bool:
        """Set state for an entity"""
        with self.lock:
            state_key = f"{state_type.value}:{entity_id}"
            old_state = self.states.get(state_key, {})

            # Record transition
            transition = StateTransition(
                transition_id=str(uuid.uuid4()),
                entity_id=entity_id,
                from_state=old_state.get('current_state'),
                to_state=state_data.get('current_state', 'unknown'),
                timestamp=time.time(),
                reason=reason,
                data=state_data
            )

            if entity_id not in self.transitions:
                self.transitions[entity_id] = []
            self.transitions[entity_id].append(transition)

            # Update state
            self.states[state_key] = {
                **state_data,
                'last_updated': time.time(),
                'version': old_state.get('version', 0) + 1
            }

            print(f"📝 State updated: {entity_id} ({state_type.value}) - {reason}")
            return True

    def create_checkpoint(self, entity_id: str, state_type: StateType,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a checkpoint/snapshot of current state"""
        with self.lock:
            state_key = f"{state_type.value}:{entity_id}"
            current_state = self.states.get(state_key, {})

            if not current_state:
                raise ValueError(f"No state found for entity {entity_id}")

            snapshot = StateSnapshot(
                snapshot_id=str(uuid.uuid4()),
                state_type=state_type,
                entity_id=entity_id,
                data=current_state.copy(),
                timestamp=time.time(),
                version=current_state.get('version', 0),
                metadata=metadata
            )

            if entity_id not in self.snapshots:
                self.snapshots[entity_id] = []

            self.snapshots[entity_id].append(snapshot)

            # Limit snapshots
            if len(self.snapshots[entity_id]) > self.max_snapshots:
                self.snapshots[entity_id] = self.snapshots[entity_id][-self.max_snapshots:]

            print(f"💾 Checkpoint created: {entity_id} (snapshot: {snapshot.snapshot_id})")
            return snapshot.snapshot_id

    def restore_from_checkpoint(self, entity_id: str, snapshot_id: str) -> bool:
        """Restore state from a checkpoint"""
        with self.lock:
            if entity_id not in self.snapshots:
                return False

            snapshot = None
            for snap in self.snapshots[entity_id]:
                if snap.snapshot_id == snapshot_id:
                    snapshot = snap
                    break

            if not snapshot:
                return False

            state_key = f"{snapshot.state_type.value}:{entity_id}"
            self.states[state_key] = snapshot.data.copy()

            print(f"🔄 State restored: {entity_id} from snapshot {snapshot_id}")
            return True

    def get_checkpoints(self, entity_id: str) -> List[StateSnapshot]:
        """Get all checkpoints for an entity"""
        with self.lock:
            return self.snapshots.get(entity_id, []).copy()

    def get_state_transitions(self, entity_id: str) -> List[StateTransition]:
        """Get state transition history for an entity"""
        with self.lock:
            return self.transitions.get(entity_id, []).copy()

    async def persist_state(self, entity_id: str, state_type: StateType):
        """Persist state to disk"""
        if not self.persistence_enabled:
            return

        try:
            state_key = f"{state_type.value}:{entity_id}"
            state_data = self.states.get(state_key)

            if not state_data:
                return

            # Create state directory
            self.state_dir.mkdir(parents=True, exist_ok=True)

            # Persist state
            state_file = self.state_dir / f"{state_key}.json"
            async with aiofiles.open(state_file, 'w') as f:
                await f.write(json.dumps(state_data, indent=2))

            # Persist snapshots
            if entity_id in self.snapshots:
                snapshots_file = self.state_dir / f"{entity_id}_snapshots.json"
                snapshots_data = [asdict(snap) for snap in self.snapshots[entity_id]]
                async with aiofiles.open(snapshots_file, 'w') as f:
                    await f.write(json.dumps(snapshots_data, indent=2))

            # Persist transitions
            if entity_id in self.transitions:
                transitions_file = self.state_dir / f"{entity_id}_transitions.json"
                transitions_data = [asdict(trans) for trans in self.transitions[entity_id]]
                async with aiofiles.open(transitions_file, 'w') as f:
                    await f.write(json.dumps(transitions_data, indent=2))

        except Exception as e:
            print(f"⚠️ Failed to persist state for {entity_id}: {e}")

    async def load_state(self, entity_id: str, state_type: StateType) -> bool:
        """Load state from disk"""
        if not self.persistence_enabled:
            return False

        try:
            state_key = f"{state_type.value}:{entity_id}"
            state_file = self.state_dir / f"{state_key}.json"

            if not state_file.exists():
                return False

            async with aiofiles.open(state_file) as f:
                state_data = json.loads(await f.read())

            with self.lock:
                self.states[state_key] = state_data

            # Load snapshots
            snapshots_file = self.state_dir / f"{entity_id}_snapshots.json"
            if snapshots_file.exists():
                async with aiofiles.open(snapshots_file) as f:
                    snapshots_data = json.loads(await f.read())

                with self.lock:
                    self.snapshots[entity_id] = [
                        StateSnapshot(**snap_data) for snap_data in snapshots_data
                    ]

            # Load transitions
            transitions_file = self.state_dir / f"{entity_id}_transitions.json"
            if transitions_file.exists():
                async with aiofiles.open(transitions_file) as f:
                    transitions_data = json.loads(await f.read())

                with self.lock:
                    self.transitions[entity_id] = [
                        StateTransition(**trans_data) for trans_data in transitions_data
                    ]

            print(f"📂 State loaded: {entity_id} ({state_type.value})")
            return True

        except Exception as e:
            print(f"⚠️ Failed to load state for {entity_id}: {e}")
            return False

    async def auto_checkpoint_task(self):
        """Background task for automatic checkpointing"""
        while self.running:
            try:
                await asyncio.sleep(self.auto_checkpoint_interval)

                # Create checkpoints for all active states
                with self.lock:
                    for state_key, state_data in self.states.items():
                        if time.time() - state_data.get('last_updated', 0) < self.auto_checkpoint_interval:
                            state_type_str, entity_id = state_key.split(':', 1)
                            state_type = StateType(state_type_str)

                            # Create checkpoint in background
                            asyncio.create_task(
                                self._create_checkpoint_async(entity_id, state_type)
                            )

            except Exception as e:
                print(f"⚠️ Auto checkpoint error: {e}")

    async def _create_checkpoint_async(self, entity_id: str, state_type: StateType):
        """Create checkpoint asynchronously"""
        try:
            checkpoint_id = self.create_checkpoint(
                entity_id,
                state_type,
                metadata={"auto_checkpoint": True}
            )
            await self.persist_state(entity_id, state_type)
        except Exception as e:
            print(f"⚠️ Failed to create auto checkpoint for {entity_id}: {e}")

    def get_state_statistics(self) -> Dict[str, Any]:
        """Get state manager statistics"""
        with self.lock:
            total_states = len(self.states)
            total_snapshots = sum(len(snapshots) for snapshots in self.snapshots.values())
            total_transitions = sum(len(transitions) for transitions in self.transitions.values())

            state_types = {}
            for state_key in self.states.keys():
                state_type = state_key.split(':', 1)[0]
                state_types[state_type] = state_types.get(state_type, 0) + 1

            return {
                'total_states': total_states,
                'total_snapshots': total_snapshots,
                'total_transitions': total_transitions,
                'state_types': state_types,
                'entities_with_snapshots': len(self.snapshots),
                'entities_with_transitions': len(self.transitions)
            }

    async def start(self):
        """Start the state manager"""
        if self.running:
            return

        self.running = True

        # Start auto checkpoint task
        asyncio.create_task(self.auto_checkpoint_task())

        print("🚀 State Manager started")

    async def stop(self):
        """Stop the state manager"""
        self.running = False

        # Persist all states
        for state_key in self.states.keys():
            state_type_str, entity_id = state_key.split(':', 1)
            state_type = StateType(state_type_str)
            await self.persist_state(entity_id, state_type)

        print("🛑 State Manager stopped")

# Global state manager instance
state_manager = StateManager()

# Convenience functions for common state operations
class TaskState:
    """Task state management"""

    @staticmethod
    def create_task(task_id: str, task_type: str, config: Dict[str, Any]) -> bool:
        """Create a new task state"""
        return state_manager.set_state(
            entity_id=task_id,
            state_type=StateType.TASK_STATE,
            state_data={
                'current_state': 'created',
                'task_type': task_type,
                'config': config,
                'created_at': time.time(),
                'steps_completed': 0,
                'total_steps': 0
            },
            reason="task_created"
        )

    @staticmethod
    def update_task_status(task_id: str, status: str, progress: Optional[Dict[str, Any]] = None) -> bool:
        """Update task status"""
        current_state = state_manager.get_state(task_id, StateType.TASK_STATE)
        if not current_state:
            return False

        return state_manager.set_state(
            entity_id=task_id,
            state_type=StateType.TASK_STATE,
            state_data={
                **current_state,
                'current_state': status,
                'progress': progress or current_state.get('progress', {}),
                'last_status_update': time.time()
            },
            reason=f"status_changed_to_{status}"
        )

    @staticmethod
    def checkpoint_task(task_id: str) -> str:
        """Create checkpoint for task"""
        return state_manager.create_checkpoint(
            entity_id=task_id,
            state_type=StateType.TASK_STATE,
            metadata={"checkpoint_type": "task_milestone"}
        )

class ExecutionState:
    """Execution state management"""

    @staticmethod
    def start_execution(execution_id: str, task_id: str, plan_id: str) -> bool:
        """Start execution state"""
        return state_manager.set_state(
            entity_id=execution_id,
            state_type=StateType.EXECUTION_STATE,
            state_data={
                'current_state': 'running',
                'task_id': task_id,
                'plan_id': plan_id,
                'started_at': time.time(),
                'current_step': 0,
                'steps': [],
                'errors': []
            },
            reason="execution_started"
        )

    @staticmethod
    def add_execution_step(execution_id: str, step_data: Dict[str, Any]) -> bool:
        """Add execution step"""
        current_state = state_manager.get_state(execution_id, StateType.EXECUTION_STATE)
        if not current_state:
            return False

        steps = current_state.get('steps', [])
        steps.append({
            **step_data,
            'timestamp': time.time(),
            'step_number': len(steps) + 1
        })

        return state_manager.set_state(
            entity_id=execution_id,
            state_type=StateType.EXECUTION_STATE,
            state_data={
                **current_state,
                'steps': steps,
                'current_step': len(steps)
            },
            reason="step_added"
        )

if __name__ == "__main__":
    async def main():
        # Example usage
        manager = StateManager()
        await manager.start()

        # Create a task
        TaskState.create_task("task_123", "deploy_edge", {"target": "production"})

        # Update task status
        TaskState.update_task_status("task_123", "planning", {"progress": 25})

        # Create checkpoint
        checkpoint_id = TaskState.checkpoint_task("task_123")
        print(f"Checkpoint created: {checkpoint_id}")

        # Start execution
        ExecutionState.start_execution("exec_456", "task_123", "plan_789")

        # Add execution step
        ExecutionState.add_execution_step("exec_456", {
            "action": "validate_config",
            "status": "completed",
            "duration": 1.5
        })

        # Get statistics
        stats = manager.get_state_statistics()
        print(f"State statistics: {stats}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await manager.stop()

    asyncio.run(main())
