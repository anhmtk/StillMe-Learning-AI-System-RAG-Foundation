#!/usr/bin/env python3
"""
Simple test to verify pytest works without async
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import asyncio

# Add agentdev to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "agentdev"))

from state_store import StateStore

class TestSimple:
    """Simple synchronous tests"""
    
    def test_simple_import(self):
        """Test that we can import StateStore"""
        assert StateStore is not None
    
    def test_simple_math(self):
        """Test basic math"""
        assert 1 + 1 == 2
    
    def test_create_job_sync(self):
        """Test job creation using asyncio.run()"""
        
        async def _test_job_creation():
            # Create temporary database
            temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
            try:
                os.close(temp_fd)  # Close the file descriptor
                
                store = StateStore(db_path=temp_path)
                await store.initialize()
                
                # Create job
                job = await store.create_job(
                    job_id="test_job_sync",
                    job_type="test",
                    config={"test": True},
                    variables={"env": "test"},
                    created_by="test_user"
                )
                
                assert job is not None
                assert job.job_id == "test_job_sync"
                assert job.status.value == "pending"
                
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # Run the async function
        asyncio.run(_test_job_creation())
