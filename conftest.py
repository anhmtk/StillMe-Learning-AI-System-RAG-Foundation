"""Pytest configuration and fixtures for StillMe Framework"""

import os
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def test_config() -> dict[str, Any]:
    """Test configuration for testing"""
    return {
        "id": "test_config",
        "name": "Test Configuration",
        "settings": {
            "debug": True,
            "verbose": False
        }
    }

@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration for testing"""
    return {
        "id": "sample_config",
        "name": "Sample Configuration",
        "settings": {
            "debug": True,
            "timeout": 30,
            "retries": 3
        }
    }

@pytest.fixture
def test_datasets():
    """Test datasets for testing"""
    return {
        "small": [1, 2, 3],
        "medium": list(range(10)),
        "large": list(range(100))
    }

@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Sample data for testing"""
    return {
        "text": "This is a test message",
        "metadata": {
            "source": "test",
            "timestamp": "2025-09-27T16:00:00Z"
        }
    }

@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def mock_ethics_system():
    """Mock ethics system for testing"""
    class MockEthicsSystem:
        def __init__(self):
            self.violations = []
            self.checks_passed = 0
            self.checks_failed = 0

        def check_ethics(self, content: str) -> bool:
            """Mock ethics check"""
            if "harmful" in content.lower():
                self.checks_failed += 1
                return False
            self.checks_passed += 1
            return True

        def get_violations(self):
            return self.violations

    return MockEthicsSystem()

@pytest.fixture
def mock_content_filter():
    """Mock content filter for testing"""
    class MockContentFilter:
        def __init__(self):
            self.filtered_content = []
            self.blocked_content = []

        def filter_content(self, content: str) -> str:
            """Mock content filtering"""
            if "spam" in content.lower():
                self.blocked_content.append(content)
                return "[BLOCKED]"
            self.filtered_content.append(content)
            return content

        def get_filtered_count(self):
            return len(self.filtered_content)

        def get_blocked_count(self):
            return len(self.blocked_content)

    return MockContentFilter()

@pytest.fixture
def mock_secure_memory():
    """Mock secure memory for testing"""
    class MockSecureMemory:
        def __init__(self):
            self.memory = {}
            self.encrypted_data = {}

        def store(self, key: str, value: str, encrypt: bool = False) -> bool:
            """Mock secure storage"""
            if encrypt:
                self.encrypted_data[key] = f"[ENCRYPTED]{value}"
            else:
                self.memory[key] = value
            return True

        def retrieve(self, key: str) -> str:
            """Mock secure retrieval"""
            if key in self.encrypted_data:
                return self.encrypted_data[key]
            return self.memory.get(key, "")

        def clear(self):
            """Mock memory clear"""
            self.memory.clear()
            self.encrypted_data.clear()

    return MockSecureMemory()

@pytest.fixture
def mock_conversational_core():
    """Mock conversational core for testing"""
    class MockConversationalCore:
        def __init__(self):
            self.conversations = []
            self.responses = []

        def process_message(self, message: str, context: dict[str, Any] = None) -> str:
            """Mock message processing"""
            self.conversations.append(message)
            response = f"Mock response to: {message}"
            self.responses.append(response)
            return response

        def get_conversation_history(self):
            return self.conversations

        def get_response_history(self):
            return self.responses

        def clear_history(self):
            self.conversations.clear()
            self.responses.clear()

    return MockConversationalCore()

@pytest.fixture
def mock_api_manager():
    """Mock API manager for testing"""
    class MockAPIManager:
        def __init__(self):
            self.requests = []
            self.responses = []
            self.errors = []

        def make_request(self, endpoint: str, data: dict[str, Any] = None) -> dict[str, Any]:
            """Mock API request"""
            self.requests.append({"endpoint": endpoint, "data": data})
            response = {"status": "success", "data": f"Mock response for {endpoint}"}
            self.responses.append(response)
            return response

        def get_requests_count(self):
            return len(self.requests)

        def get_responses_count(self):
            return len(self.responses)

        def get_errors_count(self):
            return len(self.errors)

        def clear_history(self):
            self.requests.clear()
            self.responses.clear()
            self.errors.clear()

    return MockAPIManager()

@pytest.fixture
def test_utils():
    """Test utilities for testing"""
    class TestUtils:
        @staticmethod
        def create_test_data(size: int = 10) -> list[dict[str, Any]]:
            """Create test data"""
            return [{"id": i, "value": f"test_{i}"} for i in range(size)]

        @staticmethod
        def assert_response_format(response: dict[str, Any]) -> bool:
            """Assert response format"""
            required_keys = ["status", "data"]
            return all(key in response for key in required_keys)

        @staticmethod
        def generate_test_string(length: int = 100) -> str:
            """Generate test string"""
            return "x" * length

    return TestUtils()

@pytest.fixture
def mock_framework():
    """Mock framework for testing"""
    class MockFramework:
        def __init__(self):
            self.initialized = False
            self.components = {}
            self.requests_processed = 0

        def initialize(self) -> bool:
            """Mock framework initialization"""
            self.initialized = True
            return True

        def process_request(self, request: str) -> str:
            """Mock request processing"""
            self.requests_processed += 1
            return f"Mock response to: {request}"

        def get_component(self, name: str):
            """Mock component retrieval"""
            return self.components.get(name)

        def add_component(self, name: str, component):
            """Mock component addition"""
            self.components[name] = component

        def is_initialized(self) -> bool:
            """Check if framework is initialized"""
            return self.initialized

    return MockFramework()

@pytest.fixture
def mock_memory_system():
    """Mock memory system for testing"""
    class MockMemorySystem:
        def __init__(self):
            self.memories = {}
            self.retrievals = 0
            self.storages = 0

        def store(self, key: str, value: Any) -> bool:
            """Mock memory storage"""
            self.memories[key] = value
            self.storages += 1
            return True

        def retrieve(self, key: str) -> Any:
            """Mock memory retrieval"""
            self.retrievals += 1
            return self.memories.get(key)

        def clear(self):
            """Mock memory clear"""
            self.memories.clear()
            self.retrievals = 0
            self.storages = 0

        def get_stats(self):
            """Get memory statistics"""
            return {
                "total_memories": len(self.memories),
                "retrievals": self.retrievals,
                "storages": self.storages
            }

    return MockMemorySystem()

@pytest.fixture
def mock_emotion_sense():
    """Mock emotion sense for testing"""
    class MockEmotionSense:
        def __init__(self):
            self.emotions_detected = []
            self.confidence_scores = []

        def detect_emotion(self, text: str) -> dict[str, Any]:
            """Mock emotion detection"""
            emotion = "neutral"
            confidence = 0.5

            if "happy" in text.lower():
                emotion = "happy"
                confidence = 0.8
            elif "sad" in text.lower():
                emotion = "sad"
                confidence = 0.7
            elif "angry" in text.lower():
                emotion = "angry"
                confidence = 0.9

            result = {
                "emotion": emotion,
                "confidence": confidence,
                "text": text
            }

            self.emotions_detected.append(emotion)
            self.confidence_scores.append(confidence)

            return result

        def get_emotion_history(self):
            return self.emotions_detected

        def get_average_confidence(self):
            if not self.confidence_scores:
                return 0.0
            return sum(self.confidence_scores) / len(self.confidence_scores)

        def clear_history(self):
            self.emotions_detected.clear()
            self.confidence_scores.clear()

    return MockEmotionSense()

@pytest.fixture
def mock_token_optimizer():
    """Mock token optimizer for testing"""
    class MockTokenOptimizer:
        def __init__(self):
            self.optimizations = []
            self.token_counts = []

        def optimize_tokens(self, text: str) -> dict[str, Any]:
            """Mock token optimization"""
            original_tokens = len(text.split())
            optimized_tokens = max(1, original_tokens - 2)  # Mock reduction

            result = {
                "original_text": text,
                "optimized_text": text[:len(text)//2] + "...",  # Mock truncation
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "reduction_percentage": (original_tokens - optimized_tokens) / original_tokens * 100
            }

            self.optimizations.append(result)
            self.token_counts.append(optimized_tokens)

            return result

        def get_optimization_history(self):
            return self.optimizations

        def get_average_token_count(self):
            if not self.token_counts:
                return 0
            return sum(self.token_counts) / len(self.token_counts)

        def clear_history(self):
            self.optimizations.clear()
            self.token_counts.clear()

    return MockTokenOptimizer()

@pytest.fixture
def mock_self_improvement():
    """Mock self improvement system for testing"""
    class MockSelfImprovement:
        def __init__(self):
            self.improvements = []
            self.performance_scores = []

        def analyze_performance(self, data: dict[str, Any]) -> dict[str, Any]:
            """Mock performance analysis"""
            score = 0.7  # Mock score
            improvements = ["Optimize memory usage", "Improve response time"]

            result = {
                "performance_score": score,
                "improvements": improvements,
                "analysis_date": "2025-09-27T16:00:00Z",
                "data_analyzed": data
            }

            self.improvements.append(improvements)
            self.performance_scores.append(score)

            return result

        def implement_improvement(self, improvement: str) -> bool:
            """Mock improvement implementation"""
            return True

        def get_improvement_history(self):
            return self.improvements

        def get_average_performance_score(self):
            if not self.performance_scores:
                return 0.0
            return sum(self.performance_scores) / len(self.performance_scores)

        def clear_history(self):
            self.improvements.clear()
            self.performance_scores.clear()

    return MockSelfImprovement()

@pytest.fixture
def mock_scheduler():
    """Mock scheduler for testing"""
    class MockScheduler:
        def __init__(self):
            self.tasks = []
            self.completed_tasks = []
            self.failed_tasks = []

        def schedule_task(self, task_name: str, delay: int = 0) -> str:
            """Mock task scheduling"""
            task_id = f"task_{len(self.tasks) + 1}"
            task = {
                "id": task_id,
                "name": task_name,
                "delay": delay,
                "status": "scheduled",
                "created_at": "2025-09-27T16:00:00Z"
            }
            self.tasks.append(task)
            return task_id

        def execute_task(self, task_id: str) -> bool:
            """Mock task execution"""
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    self.completed_tasks.append(task)
                    return True
            return False

        def cancel_task(self, task_id: str) -> bool:
            """Mock task cancellation"""
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = "cancelled"
                    return True
            return False

        def get_task_status(self, task_id: str) -> str:
            """Get task status"""
            for task in self.tasks:
                if task["id"] == task_id:
                    return task["status"]
            return "not_found"

        def get_all_tasks(self):
            return self.tasks

        def get_completed_tasks(self):
            return self.completed_tasks

        def get_failed_tasks(self):
            return self.failed_tasks

        def clear_tasks(self):
            self.tasks.clear()
            self.completed_tasks.clear()
            self.failed_tasks.clear()

    return MockScheduler()

@pytest.fixture
def mock_telemetry():
    """Mock telemetry system for testing"""
    class MockTelemetry:
        def __init__(self):
            self.metrics = []
            self.events = []
            self.alerts = []

        def record_metric(self, name: str, value: float, tags: dict[str, str] = None) -> bool:
            """Mock metric recording"""
            metric = {
                "name": name,
                "value": value,
                "tags": tags or {},
                "timestamp": "2025-09-27T16:00:00Z"
            }
            self.metrics.append(metric)
            return True

        def record_event(self, event_name: str, data: dict[str, Any] = None) -> bool:
            """Mock event recording"""
            event = {
                "name": event_name,
                "data": data or {},
                "timestamp": "2025-09-27T16:00:00Z"
            }
            self.events.append(event)
            return True

        def create_alert(self, alert_type: str, message: str, severity: str = "medium") -> bool:
            """Mock alert creation"""
            alert = {
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": "2025-09-27T16:00:00Z"
            }
            self.alerts.append(alert)
            return True

        def get_metrics(self, name: str = None):
            """Get metrics"""
            if name:
                return [m for m in self.metrics if m["name"] == name]
            return self.metrics

        def get_events(self, event_name: str = None):
            """Get events"""
            if event_name:
                return [e for e in self.events if e["name"] == event_name]
            return self.events

        def get_alerts(self, severity: str = None):
            """Get alerts"""
            if severity:
                return [a for a in self.alerts if a["severity"] == severity]
            return self.alerts

        def clear_data(self):
            """Clear all telemetry data"""
            self.metrics.clear()
            self.events.clear()
            self.alerts.clear()

    return MockTelemetry()

@pytest.fixture
def mock_metrics():
    """Mock metrics system for testing"""
    class MockMetrics:
        def __init__(self):
            self.counters = {}
            self.gauges = {}
            self.timers = {}
            self.histograms = {}

        def increment(self, metric_name: str, value: int = 1, tags: dict[str, str] = None) -> None:
            """Mock counter increment"""
            if metric_name not in self.counters:
                self.counters[metric_name] = 0
            self.counters[metric_name] += value

        def gauge(self, metric_name: str, value: float, tags: dict[str, str] = None) -> None:
            """Mock gauge recording"""
            self.gauges[metric_name] = value

        def timer(self, metric_name: str, value: float, tags: dict[str, str] = None) -> None:
            """Mock timer recording"""
            if metric_name not in self.timers:
                self.timers[metric_name] = []
            self.timers[metric_name].append(value)

        def histogram(self, metric_name: str, value: float, tags: dict[str, str] = None) -> None:
            """Mock histogram recording"""
            if metric_name not in self.histograms:
                self.histograms[metric_name] = []
            self.histograms[metric_name].append(value)

        def get_counter(self, metric_name: str) -> int:
            """Get counter value"""
            return self.counters.get(metric_name, 0)

        def get_gauge(self, metric_name: str) -> float:
            """Get gauge value"""
            return self.gauges.get(metric_name, 0.0)

        def get_timer_values(self, metric_name: str) -> list[float]:
            """Get timer values"""
            return self.timers.get(metric_name, [])

        def get_histogram_values(self, metric_name: str) -> list[float]:
            """Get histogram values"""
            return self.histograms.get(metric_name, [])

        def reset(self):
            """Reset all metrics"""
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
            self.histograms.clear()

    return MockMetrics()

@pytest.fixture
def mock_communication_style():
    """Mock communication style for testing"""
    class MockCommunicationStyle:
        def __init__(self):
            self.style = "default"
            self.tone = "neutral"
            self.formality = "medium"
            self.styles_applied = []

        def set_style(self, style: str) -> bool:
            """Set communication style"""
            valid_styles = ["formal", "casual", "technical", "friendly", "professional", "default"]
            if style in valid_styles:
                self.style = style
                self.styles_applied.append(style)
                return True
            return False

        def set_tone(self, tone: str) -> bool:
            """Set communication tone"""
            valid_tones = ["positive", "neutral", "empathetic", "assertive", "diplomatic"]
            if tone in valid_tones:
                self.tone = tone
                return True
            return False

        def set_formality(self, level: str) -> bool:
            """Set formality level"""
            valid_levels = ["low", "medium", "high", "very_high"]
            if level in valid_levels:
                self.formality = level
                return True
            return False

        def apply_style(self, text: str) -> str:
            """Apply communication style to text"""
            if not text:
                return ""

            # Simple style application
            styled_text = text

            if self.style == "formal":
                styled_text = f"[FORMAL] {styled_text}"
            elif self.style == "casual":
                styled_text = f"[CASUAL] {styled_text}"
            elif self.style == "technical":
                styled_text = f"[TECHNICAL] {styled_text}"
            elif self.style == "friendly":
                styled_text = f"[FRIENDLY] {styled_text}"
            elif self.style == "professional":
                styled_text = f"[PROFESSIONAL] {styled_text}"

            return styled_text

        def get_current_style(self) -> dict[str, str]:
            """Get current style settings"""
            return {
                "style": self.style,
                "tone": self.tone,
                "formality": self.formality
            }

        def get_style_history(self) -> list[str]:
            """Get history of applied styles"""
            return self.styles_applied.copy()

        def reset_style(self):
            """Reset to default style"""
            self.style = "default"
            self.tone = "neutral"
            self.formality = "medium"
            self.styles_applied.clear()

    return MockCommunicationStyle()

@pytest.fixture
def mock_input_sketcher():
    """Mock input sketcher for testing"""
    class MockInputSketcher:
        def __init__(self):
            self.sketches = []
            self.analysis_history = []
            self.patterns = {}

        def sketch_input(self, input_data: Any) -> dict[str, Any]:
            """Create a sketch/summary of input data"""
            if input_data is None:
                return {"type": "none", "size": 0, "content": ""}

            sketch = {
                "type": type(input_data).__name__,
                "size": len(str(input_data)),
                "content": str(input_data)[:100] + "..." if len(str(input_data)) > 100 else str(input_data),
                "timestamp": "2025-09-27T16:00:00Z"
            }

            self.sketches.append(sketch)
            return sketch

        def analyze_structure(self, input_data: Any) -> dict[str, Any]:
            """Analyze the structure of input data"""
            analysis = {
                "data_type": type(input_data).__name__,
                "is_iterable": hasattr(input_data, '__iter__') and not isinstance(input_data, (str, bytes)),
                "is_dict_like": hasattr(input_data, 'keys'),
                "is_numeric": isinstance(input_data, (int, float)),
                "is_string": isinstance(input_data, str),
                "complexity": "simple"
            }

            # Determine complexity
            if isinstance(input_data, dict):
                analysis["complexity"] = "medium" if len(input_data) < 10 else "high"
                analysis["keys_count"] = len(input_data)
            elif isinstance(input_data, (list, tuple)):
                analysis["complexity"] = "medium" if len(input_data) < 50 else "high"
                analysis["items_count"] = len(input_data)
            elif isinstance(input_data, str):
                analysis["complexity"] = "medium" if len(input_data) < 1000 else "high"
                analysis["char_count"] = len(input_data)

            self.analysis_history.append(analysis)
            return analysis

        def find_patterns(self, input_data: Any) -> list[dict[str, Any]]:
            """Find patterns in input data"""
            patterns = []

            if isinstance(input_data, str):
                # Simple pattern detection for strings
                if "@" in input_data and "." in input_data:
                    patterns.append({"type": "email", "confidence": 0.8})
                if input_data.startswith("http"):
                    patterns.append({"type": "url", "confidence": 0.9})
                if input_data.isdigit():
                    patterns.append({"type": "numeric", "confidence": 1.0})
                if any(char.isdigit() for char in input_data) and any(char.isalpha() for char in input_data):
                    patterns.append({"type": "mixed_alphanumeric", "confidence": 0.7})

            elif isinstance(input_data, (list, tuple)):
                # Pattern detection for sequences
                if all(isinstance(item, (int, float)) for item in input_data):
                    patterns.append({"type": "numeric_sequence", "confidence": 0.9})
                if all(isinstance(item, str) for item in input_data):
                    patterns.append({"type": "string_sequence", "confidence": 0.9})
                if all(isinstance(item, dict) for item in input_data):
                    patterns.append({"type": "object_sequence", "confidence": 0.9})

            elif isinstance(input_data, dict):
                # Pattern detection for dictionaries
                if all(isinstance(v, str) for v in input_data.values()):
                    patterns.append({"type": "string_dict", "confidence": 0.8})
                if all(isinstance(v, (int, float)) for v in input_data.values()):
                    patterns.append({"type": "numeric_dict", "confidence": 0.8})

            # Store patterns for this input type
            input_type = type(input_data).__name__
            if input_type not in self.patterns:
                self.patterns[input_type] = []
            self.patterns[input_type].extend(patterns)

            return patterns

        def get_sketch_history(self) -> list[dict[str, Any]]:
            """Get history of all sketches"""
            return self.sketches.copy()

        def get_analysis_history(self) -> list[dict[str, Any]]:
            """Get history of all structural analyses"""
            return self.analysis_history.copy()

        def get_pattern_summary(self) -> dict[str, list[dict[str, Any]]]:
            """Get summary of all detected patterns by type"""
            return self.patterns.copy()

        def clear_history(self):
            """Clear all history and patterns"""
            self.sketches.clear()
            self.analysis_history.clear()
            self.patterns.clear()

    return MockInputSketcher()

@pytest.fixture
def mock_prediction_engine():
    """Mock prediction engine for testing"""
    class MockPredictionEngine:
        def __init__(self):
            self.models = {}
            self.predictions = []
            self.training_data = {}
            self.metrics = {}

        def train_model(self, model_name: str, training_data: list[dict[str, Any]]) -> bool:
            """Train a prediction model"""
            if not training_data:
                return False

            self.training_data[model_name] = training_data
            self.models[model_name] = {
                "trained": True,
                "accuracy": 0.85 + len(training_data) * 0.001,  # Mock accuracy based on data size
                "training_size": len(training_data),
                "created_at": "2025-09-27T16:00:00Z"
            }
            return True

        def predict(self, model_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
            """Make a prediction using the specified model"""
            if model_name not in self.models:
                return {"error": f"Model {model_name} not found"}

            # Simple prediction logic
            confidence = 0.7 + hash(str(input_data)) % 30 / 100  # Mock confidence 0.7-0.99
            prediction_value = hash(str(input_data)) % 100  # Mock prediction 0-99

            prediction = {
                "model": model_name,
                "input": input_data,
                "prediction": prediction_value,
                "confidence": round(confidence, 2),
                "timestamp": "2025-09-27T16:00:00Z"
            }

            self.predictions.append(prediction)
            return prediction

        def evaluate_model(self, model_name: str, test_data: list[dict[str, Any]]) -> dict[str, Any]:
            """Evaluate model performance"""
            if model_name not in self.models:
                return {"error": f"Model {model_name} not found"}

            # Mock evaluation metrics
            evaluation = {
                "model": model_name,
                "test_size": len(test_data),
                "accuracy": self.models[model_name]["accuracy"],
                "precision": self.models[model_name]["accuracy"] * 0.95,
                "recall": self.models[model_name]["accuracy"] * 0.92,
                "f1_score": self.models[model_name]["accuracy"] * 0.93,
                "evaluated_at": "2025-09-27T16:00:00Z"
            }

            self.metrics[model_name] = evaluation
            return evaluation

        def get_model_info(self, model_name: str) -> dict[str, Any]:
            """Get information about a specific model"""
            if model_name not in self.models:
                return {"error": f"Model {model_name} not found"}

            return self.models[model_name].copy()

        def get_all_models(self) -> dict[str, dict[str, Any]]:
            """Get information about all models"""
            return self.models.copy()

        def get_prediction_history(self, model_name: str = None) -> list[dict[str, Any]]:
            """Get prediction history"""
            if model_name:
                return [p for p in self.predictions if p["model"] == model_name]
            return self.predictions.copy()

        def get_model_metrics(self, model_name: str = None) -> dict[str, Any]:
            """Get model performance metrics"""
            if model_name:
                return self.metrics.get(model_name, {})
            return self.metrics.copy()

        def delete_model(self, model_name: str) -> bool:
            """Delete a model"""
            if model_name in self.models:
                del self.models[model_name]
                if model_name in self.training_data:
                    del self.training_data[model_name]
                if model_name in self.metrics:
                    del self.metrics[model_name]
                # Remove predictions for this model
                self.predictions = [p for p in self.predictions if p["model"] != model_name]
                return True
            return False

        def clear_all_data(self):
            """Clear all models, predictions, and data"""
            self.models.clear()
            self.predictions.clear()
            self.training_data.clear()
            self.metrics.clear()

    return MockPredictionEngine()

@pytest.fixture
def mock_market_intel():
    """Mock market intelligence for testing"""
    class MockMarketIntel:
        def __init__(self):
            self.data_sources = []
            self.insights = []
            self.trends = {}
            self.competitors = {}
            self.last_update = None

        def add_data_source(self, source_name: str, source_url: str, api_key: str = None) -> bool:
            """Add a new data source"""
            source = {
                "name": source_name,
                "url": source_url,
                "api_key": api_key,
                "active": True,
                "added_at": "2025-09-27T16:00:00Z"
            }
            self.data_sources.append(source)
            return True

        def collect_market_data(self, keywords: list[str] = None) -> dict[str, Any]:
            """Collect market data from sources"""
            # Mock data collection
            market_data = {
                "keywords": keywords or ["ai", "technology", "market"],
                "trends": {
                    "ai": {"growth": 15.3, "sentiment": "positive"},
                    "technology": {"growth": 8.7, "sentiment": "positive"},
                    "market": {"growth": 3.2, "sentiment": "neutral"}
                },
                "competitors": ["CompetitorA", "CompetitorB", "CompetitorC"],
                "market_size": 125000000,  # Mock market size in USD
                "collected_at": "2025-09-27T16:00:00Z"
            }

            self.last_update = market_data["collected_at"]
            return market_data

        def analyze_trends(self, timeframe: str = "30d") -> dict[str, Any]:
            """Analyze market trends"""
            # Mock trend analysis
            trends = {
                "timeframe": timeframe,
                "top_trends": [
                    {"keyword": "artificial intelligence", "growth": 25.6, "volume": 1500000},
                    {"keyword": "machine learning", "growth": 18.2, "volume": 980000},
                    {"keyword": "data science", "growth": 12.4, "volume": 750000}
                ],
                "declining_trends": [
                    {"keyword": "old_tech", "growth": -5.2, "volume": 200000}
                ],
                "sentiment": {
                    "positive": 65.4,
                    "neutral": 25.8,
                    "negative": 8.8
                },
                "analyzed_at": "2025-09-27T16:00:00Z"
            }

            self.trends[timeframe] = trends
            return trends

        def generate_insights(self, category: str = "general") -> list[dict[str, Any]]:
            """Generate market insights"""
            # Mock insights generation
            insights = [
                {
                    "category": category,
                    "insight": f"Market shows strong growth in {category} sector",
                    "confidence": 0.85,
                    "impact": "high",
                    "recommendation": f"Consider investing more in {category} related initiatives"
                },
                {
                    "category": category,
                    "insight": f"Emerging opportunities in {category} automation",
                    "confidence": 0.72,
                    "impact": "medium",
                    "recommendation": f"Monitor {category} automation trends closely"
                }
            ]

            self.insights.extend(insights)
            return insights

        def track_competitors(self, competitor_names: list[str]) -> dict[str, Any]:
            """Track competitor information"""
            competitor_data = {}

            for name in competitor_names:
                competitor_data[name] = {
                    "market_share": hash(name) % 25 + 5,  # Mock market share 5-30%
                    "growth_rate": (hash(name) % 20) - 10,  # Mock growth -10% to +10%
                    "strength": ["technology", "marketing", "customer_service"][hash(name) % 3],
                    "weakness": ["pricing", "innovation", "market_reach"][hash(name) % 3],
                    "last_updated": "2025-09-27T16:00:00Z"
                }

            self.competitors.update(competitor_data)
            return competitor_data

        def get_market_summary(self) -> dict[str, Any]:
            """Get overall market summary"""
            return {
                "total_sources": len(self.data_sources),
                "insights_generated": len(self.insights),
                "trends_analyzed": len(self.trends),
                "competitors_tracked": len(self.competitors),
                "last_update": self.last_update,
                "status": "active" if self.data_sources else "inactive"
            }

        def export_report(self, format: str = "summary") -> dict[str, Any]:
            """Export market intelligence report"""
            if format == "summary":
                return {
                    "summary": self.get_market_summary(),
                    "recent_trends": list(self.trends.values())[-3:] if self.trends else [],
                    "key_insights": self.insights[-5:] if self.insights else [],
                    "top_competitors": dict(list(self.competitors.items())[:5]) if self.competitors else {}
                }
            elif format == "detailed":
                return {
                    "sources": self.data_sources,
                    "trends": self.trends,
                    "insights": self.insights,
                    "competitors": self.competitors,
                    "summary": self.get_market_summary()
                }
            else:
                return {"error": f"Unsupported format: {format}"}

        def clear_data(self):
            """Clear all collected data"""
            self.data_sources.clear()
            self.insights.clear()
            self.trends.clear()
            self.competitors.clear()
            self.last_update = None

    return MockMarketIntel()

@pytest.fixture
def mock_daily_learning():
    """Mock daily learning system for testing"""
    class MockDailyLearning:
        def __init__(self):
            self.sessions = []
            self.lessons = []
            self.progress = {}
            self.current_session = None
            self.learning_enabled = True

        def start_session(self, session_name: str = None) -> str:
            """Start a new learning session"""
            session_id = f"session_{len(self.sessions) + 1}_{int(time.time())}"
            session = {
                "id": session_id,
                "name": session_name or f"Session {len(self.sessions) + 1}",
                "started_at": "2025-09-27T16:00:00Z",
                "status": "active",
                "lessons_learned": 0,
                "insights_generated": 0
            }

            self.sessions.append(session)
            self.current_session = session
            return session_id

        def end_session(self, session_id: str = None) -> dict[str, Any]:
            """End a learning session"""
            if session_id:
                session = next((s for s in self.sessions if s["id"] == session_id), None)
            else:
                session = self.current_session

            if not session:
                return {"error": "Session not found"}

            session["status"] = "completed"
            session["ended_at"] = "2025-09-27T16:00:00Z"
            session["duration"] = "30m"  # Mock duration

            if self.current_session and self.current_session["id"] == session["id"]:
                self.current_session = None

            return session

        def learn_from_interaction(self, interaction: dict[str, Any]) -> dict[str, Any]:
            """Learn from a user interaction"""
            if not self.learning_enabled:
                return {"status": "disabled", "learned": False}

            lesson_id = f"lesson_{len(self.lessons) + 1}"
            lesson = {
                "id": lesson_id,
                "type": "interaction",
                "content": interaction,
                "insights": [
                    f"User prefers {interaction.get('style', 'unknown')} communication",
                    f"Common topic: {interaction.get('topic', 'general')}"
                ],
                "confidence": 0.75,
                "learned_at": "2025-09-27T16:00:00Z"
            }

            self.lessons.append(lesson)

            if self.current_session:
                self.current_session["lessons_learned"] += 1

            return {"status": "learned", "lesson_id": lesson_id}

        def learn_from_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
            """Learn from user feedback"""
            if not self.learning_enabled:
                return {"status": "disabled", "learned": False}

            lesson_id = f"feedback_{len(self.lessons) + 1}"
            lesson = {
                "id": lesson_id,
                "type": "feedback",
                "content": feedback,
                "insights": [
                    f"Feedback rating: {feedback.get('rating', 'unknown')}",
                    f"Improvement area: {feedback.get('area', 'general')}"
                ],
                "confidence": 0.85,
                "learned_at": "2025-09-27T16:00:00Z"
            }

            self.lessons.append(lesson)

            if self.current_session:
                self.current_session["insights_generated"] += 1

            return {"status": "learned", "lesson_id": lesson_id}

        def get_daily_insights(self, date: str = None) -> list[dict[str, Any]]:
            """Get insights for a specific day"""
            target_date = date or "2025-09-27"

            # Filter lessons by date (mock filtering)
            daily_lessons = [l for l in self.lessons if target_date in l["learned_at"]]

            insights = []
            for lesson in daily_lessons[-5:]:  # Last 5 lessons
                insights.extend(lesson["insights"])

            return [{"insight": insight, "confidence": 0.8} for insight in insights]

        def get_learning_progress(self) -> dict[str, Any]:
            """Get overall learning progress"""
            total_lessons = len(self.lessons)
            interaction_lessons = len([l for l in self.lessons if l["type"] == "interaction"])
            feedback_lessons = len([l for l in self.lessons if l["type"] == "feedback"])

            return {
                "total_lessons": total_lessons,
                "interaction_lessons": interaction_lessons,
                "feedback_lessons": feedback_lessons,
                "total_sessions": len(self.sessions),
                "active_sessions": len([s for s in self.sessions if s["status"] == "active"]),
                "learning_enabled": self.learning_enabled,
                "avg_confidence": 0.8 if self.lessons else 0.0
            }

        def get_session_history(self) -> list[dict[str, Any]]:
            """Get history of all learning sessions"""
            return self.sessions.copy()

        def toggle_learning(self, enabled: bool) -> bool:
            """Enable or disable learning"""
            self.learning_enabled = enabled
            return self.learning_enabled

        def export_lessons(self, format: str = "summary") -> dict[str, Any]:
            """Export learned lessons"""
            if format == "summary":
                return {
                    "total_lessons": len(self.lessons),
                    "recent_lessons": self.lessons[-10:] if self.lessons else [],
                    "progress": self.get_learning_progress()
                }
            elif format == "detailed":
                return {
                    "sessions": self.sessions,
                    "lessons": self.lessons,
                    "progress": self.get_learning_progress()
                }
            else:
                return {"error": f"Unsupported format: {format}"}

        def clear_learning_data(self):
            """Clear all learning data"""
            self.sessions.clear()
            self.lessons.clear()
            self.progress.clear()
            self.current_session = None

    return MockDailyLearning()

@pytest.fixture
def mock_persona_morph():
    """Mock persona morphing system for testing"""
    class MockPersonaMorph:
        def __init__(self):
            self.personas = {}
            self.current_persona = "default"
            self.morph_history = []
            self.traits = {}
            self.contexts = {}

        def create_persona(self, persona_id: str, traits: dict[str, Any]) -> bool:
            """Create a new persona"""
            if persona_id in self.personas:
                return False

            self.personas[persona_id] = {
                "id": persona_id,
                "traits": traits.copy(),
                "created_at": "2025-09-27T16:00:00Z",
                "usage_count": 0,
                "active": True
            }
            return True

        def morph_to_persona(self, persona_id: str, context: dict[str, Any] = None) -> dict[str, Any]:
            """Morph to a specific persona"""
            if persona_id not in self.personas:
                return {"error": f"Persona {persona_id} not found"}

            previous_persona = self.current_persona
            self.current_persona = persona_id

            # Record morph in history
            morph_record = {
                "from_persona": previous_persona,
                "to_persona": persona_id,
                "context": context or {},
                "timestamp": "2025-09-27T16:00:00Z",
                "success": True
            }
            self.morph_history.append(morph_record)

            # Update usage count
            self.personas[persona_id]["usage_count"] += 1

            return {
                "previous_persona": previous_persona,
                "current_persona": persona_id,
                "traits": self.personas[persona_id]["traits"],
                "morph_successful": True
            }

        def adapt_traits(self, trait_adjustments: dict[str, Any]) -> dict[str, Any]:
            """Adapt current persona traits"""
            if self.current_persona not in self.personas:
                return {"error": "No active persona"}

            current_traits = self.personas[self.current_persona]["traits"]
            adapted_traits = current_traits.copy()
            adapted_traits.update(trait_adjustments)

            # Save adaptation
            adaptation = {
                "persona": self.current_persona,
                "original_traits": current_traits.copy(),
                "adjustments": trait_adjustments,
                "final_traits": adapted_traits,
                "adapted_at": "2025-09-27T16:00:00Z"
            }

            self.personas[self.current_persona]["traits"] = adapted_traits

            return adaptation

        def get_current_persona(self) -> dict[str, Any]:
            """Get current active persona"""
            if self.current_persona not in self.personas:
                return {"error": "No active persona"}

            return self.personas[self.current_persona].copy()

        def get_persona_suggestions(self, context: dict[str, Any]) -> list[dict[str, Any]]:
            """Get persona suggestions based on context"""
            suggestions = []

            # Simple context-based suggestions
            context_type = context.get("type", "general")
            user_mood = context.get("mood", "neutral")

            for persona_id, persona in self.personas.items():
                if not persona["active"]:
                    continue

                # Calculate compatibility score
                compatibility = 0.5  # Base score

                if context_type == "technical" and "analytical" in persona["traits"]:
                    compatibility += 0.3
                elif context_type == "creative" and "creative" in persona["traits"]:
                    compatibility += 0.3
                elif context_type == "support" and "empathetic" in persona["traits"]:
                    compatibility += 0.3

                if user_mood == "stressed" and "calming" in persona["traits"]:
                    compatibility += 0.2
                elif user_mood == "excited" and "enthusiastic" in persona["traits"]:
                    compatibility += 0.2

                suggestions.append({
                    "persona_id": persona_id,
                    "compatibility_score": round(compatibility, 2),
                    "reason": f"Good match for {context_type} context with {user_mood} mood",
                    "traits": persona["traits"]
                })

            # Sort by compatibility score
            suggestions.sort(key=lambda x: x["compatibility_score"], reverse=True)
            return suggestions[:3]  # Top 3 suggestions

        def analyze_morph_patterns(self) -> dict[str, Any]:
            """Analyze morphing patterns"""
            if not self.morph_history:
                return {"error": "No morph history available"}

            # Count morphs per persona
            morph_counts = {}
            context_patterns = {}

            for morph in self.morph_history:
                to_persona = morph["to_persona"]
                morph_counts[to_persona] = morph_counts.get(to_persona, 0) + 1

                # Analyze context patterns
                context_type = morph["context"].get("type", "unknown")
                if context_type not in context_patterns:
                    context_patterns[context_type] = []
                context_patterns[context_type].append(to_persona)

            return {
                "total_morphs": len(self.morph_history),
                "morph_counts": morph_counts,
                "most_used_persona": max(morph_counts, key=morph_counts.get) if morph_counts else None,
                "context_patterns": context_patterns,
                "avg_morphs_per_hour": len(self.morph_history) / 24  # Mock calculation
            }

        def get_all_personas(self) -> dict[str, dict[str, Any]]:
            """Get all available personas"""
            return self.personas.copy()

        def deactivate_persona(self, persona_id: str) -> bool:
            """Deactivate a persona"""
            if persona_id in self.personas:
                self.personas[persona_id]["active"] = False
                return True
            return False

        def activate_persona(self, persona_id: str) -> bool:
            """Activate a persona"""
            if persona_id in self.personas:
                self.personas[persona_id]["active"] = True
                return True
            return False

        def export_persona_data(self, format: str = "summary") -> dict[str, Any]:
            """Export persona data"""
            if format == "summary":
                return {
                    "total_personas": len(self.personas),
                    "active_personas": len([p for p in self.personas.values() if p["active"]]),
                    "current_persona": self.current_persona,
                    "total_morphs": len(self.morph_history),
                    "morph_patterns": self.analyze_morph_patterns()
                }
            elif format == "detailed":
                return {
                    "personas": self.personas,
                    "current_persona": self.current_persona,
                    "morph_history": self.morph_history,
                    "analysis": self.analyze_morph_patterns()
                }
            else:
                return {"error": f"Unsupported format: {format}"}

        def reset_morph_system(self):
            """Reset the entire morphing system"""
            self.personas.clear()
            self.current_persona = "default"
            self.morph_history.clear()
            self.traits.clear()
            self.contexts.clear()

            # Create default persona
            self.create_persona("default", {
                "communication_style": "balanced",
                "formality": "medium",
                "empathy": "moderate",
                "technical_depth": "adaptive"
            })

    return MockPersonaMorph()

@pytest.fixture
def clean_environment():
    """Clean environment for testing"""
    # Store original environment
    original_env = os.environ.copy()

    # Clean up test environment
    test_env_vars = [
        "STILLME_ROUTER_MODE",
        "STILLME_DEBUG",
        "STILLME_LOG_LEVEL"
    ]

    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
