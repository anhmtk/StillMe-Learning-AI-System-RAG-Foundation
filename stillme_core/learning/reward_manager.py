#!/usr/bin/env python3
"""
StillMe Learning Reward Manager
===============================

Reinforcement learning system for self-learning capabilities.
Manages rewards and penalties based on learning outcomes.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import json
import logging
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class RewardType(Enum):
    """Types of rewards"""
    FIX_SUCCESS = "fix_success"
    TEST_PASS = "test_pass"
    ETHICS_COMPLIANCE = "ethics_compliance"
    SECURITY_COMPLIANCE = "security_compliance"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"

class PenaltyType(Enum):
    """Types of penalties"""
    FIX_FAILURE = "fix_failure"
    TEST_FAILURE = "test_failure"
    ETHICS_VIOLATION = "ethics_violation"
    SECURITY_VIOLATION = "security_violation"
    PERFORMANCE_REGRESSION = "performance_regression"

@dataclass
class RewardEntry:
    """Individual reward entry"""
    timestamp: str
    user_id: str
    session_id: str
    reward_type: str
    value: float
    context: Dict[str, Any]
    rationale: str

@dataclass
class PenaltyEntry:
    """Individual penalty entry"""
    timestamp: str
    user_id: str
    session_id: str
    penalty_type: str
    value: float
    context: Dict[str, Any]
    rationale: str

@dataclass
class LearningSession:
    """Learning session with reward/penalty tracking"""
    session_id: str
    user_id: str
    start_time: str
    end_time: Optional[str]
    rewards: List[RewardEntry]
    penalties: List[PenaltyEntry]
    total_reward: float
    total_penalty: float
    net_score: float

class RewardManager:
    """
    Manages rewards and penalties for learning outcomes.
    
    Features:
    - Reward system: +1 for successful fixes, test passes, compliance
    - Penalty system: -1 for failures, violations, regressions
    - Session tracking: Per-user, per-session reward/penalty aggregation
    - Trend analysis: Learning curve visualization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        
        # Storage
        self.sessions: Dict[str, LearningSession] = {}
        self.reward_history: List[RewardEntry] = []
        self.penalty_history: List[PenaltyEntry] = []
        
        # Configuration
        self.artifacts_path = Path("artifacts")
        self.artifacts_path.mkdir(exist_ok=True)
        
        # Reward/penalty values
        self.reward_values = {
            RewardType.FIX_SUCCESS: 1.0,
            RewardType.TEST_PASS: 1.0,
            RewardType.ETHICS_COMPLIANCE: 1.0,
            RewardType.SECURITY_COMPLIANCE: 1.0,
            RewardType.PERFORMANCE_IMPROVEMENT: 1.0
        }
        
        self.penalty_values = {
            PenaltyType.FIX_FAILURE: -1.0,
            PenaltyType.TEST_FAILURE: -1.0,
            PenaltyType.ETHICS_VIOLATION: -1.0,
            PenaltyType.SECURITY_VIOLATION: -1.0,
            PenaltyType.PERFORMANCE_REGRESSION: -1.0
        }
        
        self.logger.info("✅ RewardManager initialized")
    
    async def start_learning_session(self, session_id: str, user_id: str) -> LearningSession:
        """Start a new learning session"""
        session = LearningSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            rewards=[],
            penalties=[],
            total_reward=0.0,
            total_penalty=0.0,
            net_score=0.0
        )
        
        self.sessions[session_id] = session
        self.logger.info(f"🎯 Started learning session {session_id} for user {user_id}")
        
        return session
    
    async def end_learning_session(self, session_id: str) -> LearningSession:
        """End a learning session and calculate final scores"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session.end_time = datetime.now().isoformat()
        
        # Calculate final scores
        session.total_reward = sum(reward.value for reward in session.rewards)
        session.total_penalty = sum(penalty.value for penalty in session.penalties)
        session.net_score = session.total_reward + session.total_penalty
        
        self.logger.info(f"🏁 Ended learning session {session_id}. Net score: {session.net_score:.2f}")
        
        return session
    
    async def award_reward(
        self,
        session_id: str,
        reward_type: RewardType,
        context: Dict[str, Any],
        rationale: str = ""
    ) -> RewardEntry:
        """Award a reward for positive learning outcome"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        value = self.reward_values.get(reward_type, 1.0)
        
        reward = RewardEntry(
            timestamp=datetime.now().isoformat(),
            user_id=session.user_id,
            session_id=session_id,
            reward_type=reward_type.value,
            value=value,
            context=context,
            rationale=rationale
        )
        
        session.rewards.append(reward)
        self.reward_history.append(reward)
        
        self.logger.info(f"🎉 Awarded reward {reward_type.value} (+{value}) for session {session_id}")
        
        return reward
    
    async def apply_penalty(
        self,
        session_id: str,
        penalty_type: PenaltyType,
        context: Dict[str, Any],
        rationale: str = ""
    ) -> PenaltyEntry:
        """Apply a penalty for negative learning outcome"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        value = self.penalty_values.get(penalty_type, -1.0)
        
        penalty = PenaltyEntry(
            timestamp=datetime.now().isoformat(),
            user_id=session.user_id,
            session_id=session_id,
            penalty_type=penalty_type.value,
            value=value,
            context=context,
            rationale=rationale
        )
        
        session.penalties.append(penalty)
        self.penalty_history.append(penalty)
        
        self.logger.warning(f"⚠️ Applied penalty {penalty_type.value} ({value}) for session {session_id}")
        
        return penalty
    
    async def evaluate_learning_outcome(
        self,
        session_id: str,
        fix_result: Dict[str, Any],
        test_result: Dict[str, Any],
        ethics_result: Dict[str, Any],
        security_result: Dict[str, Any]
    ) -> Tuple[List[RewardEntry], List[PenaltyEntry]]:
        """
        Evaluate learning outcome and award appropriate rewards/penalties.
        
        Args:
            session_id: Learning session ID
            fix_result: Result of fix attempt
            test_result: Result of testing
            ethics_result: Ethics compliance check
            security_result: Security compliance check
            
        Returns:
            Tuple of (rewards, penalties) awarded
        """
        rewards = []
        penalties = []
        
        # Evaluate fix success
        if fix_result.get("success", False):
            reward = await self.award_reward(
                session_id=session_id,
                reward_type=RewardType.FIX_SUCCESS,
                context={"fix_details": fix_result},
                rationale="Fix applied successfully"
            )
            rewards.append(reward)
        else:
            penalty = await self.apply_penalty(
                session_id=session_id,
                penalty_type=PenaltyType.FIX_FAILURE,
                context={"fix_details": fix_result},
                rationale="Fix failed to resolve issue"
            )
            penalties.append(penalty)
        
        # Evaluate test results
        if test_result.get("passed", False):
            reward = await self.award_reward(
                session_id=session_id,
                reward_type=RewardType.TEST_PASS,
                context={"test_details": test_result},
                rationale="All tests passed"
            )
            rewards.append(reward)
        else:
            penalty = await self.apply_penalty(
                session_id=session_id,
                penalty_type=PenaltyType.TEST_FAILURE,
                context={"test_details": test_result},
                rationale="Tests failed after fix"
            )
            penalties.append(penalty)
        
        # Evaluate ethics compliance
        if ethics_result.get("compliant", True):
            reward = await self.award_reward(
                session_id=session_id,
                reward_type=RewardType.ETHICS_COMPLIANCE,
                context={"ethics_details": ethics_result},
                rationale="Ethics compliance maintained"
            )
            rewards.append(reward)
        else:
            penalty = await self.apply_penalty(
                session_id=session_id,
                penalty_type=PenaltyType.ETHICS_VIOLATION,
                context={"ethics_details": ethics_result},
                rationale="Ethics violation detected"
            )
            penalties.append(penalty)
        
        # Evaluate security compliance
        if security_result.get("compliant", True):
            reward = await self.award_reward(
                session_id=session_id,
                reward_type=RewardType.SECURITY_COMPLIANCE,
                context={"security_details": security_result},
                rationale="Security compliance maintained"
            )
            rewards.append(reward)
        else:
            penalty = await self.apply_penalty(
                session_id=session_id,
                penalty_type=PenaltyType.SECURITY_VIOLATION,
                context={"security_details": security_result},
                rationale="Security violation detected"
            )
            penalties.append(penalty)
        
        return rewards, penalties
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a learning session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "duration": self._calculate_duration(session.start_time, session.end_time),
            "total_rewards": len(session.rewards),
            "total_penalties": len(session.penalties),
            "net_score": session.net_score,
            "reward_breakdown": self._get_reward_breakdown(session.rewards),
            "penalty_breakdown": self._get_penalty_breakdown(session.penalties)
        }
    
    def get_user_learning_curve(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get learning curve for a user over specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_sessions = [
            session for session in self.sessions.values()
            if session.user_id == user_id and 
            datetime.fromisoformat(session.start_time) >= cutoff_date
        ]
        
        if not user_sessions:
            return {"error": "No sessions found for user"}
        
        # Calculate daily scores
        daily_scores = {}
        for session in user_sessions:
            date = datetime.fromisoformat(session.start_time).date()
            if date not in daily_scores:
                daily_scores[date] = []
            daily_scores[date].append(session.net_score)
        
        # Calculate averages
        daily_averages = {
            str(date): sum(scores) / len(scores)
            for date, scores in daily_scores.items()
        }
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_sessions": len(user_sessions),
            "daily_scores": daily_averages,
            "overall_average": sum(session.net_score for session in user_sessions) / len(user_sessions),
            "improvement_trend": self._calculate_improvement_trend(list(daily_averages.values()))
        }
    
    async def generate_rewards_chart(self, user_id: Optional[str] = None) -> str:
        """Generate rewards curve chart and save to artifacts"""
        try:
            # Get data for chart
            if user_id:
                curve_data = self.get_user_learning_curve(user_id)
                title = f"Learning Curve - User {user_id}"
            else:
                curve_data = self._get_global_learning_curve()
                title = "Global Learning Curve"
            
            if "error" in curve_data:
                self.logger.warning(f"Cannot generate chart: {curve_data['error']}")
                return ""
            
            # Create chart
            plt.figure(figsize=(12, 6))
            dates = list(curve_data["daily_scores"].keys())
            scores = list(curve_data["daily_scores"].values())
            
            plt.plot(dates, scores, marker='o', linewidth=2, markersize=4)
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("Net Score (Rewards - Penalties)")
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            chart_path = self.artifacts_path / "self_learning_rewards.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"📊 Rewards chart saved to {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate rewards chart: {e}")
            return ""
    
    def _calculate_duration(self, start_time: str, end_time: Optional[str]) -> float:
        """Calculate session duration in minutes"""
        if not end_time:
            return 0.0
        
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        return (end - start).total_seconds() / 60
    
    def _get_reward_breakdown(self, rewards: List[RewardEntry]) -> Dict[str, int]:
        """Get breakdown of reward types"""
        breakdown = {}
        for reward in rewards:
            reward_type = reward.reward_type
            breakdown[reward_type] = breakdown.get(reward_type, 0) + 1
        return breakdown
    
    def _get_penalty_breakdown(self, penalties: List[PenaltyEntry]) -> Dict[str, int]:
        """Get breakdown of penalty types"""
        breakdown = {}
        for penalty in penalties:
            penalty_type = penalty.penalty_type
            breakdown[penalty_type] = breakdown.get(penalty_type, 0) + 1
        return breakdown
    
    def _calculate_improvement_trend(self, scores: List[float]) -> str:
        """Calculate improvement trend from scores"""
        if len(scores) < 2:
            return "insufficient_data"
        
        recent_avg = sum(scores[-3:]) / len(scores[-3:]) if len(scores) >= 3 else scores[-1]
        early_avg = sum(scores[:3]) / len(scores[:3]) if len(scores) >= 3 else scores[0]
        
        if recent_avg > early_avg * 1.1:
            return "improving"
        elif recent_avg < early_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _get_global_learning_curve(self) -> Dict[str, Any]:
        """Get global learning curve across all users"""
        # Simplified implementation - in practice would aggregate all user data
        return {
            "daily_scores": {},
            "total_sessions": len(self.sessions),
            "overall_average": 0.0
        }
    
    async def save_learning_data(self):
        """Save learning data to persistent storage"""
        data = {
            "sessions": {sid: asdict(session) for sid, session in self.sessions.items()},
            "reward_history": [asdict(reward) for reward in self.reward_history],
            "penalty_history": [asdict(penalty) for penalty in self.penalty_history],
            "timestamp": datetime.now().isoformat()
        }
        
        data_file = self.artifacts_path / "learning_rewards_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Learning data saved to {data_file}")
    
    def get_development_status(self) -> Dict[str, Any]:
        """Get development status and statistics"""
        return {
            "total_sessions": len(self.sessions),
            "total_rewards": sum(len(session.rewards) for session in self.sessions.values()),
            "total_penalties": sum(len(session.penalties) for session in self.sessions.values()),
            "avg_reward_per_session": self._calculate_avg_reward_per_session() if hasattr(self, '_calculate_avg_reward_per_session') else 0.0,
            "development_phase": "experimental",
            "last_updated": datetime.now().isoformat()
        }
    
    async def calculate_delayed_reward(
        self, 
        session_id: str, 
        reward_type: str,
        cumulative_success_rate: float,
        time_decay_factor: float = 0.9
    ) -> float:
        """
        Calculate delayed reward based on cumulative success over multiple sessions
        
        Args:
            session_id: Current session ID
            reward_type: Type of reward (SUCCESSFUL_FIX, ETHICS_COMPLIANCE, etc.)
            cumulative_success_rate: Success rate over multiple sessions (0.0-1.0)
            time_decay_factor: Time decay factor for older sessions (0.0-1.0)
            
        Returns:
            Calculated delayed reward value
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found for delayed reward calculation")
            return 0.0
        
        session = self.sessions[session_id]
        
        # Base reward calculation
        base_reward = self._get_base_reward_value(reward_type)
        
        # Apply cumulative success multiplier
        success_multiplier = 1.0 + (cumulative_success_rate * 0.5)  # Up to 50% bonus
        
        # Apply time decay for older sessions
        session_age = (datetime.now() - session.start_time).total_seconds() / 3600  # Hours
        time_decay = time_decay_factor ** (session_age / 24)  # Decay per day
        
        # Calculate final delayed reward
        delayed_reward = base_reward * success_multiplier * time_decay
        
        logger.info(f"Delayed reward calculated: {delayed_reward:.2f} (base: {base_reward}, success: {cumulative_success_rate:.2f})")
        
        return delayed_reward
    
    def _get_base_reward_value(self, reward_type: str) -> float:
        """Get base reward value for different reward types"""
        reward_values = {
            "SUCCESSFUL_FIX": 1.0,
            "ETHICS_COMPLIANCE": 1.5,
            "SECURITY_PASS": 2.0,
            "USER_SATISFACTION": 1.2,
            "PERFORMANCE_IMPROVEMENT": 1.3,
            "ACCURACY_IMPROVEMENT": 1.1
        }
        return reward_values.get(reward_type, 1.0)
    
    async def calculate_multi_objective_reward(
        self,
        session_id: str,
        objectives: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate rewards for multiple objectives simultaneously
        
        Args:
            session_id: Session ID
            objectives: Dictionary of objective names and their weights
            
        Returns:
            Dictionary of calculated rewards for each objective
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found for multi-objective reward")
            return {}
        
        session = self.sessions[session_id]
        calculated_rewards = {}
        
        for objective, weight in objectives.items():
            # Calculate reward for this objective
            if objective == "accuracy":
                reward = await self._calculate_accuracy_reward(session)
            elif objective == "ethics":
                reward = await self._calculate_ethics_reward(session)
            elif objective == "performance":
                reward = await self._calculate_performance_reward(session)
            elif objective == "safety":
                reward = await self._calculate_safety_reward(session)
            else:
                reward = 0.0
            
            # Apply weight
            calculated_rewards[objective] = reward * weight
        
        logger.info(f"Multi-objective rewards calculated: {calculated_rewards}")
        return calculated_rewards
    
    async def _calculate_accuracy_reward(self, session) -> float:
        """Calculate accuracy-based reward"""
        if not session.rewards:
            return 0.0
        
        accuracy_rewards = [r for r in session.rewards if r.reward_type == "ACCURACY_IMPROVEMENT"]
        return sum(r.value for r in accuracy_rewards)
    
    async def _calculate_ethics_reward(self, session) -> float:
        """Calculate ethics-based reward"""
        if not session.rewards:
            return 0.0
        
        ethics_rewards = [r for r in session.rewards if r.reward_type == "ETHICS_COMPLIANCE"]
        return sum(r.value for r in ethics_rewards)
    
    async def _calculate_performance_reward(self, session) -> float:
        """Calculate performance-based reward"""
        if not session.rewards:
            return 0.0
        
        performance_rewards = [r for r in session.rewards if r.reward_type == "PERFORMANCE_IMPROVEMENT"]
        return sum(r.value for r in performance_rewards)
    
    async def _calculate_safety_reward(self, session) -> float:
        """Calculate safety-based reward"""
        if not session.rewards:
            return 0.0
        
        safety_rewards = [r for r in session.rewards if r.reward_type == "SECURITY_PASS"]
        return sum(r.value for r in safety_rewards)
    
    async def export_reward_curve(self, output_path: str = "artifacts/self_learning_rewards.png"):
        """Export reward curve visualization"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Collect all session data
            session_data = []
            for session in self.sessions.values():
                session_data.append({
                    'timestamp': session.start_time,
                    'total_rewards': sum(r.value for r in session.rewards),
                    'total_penalties': sum(p.value for p in session.penalties)
                })
            
            if not session_data:
                logger.warning("No session data available for reward curve")
                return
            
            # Sort by timestamp
            session_data.sort(key=lambda x: x['timestamp'])
            
            # Extract data for plotting
            timestamps = [d['timestamp'] for d in session_data]
            rewards = [d['total_rewards'] for d in session_data]
            penalties = [abs(d['total_penalties']) for d in session_data]
            
            # Create plot
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, rewards, 'g-', label='Rewards', linewidth=2)
            plt.plot(timestamps, penalties, 'r-', label='Penalties', linewidth=2)
            plt.xlabel('Time')
            plt.ylabel('Reward/Penalty Value')
            plt.title('StillMe Self-Learning Reward Curve')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save plot
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Reward curve exported to {output_path}")
            
        except ImportError:
            logger.warning("Matplotlib not available, skipping reward curve export")
        except Exception as e:
            logger.error(f"Failed to export reward curve: {e}")
    
    def get_reward_statistics(self) -> Dict[str, Any]:
        """Get comprehensive reward statistics"""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_rewards": 0,
                "total_penalties": 0,
                "avg_reward_per_session": 0.0,
                "reward_distribution": {},
                "penalty_distribution": {},
                "success_rate": 0.0
            }
        
        # Calculate statistics
        total_sessions = len(self.sessions)
        all_rewards = []
        all_penalties = []
        reward_types = {}
        penalty_types = {}
        
        for session in self.sessions.values():
            for reward in session.rewards:
                all_rewards.append(reward.value)
                reward_types[reward.reward_type] = reward_types.get(reward.reward_type, 0) + 1
            
            for penalty in session.penalties:
                all_penalties.append(abs(penalty.value))
                penalty_types[penalty.penalty_type] = penalty_types.get(penalty.penalty_type, 0) + 1
        
        # Calculate success rate
        successful_sessions = sum(1 for session in self.sessions.values() 
                                if len(session.rewards) > len(session.penalties))
        success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0.0
        
        return {
            "total_sessions": total_sessions,
            "total_rewards": len(all_rewards),
            "total_penalties": len(all_penalties),
            "avg_reward_per_session": sum(all_rewards) / total_sessions if total_sessions > 0 else 0.0,
            "reward_distribution": reward_types,
            "penalty_distribution": penalty_types,
            "success_rate": success_rate,
            "avg_reward_value": sum(all_rewards) / len(all_rewards) if all_rewards else 0.0,
            "avg_penalty_value": sum(all_penalties) / len(all_penalties) if all_penalties else 0.0
        }
