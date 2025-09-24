#!/usr/bin/env python3
"""
State Management Basic Tests - SEAL-grade Unit Tests (Fixed Version)
Validates core state operations: job creation, step tracking, checkpoints.
Uses asyncio.run() instead of pytest-asyncio for compatibility.
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

class TestStateFixed:
    """Basic state store functionality tests (Fixed)"""
    
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
    
    def test_add_job_step(self):
        """Test adding steps to a job"""
        
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
                
                # Add step
                step = await store.add_job_step(
                    job_id=job_id,
                    step_name="test_step",
                    tool_name="test_tool",
                    parameters={"param1": "value1"},
                    expected_output_schema={"type": "object"}
                )
                
                assert step.job_id == job_id
                assert step.step_name == "test_step"
                assert step.tool_name == "test_tool"
                assert step.status == StepStatus.PENDING
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_complete_job_step(self):
        """Test completing a job step"""
        
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
                
                # Add step
                step = await store.add_job_step(
                    job_id=job_id,
                    step_name="test_step",
                    tool_name="test_tool",
                    parameters={"param1": "value1"},
                    expected_output_schema={"type": "object"}
                )
                
                # Complete step
                completed_step = await store.complete_job_step(
                    job_id=job_id,
                    step_id=step.step_id,
                    result={"success": True},
                    execution_log="Step completed successfully"
                )
                
                assert completed_step.status == StepStatus.COMPLETED
                assert completed_step.result == {"success": True}
                assert "Step completed successfully" in completed_step.execution_log
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_create_checkpoint(self):
        """Test creating checkpoints"""
        
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
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_store_artifact(self):
        """Test storing artifacts"""
        
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
                
                # Store artifact
                artifact = await store.store_artifact(
                    job_id=job_id,
                    artifact_name="test_file.txt",
                    file_path="/tmp/test_file.txt",
                    content_type="text/plain",
                    metadata={"size": 100}
                )
                
                assert artifact.job_id == job_id
                assert artifact.artifact_name == "test_file.txt"
                assert artifact.file_path == "/tmp/test_file.txt"
                assert artifact.content_type == "text/plain"
                assert artifact.metadata == {"size": 100}
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_list_jobs(self):
        """Test listing jobs"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                # Create multiple jobs
                job_ids = []
                for i in range(3):
                    job_id = f"test_job_{i}_{uuid.uuid4().hex[:8]}"
                    job_ids.append(job_id)
                    await store.create_job(
                        job_id=job_id,
                        job_type="test",
                        config={"test": True, "index": i},
                        variables={"env": "test"},
                        created_by="test_user"
                    )
                
                # List jobs
                jobs = await store.list_jobs(limit=10)
                
                # Should have at least 3 jobs
                assert len(jobs) >= 3
                
                # Check that our jobs are in the list
                found_job_ids = [job.job_id for job in jobs]
                for job_id in job_ids:
                    assert job_id in found_job_ids
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_get_job_details(self):
        """Test getting job details with steps and checkpoints"""
        
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
                
                # Add step
                step = await store.add_job_step(
                    job_id=job_id,
                    step_name="test_step",
                    tool_name="test_tool",
                    parameters={"param1": "value1"},
                    expected_output_schema={"type": "object"}
                )
                
                # Create checkpoint
                checkpoint = await store.create_checkpoint(
                    job_id=job_id,
                    checkpoint_type=CheckpointType.MANUAL,
                    state_snapshot={"current_step": 1},
                    description="Test checkpoint"
                )
                
                # Get job details
                job_details = await store.get_job_details(job_id)
                
                assert job_details["job"].job_id == job_id
                assert len(job_details["steps"]) == 1
                assert job_details["steps"][0].step_id == step.step_id
                assert len(job_details["checkpoints"]) == 1
                assert job_details["checkpoints"][0].checkpoint_id == checkpoint.checkpoint_id
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_resume_from_checkpoint(self):
        """Test resuming from a specific checkpoint"""
        
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
                
                # Create checkpoint
                checkpoint = await store.create_checkpoint(
                    job_id=job_id,
                    checkpoint_type=CheckpointType.MANUAL,
                    state_snapshot={"current_step": 1, "data": "test"},
                    description="Test checkpoint"
                )
                
                # Resume from checkpoint
                resume_data = await store.resume_from_checkpoint(checkpoint.checkpoint_id)
                
                assert resume_data["job"].job_id == job_id
                assert resume_data["checkpoint"].checkpoint_id == checkpoint.checkpoint_id
                assert resume_data["state_snapshot"] == {"current_step": 1, "data": "test"}
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
    
    def test_ttl_cleanup(self):
        """Test TTL cleanup functionality"""
        
        async def _test():
            store, temp_path = await self._create_temp_store()
            try:
                # This test would require waiting for TTL expiration
                # For now, just test that the cleanup method exists and can be called
                cleanup_count = await store.cleanup_expired_data()
                
                # Should return a number (could be 0 if nothing to cleanup)
                assert isinstance(cleanup_count, int)
                assert cleanup_count >= 0
                
            finally:
                self._cleanup_temp_store(temp_path)
        
        asyncio.run(_test())
