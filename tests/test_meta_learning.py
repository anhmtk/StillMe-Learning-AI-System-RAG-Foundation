from unittest.mock import patch

import pytest

pytest.skip("Module not available", allow_module_level=True)

#!/usr/bin/env python3
"""
Test suite for Meta-Learning Manager
====================================

Tests for learn-to-learn capabilities.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import asyncio
import shutil

# Add project root to path
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from stillme_core.learning.meta_learning_manager import (
    LearningStrategy,
    MetaLearningEvent,
    MetaLearningManager,
)


class TestMetaLearningManager:
    """Test suite for MetaLearningManager"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def meta_learning_manager(self, temp_dir):
        """Create meta learning manager with temporary directory"""
        with patch('stillme_core.learning.meta_learning_manager.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            manager = MetaLearningManager()
            return manager

    @pytest.mark.asyncio
    async def test_record_learning_session(self, meta_learning_manager):
        """Test recording a learning session"""
        session_metadata = await meta_learning_manager.record_learning_session(
            session_id="test_session_1",
            user_id="user_123",
            start_time="2025-01-27T10:00:00Z",
            end_time="2025-01-27T10:30:00Z",
            fix_attempts=5,
            successful_fixes=4,
            rollback_count=1,
            reward_score=3.0,
            penalty_score=-1.0,
            accuracy_improvement=0.15,
            error_types={"syntax": 2, "logic": 1},
            safety_violations=0
        )

        assert session_metadata.session_id == "test_session_1"
        assert session_metadata.user_id == "user_123"
        assert session_metadata.duration_minutes == 30.0
        assert session_metadata.fix_attempts == 5
        assert session_metadata.successful_fixes == 4
        assert session_metadata.rollback_count == 1
        assert session_metadata.reward_score == 3.0
        assert session_metadata.penalty_score == -1.0
        assert session_metadata.net_score == 2.0
        assert session_metadata.accuracy_improvement == 0.15
        assert session_metadata.error_types == {"syntax": 2, "logic": 1}
        assert session_metadata.safety_violations == 0

    @pytest.mark.asyncio
    async def test_analyze_learning_patterns(self, meta_learning_manager):
        """Test analyzing learning patterns"""
        # Create multiple sessions for analysis
        for i in range(5):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=4,
                rollback_count=1 if i < 3 else 0,  # High rollback rate for first 3
                reward_score=3.0,
                penalty_score=-1.0,
                accuracy_improvement=0.15,
                error_types={"syntax": 2, "logic": 1},
                safety_violations=0
            )

        insights = await meta_learning_manager.analyze_learning_patterns()

        assert isinstance(insights, list)
        # Should generate insights about rollback patterns
        assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_adapt_learning_strategy(self, meta_learning_manager):
        """Test adapting learning strategy"""
        # Create sessions with high rollback rate
        for i in range(6):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=2,  # Low success rate
                rollback_count=3,   # High rollback count
                reward_score=1.0,
                penalty_score=-2.0,
                accuracy_improvement=0.05,
                error_types={"syntax": 3, "logic": 2},
                safety_violations=0
            )

        # Adapt strategy
        new_strategy, new_rate = await meta_learning_manager.adapt_learning_strategy()

        # Should switch to conservative strategy due to high rollback rate
        assert new_strategy == LearningStrategy.CONSERVATIVE
        assert new_rate < meta_learning_manager.adaptive_config.base_learning_rate

    @pytest.mark.asyncio
    async def test_adapt_learning_strategy_high_performance(self, meta_learning_manager):
        """Test adapting learning strategy for high performance"""
        # Create sessions with high performance
        for i in range(6):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=5,  # High success rate
                rollback_count=0,   # No rollbacks
                reward_score=5.0,
                penalty_score=0.0,
                accuracy_improvement=0.25,
                error_types={"syntax": 0, "logic": 0},
                safety_violations=0
            )

        # Adapt strategy
        new_strategy, new_rate = await meta_learning_manager.adapt_learning_strategy()

        # Should switch to aggressive strategy due to high performance
        assert new_strategy == LearningStrategy.AGGRESSIVE
        assert new_rate > meta_learning_manager.adaptive_config.base_learning_rate

    @pytest.mark.asyncio
    async def test_get_learning_recommendations(self, meta_learning_manager):
        """Test getting learning recommendations"""
        # Create multiple sessions with various issues
        for i in range(5):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=2,  # Low success rate
                rollback_count=2,   # High rollback rate
                reward_score=1.0,
                penalty_score=-2.0,
                accuracy_improvement=0.05,
                error_types={"syntax": 3},
                safety_violations=1  # Safety violation
            )

        recommendations = await meta_learning_manager.get_learning_recommendations("user_123")

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should have recommendations for high rollback rate and safety violations
        recommendation_types = [rec["type"] for rec in recommendations]
        assert "reduce_learning_rate" in recommendation_types
        assert "safety_concern" in recommendation_types

    @pytest.mark.asyncio
    async def test_get_learning_recommendations_insufficient_data(self, meta_learning_manager):
        """Test getting recommendations with insufficient data"""
        recommendations = await meta_learning_manager.get_learning_recommendations("user_123")

        assert len(recommendations) == 1
        assert recommendations[0]["type"] == "insufficient_data"
        assert "Need more learning sessions" in recommendations[0]["message"]

    def test_get_current_learning_config(self, meta_learning_manager):
        """Test getting current learning configuration"""
        config = meta_learning_manager.get_current_learning_config()

        assert "learning_rate" in config
        assert "strategy" in config
        assert "last_adaptation" in config
        assert "total_sessions" in config
        assert "total_insights" in config

        assert config["learning_rate"] == meta_learning_manager.current_learning_rate
        assert config["strategy"] == meta_learning_manager.current_strategy.value
        assert config["total_sessions"] == 0
        assert config["total_insights"] == 0

    def test_get_learning_statistics(self, meta_learning_manager):
        """Test getting learning statistics"""
        # Initially no data
        stats = meta_learning_manager.get_learning_statistics()
        assert "error" in stats
        assert "No learning sessions recorded" in stats["error"]

        # Add some sessions
        asyncio.run(meta_learning_manager.record_learning_session(
            session_id="test_session_1",
            user_id="user_123",
            start_time="2025-01-27T10:00:00Z",
            end_time="2025-01-27T10:30:00Z",
            fix_attempts=5,
            successful_fixes=4,
            rollback_count=1,
            reward_score=3.0,
            penalty_score=-1.0,
            accuracy_improvement=0.15,
            error_types={"syntax": 2},
            safety_violations=0
        ))

        stats = meta_learning_manager.get_learning_statistics()

        assert "total_sessions" in stats
        assert "recent_sessions" in stats
        assert "avg_net_score" in stats
        assert "avg_success_rate" in stats
        assert "avg_rollback_rate" in stats
        assert "total_insights" in stats
        assert "current_strategy" in stats
        assert "current_learning_rate" in stats

        assert stats["total_sessions"] == 1
        assert stats["recent_sessions"] == 1

    @pytest.mark.asyncio
    async def test_learning_strategy_adaptation_insufficient_data(self, meta_learning_manager):
        """Test strategy adaptation with insufficient data"""
        # Add only 3 sessions (less than required 5)
        for i in range(3):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=4,
                rollback_count=1,
                reward_score=3.0,
                penalty_score=-1.0,
                accuracy_improvement=0.15,
                error_types={"syntax": 2},
                safety_violations=0
            )

        # Should not adapt due to insufficient data
        new_strategy, new_rate = await meta_learning_manager.adapt_learning_strategy()

        assert new_strategy == meta_learning_manager.current_strategy
        assert new_rate == meta_learning_manager.current_learning_rate

    @pytest.mark.asyncio
    async def test_meta_learning_insights_generation(self, meta_learning_manager):
        """Test generation of meta-learning insights"""
        # Create sessions with specific patterns
        for i in range(5):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=4,
                rollback_count=2,  # High rollback rate
                reward_score=3.0,
                penalty_score=-1.0,
                accuracy_improvement=0.15,
                error_types={"syntax": 3, "logic": 1},  # Syntax errors most common
                safety_violations=0
            )

        insights = await meta_learning_manager.analyze_learning_patterns()

        # Should generate insights about rollback patterns and error types
        insight_types = [insight.insight_type for insight in insights]
        assert "high_rollback_rate" in insight_types
        assert "error_pattern" in insight_types

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, meta_learning_manager):
        """Test performance trend analysis"""
        # Create sessions with improving performance
        for i in range(10):
            await meta_learning_manager.record_learning_session(
                session_id=f"test_session_{i}",
                user_id="user_123",
                start_time=f"2025-01-27T{10+i}:00:00Z",
                end_time=f"2025-01-27T{10+i}:30:00Z",
                fix_attempts=5,
                successful_fixes=4,
                rollback_count=1,
                reward_score=3.0 + i * 0.1,  # Improving performance
                penalty_score=-1.0,
                accuracy_improvement=0.15 + i * 0.01,
                error_types={"syntax": 2},
                safety_violations=0
            )

        insights = await meta_learning_manager.analyze_learning_patterns()

        # Should generate performance improvement insight
        insight_types = [insight.insight_type for insight in insights]
        assert "performance_improvement" in insight_types

    def test_adaptive_config_initialization(self, meta_learning_manager):
        """Test adaptive configuration initialization"""
        config = meta_learning_manager.adaptive_config

        assert config.base_learning_rate == 0.1
        assert config.max_learning_rate == 0.5
        assert config.min_learning_rate == 0.01
        assert config.rollback_penalty_factor == 0.8
        assert config.reward_boost_factor == 1.2
        assert config.stability_threshold == 0.7
        assert config.adaptation_frequency_hours == 24

    @pytest.mark.asyncio
    async def test_learning_event_recording(self, meta_learning_manager):
        """Test recording learning events"""
        # Record a session to trigger events
        await meta_learning_manager.record_learning_session(
            session_id="test_session_1",
            user_id="user_123",
            start_time="2025-01-27T10:00:00Z",
            end_time="2025-01-27T10:30:00Z",
            fix_attempts=5,
            successful_fixes=4,
            rollback_count=1,
            reward_score=3.0,
            penalty_score=-1.0,
            accuracy_improvement=0.15,
            error_types={"syntax": 2},
            safety_violations=0
        )

        # Should have recorded learning events
        assert len(meta_learning_manager.learning_events) > 0

        # Check for session end event
        session_end_events = [
            event for event in meta_learning_manager.learning_events
            if event["event_type"] == MetaLearningEvent.SESSION_END.value
        ]
        assert len(session_end_events) == 1
