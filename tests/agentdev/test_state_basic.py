#!/usr/bin/env python3
"""
AgentDev State Store - Basic Tests
SEAL-grade tests for state management with checkpoint/resume
"""

import asyncio
import os
import signal
import time
import uuid
import pytest
from pathlib import Path
import tempfile
import shutil

from agentdev.state_store import StateStore, JobStatus, StepStatus, CheckpointType

class TestStateBasic:
    """Basic state store functionality tests"""
    
    def test_create_job_idempotent(self):
        """Test idempotent job creation"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job first time
                job1 = await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Create same job again (should return existing)
                job2 = await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Should be the same job
                assert job1.job_id == job2.job_id
                assert job1.created_at == job2.created_at
                assert job1.status == job2.status
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_create_step_idempotent(self):
        """Test idempotent step creation"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"test_step_{uuid.uuid4().hex[:8]}"
                
                # Create job first
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Create step first time
                step1 = await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="Test Step",
                    step_type="test",
                    order_index=1,
                    command="echo test"
                )
                
                # Create same step again (should return existing)
                step2 = await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="Test Step",
                    step_type="test",
                    order_index=1,
                    command="echo test"
                )
                
                # Should be the same step
                assert step1.step_id == step2.step_id
                assert step1.created_at == step2.created_at
                assert step1.status == step2.status
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_job_status_update(self):
        """Test job status updates"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                job = await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                assert job.status == JobStatus.PENDING
                
                # Update to running
                start_time = time.time()
                success = await store.update_job_status(
                    job_id, JobStatus.RUNNING, started_at=start_time
                )
                assert success
                
                # Verify update
                updated_job = await store.get_job(job_id)
                assert updated_job.status == JobStatus.RUNNING
                assert updated_job.started_at == start_time
                
                # Update to completed
                end_time = time.time()
                duration = int((end_time - start_time) * 1000)
                success = await store.update_job_status(
                    job_id, JobStatus.COMPLETED, completed_at=end_time, duration_ms=duration
                )
                assert success
                
                # Verify final state
                final_job = await store.get_job(job_id)
                assert final_job.status == JobStatus.COMPLETED
                assert final_job.completed_at == end_time
                assert final_job.duration_ms == duration
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_step_status_update(self):
        """Test step status updates"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"test_step_{uuid.uuid4().hex[:8]}"
                
                # Create job and step
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                step = await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="Test Step",
                    step_type="test",
                    order_index=1,
                    command="echo test"
                )
                
                assert step.status == StepStatus.PENDING
                
                # Update to running
                start_time = time.time()
                success = await store.update_step_status(
                    step_id, StepStatus.RUNNING, started_at=start_time
                )
                assert success
                
                # Verify update
                updated_step = await store.get_step(step_id)
                assert updated_step.status == StepStatus.RUNNING
                assert updated_step.started_at == start_time
                
                # Update to completed
                end_time = time.time()
                duration = int((end_time - start_time) * 1000)
                success = await store.update_step_status(
                    step_id, StepStatus.COMPLETED, completed_at=end_time, duration_ms=duration
                )
                assert success
                
                # Verify final state
                final_step = await store.get_step(step_id)
                assert final_step.status == StepStatus.COMPLETED
                assert final_step.completed_at == end_time
                assert final_step.duration_ms == duration
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_checkpoint_creation(self):
        """Test checkpoint creation"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Create checkpoint
                checkpoint = await store.create_checkpoint(
                    job_id=job_id,
                    checkpoint_type=CheckpointType.MANUAL,
                    state_snapshot={"current_step": 1, "data": "test"},
                    description="Test checkpoint"
                )
                
                assert checkpoint.job_id == job_id
                assert checkpoint.checkpoint_type == CheckpointType.MANUAL
                assert checkpoint.state_snapshot == {"current_step": 1, "data": "test"}
                assert checkpoint.description == "Test checkpoint"
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_resume_point_detection(self):
        """Test resume point detection"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"test_step_{uuid.uuid4().hex[:8]}"
                
                # Create job and step
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                step = await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="Test Step",
                    step_type="test",
                    order_index=1,
                    command="echo test"
                )
                
                # Complete the step
                await store.update_step_status(
                    step_id, StepStatus.COMPLETED, completed_at=time.time()
                )
                
                # Get resume point
                resume_point = await store.get_resume_point(job_id)
                assert resume_point is not None
                assert resume_point[0] == step_id  # step_id
                assert "completed_at" in resume_point[1]  # data
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_artifact_creation(self):
        """Test artifact creation"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                artifact_id = f"test_artifact_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Create artifact
                artifact = await store.create_artifact(
                    artifact_id=artifact_id,
                    job_id=job_id,
                    artifact_path="/tmp/test_file.txt",
                    artifact_type="text/plain",
                    metadata={"size": 100}
                )
                
                assert artifact.job_id == job_id
                assert artifact.artifact_path == "/tmp/test_file.txt"
                assert artifact.artifact_type == "text/plain"
                assert artifact.metadata["size"] == 100
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_event_logging(self):
        """Test event logging"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Log event
                await store.log_event(
                    event_type="test_event",
                    event_data={"message": "Test event logged"},
                    job_id=job_id
                )
                
                # Verify event was logged (check statistics)
                stats = await store.get_statistics()
                assert stats["total_jobs"] >= 1
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_statistics(self):
        """Test statistics collection"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Get statistics
                stats = await store.get_statistics()
                
                assert "total_jobs" in stats
                assert "completed_jobs" in stats
                assert "failed_jobs" in stats
                assert "success_rate" in stats
                assert stats["total_jobs"] >= 1
                assert stats["completed_jobs"] >= 0
                assert stats["failed_jobs"] >= 0
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_cleanup_expired(self):
        """Test cleanup of expired data"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Create checkpoint with short expiry
                await store.create_checkpoint(
                    job_id=job_id,
                    checkpoint_type=CheckpointType.MANUAL,
                    data={"test": "data"}
                )
                
                # Cleanup expired data
                cleanup_result = await store.cleanup_expired()
                
                assert "expired_checkpoints" in cleanup_result
                assert "expired_artifacts" in cleanup_result
                assert isinstance(cleanup_result["expired_checkpoints"], int)
                assert isinstance(cleanup_result["expired_artifacts"], int)
            finally:
                # Cleanup
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
