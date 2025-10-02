from typing import Any
from unittest.mock import Mock

"""
SEAL-GRADE SYSTEM TESTS - Test Configuration
Cấu hình kiểm thử cho hệ thống SEAL-GRADE

This module provides shared fixtures and configuration for all test modules.
Module này cung cấp fixtures và cấu hình chung cho tất cả test modules.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

# Import StillMe modules
try:
    from stillme_core.framework import StillMeFramework
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
    from stillme_core.modules.automated_scheduler import AutomatedScheduler
    from stillme_core.modules.communication_style_manager import (
        CommunicationStyleManager,
    )
    from stillme_core.modules.content_integrity_filter import ContentIntegrityFilter
    from stillme_core.modules.conversational_core_v1 import ConversationalCore
    from stillme_core.modules.daily_learning_manager import DailyLearningManager
    from stillme_core.modules.emotionsense_v1 import EmotionSenseV1
    from stillme_core.modules.ethical_core_system_v1 import EthicalCoreSystem
    from stillme_core.modules.framework_metrics import FrameworkMetrics
    from stillme_core.modules.input_sketcher import InputSketcher
    from stillme_core.modules.layered_memory_v1 import LayeredMemoryV1
    from stillme_core.modules.market_intel import MarketIntelligence
    from stillme_core.modules.persona_morph import PersonaMorph
    from stillme_core.modules.prediction_engine import PredictionEngine
    from stillme_core.modules.secure_memory_manager import SecureMemoryManager
    from stillme_core.modules.self_improvement_manager import SelfImprovementManager
    from stillme_core.modules.telemetry import Telemetry
    from stillme_core.modules.token_optimizer_v1 import TokenOptimizer
except ImportError as e:
    print(f"Warning: Could not import StillMe modules: {e}")
    # Create mock modules for testing
    StillMeFramework = Mock
    LayeredMemoryV1 = Mock
    SecureMemoryManager = Mock
    EthicalCoreSystem = Mock
    ContentIntegrityFilter = Mock
    ConversationalCore = Mock
    PersonaMorph = Mock
    EmotionSenseV1 = Mock
    TokenOptimizer = Mock
    SelfImprovementManager = Mock
    DailyLearningManager = Mock
    AutomatedScheduler = Mock
    UnifiedAPIManager = Mock
    PredictionEngine = Mock
    MarketIntelligence = Mock
    Telemetry = Mock
    FrameworkMetrics = Mock
    CommunicationStyleManager = Mock
    InputSketcher = Mock


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from YAML file."""
    config_path = Path("config/test_defaults.yaml")
    if config_path.exists():
        with open(config_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # Default configuration if file doesn't exist
        return {
            "performance": {
                "gateway_p95_slo": 300,
                "gateway_p95_threshold": 500,
                "error_rate_threshold": 0.01,
                "recovery_time_threshold": 5,
                "ethics_violation_threshold": 0.001
            },
            "coverage": {
                "lines_minimum": 90,
                "branches_minimum": 80,
                "mutation_minimum": 70
            },
            "load_testing": {
                "concurrent_users": 500,
                "requests_per_hour": 10000,
                "soak_duration_hours": 2
            },
            "security": {
                "injection_test_cases": 50,
                "jailbreak_test_cases": 30,
                "pii_redaction_cases": 25
            },
            "chaos": {
                "network_delay_ms": 1000,
                "network_drop_percent": 10,
                "api_timeout_seconds": 30
            }
        }


@pytest.fixture(scope="session")
def test_datasets():
    """Load test datasets."""
    datasets = {}

    # Load ambiguous prompts
    ambiguous_path = Path("datasets/ambiguous_prompts.json")
    if ambiguous_path.exists():
        with open(ambiguous_path, encoding='utf-8') as f:
            datasets['ambiguous_prompts'] = json.load(f)

    # Load red team prompts
    redteam_path = Path("datasets/redteam_prompts.json")
    if redteam_path.exists():
        with open(redteam_path, encoding='utf-8') as f:
            datasets['redteam_prompts'] = json.load(f)

    # Load PII samples
    pii_path = Path("datasets/pii_samples.json")
    if pii_path.exists():
        with open(pii_path, encoding='utf-8') as f:
            datasets['pii_samples'] = json.load(f)

    return datasets


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_framework():
    """Mock StillMe framework for testing."""
    framework = Mock(spec=StillMeFramework)
    framework.initialize = Mock(return_value=True)
    framework.process_request = Mock(return_value={"response": "Test response"})
    framework.get_health_status = Mock(return_value={"status": "healthy"})
    return framework


@pytest.fixture(scope="function")
def mock_memory_system():
    """Mock memory system for testing."""
    memory = Mock(spec=LayeredMemoryV1)
    memory.store = Mock(return_value=True)
    memory.retrieve = Mock(return_value={"data": "test data"})
    memory.search = Mock(return_value=[{"id": "1", "content": "test"}])
    memory.clear = Mock(return_value=True)
    return memory


@pytest.fixture(scope="function")
def mock_secure_memory():
    """Mock secure memory manager for testing."""
    secure_memory = Mock(spec=SecureMemoryManager)
    secure_memory.encrypt = Mock(return_value="encrypted_data")
    secure_memory.decrypt = Mock(return_value="decrypted_data")
    secure_memory.rotate_key = Mock(return_value=True)
    secure_memory.backup = Mock(return_value=True)
    return secure_memory


@pytest.fixture(scope="function")
def mock_ethics_system():
    """Mock ethics system for testing."""
    ethics = Mock(spec=EthicalCoreSystem)
    ethics.validate = Mock(return_value={"is_safe": True, "violations": []})
    ethics.check_content = Mock(return_value={"is_safe": True, "score": 0.1})
    ethics.get_violations = Mock(return_value=[])
    return ethics


@pytest.fixture(scope="function")
def mock_content_filter():
    """Mock content integrity filter for testing."""
    filter_mock = Mock(spec=ContentIntegrityFilter)
    filter_mock.filter = Mock(return_value={"is_safe": True, "filtered_content": "test"})
    filter_mock.detect_harmful = Mock(return_value=False)
    filter_mock.sanitize = Mock(return_value="sanitized_content")
    return filter_mock


@pytest.fixture(scope="function")
def mock_conversational_core():
    """Mock conversational core for testing."""
    conv_core = Mock(spec=ConversationalCore)
    conv_core.process_message = Mock(return_value={"response": "Hello!"})
    conv_core.get_context = Mock(return_value={"context": "test context"})
    conv_core.update_context = Mock(return_value=True)
    return conv_core


@pytest.fixture(scope="function")
def mock_api_manager():
    """Mock API provider manager for testing."""
    api_manager = Mock(spec=UnifiedAPIManager)
    api_manager.send_request = Mock(return_value={"response": "API response"})
    api_manager.get_health = Mock(return_value={"status": "healthy"})
    api_manager.fallback = Mock(return_value={"response": "Fallback response"})
    return api_manager


@pytest.fixture(scope="function")
def mock_emotion_sense():
    """Mock emotion sense for testing."""
    emotion = Mock(spec=EmotionSenseV1)
    emotion.detect_emotion = Mock(return_value={"emotion": "happy", "confidence": 0.8})
    emotion.analyze_sentiment = Mock(return_value={"sentiment": "positive", "score": 0.7})
    return emotion


@pytest.fixture(scope="function")
def mock_token_optimizer():
    """Mock token optimizer for testing."""
    optimizer = Mock(spec=TokenOptimizer)
    optimizer.optimize = Mock(return_value={"optimized_text": "test", "tokens_saved": 10})
    optimizer.estimate_tokens = Mock(return_value=100)
    optimizer.cache_similar = Mock(return_value=True)
    return optimizer


@pytest.fixture(scope="function")
def mock_self_improvement():
    """Mock self improvement manager for testing."""
    improvement = Mock(spec=SelfImprovementManager)
    improvement.analyze_performance = Mock(return_value={"score": 0.8, "suggestions": []})
    improvement.improve = Mock(return_value={"improved": True, "changes": []})
    improvement.get_metrics = Mock(return_value={"accuracy": 0.9, "speed": 0.8})
    return improvement


@pytest.fixture(scope="function")
def mock_scheduler():
    """Mock automated scheduler for testing."""
    scheduler = Mock(spec=AutomatedScheduler)
    scheduler.schedule_job = Mock(return_value=True)
    scheduler.run_job = Mock(return_value={"status": "completed"})
    scheduler.get_status = Mock(return_value={"active_jobs": 0})
    return scheduler


@pytest.fixture(scope="function")
def mock_telemetry():
    """Mock telemetry system for testing."""
    telemetry = Mock(spec=Telemetry)
    telemetry.track_event = Mock(return_value=True)
    telemetry.get_metrics = Mock(return_value={"events": 100, "errors": 0})
    telemetry.export_data = Mock(return_value={"data": "exported"})
    return telemetry


@pytest.fixture(scope="function")
def mock_metrics():
    """Mock framework metrics for testing."""
    metrics = Mock(spec=FrameworkMetrics)
    metrics.record_metric = Mock(return_value=True)
    metrics.get_summary = Mock(return_value={"total_requests": 1000, "avg_response_time": 100})
    metrics.export_report = Mock(return_value={"report": "generated"})
    return metrics


@pytest.fixture(scope="function")
def mock_communication_style():
    """Mock communication style manager for testing."""
    style_manager = Mock(spec=CommunicationStyleManager)
    style_manager.get_style = Mock(return_value={"style": "friendly", "tone": "casual"})
    style_manager.adapt_style = Mock(return_value="adapted message")
    style_manager.learn_style = Mock(return_value=True)
    return style_manager


@pytest.fixture(scope="function")
def mock_input_sketcher():
    """Mock input sketcher for testing."""
    sketcher = Mock(spec=InputSketcher)
    sketcher.sketch = Mock(return_value={"sketch": "test sketch", "confidence": 0.8})
    sketcher.enhance = Mock(return_value="enhanced input")
    sketcher.validate = Mock(return_value={"is_valid": True, "errors": []})
    return sketcher


@pytest.fixture(scope="function")
def mock_prediction_engine():
    """Mock prediction engine for testing."""
    prediction = Mock(spec=PredictionEngine)
    prediction.predict = Mock(return_value={"prediction": "test", "confidence": 0.8})
    prediction.train = Mock(return_value={"accuracy": 0.9})
    prediction.evaluate = Mock(return_value={"score": 0.85})
    return prediction


@pytest.fixture(scope="function")
def mock_market_intel():
    """Mock market intelligence for testing."""
    market = Mock(spec=MarketIntelligence)
    market.analyze_trends = Mock(return_value={"trends": ["AI", "ML"], "confidence": 0.8})
    market.get_insights = Mock(return_value={"insights": "test insights"})
    market.update_data = Mock(return_value=True)
    return market


@pytest.fixture(scope="function")
def mock_daily_learning():
    """Mock daily learning manager for testing."""
    learning = Mock(spec=DailyLearningManager)
    learning.run_session = Mock(return_value={"completed": True, "score": 0.8})
    learning.get_progress = Mock(return_value={"sessions": 10, "avg_score": 0.75})
    learning.add_case = Mock(return_value=True)
    return learning


@pytest.fixture(scope="function")
def mock_persona_morph():
    """Mock persona morph for testing."""
    persona = Mock(spec=PersonaMorph)
    persona.morph = Mock(return_value={"new_persona": "friendly", "confidence": 0.8})
    persona.get_current = Mock(return_value={"persona": "default"})
    persona.reset = Mock(return_value=True)
    return persona


# Pytest markers configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "ethics: Ethics tests")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "chaos: Chaos engineering tests")
    config.addinivalue_line("markers", "soak: Soak tests")
    config.addinivalue_line("markers", "ux: User experience tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network access")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_unit_" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration_" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_security_" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_ethics_" in item.nodeid:
            item.add_marker(pytest.mark.ethics)
        elif "test_load_" in item.nodeid:
            item.add_marker(pytest.mark.load)
        elif "test_chaos_" in item.nodeid:
            item.add_marker(pytest.mark.chaos)
        elif "test_soak_" in item.nodeid:
            item.add_marker(pytest.mark.soak)
        elif "test_ux_" in item.nodeid:
            item.add_marker(pytest.mark.ux)

        # Add slow marker for tests that take more than 5 seconds
        if "slow" in item.name or "load" in item.name or "soak" in item.name:
            item.add_marker(pytest.mark.slow)


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def load_json_fixture(file_path: str) -> dict[str, Any]:
        """Load JSON fixture file."""
        with open(file_path, encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json_fixture(data: dict[str, Any], file_path: str) -> None:
        """Save data as JSON fixture."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create_mock_response(status_code: int = 200, data: dict[str, Any] = None) -> Mock:
        """Create mock HTTP response."""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data or {}
        response.text = json.dumps(data or {})
        return response

    @staticmethod
    def assert_response_time(response_time: float, threshold: float) -> None:
        """Assert response time is within threshold."""
        assert response_time <= threshold, f"Response time {response_time}ms exceeds threshold {threshold}ms"

    @staticmethod
    def assert_error_rate(errors: int, total: int, threshold: float) -> None:
        """Assert error rate is within threshold."""
        error_rate = errors / total if total > 0 else 0
        assert error_rate <= threshold, f"Error rate {error_rate:.2%} exceeds threshold {threshold:.2%}"


@pytest.fixture(scope="session")
def test_utils():
    """Provide test utilities."""
    return TestUtils


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    # Set test environment variables
    os.environ["STILLME_TEST_MODE"] = "true"
    os.environ["STILLME_LOG_LEVEL"] = "DEBUG"
    os.environ["STILLME_DISABLE_TELEMETRY"] = "true"

    # Create test directories
    test_dirs = ["logs", "reports", "artifacts", "temp"]
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)

    yield

    # Cleanup
    os.environ.pop("STILLME_TEST_MODE", None)
    os.environ.pop("STILLME_LOG_LEVEL", None)
    os.environ.pop("STILLME_DISABLE_TELEMETRY", None)
