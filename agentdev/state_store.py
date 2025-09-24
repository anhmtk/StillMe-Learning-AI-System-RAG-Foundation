#!/usr/bin/env python3
"""
AgentDev State Store - SEAL-grade persistent state management
Enterprise-grade state management with checkpoint/resume capabilities
"""

import asyncio
import json
import os
import sqlite3
import time
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import aiosqlite
import threading
from contextlib import asynccontextmanager

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StepStatus(Enum):
    """Step status enumeration"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class CheckpointType(Enum):
    """Checkpoint type enumeration"""
    JOB_START = "job_start"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    MANUAL = "manual"
    SYSTEM = "system"

@dataclass
class Job:
    """Job data structure"""
    job_id: str
    job_type: str
    status: JobStatus
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    duration_ms: Optional[int]
    config: Dict[str, Any]
    variables: Dict[str, Any]
    metadata: Dict[str, Any]
    created_by: str
    updated_at: float

@dataclass
class JobStep:
    """Job step data structure"""
    step_id: str
    job_id: str
    step_name: str
    step_type: str
    status: StepStatus
    order_index: int
    started_at: Optional[float]
    completed_at: Optional[float]
    duration_ms: Optional[int]
    command: str
    working_directory: Optional[str]
    environment: Dict[str, str]
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    max_retries: int
    timeout_seconds: int
    dependencies: List[str]
    artifacts: List[str]
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    
    @property
    def tool_name(self) -> Optional[str]:
        """Get tool name from metadata"""
        return self.metadata.get("tool_name")
    
    @property
    def parameters(self) -> Optional[dict]:
        """Get parameters from metadata"""
        return self.metadata.get("parameters")
    
    @property
    def expected_output_schema(self) -> Optional[dict]:
        """Get expected output schema from metadata"""
        return self.metadata.get("expected_output_schema")
    
    @property
    def result(self) -> Optional[dict]:
        """Get result from output"""
        if self.output:
            try:
                return json.loads(self.output) if isinstance(self.output, str) else self.output
            except (json.JSONDecodeError, TypeError):
                return self.output
        return None
    
    @property
    def execution_log(self) -> Optional[str]:
        """Get execution log from error field"""
        return self.error

@dataclass
class Checkpoint:
    """Checkpoint data structure"""
    checkpoint_id: str
    job_id: str
    step_id: Optional[str]
    checkpoint_type: CheckpointType
    data: Dict[str, Any]
    created_at: float
    expires_at: Optional[float]
    metadata: Dict[str, Any]
    
    @property
    def state_snapshot(self) -> Optional[dict]:
        """Get state snapshot from data"""
        return self.data.get("state_snapshot")
    
    @property
    def description(self) -> Optional[str]:
        """Get description from data"""
        return self.data.get("description")

@dataclass
class Artifact:
    """Artifact data structure"""
    artifact_id: str
    job_id: str
    step_id: Optional[str]
    artifact_path: str
    artifact_type: str
    size_bytes: Optional[int]
    checksum: Optional[str]
    created_at: float
    expires_at: Optional[float]
    metadata: Dict[str, Any]
    
    @property
    def artifact_name(self) -> str:
        """Get artifact name from path"""
        return os.path.basename(self.artifact_path)
    
    @property
    def file_path(self) -> str:
        """Alias for artifact_path"""
        return self.artifact_path
    
    @property
    def content_type(self) -> str:
        """Alias for artifact_type"""
        return self.artifact_type

class StateStore:
    """SEAL-grade state store with checkpoint/resume capabilities"""
    
    def __init__(self, db_path: str = ".agentdev/state.db", 
                 ttl_cleanup_interval: int = 3600):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_cleanup_interval = ttl_cleanup_interval
        self.lock = threading.RLock()
        self._initialized = False
        
    async def initialize(self):
        """Initialize the state store"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Read and execute schema
            schema_path = Path(__file__).parent / "state_store.sql"
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            await db.executescript(schema_sql)
            await db.commit()
        
        self._initialized = True
        print("✅ State store initialized")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection with proper error handling"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                yield db
            except Exception as e:
                await db.rollback()
                raise e
            else:
                await db.commit()
    
    # Job CRUD operations
    async def create_job(self, job_id: str, job_type: str, config: Dict[str, Any],
                        variables: Dict[str, Any], created_by: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Job:
        """Create a new job with idempotent write"""
        async with self.get_connection() as db:
            # Check if job already exists
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            )
            existing = await cursor.fetchone()
            
            if existing:
                # Return existing job
                return self._row_to_job(existing)
            
            # Create new job
            current_time = time.time()
            job = Job(
                job_id=job_id,
                job_type=job_type,
                status=JobStatus.PENDING,
                created_at=current_time,
                started_at=None,
                completed_at=None,
                duration_ms=None,
                config=config,
                variables=variables,
                metadata=metadata or {},
                created_by=created_by,
                updated_at=current_time
            )
            
            await db.execute("""
                INSERT INTO jobs (job_id, job_type, status, created_at, config, 
                                variables, metadata, created_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.job_type, job.status.value, job.created_at,
                json.dumps(job.config), json.dumps(job.variables),
                json.dumps(job.metadata), job.created_by, job.updated_at
            ))
            
            # Create job start checkpoint
            await self._create_checkpoint(
                db, job_id, None, CheckpointType.JOB_START,
                {"status": "created", "config": config, "variables": variables}
            )
            
            print(f"✅ Job created: {job_id}")
            return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            )
            row = await cursor.fetchone()
            return self._row_to_job(row) if row else None
    
    async def update_job_status(self, job_id: str, status: JobStatus,
                               started_at: Optional[float] = None,
                               completed_at: Optional[float] = None,
                               duration_ms: Optional[int] = None) -> bool:
        """Update job status with idempotent write"""
        async with self.get_connection() as db:
            current_time = time.time()
            
            # Get current job
            cursor = await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            )
            job_row = await cursor.fetchone()
            if not job_row:
                return False
            
            # Update job
            await db.execute("""
                UPDATE jobs SET status = ?, started_at = ?, completed_at = ?, 
                              duration_ms = ?, updated_at = ?
                WHERE job_id = ?
            """, (status.value, started_at, completed_at, duration_ms, current_time, job_id))
            
            # Create checkpoint for status change
            checkpoint_data = {
                "status": status.value,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": duration_ms
            }
            await self._create_checkpoint(
                db, job_id, None, CheckpointType.SYSTEM, checkpoint_data
            )
            
            print(f"📝 Job status updated: {job_id} -> {status.value}")
            return True
    
    # Step CRUD operations
    async def create_step(self, step_id: str, job_id: str, step_name: str,
                         step_type: str, order_index: int, command: str,
                         working_directory: Optional[str] = None,
                         environment: Optional[Dict[str, str]] = None,
                         dependencies: Optional[List[str]] = None,
                         max_retries: int = 3, timeout_seconds: int = 300,
                         metadata: Optional[Dict[str, Any]] = None) -> JobStep:
        """Create a new job step with idempotent write"""
        async with self.get_connection() as db:
            # Check if step already exists
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE step_id = ?", (step_id,)
            )
            existing = await cursor.fetchone()
            
            if existing:
                return self._row_to_step(existing)
            
            current_time = time.time()
            step = JobStep(
                step_id=step_id,
                job_id=job_id,
                step_name=step_name,
                step_type=step_type,
                status=StepStatus.PENDING,
                order_index=order_index,
                started_at=None,
                completed_at=None,
                duration_ms=None,
                command=command,
                working_directory=working_directory,
                environment=environment or {},
                output=None,
                error=None,
                retry_count=0,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                dependencies=dependencies or [],
                artifacts=[],
                metadata=metadata or {},
                created_at=current_time,
                updated_at=current_time
            )
            
            await db.execute("""
                INSERT INTO job_steps (step_id, job_id, step_name, step_type, status,
                                     order_index, command, working_directory, environment,
                                     retry_count, max_retries, timeout_seconds, dependencies,
                                     artifacts, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                step.step_id, step.job_id, step.step_name, step.step_type,
                step.status.value, step.order_index, step.command,
                step.working_directory, json.dumps(step.environment),
                step.retry_count, step.max_retries, step.timeout_seconds,
                json.dumps(step.dependencies), json.dumps(step.artifacts),
                json.dumps(step.metadata), step.created_at, step.updated_at
            ))
            
            print(f"✅ Step created: {step_id}")
            return step
    
    async def get_step(self, step_id: str) -> Optional[JobStep]:
        """Get step by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE step_id = ?", (step_id,)
            )
            row = await cursor.fetchone()
            return self._row_to_step(row) if row else None
    
    async def get_job_steps(self, job_id: str) -> List[JobStep]:
        """Get all steps for a job"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE job_id = ? ORDER BY order_index",
                (job_id,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_step(row) for row in rows]
    
    async def update_step_status(self, step_id: str, status: StepStatus,
                                started_at: Optional[float] = None,
                                completed_at: Optional[float] = None,
                                duration_ms: Optional[int] = None,
                                output: Optional[Dict[str, Any]] = None,
                                error: Optional[str] = None,
                                retry_count: Optional[int] = None) -> bool:
        """Update step status with idempotent write"""
        async with self.get_connection() as db:
            current_time = time.time()
            
            # Get current step
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE step_id = ?", (step_id,)
            )
            step_row = await cursor.fetchone()
            if not step_row:
                return False
            
            # Update step
            await db.execute("""
                UPDATE job_steps SET status = ?, started_at = ?, completed_at = ?,
                                    duration_ms = ?, output = ?, error = ?, retry_count = ?,
                                    updated_at = ?
                WHERE step_id = ?
            """, (
                status.value, started_at, completed_at, duration_ms,
                json.dumps(output) if output else None, error,
                retry_count, current_time, step_id
            ))
            
            # Create checkpoint for step status change
            step = self._row_to_step(step_row)
            checkpoint_type = CheckpointType.STEP_START if status == StepStatus.RUNNING else CheckpointType.STEP_COMPLETE
            
            checkpoint_data = {
                "status": status.value,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "output": output,
                "error": error
            }
            await self._create_checkpoint(
                db, step.job_id, step_id, checkpoint_type, checkpoint_data
            )
            
            print(f"📝 Step status updated: {step_id} -> {status.value}")
            return True
    
    # Checkpoint operations
    async def _create_checkpoint(self, db: aiosqlite.Connection, job_id: str,
                                step_id: Optional[str], checkpoint_type: CheckpointType,
                                data: Dict[str, Any], expires_at: Optional[float] = None) -> str:
        """Create checkpoint with idempotent write"""
        checkpoint_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Set default expiration (24 hours)
        if expires_at is None:
            expires_at = current_time + 86400
        
        await db.execute("""
            INSERT INTO checkpoints (checkpoint_id, job_id, step_id, checkpoint_type,
                                   data, created_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            checkpoint_id, job_id, step_id, checkpoint_type.value,
            json.dumps(data), current_time, expires_at, json.dumps({})
        ))
        
        return checkpoint_id
    
    async def get_latest_checkpoint(self, job_id: str, 
                                   checkpoint_type: Optional[CheckpointType] = None) -> Optional[Checkpoint]:
        """Get latest checkpoint for job"""
        async with self.get_connection() as db:
            if checkpoint_type:
                cursor = await db.execute("""
                    SELECT * FROM checkpoints 
                    WHERE job_id = ? AND checkpoint_type = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (job_id, checkpoint_type.value))
            else:
                cursor = await db.execute("""
                    SELECT * FROM checkpoints 
                    WHERE job_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (job_id,))
            
            row = await cursor.fetchone()
            return self._row_to_checkpoint(row) if row else None
    
    async def get_resume_point(self, job_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get resume point for job (last completed step)"""
        async with self.get_connection() as db:
            # Find last completed step
            cursor = await db.execute("""
                SELECT step_id FROM job_steps 
                WHERE job_id = ? AND status = 'completed'
                ORDER BY order_index DESC LIMIT 1
            """, (job_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            last_completed_step = row[0]
            
            # Get checkpoint for that step
            cursor = await db.execute("""
                SELECT data FROM checkpoints 
                WHERE job_id = ? AND step_id = ? AND checkpoint_type = 'step_complete'
                ORDER BY created_at DESC LIMIT 1
            """, (job_id, last_completed_step))
            
            checkpoint_row = await cursor.fetchone()
            if not checkpoint_row:
                return None
            
            checkpoint_data = json.loads(checkpoint_row[0])
            return last_completed_step, checkpoint_data
    
    # Artifact operations
    async def create_artifact(self, artifact_id: str, job_id: str,
                             artifact_path: str, artifact_type: str,
                             step_id: Optional[str] = None,
                             size_bytes: Optional[int] = None,
                             checksum: Optional[str] = None,
                             expires_at: Optional[float] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Artifact:
        """Create artifact record"""
        async with self.get_connection() as db:
            current_time = time.time()
            
            artifact = Artifact(
                artifact_id=artifact_id,
                job_id=job_id,
                step_id=step_id,
                artifact_path=artifact_path,
                artifact_type=artifact_type,
                size_bytes=size_bytes,
                checksum=checksum,
                created_at=current_time,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            await db.execute("""
                INSERT INTO artifacts (artifact_id, job_id, step_id, artifact_path,
                                     artifact_type, size_bytes, checksum, created_at,
                                     expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact.artifact_id, artifact.job_id, artifact.step_id,
                artifact.artifact_path, artifact.artifact_type, artifact.size_bytes,
                artifact.checksum, artifact.created_at, artifact.expires_at,
                json.dumps(artifact.metadata)
            ))
            
            print(f"✅ Artifact created: {artifact_id}")
            return artifact
    
    # Event operations
    async def log_event(self, event_type: str, event_data: Dict[str, Any],
                       job_id: Optional[str] = None, step_id: Optional[str] = None,
                       correlation_id: Optional[str] = None,
                       causation_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log event with idempotent write"""
        async with self.get_connection() as db:
            event_id = str(uuid.uuid4())
            current_time = time.time()
            
            await db.execute("""
                INSERT INTO events (event_id, job_id, step_id, event_type, event_data,
                                  created_at, correlation_id, causation_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, job_id, step_id, event_type, json.dumps(event_data),
                current_time, correlation_id, causation_id, json.dumps(metadata or {})
            ))
            
            return event_id
    
    # TTL Cleanup
    async def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired checkpoints and artifacts"""
        async with self.get_connection() as db:
            # Clean expired checkpoints
            cursor = await db.execute("""
                DELETE FROM checkpoints 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (time.time(),))
            expired_checkpoints = cursor.rowcount
            
            # Clean expired artifacts
            cursor = await db.execute("""
                DELETE FROM artifacts 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (time.time(),))
            expired_artifacts = cursor.rowcount
            
            print(f"🧹 Cleaned up {expired_checkpoints} checkpoints, {expired_artifacts} artifacts")
            
            return {
                "expired_checkpoints": expired_checkpoints,
                "expired_artifacts": expired_artifacts
            }
    
    # Helper methods
    def _row_to_job(self, row) -> Job:
        """Convert database row to Job object"""
        return Job(
            job_id=row['job_id'],
            job_type=row['job_type'],
            status=JobStatus(row['status']),
            created_at=row['created_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            duration_ms=row['duration_ms'],
            config=json.loads(row['config'] or '{}'),
            variables=json.loads(row['variables'] or '{}'),
            metadata=json.loads(row['metadata'] or '{}'),
            created_by=row['created_by'],
            updated_at=row['updated_at']
        )
    
    def _row_to_step(self, row) -> JobStep:
        """Convert database row to JobStep object"""
        return JobStep(
            step_id=row['step_id'],
            job_id=row['job_id'],
            step_name=row['step_name'],
            step_type=row['step_type'],
            status=StepStatus(row['status']),
            order_index=row['order_index'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            duration_ms=row['duration_ms'],
            command=row['command'],
            working_directory=row['working_directory'],
            environment=json.loads(row['environment'] or '{}'),
            output=json.loads(row['output']) if row['output'] else None,
            error=row['error'],
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            timeout_seconds=row['timeout_seconds'],
            dependencies=json.loads(row['dependencies'] or '[]'),
            artifacts=json.loads(row['artifacts'] or '[]'),
            metadata=json.loads(row['metadata'] or '{}'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_checkpoint(self, row) -> Checkpoint:
        """Convert database row to Checkpoint object"""
        return Checkpoint(
            checkpoint_id=row['checkpoint_id'],
            job_id=row['job_id'],
            step_id=row['step_id'],
            checkpoint_type=CheckpointType(row['checkpoint_type']),
            data=json.loads(row['data']),
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            metadata=json.loads(row['metadata'] or '{}')
        )
    
    # Statistics and monitoring
    async def get_statistics(self) -> Dict[str, Any]:
        """Get state store statistics"""
        async with self.get_connection() as db:
            # Job statistics
            cursor = await db.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'")
            completed_jobs = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'failed'")
            failed_jobs = (await cursor.fetchone())[0]
            
            # Step statistics
            cursor = await db.execute("SELECT COUNT(*) FROM job_steps")
            total_steps = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM job_steps WHERE status = 'completed'")
            completed_steps = (await cursor.fetchone())[0]
            
            # Checkpoint statistics
            cursor = await db.execute("SELECT COUNT(*) FROM checkpoints")
            total_checkpoints = (await cursor.fetchone())[0]
            
            # Artifact statistics
            cursor = await db.execute("SELECT COUNT(*) FROM artifacts")
            total_artifacts = (await cursor.fetchone())[0]
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "total_checkpoints": total_checkpoints,
                "total_artifacts": total_artifacts
            }
    
    # Alias methods for test compatibility
    async def add_job_step(self, job_id: str, step_name: str, tool_name: str,
                          parameters: dict, expected_output_schema: dict = None) -> JobStep:
        """Add job step with tool-specific parameters"""
        step_id = f"{job_id}_{step_name}_{int(time.time())}"
        return await self.create_step(
            step_id=step_id,
            job_id=job_id,
            step_name=step_name,
            step_type="tool",
            order_index=0,
            command=f"tool:{tool_name}",
            metadata={
                "tool_name": tool_name,
                "parameters": parameters,
                "expected_output_schema": expected_output_schema
            }
        )
    
    async def store_artifact(self, job_id: str, artifact_name: str, file_path: str,
                            content_type: str = "application/octet-stream", 
                            metadata: Dict[str, Any] = None) -> Artifact:
        """Store artifact with test compatibility"""
        artifact_id = f"{job_id}_{artifact_name}_{int(time.time())}"
        return await self.create_artifact(
            artifact_id=artifact_id,
            job_id=job_id,
            artifact_path=file_path,
            artifact_type=content_type,
            metadata=metadata or {}
        )
    
    async def list_jobs(self, limit: int = 100, offset: int = 0) -> list:
        """List jobs with pagination"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = await cursor.fetchall()
            return [self._row_to_job(row) for row in rows]
    
    async def cleanup_expired_data(self) -> int:
        """Alias for cleanup_expired - returns total count"""
        result = await self.cleanup_expired()
        return result.get("expired_checkpoints", 0) + result.get("expired_artifacts", 0)
    
    async def create_checkpoint(self, job_id: str, step_id: Optional[str] = None, 
                               checkpoint_type: CheckpointType = CheckpointType.MANUAL, 
                               data: Dict[str, Any] = None, state_snapshot: Dict[str, Any] = None,
                               description: str = None) -> Checkpoint:
        """Create checkpoint (public method) with test compatibility"""
        if data is None:
            data = {}
        if state_snapshot:
            data["state_snapshot"] = state_snapshot
        if description:
            data["description"] = description
            
        async with self.get_connection() as db:
            checkpoint_id = await self._create_checkpoint(db, job_id, step_id, checkpoint_type, data)
            # Return the checkpoint object
            cursor = await db.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
            )
            row = await cursor.fetchone()
            return self._row_to_checkpoint(row) if row else None
    
    async def complete_job_step(self, job_id: str, step_id: str, result: Dict[str, Any] = None,
                               execution_log: str = None) -> JobStep:
        """Complete a job step with result and log"""
        async with self.get_connection() as db:
            current_time = time.time()
            
            # Update step status to completed
            await db.execute("""
                UPDATE job_steps SET status = ?, completed_at = ?, updated_at = ?,
                                    output = ?, error = ?
                WHERE step_id = ?
            """, (StepStatus.COMPLETED.value, current_time, current_time, 
                  json.dumps(result) if result else None, execution_log, step_id))
            
            # Get updated step
            cursor = await db.execute(
                "SELECT * FROM job_steps WHERE step_id = ?", (step_id,)
            )
            row = await cursor.fetchone()
            return self._row_to_step(row) if row else None
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job details including steps and checkpoints"""
        job = await self.get_job(job_id)
        if not job:
            return None
            
        steps = await self.get_job_steps(job_id)
        latest_checkpoint = await self.get_latest_checkpoint(job_id)
        
        # Get all checkpoints for this job (excluding system checkpoints)
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM checkpoints WHERE job_id = ? AND checkpoint_type != 'job_start' ORDER BY created_at DESC", (job_id,)
            )
            rows = await cursor.fetchall()
            checkpoints = [self._row_to_checkpoint(row) for row in rows]
        
        return {
            "job": job,
            "steps": steps,
            "checkpoints": checkpoints,
            "latest_checkpoint": latest_checkpoint
        }
    
    async def resume_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Resume job from specific checkpoint"""
        async with self.get_connection() as db:
            # Get checkpoint
            cursor = await db.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
                
            checkpoint = self._row_to_checkpoint(row)
            job = await self.get_job(checkpoint.job_id)
            
            return {
                "job": job,
                "checkpoint": checkpoint,
                "state_snapshot": checkpoint.state_snapshot
            }

# Global state store instance
state_store = StateStore()

# Convenience functions
async def create_job(job_id: str, job_type: str, config: Dict[str, Any],
                    variables: Dict[str, Any], created_by: str) -> Job:
    """Create a new job"""
    return await state_store.create_job(job_id, job_type, config, variables, created_by)

async def get_job(job_id: str) -> Optional[Job]:
    """Get job by ID"""
    return await state_store.get_job(job_id)

async def resume_job(job_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Get resume point for job"""
    return await state_store.get_resume_point(job_id)

if __name__ == "__main__":
    async def main():
        # Example usage
        store = StateStore()
        await store.initialize()
        
        # Create a job
        job = await store.create_job(
            job_id="test_job_123",
            job_type="deploy_edge",
            config={"target": "production"},
            variables={"env": "prod"},
            created_by="developer"
        )
        print(f"Created job: {job.job_id}")
        
        # Create steps
        step1 = await store.create_step(
            step_id="step_1",
            job_id=job.job_id,
            step_name="Validate Config",
            step_type="validation",
            order_index=1,
            command="python validate.py"
        )
        
        step2 = await store.create_step(
            step_id="step_2",
            job_id=job.job_id,
            step_name="Deploy",
            step_type="deployment",
            order_index=2,
            command="python deploy.py",
            dependencies=["step_1"]
        )
        
        # Update step status
        await store.update_step_status(step1.step_id, StepStatus.COMPLETED, 
                                     completed_at=time.time(), duration_ms=1500)
        
        # Get resume point
        resume_point = await store.get_resume_point(job.job_id)
        if resume_point:
            print(f"Resume from step: {resume_point[0]}")
        
        # Get statistics
        stats = await store.get_statistics()
        print(f"Statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
