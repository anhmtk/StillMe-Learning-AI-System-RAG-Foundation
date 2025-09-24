#!/usr/bin/env python3
"""
State Management Simple Tests - SEAL-grade Unit Tests (Minimal Version)
Tests basic state operations using the actual StateStore API.
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import asyncio
import uuid
import time

# Add agentdev to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "agentdev"))

from state_store import StateStore, JobStatus, StepStatus, CheckpointType

class TestStateSimple:
    """Basic state store functionality tests (Simple)"""
    
    async def _create_temp_store(self):
        """Helper to create temporary state store"""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        try:
            os.close(temp_fd)  # Close the file descriptor
            store = StateStore(db_path=temp_path)
            await store.initialize()
            return store, temp_path
        except:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def _cleanup_temp_store(self, temp_path):
        """Helper to cleanup temporary database"""
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_create_job_basic(self):
        """Test basic job creation"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                job = await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                assert job is not None
                assert job.job_id == job_id
                assert job.status == JobStatus.PENDING
                assert job.job_type == "test"
                assert job.created_by == "test_user"
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_create_job_idempotent(self):
        """Test idempotent job creation"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
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
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_get_job(self):
        """Test getting job by ID"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                created_job = await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Get job by ID
                retrieved_job = await store.get_job(job_id)
                
                assert retrieved_job is not None
                assert retrieved_job.job_id == created_job.job_id
                assert retrieved_job.status == created_job.status
                assert retrieved_job.created_at == created_job.created_at
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_update_job_status(self):
        """Test updating job status"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Update status to running
                start_time = time.time()
                update_result = await store.update_job_status(
                    job_id=job_id,
                    status=JobStatus.RUNNING,
                    started_at=start_time
                )
                
                assert update_result is True
                
                # Get updated job to verify
                updated_job = await store.get_job(job_id)
                assert updated_job.status == JobStatus.RUNNING
                assert updated_job.started_at == start_time
                
                # Update status to completed
                complete_time = time.time()
                duration = int((complete_time - start_time) * 1000)
                complete_result = await store.update_job_status(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=complete_time,
                    duration_ms=duration
                )
                
                assert complete_result is True
                
                # Get completed job to verify
                completed_job = await store.get_job(job_id)
                assert completed_job.status == JobStatus.COMPLETED
                assert completed_job.completed_at == complete_time
                assert completed_job.duration_ms == duration
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_create_step(self):
        """Test creating job steps"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"step_{uuid.uuid4().hex[:8]}"
                
                # Create job first
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Create step
                step = await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="test_step",
                    step_type="test_tool",
                    order_index=1,
                    command="echo 'test'",
                    working_directory="/tmp",
                    environment={"ENV": "test"}
                )
                
                assert step is not None
                assert step.step_id == step_id
                assert step.job_id == job_id
                assert step.step_name == "test_step"
                assert step.status == StepStatus.PENDING
                assert step.order_index == 1
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_get_job_steps(self):
        """Test getting steps for a job"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                # Create multiple steps
                step_ids = []
                for i in range(3):
                    step_id = f"step_{i}_{uuid.uuid4().hex[:8]}"
                    step_ids.append(step_id)
                    await store.create_step(
                        step_id=step_id,
                        job_id=job_id,
                        step_name=f"test_step_{i}",
                        step_type="test_tool",
                        order_index=i+1,
                        command=f"echo 'test {i}'",
                        working_directory="/tmp"
                    )
                
                # Get all steps for the job
                steps = await store.get_job_steps(job_id)
                
                assert len(steps) == 3
                for i, step in enumerate(steps):
                    assert step.job_id == job_id
                    assert step.step_name == f"test_step_{i}"
                    assert step.order_index == i + 1
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_update_step_status(self):
        """Test updating step status"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"step_{uuid.uuid4().hex[:8]}"
                
                # Create job and step
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                await store.create_step(
                    step_id=step_id,
                    job_id=job_id,
                    step_name="test_step",
                    step_type="test_tool",
                    order_index=1,
                    command="echo 'test'"
                )
                
                # Update step status to running
                start_time = time.time()
                update_result = await store.update_step_status(
                    step_id=step_id,
                    status=StepStatus.RUNNING,
                    started_at=start_time
                )
                
                assert update_result is True
                
                # Get updated step to verify
                updated_step = await store.get_step(step_id)
                assert updated_step.status == StepStatus.RUNNING
                assert updated_step.started_at == start_time
                
                # Update step status to completed with output
                complete_time = time.time()
                duration = int((complete_time - start_time) * 1000)
                complete_result = await store.update_step_status(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    completed_at=complete_time,
                    duration_ms=duration,
                    output={"result": "success"}
                )
                
                assert complete_result is True
                
                # Get completed step to verify
                completed_step = await store.get_step(step_id)
                assert completed_step.status == StepStatus.COMPLETED
                assert completed_step.completed_at == complete_time
                assert completed_step.duration_ms == duration
                assert completed_step.output == {"result": "success"}
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_cleanup_expired(self):
        """Test cleanup expired data functionality"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                # This test would require waiting for TTL expiration
                # For now, just test that the cleanup method exists and can be called
                cleanup_result = await store.cleanup_expired()
                
                # Should return a dictionary with cleanup counts
                assert isinstance(cleanup_result, dict)
                assert "expired_checkpoints" in cleanup_result
                assert "expired_artifacts" in cleanup_result
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
