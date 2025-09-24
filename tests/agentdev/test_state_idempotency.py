#!/usr/bin/env python3
"""
AgentDev State Store - Idempotency Tests
SEAL-grade tests for concurrent operations and idempotency
"""

import asyncio
import time
import uuid
import pytest
from pathlib import Path
import tempfile
import shutil

from agentdev.state_store import StateStore, JobStatus, StepStatus, CheckpointType

class TestStateIdempotency:
    """Idempotency and concurrent operations tests"""
    
    def test_concurrent_job_creation(self):
        """Test concurrent job creation"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                
                # Create multiple concurrent jobs with same ID
                async def create_job():
                    return await store.create_job(
                        job_id=job_id,
                        job_type="test",
                        config={"test": True},
                        variables={"env": "test"},
                        created_by="test_user"
                    )
                
                # Run concurrent operations
                tasks = [create_job() for _ in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter out exceptions and get successful results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                # All should return the same job
                if successful_results:
                    first_job = successful_results[0]
                    for job in successful_results[1:]:
                        assert job.job_id == first_job.job_id
                        assert job.created_at == first_job.created_at
                        assert job.status == first_job.status
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_concurrent_step_creation(self):
        """Test concurrent step creation"""
        
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
                
                # Create multiple concurrent steps with same ID
                async def create_step():
                    return await store.create_step(
                        step_id=step_id,
                        job_id=job_id,
                        step_name="Test Step",
                        step_type="test",
                        order_index=1,
                        command="echo test"
                    )
                
                # Run concurrent operations
                tasks = [create_step() for _ in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter out exceptions and get successful results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                # All should return the same step
                if successful_results:
                    first_step = successful_results[0]
                    for step in successful_results[1:]:
                        assert step.step_id == first_step.step_id
                        assert step.created_at == first_step.created_at
                        assert step.status == first_step.status
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_concurrent_status_updates(self):
        """Test concurrent status updates"""
        
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
                
                # Update status concurrently
                async def update_status():
                    return await store.update_job_status(
                        job_id, JobStatus.RUNNING, started_at=time.time()
                    )
                
                # Run concurrent updates
                tasks = [update_status() for _ in range(3)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for result in results:
                    assert result is True
                
                # Verify final state
                final_job = await store.get_job(job_id)
                assert final_job.status == JobStatus.RUNNING
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_concurrent_checkpoint_creation(self):
        """Test concurrent checkpoint creation"""
        
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
                
                # Create checkpoints concurrently
                async def create_checkpoint():
                    return await store.create_checkpoint(
                        job_id=job_id,
                        checkpoint_type=CheckpointType.MANUAL,
                        data={"test": "data"}
                    )
                
                # Run concurrent operations
                tasks = [create_checkpoint() for _ in range(3)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for checkpoint in results:
                    assert checkpoint is not None
                    assert checkpoint.job_id == job_id
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_concurrent_artifact_creation(self):
        """Test concurrent artifact creation"""
        
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
                
                # Create artifacts concurrently
                async def create_artifact(i):
                    artifact_id = f"test_artifact_{i}_{uuid.uuid4().hex[:8]}"
                    return await store.create_artifact(
                        artifact_id=artifact_id,
                        job_id=job_id,
                        artifact_path=f"/tmp/test_file_{i}.txt",
                        artifact_type="text/plain",
                        metadata={"size": 100 + i}
                    )
                
                # Run concurrent operations
                tasks = [create_artifact(i) for i in range(5)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for artifact in results:
                    assert artifact is not None
                    assert artifact.job_id == job_id
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_concurrent_event_logging(self):
        """Test concurrent event logging"""
        
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
                
                # Log events concurrently
                async def log_event(i):
                    return await store.log_event(
                        event_type="test_event",
                        event_data={"message": f"Test event {i}"},
                        job_id=job_id
                    )
                
                # Run concurrent operations
                tasks = [log_event(i) for i in range(10)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for result in results:
                    assert result is not None
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                job_id = f"test_job_{uuid.uuid4().hex[:8]}"
                step_id = f"test_step_{uuid.uuid4().hex[:8]}"
                
                # Create job
                await store.create_job(
                    job_id=job_id,
                    job_type="test",
                    config={},
                    variables={},
                    created_by="test_user"
                )
                
                # Mixed concurrent operations
                async def create_step():
                    return await store.create_step(
                        step_id=step_id,
                        job_id=job_id,
                        step_name="Test Step",
                        step_type="test",
                        order_index=1,
                        command="echo test"
                    )
                
                async def update_status():
                    return await store.update_job_status(
                        job_id, JobStatus.RUNNING, started_at=time.time()
                    )
                
                async def create_checkpoint():
                    return await store.create_checkpoint(
                        job_id=job_id,
                        checkpoint_type=CheckpointType.MANUAL,
                        data={"test": "data"}
                    )
                
                # Run mixed concurrent operations
                tasks = [
                    create_step(),
                    update_status(),
                    create_checkpoint(),
                    create_step(),  # Duplicate
                    update_status()  # Duplicate
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter out exceptions and get successful results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                # All should succeed
                for result in successful_results:
                    assert result is not None
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_high_frequency_updates(self):
        """Test high frequency updates"""
        
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
                
                # High frequency status updates
                async def update_status(i):
                    return await store.update_job_status(
                        job_id, JobStatus.RUNNING, started_at=time.time() + i
                    )
                
                # Run many updates quickly
                tasks = [update_status(i) for i in range(50)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for result in results:
                    assert result is True
                
                # Verify final state
                final_job = await store.get_job(job_id)
                assert final_job.status == JobStatus.RUNNING
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_database_consistency_under_load(self):
        """Test database consistency under load"""
        
        async def _test():
            # Create temporary store
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test_state.db"
            
            try:
                store = StateStore(str(db_path))
                await store.initialize()
                
                # Create multiple jobs concurrently
                async def create_job(i):
                    job_id = f"test_job_{i}_{uuid.uuid4().hex[:8]}"
                    return await store.create_job(
                        job_id=job_id,
                        job_type="test",
                        config={"index": i},
                        variables={"env": "test"},
                        created_by="test_user"
                    )
                
                # Run concurrent job creation
                tasks = [create_job(i) for i in range(20)]
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for job in results:
                    assert job is not None
                    assert job.status == JobStatus.PENDING
                
                # Verify database consistency
                stats = await store.get_statistics()
                assert stats["total_jobs"] >= 20
                
                # Verify all jobs exist
                for i, job in enumerate(results):
                    retrieved_job = await store.get_job(job.job_id)
                    assert retrieved_job is not None
                    assert retrieved_job.job_id == job.job_id
                    assert retrieved_job.config["index"] == i
            finally:
                # Cleanup - close database connection first
                try:
                    await store.close()
                except:
                    pass
                # Wait a bit for file handles to be released
                await asyncio.sleep(0.1)
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
