#!/usr/bin/env python3
"""
Test suite for Reward Manager
=============================

Tests for reinforcement learning system.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from stillme_core.learning.reward_manager import (
    RewardManager,
    RewardType,
    PenaltyType,
    LearningSession
)

class TestRewardManager:
    """Test suite for RewardManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reward_manager(self, temp_dir):
        """Create reward manager with temporary directory"""
        with patch('stillme_core.learning.reward_manager.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            manager = RewardManager()
            return manager
    
    @pytest.mark.asyncio
    async def test_start_learning_session(self, reward_manager):
        """Test starting a learning session"""
        session = await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        assert session.session_id == "test_session"
        assert session.user_id == "user_123"
        assert session.start_time is not None
        assert session.end_time is None
        assert len(session.rewards) == 0
        assert len(session.penalties) == 0
        assert session.total_reward == 0.0
        assert session.total_penalty == 0.0
        assert session.net_score == 0.0
    
    @pytest.mark.asyncio
    async def test_end_learning_session(self, reward_manager):
        """Test ending a learning session"""
        # Start session
        session = await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        # Add some rewards and penalties
        await reward_manager.award_reward(
            session_id="test_session",
            reward_type=RewardType.FIX_SUCCESS,
            context={"fix": "test"},
            rationale="Test reward"
        )
        
        await reward_manager.apply_penalty(
            session_id="test_session",
            penalty_type=PenaltyType.FIX_FAILURE,
            context={"error": "test"},
            rationale="Test penalty"
        )
        
        # End session
        ended_session = await reward_manager.end_learning_session("test_session")
        
        assert ended_session.end_time is not None
        assert ended_session.total_reward == 1.0
        assert ended_session.total_penalty == -1.0
        assert ended_session.net_score == 0.0
    
    @pytest.mark.asyncio
    async def test_award_reward(self, reward_manager):
        """Test awarding a reward"""
        # Start session
        await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        # Award reward
        reward = await reward_manager.award_reward(
            session_id="test_session",
            reward_type=RewardType.FIX_SUCCESS,
            context={"fix": "test"},
            rationale="Test reward"
        )
        
        assert reward.session_id == "test_session"
        assert reward.user_id == "user_123"
        assert reward.reward_type == "fix_success"
        assert reward.value == 1.0
        assert reward.context == {"fix": "test"}
        assert reward.rationale == "Test reward"
    
    @pytest.mark.asyncio
    async def test_apply_penalty(self, reward_manager):
        """Test applying a penalty"""
        # Start session
        await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        # Apply penalty
        penalty = await reward_manager.apply_penalty(
            session_id="test_session",
            penalty_type=PenaltyType.FIX_FAILURE,
            context={"error": "test"},
            rationale="Test penalty"
        )
        
        assert penalty.session_id == "test_session"
        assert penalty.user_id == "user_123"
        assert penalty.penalty_type == "fix_failure"
        assert penalty.value == -1.0
        assert penalty.context == {"error": "test"}
        assert penalty.rationale == "Test penalty"
    
    @pytest.mark.asyncio
    async def test_evaluate_learning_outcome(self, reward_manager):
        """Test evaluating learning outcome"""
        # Start session
        await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        # Evaluate learning outcome
        fix_result = {"success": True, "details": "Fix applied"}
        test_result = {"passed": True, "details": "All tests passed"}
        ethics_result = {"compliant": True, "details": "Ethics check passed"}
        security_result = {"compliant": True, "details": "Security check passed"}
        
        rewards, penalties = await reward_manager.evaluate_learning_outcome(
            session_id="test_session",
            fix_result=fix_result,
            test_result=test_result,
            ethics_result=ethics_result,
            security_result=security_result
        )
        
        # Should have 4 rewards (one for each positive outcome)
        assert len(rewards) == 4
        assert len(penalties) == 0
        
        # Check reward types
        reward_types = [reward.reward_type for reward in rewards]
        assert "fix_success" in reward_types
        assert "test_pass" in reward_types
        assert "ethics_compliance" in reward_types
        assert "security_compliance" in reward_types
    
    @pytest.mark.asyncio
    async def test_evaluate_learning_outcome_with_failures(self, reward_manager):
        """Test evaluating learning outcome with failures"""
        # Start session
        await reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        )
        
        # Evaluate learning outcome with failures
        fix_result = {"success": False, "details": "Fix failed"}
        test_result = {"passed": False, "details": "Tests failed"}
        ethics_result = {"compliant": False, "details": "Ethics violation"}
        security_result = {"compliant": False, "details": "Security violation"}
        
        rewards, penalties = await reward_manager.evaluate_learning_outcome(
            session_id="test_session",
            fix_result=fix_result,
            test_result=test_result,
            ethics_result=ethics_result,
            security_result=security_result
        )
        
        # Should have 4 penalties (one for each failure)
        assert len(rewards) == 0
        assert len(penalties) == 4
        
        # Check penalty types
        penalty_types = [penalty.penalty_type for penalty in penalties]
        assert "fix_failure" in penalty_types
        assert "test_failure" in penalty_types
        assert "ethics_violation" in penalty_types
        assert "security_violation" in penalty_types
    
    def test_get_session_summary(self, reward_manager):
        """Test getting session summary"""
        # Start session and add rewards/penalties
        asyncio.run(reward_manager.start_learning_session(
            session_id="test_session",
            user_id="user_123"
        ))
        
        asyncio.run(reward_manager.award_reward(
            session_id="test_session",
            reward_type=RewardType.FIX_SUCCESS,
            context={"fix": "test"},
            rationale="Test reward"
        ))
        
        asyncio.run(reward_manager.apply_penalty(
            session_id="test_session",
            penalty_type=PenaltyType.FIX_FAILURE,
            context={"error": "test"},
            rationale="Test penalty"
        ))
        
        # End session
        asyncio.run(reward_manager.end_learning_session("test_session"))
        
        # Get summary
        summary = reward_manager.get_session_summary("test_session")
        
        assert summary["session_id"] == "test_session"
        assert summary["user_id"] == "user_123"
        assert summary["total_rewards"] == 1
        assert summary["total_penalties"] == 1
        assert summary["net_score"] == 0.0
        assert "reward_breakdown" in summary
        assert "penalty_breakdown" in summary
    
    def test_get_user_learning_curve(self, reward_manager):
        """Test getting user learning curve"""
        # Create multiple sessions for a user
        user_id = "user_123"
        
        for i in range(3):
            session_id = f"session_{i}"
            asyncio.run(reward_manager.start_learning_session(session_id, user_id))
            
            # Add some rewards
            asyncio.run(reward_manager.award_reward(
                session_id=session_id,
                reward_type=RewardType.FIX_SUCCESS,
                context={"fix": f"test_{i}"},
                rationale=f"Test reward {i}"
            ))
            
            asyncio.run(reward_manager.end_learning_session(session_id))
        
        # Get learning curve
        curve = reward_manager.get_user_learning_curve(user_id, days=30)
        
        assert curve["user_id"] == user_id
        assert curve["total_sessions"] == 3
        assert "daily_scores" in curve
        assert "overall_average" in curve
        assert "improvement_trend" in curve
    
    @pytest.mark.asyncio
    async def test_generate_rewards_chart(self, reward_manager):
        """Test generating rewards chart"""
        # Create some test data
        await reward_manager.start_learning_session("test_session", "user_123")
        await reward_manager.award_reward(
            session_id="test_session",
            reward_type=RewardType.FIX_SUCCESS,
            context={"fix": "test"},
            rationale="Test reward"
        )
        await reward_manager.end_learning_session("test_session")
        
        # Generate chart
        with patch('matplotlib.pyplot.savefig') as mock_savefig:
            chart_path = await reward_manager.generate_rewards_chart("user_123")
            
            # Should attempt to save chart
            mock_savefig.assert_called_once()
    
    def test_get_development_status(self, reward_manager):
        """Test getting development status"""
        status = reward_manager.get_development_status()
        
        assert "status" in status
        assert "completion_percentage" in status
        assert "planned_features" in status
        assert "estimated_completion" in status
        assert "current_limitations" in status
    
    @pytest.mark.asyncio
    async def test_save_learning_data(self, reward_manager):
        """Test saving learning data"""
        # Create some test data
        await reward_manager.start_learning_session("test_session", "user_123")
        await reward_manager.award_reward(
            session_id="test_session",
            reward_type=RewardType.FIX_SUCCESS,
            context={"fix": "test"},
            rationale="Test reward"
        )
        await reward_manager.end_learning_session("test_session")
        
        # Save data
        await reward_manager.save_learning_data()
        
        # Check if file was created
        data_file = reward_manager.artifacts_path / "learning_rewards_data.json"
        assert data_file.exists()
    
    @pytest.mark.asyncio
    async def test_reward_values_configuration(self, reward_manager):
        """Test reward values configuration"""
        # Check default reward values
        assert reward_manager.reward_values[RewardType.FIX_SUCCESS] == 1.0
        assert reward_manager.reward_values[RewardType.TEST_PASS] == 1.0
        assert reward_manager.reward_values[RewardType.ETHICS_COMPLIANCE] == 1.0
        
        # Check default penalty values
        assert reward_manager.penalty_values[PenaltyType.FIX_FAILURE] == -1.0
        assert reward_manager.penalty_values[PenaltyType.TEST_FAILURE] == -1.0
        assert reward_manager.penalty_values[PenaltyType.ETHICS_VIOLATION] == -1.0
    
    @pytest.mark.asyncio
    async def test_session_not_found_error(self, reward_manager):
        """Test error handling for non-existent session"""
        with pytest.raises(ValueError, match="Session nonexistent_session not found"):
            await reward_manager.award_reward(
                session_id="nonexistent_session",
                reward_type=RewardType.FIX_SUCCESS,
                context={"fix": "test"},
                rationale="Test reward"
            )
    
    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self, reward_manager):
        """Test ending non-existent session"""
        with pytest.raises(ValueError, match="Session nonexistent_session not found"):
            await reward_manager.end_learning_session("nonexistent_session")
