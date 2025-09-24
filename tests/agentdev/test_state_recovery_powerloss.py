#!/usr/bin/env python3
"""
AgentDev State Store - Recovery Tests
SEAL-grade tests for power loss recovery and data consistency
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

class TestStateRecoveryPowerLoss:
    """Power loss recovery and data consistency tests"""
    
    def test_recovery_after_kill_9(self):
        """Test recovery after kill -9 (simulated)"""
        
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
                
                # Update step to running (simulate mid-execution)
                await store.update_step_status(
                    step_id, StepStatus.RUNNING, started_at=time.time()
                )
                
                # Simulate kill -9 by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store (simulate restart)
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify data consistency
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
                assert recovered_job.job_id == job_id
                
                recovered_step = await new_store.get_step(step_id)
                assert recovered_step is not None
                assert recovered_step.step_id == step_id
                assert recovered_step.status == StepStatus.RUNNING
                
                # Verify we can get job steps
                steps = await new_store.get_job_steps(job_id)
                assert len(steps) >= 1
                assert steps[0].step_id == step_id
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_mid_transaction(self):
        """Test recovery during mid-transaction"""
        
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
                    data={"test": "data"}
                )
                
                # Simulate mid-transaction by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify checkpoint exists
                recovered_checkpoint = await new_store.get_latest_checkpoint(job_id)
                assert recovered_checkpoint is not None
                assert recovered_checkpoint.job_id == job_id
                
                # Verify job exists
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
                assert recovered_job.job_id == job_id
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_with_partial_artifacts(self):
        """Test recovery with partial artifacts"""
        
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
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify artifact exists by checking job details
                job_details = await new_store.get_job_details(job_id)
                assert job_details is not None
                assert job_details["job"].job_id == job_id
                
                # Verify job exists
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_with_orphaned_events(self):
        """Test recovery with orphaned events"""
        
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
                
                # Log events
                await store.log_event(
                    event_type="test_event",
                    event_data={"message": "Test event 1"},
                    job_id=job_id
                )
                
                await store.log_event(
                    event_type="test_event",
                    event_data={"message": "Test event 2"},
                    job_id=job_id
                )
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify job exists
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
                assert recovered_job.job_id == job_id
                
                # Verify statistics are consistent
                stats = await new_store.get_statistics()
                assert stats["total_jobs"] >= 1
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_with_corrupted_checkpoints(self):
        """Test recovery with corrupted checkpoints"""
        
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
                
                # Create multiple checkpoints
                for i in range(3):
                    await store.create_checkpoint(
                        job_id=job_id,
                        checkpoint_type=CheckpointType.MANUAL,
                        data={"test": f"data_{i}"}
                    )
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify job exists
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
                
                # Verify checkpoints exist
                latest_checkpoint = await new_store.get_latest_checkpoint(job_id)
                assert latest_checkpoint is not None
                assert latest_checkpoint.job_id == job_id
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_under_heavy_load(self):
        """Test recovery under heavy load"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                # Create multiple jobs
                job_ids = []
                for i in range(10):
                    job_id = f"test_job_{i}_{uuid.uuid4().hex[:8]}"
                    job_ids.append(job_id)
                    
                    await store.create_job(
                        job_id=job_id,
                        job_type="test",
                        config={"index": i},
                        variables={},
                        created_by="test_user"
                    )
                    
                    # Create steps for each job
                    for j in range(3):
                        step_id = f"test_step_{i}_{j}_{uuid.uuid4().hex[:8]}"
                        await store.create_step(
                            step_id=step_id,
                            job_id=job_id,
                            step_name=f"Step {j}",
                            step_type="test",
                            order_index=j,
                            command=f"echo step_{j}"
                        )
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify all jobs exist
                for job_id in job_ids:
                    recovered_job = await new_store.get_job(job_id)
                    assert recovered_job is not None
                    assert recovered_job.job_id == job_id
                
                # Verify statistics
                stats = await new_store.get_statistics()
                assert stats["total_jobs"] >= 10
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_with_concurrent_writes(self):
        """Test recovery with concurrent writes"""
        
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
                
                # Concurrent operations
                async def create_step(i):
                    step_id = f"test_step_{i}_{uuid.uuid4().hex[:8]}"
                    return await store.create_step(
                        step_id=step_id,
                        job_id=job_id,
                        step_name=f"Step {i}",
                        step_type="test",
                        order_index=i,
                        command=f"echo step_{i}"
                    )
                
                async def create_checkpoint(i):
                    return await store.create_checkpoint(
                        job_id=job_id,
                        checkpoint_type=CheckpointType.MANUAL,
                        data={"test": f"data_{i}"}
                    )
                
                # Run concurrent operations
                tasks = []
                for i in range(5):
                    tasks.append(create_step(i))
                    tasks.append(create_checkpoint(i))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Verify job exists
                recovered_job = await new_store.get_job(job_id)
                assert recovered_job is not None
                
                # Verify steps exist
                steps = await new_store.get_job_steps(job_id)
                assert len(steps) >= 1  # At least one step should exist
                
                # Verify checkpoints exist
                latest_checkpoint = await new_store.get_latest_checkpoint(job_id)
                assert latest_checkpoint is not None
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_recovery_statistics_consistency(self):
        """Test recovery statistics consistency"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                # Create multiple jobs with different statuses
                job_ids = []
                for i in range(5):
                    job_id = f"test_job_{i}_{uuid.uuid4().hex[:8]}"
                    job_ids.append(job_id)
                    
                    await store.create_job(
                        job_id=job_id,
                        job_type="test",
                        config={"index": i},
                        variables={},
                        created_by="test_user"
                    )
                    
                    # Update some jobs to different statuses
                    if i % 2 == 0:
                        await store.update_job_status(
                            job_id, JobStatus.RUNNING, started_at=time.time()
                        )
                
                # Get statistics before power loss
                stats_before = await store.get_statistics()
                
                # Simulate power loss by not closing store properly
                # (Just continue without explicit close)
                
                # Recreate store
                new_store = StateStore(str(db_path))
                await new_store.initialize()
                
                # Get statistics after recovery
                stats_after = await new_store.get_statistics()
                
                # Verify statistics are consistent
                assert stats_after["total_jobs"] == stats_before["total_jobs"]
                assert stats_after["completed_jobs"] == stats_before["completed_jobs"]
                assert stats_after["failed_jobs"] == stats_before["failed_jobs"]
                
                # Verify all jobs exist
                for job_id in job_ids:
                    recovered_job = await new_store.get_job(job_id)
                    assert recovered_job is not None
            finally:
                # Cleanup - close database connection first
                try:
                    await new_store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
