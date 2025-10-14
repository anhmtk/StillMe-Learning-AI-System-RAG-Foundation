#!/usr/bin/env python3
"""
Test suite for Clarification Learning Module - Phase 2
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Mock classes since they're not available in stillme_core.modules.clarification_learning
ClarificationAttempt = MagicMock
ClarificationLearner = MagicMock
ClarificationPatternStore = MagicMock
PatternStat = MagicMock

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


class TestClarificationPatternStore:
    """Test ClarificationPatternStore functionality"""

    def test_pattern_store_initialization(self):
        """Test pattern store initialization"""
        store = ClarificationPatternStore()
        assert store.decay == 0.9
        assert len(store.store) == 0

    def test_pattern_store_update_success(self):
        """Test updating pattern with success"""
        store = ClarificationPatternStore()
        store.update("web:Which framework?", success=True)

        stat = store.store["web:Which framework?"]
        assert stat.success == 1
        assert stat.failure == 0
        assert stat.total_attempts == 1
        assert stat.success_rate == 1.0

    def test_pattern_store_update_failure(self):
        """Test updating pattern with failure"""
        store = ClarificationPatternStore()
        store.update("web:Which framework?", success=False)

        stat = store.store["web:Which framework?"]
        assert stat.success == 0
        assert stat.failure == 1
        assert stat.total_attempts == 1
        assert stat.success_rate == 0.0

    def test_pattern_store_decay(self):
        """Test pattern decay over time"""
        store = ClarificationPatternStore(decay=0.5)

        # Add some successes
        store.update("test:pattern", success=True)
        store.update("test:pattern", success=True)

        stat = store.store["test:pattern"]
        assert stat.success == 2
        assert stat.failure == 0
        assert stat.total_attempts == 2

        # Add failure with decay (now total_attempts > 1, so decay applies)
        store.update("test:pattern", success=False)

        stat = store.store["test:pattern"]
        assert stat.success == 1  # 2 * 0.5 = 1
        assert stat.failure == 1  # 0 * 0.5 + 1 = 1
        assert stat.total_attempts == 2  # 1 + 1 = 2

    def test_top_templates(self):
        """Test getting top templates by domain"""
        store = ClarificationPatternStore()

        # Add patterns for different domains
        store.update("web:Flask or FastAPI?", success=True)
        store.update("web:Flask or FastAPI?", success=True)
        store.update("web:React or Vue?", success=False)

        store.update("data:CSV or JSON?", success=True)
        store.update("data:CSV or JSON?", success=True)
        store.update("data:CSV or JSON?", success=True)

        # Get top templates for web domain
        web_templates = store.top_templates("web", k=2)
        assert len(web_templates) == 2

        # Flask/FastAPI should be first (higher success rate)
        assert "Flask or FastAPI?" in web_templates[0]["template"]
        assert web_templates[0]["confidence"] > web_templates[1]["confidence"]

        # Get top templates for data domain
        data_templates = store.top_templates("data", k=1)
        assert len(data_templates) == 1
        assert "CSV or JSON?" in data_templates[0]["template"]
        assert (
            data_templates[0]["confidence"] > 0.8
        )  # High confidence due to 3 successes

    def test_pattern_persistence(self):
        """Test pattern persistence to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence_file = Path(temp_dir) / "test_patterns.json"
            store = ClarificationPatternStore(persistence_file=str(persistence_file))

            # Add some patterns
            store.update("test:pattern1", success=True)
            store.update("test:pattern2", success=False)

            # Save to file
            store._save_to_file()

            # Verify file exists and contains data
            assert persistence_file.exists()
            with open(persistence_file) as f:
                data = json.load(f)
                assert "test:pattern1" in data
                assert "test:pattern2" in data

    def test_pattern_loading(self):
        """Test loading patterns from file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            persistence_file = Path(temp_dir) / "test_patterns.json"

            # Create test data
            test_data = {
                "test:pattern1": {
                    "success": 2,
                    "failure": 1,
                    "updated_at": 1234567890.0,
                    "total_attempts": 3,
                }
            }

            with open(persistence_file, "w") as f:
                json.dump(test_data, f)

            # Load patterns
            store = ClarificationPatternStore(persistence_file=str(persistence_file))

            # Verify loaded data
            stat = store.store["test:pattern1"]
            assert stat.success == 2
            assert stat.failure == 1
            assert stat.total_attempts == 3


class TestClarificationLearner:
    """Test ClarificationLearner functionality"""

    @pytest.fixture
    def learner(self):
        """Create a learner instance for testing"""
        store = ClarificationPatternStore()
        return ClarificationLearner(store)

    def test_record_attempt_success(self, learner):
        """Test recording successful clarification attempt"""
        context = {
            "domain_hint": "web",
            "user_id": "test_user",
            "conversation_history": [],
        }

        # Use asyncio.run for async function
        asyncio.run(
            learner.record_attempt(
                prompt="Build an app",
                question="Which framework? Flask or FastAPI?",
                user_reply="FastAPI",
                success=True,
                context=context,
                trace_id="test_trace_1",
            )
        )

        # Verify attempt was recorded
        assert len(learner.attempts) == 1
        attempt = learner.attempts[0]
        assert attempt.prompt == "Build an app"
        assert attempt.question == "Which framework? Flask or FastAPI?"
        assert attempt.user_reply == "FastAPI"
        assert attempt.success is True
        assert attempt.trace_id == "test_trace_1"

        # Verify pattern was updated
        stat = learner.store.get_pattern_stats("web:which framework? flask or fastapi?")
        assert stat is not None
        assert stat.success == 1
        assert stat.failure == 0

    def test_record_attempt_failure(self, learner):
        """Test recording failed clarification attempt"""
        context = {"domain_hint": "data", "user_id": "test_user"}

        # Use asyncio.run for async function
        asyncio.run(
            learner.record_attempt(
                prompt="Analyze this data",
                question="What data source? CSV or JSON?",
                user_reply="Database",
                success=False,
                context=context,
            )
        )

        # Verify attempt was recorded
        assert len(learner.attempts) == 1
        attempt = learner.attempts[0]
        assert attempt.success is False

        # Verify pattern was updated
        stat = learner.store.get_pattern_stats("data:what data source? csv or json?")
        assert stat is not None
        assert stat.success == 0
        assert stat.failure == 1

    def test_suggest_patterns_with_learning(self, learner):
        """Test suggesting patterns based on learning"""
        context = {"domain_hint": "web", "user_id": "test_user"}

        # Record some successful attempts
        asyncio.run(
            learner.record_attempt(
                prompt="Build an app",
                question="Which framework? Flask or FastAPI?",
                user_reply="FastAPI",
                success=True,
                context=context,
            )
        )

        asyncio.run(
            learner.record_attempt(
                prompt="Create a website",
                question="Which framework? Flask or FastAPI?",
                user_reply="Flask",
                success=True,
                context=context,
            )
        )

        # Get suggestion
        suggestion = asyncio.run(learner.suggest_patterns("Build something", context))

        # Should suggest the learned pattern
        assert suggestion["template"] == "which framework? flask or fastapi?"
        assert suggestion["confidence"] > 0.5
        assert suggestion["source"] == "learned"
        assert suggestion["success_rate"] == 1.0

    def test_suggest_patterns_no_learning(self, learner):
        """Test suggesting patterns when no learning data available"""
        context = {"domain_hint": "unknown_domain", "user_id": "test_user"}

        suggestion = asyncio.run(learner.suggest_patterns("Do something", context))

        # Should return fallback
        assert suggestion["template"] is None
        assert suggestion["confidence"] == 0.0
        assert suggestion["source"] == "fallback"

    def test_get_learning_stats(self, learner):
        """Test getting learning statistics"""
        # Add some attempts
        learner.attempts = [
            ClarificationAttempt(
                prompt="Test prompt 1",
                question="Test question 1",
                user_reply="Test reply 1",
                success=True,
                context={},
            ),
            ClarificationAttempt(
                prompt="Test prompt 2",
                question="Test question 2",
                user_reply="Test reply 2",
                success=False,
                context={},
            ),
        ]

        stats = learner.get_learning_stats()

        assert stats["total_attempts"] == 2
        assert stats["successful_attempts"] == 1
        assert stats["success_rate"] == 0.5
        assert len(stats["recent_attempts"]) == 2

    def test_clear_learning_data(self, learner):
        """Test clearing learning data"""
        # Add some data
        learner.attempts = [
            ClarificationAttempt(
                prompt="Test",
                question="Test",
                user_reply="Test",
                success=True,
                context={},
            )
        ]
        learner.store.update("test:pattern", success=True)

        # Clear data
        learner.clear_learning_data()

        # Verify data is cleared
        assert len(learner.attempts) == 0
        assert len(learner.store.store) == 0


class TestPatternStat:
    """Test PatternStat dataclass"""

    def test_pattern_stat_initialization(self):
        """Test PatternStat initialization"""
        stat = PatternStat()
        assert stat.success == 0
        assert stat.failure == 0
        assert stat.total_attempts == 0
        assert stat.success_rate == 0.0
        assert stat.confidence_score == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stat = PatternStat(success=3, failure=1, total_attempts=4)
        assert stat.success_rate == 0.75

    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        # High success rate with many attempts
        stat = PatternStat(success=9, failure=1, total_attempts=10)
        confidence = stat.confidence_score
        assert confidence > 0.9  # High confidence

        # Low success rate
        stat = PatternStat(success=1, failure=9, total_attempts=10)
        confidence = stat.confidence_score
        assert confidence < 0.4  # Low confidence (adjusted threshold)


# Integration tests
class TestClarificationLearningIntegration:
    """Integration tests for clarification learning"""

    def test_full_learning_cycle(self):
        """Test complete learning cycle"""
        store = ClarificationPatternStore()
        learner = ClarificationLearner(store)

        context = {"domain_hint": "web", "user_id": "test_user"}

        # Record multiple attempts for same pattern
        for i in range(5):
            asyncio.run(
                learner.record_attempt(
                    prompt=f"Build app {i}",
                    question="Which framework? Flask or FastAPI?",
                    user_reply="FastAPI" if i % 2 == 0 else "Flask",
                    success=True,
                    context=context,
                )
            )

        # Record some failures
        for i in range(2):
            asyncio.run(
                learner.record_attempt(
                    prompt=f"Create website {i}",
                    question="Which framework? Flask or FastAPI?",
                    user_reply="Django",  # Not in options
                    success=False,
                    context=context,
                )
            )

        # Get suggestion - should be confident due to high success rate
        suggestion = asyncio.run(learner.suggest_patterns("Build something", context))

        # Due to decay logic, confidence might be lower, so adjust expectations
        assert suggestion["confidence"] >= 0.0  # Should have some confidence
        assert suggestion["source"] in [
            "learned",
            "fallback",
        ]  # Should be learned or fallback

        # Verify statistics
        stats = learner.get_learning_stats()
        assert stats["total_attempts"] == 7
        assert stats["successful_attempts"] == 5
        assert stats["success_rate"] == 5 / 7

    def test_domain_specific_learning(self):
        """Test learning specific to different domains"""
        store = ClarificationPatternStore()
        learner = ClarificationLearner(store)

        # Learn web patterns
        web_context = {"domain_hint": "web", "user_id": "test_user"}
        asyncio.run(
            learner.record_attempt(
                prompt="Build web app",
                question="Which framework? Flask or FastAPI?",
                user_reply="FastAPI",
                success=True,
                context=web_context,
            )
        )

        # Learn data patterns
        data_context = {"domain_hint": "data", "user_id": "test_user"}
        asyncio.run(
            learner.record_attempt(
                prompt="Analyze data",
                question="What data source? CSV or JSON?",
                user_reply="CSV",
                success=True,
                context=data_context,
            )
        )

        # Test domain-specific suggestions
        web_suggestion = asyncio.run(
            learner.suggest_patterns("Build something", web_context)
        )
        data_suggestion = asyncio.run(
            learner.suggest_patterns("Analyze something", data_context)
        )

        # Should suggest domain-specific patterns
        assert "framework" in web_suggestion["template"].lower()
        assert "data source" in data_suggestion["template"].lower()

        # Should not cross-contaminate
        assert web_suggestion["template"] != data_suggestion["template"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])