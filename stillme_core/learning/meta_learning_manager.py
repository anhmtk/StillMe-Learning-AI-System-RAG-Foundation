#!/usr/bin/env python3
"""
StillMe Meta-Learning Manager
=============================

Learn-to-learn system that analyzes learning patterns and adapts learning strategies.

Author: StillMe AI Framework Team
Version: 1.0.0
Status: EXPERIMENTAL
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class LearningStrategy(Enum):
    """Learning strategies that can be adapted"""
    CONSERVATIVE = "conservative"  # Slow, careful learning
    BALANCED = "balanced"         # Moderate learning rate
    AGGRESSIVE = "aggressive"     # Fast learning with higher risk
    ADAPTIVE = "adaptive"         # Dynamically adjusted

class MetaLearningEvent(Enum):
    """Types of meta-learning events"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ROLLBACK_OCCURRED = "rollback_occurred"
    REWARD_THRESHOLD_HIT = "reward_threshold_hit"
    PENALTY_THRESHOLD_HIT = "penalty_threshold_hit"
    LEARNING_RATE_ADJUSTED = "learning_rate_adjusted"

@dataclass
class LearningSessionMetadata:
    """Metadata about a learning session"""
    session_id: str
    user_id: str
    start_time: str
    end_time: str
    duration_minutes: float
    fix_attempts: int
    successful_fixes: int
    rollback_count: int
    reward_score: float
    penalty_score: float
    net_score: float
    learning_strategy: str
    learning_rate: float
    accuracy_improvement: float
    error_types: Dict[str, int]
    safety_violations: int

@dataclass
class MetaLearningInsight:
    """Insight derived from meta-learning analysis"""
    insight_type: str
    description: str
    confidence: float
    recommendation: str
    evidence: Dict[str, Any]
    timestamp: str

@dataclass
class AdaptiveLearningConfig:
    """Configuration for adaptive learning"""
    base_learning_rate: float
    max_learning_rate: float
    min_learning_rate: float
    rollback_penalty_factor: float
    reward_boost_factor: float
    stability_threshold: float
    adaptation_frequency_hours: int

class MetaLearningManager:
    """
    Meta-learning system that learns how to learn more effectively.
    
    Features:
    - Collects metadata about learning sessions
    - Analyzes patterns to adapt learning strategies
    - Adjusts learning rates based on performance
    - Provides insights for learning optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        
        # Storage
        self.session_metadata: List[LearningSessionMetadata] = []
        self.meta_insights: List[MetaLearningInsight] = []
        self.learning_events: List[Dict[str, Any]] = []
        
        # Configuration
        self.artifacts_path = Path("artifacts")
        self.artifacts_path.mkdir(exist_ok=True)
        
        # Adaptive learning configuration
        self.adaptive_config = AdaptiveLearningConfig(
            base_learning_rate=0.1,
            max_learning_rate=0.5,
            min_learning_rate=0.01,
            rollback_penalty_factor=0.8,
            reward_boost_factor=1.2,
            stability_threshold=0.7,
            adaptation_frequency_hours=24
        )
        
        # Current learning state
        self.current_learning_rate = self.adaptive_config.base_learning_rate
        self.current_strategy = LearningStrategy.BALANCED
        self.last_adaptation = datetime.now()
        
        # Performance tracking
        self.performance_history: List[Dict[str, float]] = []
        
        self.logger.info("✅ MetaLearningManager initialized (EXPERIMENTAL)")
    
    async def record_learning_session(
        self,
        session_id: str,
        user_id: str,
        start_time: str,
        end_time: str,
        fix_attempts: int,
        successful_fixes: int,
        rollback_count: int,
        reward_score: float,
        penalty_score: float,
        accuracy_improvement: float,
        error_types: Dict[str, int],
        safety_violations: int
    ) -> LearningSessionMetadata:
        """
        Record metadata about a learning session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            start_time: Session start timestamp
            end_time: Session end timestamp
            fix_attempts: Number of fix attempts made
            successful_fixes: Number of successful fixes
            rollback_count: Number of rollbacks performed
            reward_score: Total reward score
            penalty_score: Total penalty score
            accuracy_improvement: Accuracy improvement achieved
            error_types: Distribution of error types
            safety_violations: Number of safety violations
            
        Returns:
            LearningSessionMetadata object
        """
        # Calculate duration
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        duration_minutes = (end_dt - start_dt).total_seconds() / 60
        
        # Calculate net score
        net_score = reward_score + penalty_score
        
        # Create metadata
        metadata = LearningSessionMetadata(
            session_id=session_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            fix_attempts=fix_attempts,
            successful_fixes=successful_fixes,
            rollback_count=rollback_count,
            reward_score=reward_score,
            penalty_score=penalty_score,
            net_score=net_score,
            learning_strategy=self.current_strategy.value,
            learning_rate=self.current_learning_rate,
            accuracy_improvement=accuracy_improvement,
            error_types=error_types,
            safety_violations=safety_violations
        )
        
        # Store metadata
        self.session_metadata.append(metadata)
        
        # Record learning event
        await self._record_learning_event(
            MetaLearningEvent.SESSION_END,
            {
                "session_id": session_id,
                "metadata": asdict(metadata)
            }
        )
        
        # Analyze for meta-learning insights
        await self._analyze_session_patterns(metadata)
        
        # Check if adaptation is needed
        await self._check_adaptation_need()
        
        self.logger.info(f"📊 Recorded learning session {session_id}: {net_score:.2f} net score")
        
        return metadata
    
    async def analyze_learning_patterns(self) -> List[MetaLearningInsight]:
        """
        Analyze learning patterns to generate meta-learning insights.
        
        Returns:
            List of MetaLearningInsight objects
        """
        insights = []
        
        if len(self.session_metadata) < 3:
            return insights  # Need at least 3 sessions for meaningful analysis
        
        # Analyze rollback patterns
        rollback_insight = await self._analyze_rollback_patterns()
        if rollback_insight:
            insights.append(rollback_insight)
        
        # Analyze learning rate effectiveness
        rate_insight = await self._analyze_learning_rate_effectiveness()
        if rate_insight:
            insights.append(rate_insight)
        
        # Analyze error type patterns
        error_insight = await self._analyze_error_patterns()
        if error_insight:
            insights.append(error_insight)
        
        # Analyze performance trends
        performance_insight = await self._analyze_performance_trends()
        if performance_insight:
            insights.append(performance_insight)
        
        # Store insights
        self.meta_insights.extend(insights)
        
        # Save insights to artifacts
        await self._save_meta_insights()
        
        self.logger.info(f"🧠 Generated {len(insights)} meta-learning insights")
        
        return insights
    
    async def adapt_learning_strategy(self) -> Tuple[LearningStrategy, float]:
        """
        Adapt learning strategy based on meta-learning analysis.
        
        Returns:
            Tuple of (new_strategy, new_learning_rate)
        """
        if len(self.session_metadata) < 5:
            # Not enough data for adaptation
            return self.current_strategy, self.current_learning_rate
        
        # Analyze recent performance
        recent_sessions = self.session_metadata[-10:]  # Last 10 sessions
        
        # Calculate performance metrics
        avg_net_score = statistics.mean([s.net_score for s in recent_sessions])
        avg_rollback_rate = statistics.mean([s.rollback_count / max(s.fix_attempts, 1) for s in recent_sessions])
        avg_success_rate = statistics.mean([s.successful_fixes / max(s.fix_attempts, 1) for s in recent_sessions])
        
        # Determine new strategy based on performance
        new_strategy = self.current_strategy
        new_learning_rate = self.current_learning_rate
        
        if avg_rollback_rate > 0.3:  # High rollback rate
            new_strategy = LearningStrategy.CONSERVATIVE
            new_learning_rate = max(
                self.adaptive_config.min_learning_rate,
                self.current_learning_rate * self.adaptive_config.rollback_penalty_factor
            )
            self.logger.info("🛡️ Switching to conservative strategy due to high rollback rate")
            
        elif avg_net_score > 2.0 and avg_success_rate > 0.8:  # High performance
            new_strategy = LearningStrategy.AGGRESSIVE
            new_learning_rate = min(
                self.adaptive_config.max_learning_rate,
                self.current_learning_rate * self.adaptive_config.reward_boost_factor
            )
            self.logger.info("🚀 Switching to aggressive strategy due to high performance")
            
        elif avg_net_score > 0.5 and avg_success_rate > 0.6:  # Good performance
            new_strategy = LearningStrategy.BALANCED
            new_learning_rate = self.adaptive_config.base_learning_rate
            self.logger.info("⚖️ Maintaining balanced strategy")
        
        # Update current state
        self.current_strategy = new_strategy
        self.current_learning_rate = new_learning_rate
        self.last_adaptation = datetime.now()
        
        # Record adaptation event
        await self._record_learning_event(
            MetaLearningEvent.LEARNING_RATE_ADJUSTED,
            {
                "old_strategy": self.current_strategy.value,
                "new_strategy": new_strategy.value,
                "old_rate": self.current_learning_rate,
                "new_rate": new_learning_rate,
                "reason": "meta_learning_adaptation"
            }
        )
        
        self.logger.info(f"🔄 Adapted learning strategy: {new_strategy.value} (rate: {new_learning_rate:.3f})")
        
        return new_strategy, new_learning_rate
    
    async def get_learning_recommendations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get personalized learning recommendations based on meta-learning analysis.
        
        Args:
            user_id: Optional user ID for personalized recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Filter sessions by user if specified
        sessions = self.session_metadata
        if user_id:
            sessions = [s for s in self.session_metadata if s.user_id == user_id]
        
        if len(sessions) < 3:
            return [{"type": "insufficient_data", "message": "Need more learning sessions for recommendations"}]
        
        # Analyze user patterns
        recent_sessions = sessions[-5:]
        
        # Check for high rollback rate
        avg_rollback_rate = statistics.mean([s.rollback_count / max(s.fix_attempts, 1) for s in recent_sessions])
        if avg_rollback_rate > 0.2:
            recommendations.append({
                "type": "reduce_learning_rate",
                "priority": "high",
                "message": f"High rollback rate ({avg_rollback_rate:.1%}). Consider reducing learning rate.",
                "action": "decrease_learning_rate"
            })
        
        # Check for low success rate
        avg_success_rate = statistics.mean([s.successful_fixes / max(s.fix_attempts, 1) for s in recent_sessions])
        if avg_success_rate < 0.5:
            recommendations.append({
                "type": "improve_fix_quality",
                "priority": "medium",
                "message": f"Low success rate ({avg_success_rate:.1%}). Focus on fix quality over quantity.",
                "action": "increase_fix_validation"
            })
        
        # Check for safety violations
        total_violations = sum(s.safety_violations for s in recent_sessions)
        if total_violations > 0:
            recommendations.append({
                "type": "safety_concern",
                "priority": "high",
                "message": f"Safety violations detected ({total_violations}). Review safety protocols.",
                "action": "strengthen_safety_checks"
            })
        
        # Check for performance trends
        if len(recent_sessions) >= 3:
            net_scores = [s.net_score for s in recent_sessions]
            if net_scores[-1] < net_scores[0] * 0.8:  # 20% decline
                recommendations.append({
                    "type": "performance_decline",
                    "priority": "medium",
                    "message": "Performance declining. Consider reviewing learning approach.",
                    "action": "review_learning_strategy"
                })
        
        return recommendations
    
    async def _analyze_session_patterns(self, metadata: LearningSessionMetadata):
        """Analyze patterns in a single session"""
        # Record performance metrics
        performance_data = {
            "timestamp": metadata.end_time,
            "net_score": metadata.net_score,
            "success_rate": metadata.successful_fixes / max(metadata.fix_attempts, 1),
            "rollback_rate": metadata.rollback_count / max(metadata.fix_attempts, 1),
            "learning_rate": metadata.learning_rate,
            "strategy": metadata.learning_strategy
        }
        
        self.performance_history.append(performance_data)
        
        # Keep only recent history (last 100 sessions)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    async def _check_adaptation_need(self):
        """Check if learning strategy adaptation is needed"""
        time_since_adaptation = datetime.now() - self.last_adaptation
        
        if time_since_adaptation >= timedelta(hours=self.adaptive_config.adaptation_frequency_hours):
            await self.adapt_learning_strategy()
    
    async def _analyze_rollback_patterns(self) -> Optional[MetaLearningInsight]:
        """Analyze rollback patterns for insights"""
        if len(self.session_metadata) < 5:
            return None
        
        recent_sessions = self.session_metadata[-10:]
        rollback_rates = [s.rollback_count / max(s.fix_attempts, 1) for s in recent_sessions]
        avg_rollback_rate = statistics.mean(rollback_rates)
        
        if avg_rollback_rate > 0.3:
            return MetaLearningInsight(
                insight_type="high_rollback_rate",
                description=f"High rollback rate detected ({avg_rollback_rate:.1%})",
                confidence=0.8,
                recommendation="Consider reducing learning rate or improving fix validation",
                evidence={"avg_rollback_rate": avg_rollback_rate, "sessions_analyzed": len(recent_sessions)},
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    async def _analyze_learning_rate_effectiveness(self) -> Optional[MetaLearningInsight]:
        """Analyze learning rate effectiveness"""
        if len(self.session_metadata) < 5:
            return None
        
        # Group sessions by learning rate ranges
        low_rate_sessions = [s for s in self.session_metadata if s.learning_rate < 0.1]
        high_rate_sessions = [s for s in self.session_metadata if s.learning_rate > 0.3]
        
        if len(low_rate_sessions) >= 3 and len(high_rate_sessions) >= 3:
            low_rate_avg_score = statistics.mean([s.net_score for s in low_rate_sessions])
            high_rate_avg_score = statistics.mean([s.net_score for s in high_rate_sessions])
            
            if high_rate_avg_score > low_rate_avg_score * 1.2:
                return MetaLearningInsight(
                    insight_type="learning_rate_effectiveness",
                    description="Higher learning rates show better performance",
                    confidence=0.7,
                    recommendation="Consider increasing learning rate for better performance",
                    evidence={
                        "low_rate_avg": low_rate_avg_score,
                        "high_rate_avg": high_rate_avg_score,
                        "improvement": (high_rate_avg_score - low_rate_avg_score) / low_rate_avg_score
                    },
                    timestamp=datetime.now().isoformat()
                )
        
        return None
    
    async def _analyze_error_patterns(self) -> Optional[MetaLearningInsight]:
        """Analyze error type patterns"""
        if len(self.session_metadata) < 5:
            return None
        
        # Aggregate error types across recent sessions
        error_aggregate = {}
        for session in self.session_metadata[-10:]:
            for error_type, count in session.error_types.items():
                error_aggregate[error_type] = error_aggregate.get(error_type, 0) + count
        
        # Find most common error type
        if error_aggregate:
            most_common_error = max(error_aggregate.items(), key=lambda x: x[1])
            
            return MetaLearningInsight(
                insight_type="error_pattern",
                description=f"Most common error type: {most_common_error[0]} ({most_common_error[1]} occurrences)",
                confidence=0.6,
                recommendation=f"Focus learning efforts on {most_common_error[0]} error handling",
                evidence={"error_distribution": error_aggregate, "most_common": most_common_error},
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    async def _analyze_performance_trends(self) -> Optional[MetaLearningInsight]:
        """Analyze performance trends over time"""
        if len(self.performance_history) < 10:
            return None
        
        # Calculate trend
        recent_scores = [p["net_score"] for p in self.performance_history[-10:]]
        early_scores = [p["net_score"] for p in self.performance_history[:10]]
        
        recent_avg = statistics.mean(recent_scores)
        early_avg = statistics.mean(early_scores)
        
        improvement = (recent_avg - early_avg) / early_avg if early_avg != 0 else 0
        
        if improvement > 0.2:  # 20% improvement
            return MetaLearningInsight(
                insight_type="performance_improvement",
                description=f"Significant performance improvement detected ({improvement:.1%})",
                confidence=0.8,
                recommendation="Current learning strategy is effective, maintain approach",
                evidence={"improvement": improvement, "recent_avg": recent_avg, "early_avg": early_avg},
                timestamp=datetime.now().isoformat()
            )
        elif improvement < -0.2:  # 20% decline
            return MetaLearningInsight(
                insight_type="performance_decline",
                description=f"Performance decline detected ({improvement:.1%})",
                confidence=0.7,
                recommendation="Review and adjust learning strategy",
                evidence={"decline": abs(improvement), "recent_avg": recent_avg, "early_avg": early_avg},
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    async def _record_learning_event(self, event_type: MetaLearningEvent, data: Dict[str, Any]):
        """Record a meta-learning event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "data": data
        }
        
        self.learning_events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.learning_events) > 1000:
            self.learning_events = self.learning_events[-1000:]
    
    async def _save_meta_insights(self):
        """Save meta-learning insights to artifacts"""
        data = {
            "insights": [asdict(insight) for insight in self.meta_insights],
            "session_metadata": [asdict(session) for session in self.session_metadata[-50:]],  # Last 50 sessions
            "current_config": {
                "learning_rate": self.current_learning_rate,
                "strategy": self.current_strategy.value,
                "last_adaptation": self.last_adaptation.isoformat()
            },
            "performance_history": self.performance_history[-100:],  # Last 100 performance records
            "timestamp": datetime.now().isoformat()
        }
        
        insights_file = self.artifacts_path / "meta_learning_stats.json"
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Meta-learning insights saved to {insights_file}")
    
    def get_current_learning_config(self) -> Dict[str, Any]:
        """Get current learning configuration"""
        return {
            "learning_rate": self.current_learning_rate,
            "strategy": self.current_strategy.value,
            "last_adaptation": self.last_adaptation.isoformat(),
            "total_sessions": len(self.session_metadata),
            "total_insights": len(self.meta_insights)
        }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        if not self.session_metadata:
            return {"error": "No learning sessions recorded"}
        
        recent_sessions = self.session_metadata[-10:]
        
        return {
            "total_sessions": len(self.session_metadata),
            "recent_sessions": len(recent_sessions),
            "avg_net_score": statistics.mean([s.net_score for s in recent_sessions]),
            "avg_success_rate": statistics.mean([s.successful_fixes / max(s.fix_attempts, 1) for s in recent_sessions]),
            "avg_rollback_rate": statistics.mean([s.rollback_count / max(s.fix_attempts, 1) for s in recent_sessions]),
            "total_insights": len(self.meta_insights),
            "current_strategy": self.current_strategy.value,
            "current_learning_rate": self.current_learning_rate
        }
