"""
SEAL-GRADE Test Configuration
Configuration for comprehensive testing
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

# Test markers - moved to top-level conftest.py


def pytest_configure(config):
    """Configure pytest for SEAL-GRADE tests"""
    config.addinivalue_line("markers", "seal: SEAL-GRADE test")
    config.addinivalue_line("markers", "property: Property-based test")
    config.addinivalue_line("markers", "fuzz: Fuzzing test")
    config.addinivalue_line("markers", "chaos: Chaos engineering test")
    config.addinivalue_line("markers", "mutation: Mutation testing")
    config.addinivalue_line("markers", "load: Load/Performance test")
    config.addinivalue_line("markers", "security: Red/Blue security test")
    config.addinivalue_line("markers", "recovery: Recovery test")
    config.addinivalue_line("markers", "slow: Slow test")


def pytest_collection_modifyitems(config, items):
    """Modify test items for SEAL-GRADE tests"""
    for item in items:
        # Add markers based on test file
        if "test_properties" in item.nodeid:
            item.add_marker(pytest.mark.property)
        elif "test_fuzz" in item.nodeid:
            item.add_marker(pytest.mark.fuzz)
        elif "test_chaos" in item.nodeid:
            item.add_marker(pytest.mark.chaos)
        elif "test_mutation" in item.nodeid:
            item.add_marker(pytest.mark.mutation)
        elif "test_load" in item.nodeid:
            item.add_marker(pytest.mark.load)
        elif "test_red_blue" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_recovery" in item.nodeid:
            item.add_marker(pytest.mark.recovery)

        # Add SEAL-GRADE marker to all tests
        item.add_marker(pytest.mark.seal)

        # Add slow marker to certain tests
        if any(
            keyword in item.nodeid
            for keyword in ["load", "performance", "chaos", "mutation"]
        ):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db():
    """Create temporary database for tests"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    yield temp_db.name
    # Cleanup
    Path(temp_db.name).unlink(missing_ok=True)


@pytest.fixture
def test_timeout():
    """Test timeout configuration"""
    return 30.0


@pytest.fixture
def performance_threshold():
    """Performance threshold configuration"""
    return {
        "response_time": 0.1,  # seconds
        "throughput": 100,  # ops/s
        "memory_usage": 100,  # MB
        "cpu_usage": 50,  # %
    }


@pytest.fixture
def security_threshold():
    """Security threshold configuration"""
    return {
        "injection_blocked": 100,  # %
        "xss_blocked": 100,  # %
        "csrf_blocked": 100,  # %
        "auth_bypass_blocked": 100,  # %
    }


@pytest.fixture
def recovery_threshold():
    """Recovery threshold configuration"""
    return {
        "recovery_time": 1.0,  # seconds
        "recovery_success": 80,  # %
        "data_consistency": 100,  # %
    }
