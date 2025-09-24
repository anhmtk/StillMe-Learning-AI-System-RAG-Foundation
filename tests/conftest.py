"""
Pytest configuration for AgentDev SEAL-grade tests.
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_store():
    """Create a temporary SQLite database for testing."""
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "agentdev"))
    
    from state_store import StateStore
    
    # Create temporary database
    temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
    try:
        os.close(temp_fd)  # Close the file descriptor
        
        store = StateStore(db_path=temp_path)
        await store.initialize()
        
        yield store
    finally:
        # Cleanup
        try:
            await store.close()
        except:
            pass
        if os.path.exists(temp_path):
            os.unlink(temp_path)
