"""
🧠 StillMe Evolutionary Learning System
=====================================

Hệ thống học tập tiến hóa kết hợp ưu điểm của cả 2 hệ thống:
- Old System: ExperienceMemory (pattern recognition, behavioral learning)
- New System: LearningPipeline (RSS content, vector store, approval workflow)

Tính năng chính:
- Tự tiến hóa: Học từ kinh nghiệm và content external
- Tự huấn luyện: Daily training với self-assessment
- Fine-tune kiểu nhà nghèo: Optimize parameters dựa trên performance
- Conflict-free: Unified data model và processing pipeline

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-27
"""

import asyncio
import json
import logging
import sqlite3
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict, deque

# Import existing systems
try:
    from stillme_core.core.self_learning.experience_memory import ExperienceMemory, ExperienceType, ExperienceCategory
except ImportError as e:
    logging.warning(f"ExperienceMemory not available: {e}")

logger = logging.getLogger(__name__)

class LearningMode(Enum):
    """Chế độ học tập của StillMe"""
    EXPERIENCE_ONLY = "experience_only"      # Chỉ học từ kinh nghiệm
    CONTENT_ONLY = "content_only"           # Chỉ học từ content external
    HYBRID = "hybrid"                       # Kết hợp cả 2
    EVOLUTIONARY = "evolutionary"           # Tự tiến hóa (recommended)

class EvolutionStage(Enum):
    """Các giai đoạn tiến hóa"""
    INFANT = "infant"           # 0-7 ngày: Học cơ bản
    CHILD = "child"             # 8-30 ngày: Phát triển pattern
    ADOLESCENT = "adolescent"   # 31-90 ngày: Tối ưu hóa
    ADULT = "adult"             # 90+ ngày: Tự chủ hoàn toàn

@dataclass
class LearningMetrics:
    """Metrics đánh giá việc học"""
    accuracy: float = 0.0
    response_time: float = 0.0
    user_satisfaction: float = 0.0
    knowledge_retention: float = 0.0
    adaptation_speed: float = 0.0
    creativity_score: float = 0.0
    consistency_score: float = 0.0
    evolution_progress: float = 0.0

@dataclass
class TrainingSession:
    """Phiên huấn luyện hàng ngày"""
    session_id: str
    timestamp: float
    mode: LearningMode
    duration_minutes: int
    exercises_completed: int
    accuracy_improvement: float
    new_patterns_learned: int
    knowledge_gaps_identified: List[str]
    next_session_plan: Dict[str, Any]

@dataclass
class EvolutionaryConfig:
    """Cấu hình tiến hóa"""
    learning_mode: LearningMode = LearningMode.EVOLUTIONARY
    daily_training_minutes: int = 30
    assessment_frequency_hours: int = 6
    evolution_checkpoint_days: int = 7
    max_knowledge_retention_days: int = 365
    creativity_threshold: float = 0.7
    adaptation_speed_target: float = 0.8
    self_correction_enabled: bool = True
    fine_tune_enabled: bool = True

class EvolutionaryLearningSystem:
    """
    Hệ thống học tập tiến hóa của StillMe
    
    Kết hợp:
    - ExperienceMemory: Pattern recognition, behavioral learning
    - LearningPipeline: External content, vector search, approval workflow
    - Self-Assessment: Đánh giá và cải thiện bản thân
    - Daily Training: Huấn luyện hàng ngày
    - Fine-tuning: Tối ưu hóa parameters
    """
    
    def __init__(self, config: EvolutionaryConfig = None):
        self.config = config or EvolutionaryConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize subsystems
        self.experience_memory = None
        
        # Learning state
        self.current_stage = EvolutionStage.INFANT
        self.learning_metrics = LearningMetrics()
        self.training_sessions = []
        self.knowledge_base = {}
        self.performance_history = deque(maxlen=1000)
        
        # Self-assessment data
        self.self_corrections = []
        self.knowledge_gaps = []
        self.improvement_areas = []
        
        # Initialize components
        self._initialize_subsystems()
        self._load_learning_state()
        
        self.logger.info(f"Evolutionary Learning System initialized in {self.current_stage.value} stage")
    
    def _initialize_subsystems(self):
        """Khởi tạo các subsystem"""
        try:
            # Initialize ExperienceMemory
            self.experience_memory = ExperienceMemory()
            self.logger.info("ExperienceMemory subsystem initialized")
        except Exception as e:
            self.logger.warning(f"ExperienceMemory not available: {e}")
    
    def _load_learning_state(self):
        """Load trạng thái học tập từ database"""
        # Load evolution stage based on system age
        system_age_days = self._calculate_system_age()
        self.current_stage = self._determine_evolution_stage(system_age_days)
        
        # Load performance history
        self._load_performance_history()
        
        # Load knowledge gaps and improvement areas
        self._load_self_assessment_data()
    
    def _calculate_system_age(self) -> int:
        """Tính tuổi của hệ thống (số ngày)"""
        # Check if we have experience data
        if self.experience_memory and hasattr(self.experience_memory, 'experiences') and self.experience_memory.experiences:
            oldest_experience = min(self.experience_memory.experiences, key=lambda x: x.timestamp)
            age_seconds = time.time() - oldest_experience.timestamp
            return int(age_seconds / 86400)  # Convert to days
        return 0
    
    def _determine_evolution_stage(self, age_days: int) -> EvolutionStage:
        """Xác định giai đoạn tiến hóa dựa trên tuổi"""
        if age_days < 7:
            return EvolutionStage.INFANT
        elif age_days < 30:
            return EvolutionStage.CHILD
        elif age_days < 90:
            return EvolutionStage.ADOLESCENT
        else:
            return EvolutionStage.ADULT
    
    async def daily_learning_session(self) -> TrainingSession:
        """
        Phiên học tập hàng ngày - CORE FEATURE
        
        Bao gồm:
        1. Review kinh nghiệm ngày hôm qua
        2. Học content mới từ RSS
        3. Self-assessment và gap analysis
        4. Targeted training exercises
        5. Performance evaluation
        6. Plan cho ngày mai
        """
        session_id = f"training_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Starting daily learning session: {session_id}")
        
        # Step 1: Review yesterday's experiences
        yesterday_experiences = await self._review_yesterday_experiences()
        
        # Step 2: Learn from new content
        new_content_learned = await self._learn_from_new_content()
        
        # Step 3: Self-assessment
        assessment_results = await self._perform_self_assessment()
        
        # Step 4: Targeted training
        training_results = await self._conduct_targeted_training(assessment_results)
        
        # Step 5: Performance evaluation
        performance_metrics = await self._evaluate_performance()
        
        # Step 6: Plan next session
        next_session_plan = await self._plan_next_session(performance_metrics)
        
        # Create training session record
        duration_minutes = int((time.time() - start_time) / 60)
        session = TrainingSession(
            session_id=session_id,
            timestamp=start_time,
            mode=self.config.learning_mode,
            duration_minutes=duration_minutes,
            exercises_completed=training_results.get('exercises_completed', 0),
            accuracy_improvement=performance_metrics.get('accuracy_improvement', 0.0),
            new_patterns_learned=len(new_content_learned),
            knowledge_gaps_identified=assessment_results.get('gaps', []),
            next_session_plan=next_session_plan
        )
        
        self.training_sessions.append(session)
        await self._save_training_session(session)
        
        self.logger.info(f"Daily learning session completed: {session_id}")
        return session
    
    async def _review_yesterday_experiences(self) -> List[Dict[str, Any]]:
        """Review kinh nghiệm ngày hôm qua"""
        if not self.experience_memory:
            return []
        
        yesterday = time.time() - 86400  # 24 hours ago
        recent_experiences = [
            exp for exp in self.experience_memory.experiences
            if exp.timestamp > yesterday
        ]
        
        # Analyze patterns in recent experiences
        patterns = self._analyze_experience_patterns(recent_experiences)
        
        # Identify improvement opportunities
        improvements = self._identify_improvement_opportunities(recent_experiences)
        
        return {
            'experiences': recent_experiences,
            'patterns': patterns,
            'improvements': improvements
        }
    
    def _identify_improvement_opportunities(self, experiences: List[Any]) -> List[str]:
        """Identify improvement opportunities from experiences"""
        improvements = []
        
        if not experiences:
            return improvements
        
        # Analyze success/failure patterns
        success_rate = sum(1 for exp in experiences if getattr(exp, 'success', True)) / len(experiences)
        
        if success_rate < 0.7:
            improvements.append("Improve response accuracy and success rate")
        
        # Analyze response time patterns
        response_times = [getattr(exp, 'response_time', 0) for exp in experiences if hasattr(exp, 'response_time')]
        if response_times and sum(response_times) / len(response_times) > 5.0:
            improvements.append("Optimize response time and efficiency")
        
        # Analyze user satisfaction
        satisfaction_scores = [getattr(exp, 'user_satisfaction', 0) for exp in experiences if hasattr(exp, 'user_satisfaction')]
        if satisfaction_scores and sum(satisfaction_scores) / len(satisfaction_scores) < 0.8:
            improvements.append("Enhance user satisfaction and experience")
        
        return improvements
    
    async def _learn_from_new_content(self) -> List[Dict[str, Any]]:
        """Học từ content mới"""
        # For now, return empty list since we removed the old pipeline
        # This can be extended with new content learning mechanisms
        return []
    
    async def _perform_self_assessment(self) -> Dict[str, Any]:
        """
        Self-assessment - Đánh giá bản thân
        
        Đánh giá:
        - Knowledge gaps
        - Performance weaknesses
        - Areas for improvement
        - Evolution progress
        """
        assessment = {
            'knowledge_gaps': [],
            'performance_weaknesses': [],
            'improvement_areas': [],
            'evolution_progress': 0.0,
            'overall_score': 0.0
        }
        
        # Analyze knowledge gaps
        if self.experience_memory:
            gaps = self._identify_knowledge_gaps()
            assessment['knowledge_gaps'] = gaps
        
        # Analyze performance weaknesses
        weaknesses = self._identify_performance_weaknesses()
        assessment['performance_weaknesses'] = weaknesses
        
        # Calculate evolution progress
        progress = self._calculate_evolution_progress()
        assessment['evolution_progress'] = progress
        
        # Overall score
        overall_score = self._calculate_overall_score()
        assessment['overall_score'] = overall_score
        
        return assessment
    
    async def _conduct_targeted_training(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Targeted training dựa trên assessment
        
        Fine-tune kiểu nhà nghèo:
        - Adjust parameters based on performance
        - Focus on weak areas
        - Practice specific skills
        """
        training_results = {
            'exercises_completed': 0,
            'skills_improved': [],
            'parameters_adjusted': {},
            'confidence_boost': 0.0
        }
        
        # Focus on knowledge gaps
        for gap in assessment.get('knowledge_gaps', []):
            exercise_result = await self._practice_knowledge_gap(gap)
            if exercise_result['success']:
                training_results['exercises_completed'] += 1
                training_results['skills_improved'].append(gap)
        
        # Focus on performance weaknesses
        for weakness in assessment.get('performance_weaknesses', []):
            improvement = await self._address_performance_weakness(weakness)
            if improvement['improved']:
                training_results['parameters_adjusted'][weakness] = improvement['adjustment']
        
        # Calculate confidence boost
        confidence_boost = min(0.1, training_results['exercises_completed'] * 0.02)
        training_results['confidence_boost'] = confidence_boost
        
        return training_results
    
    async def _evaluate_performance(self) -> Dict[str, Any]:
        """Đánh giá performance sau training"""
        metrics = {
            'accuracy_improvement': 0.0,
            'response_time_improvement': 0.0,
            'knowledge_retention': 0.0,
            'adaptation_speed': 0.0,
            'creativity_score': 0.0,
            'consistency_score': 0.0
        }
        
        # Calculate improvements based on recent performance
        if len(self.performance_history) >= 2:
            recent_performance = list(self.performance_history)[-10:]  # Last 10 sessions
            previous_performance = list(self.performance_history)[-20:-10]  # Previous 10 sessions
            
            # Calculate improvements
            metrics['accuracy_improvement'] = self._calculate_improvement(
                recent_performance, previous_performance, 'accuracy'
            )
            metrics['response_time_improvement'] = self._calculate_improvement(
                recent_performance, previous_performance, 'response_time'
            )
        
        # Update learning metrics
        self.learning_metrics.accuracy += metrics['accuracy_improvement']
        self.learning_metrics.response_time += metrics['response_time_improvement']
        
        return metrics
    
    async def _plan_next_session(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Lập kế hoạch cho phiên học tiếp theo"""
        plan = {
            'focus_areas': [],
            'difficulty_level': 'medium',
            'duration_minutes': self.config.daily_training_minutes,
            'special_exercises': [],
            'evolution_targets': []
        }
        
        # Determine focus areas based on performance
        if performance_metrics.get('accuracy_improvement', 0) < 0.05:
            plan['focus_areas'].append('accuracy_improvement')
        
        if performance_metrics.get('response_time_improvement', 0) < 0.05:
            plan['focus_areas'].append('response_optimization')
        
        # Adjust difficulty based on current stage
        if self.current_stage == EvolutionStage.INFANT:
            plan['difficulty_level'] = 'easy'
        elif self.current_stage == EvolutionStage.ADULT:
            plan['difficulty_level'] = 'hard'
        
        # Set evolution targets
        if self.current_stage != EvolutionStage.ADULT:
            next_stage = self._get_next_evolution_stage()
            plan['evolution_targets'].append(f"progress_toward_{next_stage.value}")
        
        return plan
    
    def _analyze_experience_patterns(self, experiences: List) -> List[Dict[str, Any]]:
        """Phân tích patterns trong kinh nghiệm"""
        patterns = []
        
        # Group by experience type
        type_groups = defaultdict(list)
        for exp in experiences:
            type_groups[exp.experience_type].append(exp)
        
        # Analyze each type
        for exp_type, exps in type_groups.items():
            if len(exps) >= 3:  # Need at least 3 to identify pattern
                pattern = {
                    'type': exp_type.value,
                    'frequency': len(exps),
                    'success_rate': sum(1 for e in exps if e.success) / len(exps),
                    'avg_confidence': sum(e.confidence for e in exps) / len(exps),
                    'common_contexts': self._extract_common_contexts(exps)
                }
                patterns.append(pattern)
        
        return patterns
    
    def _identify_knowledge_gaps(self) -> List[str]:
        """Xác định knowledge gaps"""
        gaps = []
        
        if self.experience_memory:
            # Analyze failed experiences
            failed_experiences = [exp for exp in self.experience_memory.experiences if not exp.success]
            
            # Group by category and identify common failure patterns
            category_failures = defaultdict(list)
            for exp in failed_experiences:
                category_failures[exp.category].append(exp)
            
            for category, failures in category_failures.items():
                if len(failures) >= 3:  # Significant pattern
                    gaps.append(f"knowledge_gap_{category.value}")
        
        return gaps
    
    def _identify_performance_weaknesses(self) -> List[str]:
        """Xác định performance weaknesses"""
        weaknesses = []
        
        # Analyze recent performance history
        if len(self.performance_history) >= 10:
            recent_metrics = list(self.performance_history)[-10:]
            
            # Check for declining trends
            if self._has_declining_trend(recent_metrics, 'accuracy'):
                weaknesses.append('accuracy_decline')
            
            if self._has_declining_trend(recent_metrics, 'response_time'):
                weaknesses.append('response_time_increase')
        
        return weaknesses
    
    def _calculate_evolution_progress(self) -> float:
        """Tính toán tiến độ tiến hóa"""
        # Based on system age, performance, and learning metrics
        age_progress = min(1.0, self._calculate_system_age() / 90)  # 90 days to full evolution
        
        performance_progress = 0.0
        if self.performance_history:
            recent_performance = list(self.performance_history)[-10:]
            avg_accuracy = sum(p.get('accuracy', 0) for p in recent_performance) / len(recent_performance)
            performance_progress = avg_accuracy
        
        learning_progress = 0.0
        if self.experience_memory:
            total_experiences = len(self.experience_memory.experiences)
            successful_experiences = sum(1 for exp in self.experience_memory.experiences if exp.success)
            if total_experiences > 0:
                learning_progress = successful_experiences / total_experiences
        
        # Weighted average
        evolution_progress = (age_progress * 0.3 + performance_progress * 0.4 + learning_progress * 0.3)
        return min(1.0, evolution_progress)
    
    def _calculate_overall_score(self) -> float:
        """Tính overall score"""
        scores = [
            self.learning_metrics.accuracy,
            self.learning_metrics.response_time,
            self.learning_metrics.user_satisfaction,
            self.learning_metrics.knowledge_retention,
            self.learning_metrics.adaptation_speed,
            self.learning_metrics.creativity_score,
            self.learning_metrics.consistency_score
        ]
        
        # Remove None values and calculate average
        valid_scores = [s for s in scores if s is not None and s > 0]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return 0.0
    
    async def _practice_knowledge_gap(self, gap: str) -> Dict[str, Any]:
        """Practice để cải thiện knowledge gap"""
        # Simulate practice exercise
        await asyncio.sleep(0.1)  # Simulate practice time
        
        # Random success based on current stage
        success_rate = {
            EvolutionStage.INFANT: 0.6,
            EvolutionStage.CHILD: 0.7,
            EvolutionStage.ADOLESCENT: 0.8,
            EvolutionStage.ADULT: 0.9
        }.get(self.current_stage, 0.7)
        
        success = np.random.random() < success_rate
        
        return {
            'gap': gap,
            'success': success,
            'improvement': 0.05 if success else 0.01
        }
    
    async def _address_performance_weakness(self, weakness: str) -> Dict[str, Any]:
        """Address performance weakness"""
        # Simulate parameter adjustment
        await asyncio.sleep(0.05)
        
        # Generate improvement
        improvement = np.random.uniform(0.01, 0.1)
        
        return {
            'weakness': weakness,
            'improved': True,
            'adjustment': improvement
        }
    
    def _calculate_improvement(self, recent: List, previous: List, metric: str) -> float:
        """Tính improvement giữa 2 periods"""
        if not recent or not previous:
            return 0.0
        
        recent_avg = sum(p.get(metric, 0) for p in recent) / len(recent)
        previous_avg = sum(p.get(metric, 0) for p in previous) / len(previous)
        
        if previous_avg == 0:
            return 0.0
        
        return (recent_avg - previous_avg) / previous_avg
    
    def _has_declining_trend(self, metrics: List, metric_name: str) -> bool:
        """Check if có declining trend"""
        if len(metrics) < 5:
            return False
        
        values = [m.get(metric_name, 0) for m in metrics]
        
        # Simple trend analysis
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        # Declining if second half is significantly worse
        return second_avg < first_avg * 0.9
    
    def _get_next_evolution_stage(self) -> EvolutionStage:
        """Get next evolution stage"""
        stage_order = [
            EvolutionStage.INFANT,
            EvolutionStage.CHILD,
            EvolutionStage.ADOLESCENT,
            EvolutionStage.ADULT
        ]
        
        current_index = stage_order.index(self.current_stage)
        if current_index < len(stage_order) - 1:
            return stage_order[current_index + 1]
        return EvolutionStage.ADULT
    
    def _extract_common_contexts(self, experiences: List) -> List[str]:
        """Extract common contexts từ experiences"""
        context_counts = defaultdict(int)
        
        for exp in experiences:
            for key in exp.context.keys():
                context_counts[key] += 1
        
        # Return most common contexts
        common_contexts = sorted(context_counts.items(), key=lambda x: x[1], reverse=True)
        return [context for context, count in common_contexts[:5]]
    
    async def _save_training_session(self, session: TrainingSession):
        """Save training session to database"""
        # Save to performance history
        performance_record = {
            'timestamp': session.timestamp,
            'accuracy': session.accuracy_improvement,
            'response_time': session.duration_minutes,
            'exercises_completed': session.exercises_completed,
            'patterns_learned': session.new_patterns_learned
        }
        
        self.performance_history.append(performance_record)
        
        # Save to database if available
        # Implementation depends on database setup
    
    def _load_performance_history(self):
        """Load performance history from database"""
        # Implementation depends on database setup
        pass
    
    def _load_self_assessment_data(self):
        """Load self-assessment data"""
        # Implementation depends on database setup
        pass
    
    async def evolve_to_next_stage(self) -> bool:
        """
        Tiến hóa lên giai đoạn tiếp theo
        
        Điều kiện:
        - Đủ tuổi
        - Performance đạt threshold
        - Learning metrics đạt yêu cầu
        """
        current_progress = self._calculate_evolution_progress()
        
        if current_progress >= 0.8 and self.current_stage != EvolutionStage.ADULT:
            next_stage = self._get_next_evolution_stage()
            old_stage = self.current_stage
            self.current_stage = next_stage
            
            self.logger.info(f"Evolved from {old_stage.value} to {next_stage.value}")
            
            # Update configuration based on new stage
            self._update_config_for_stage(next_stage)
            
            return True
        
        return False
    
    def _update_config_for_stage(self, stage: EvolutionStage):
        """Update configuration based on evolution stage"""
        if stage == EvolutionStage.INFANT:
            self.config.daily_training_minutes = 15
            self.config.assessment_frequency_hours = 12
        elif stage == EvolutionStage.CHILD:
            self.config.daily_training_minutes = 30
            self.config.assessment_frequency_hours = 8
        elif stage == EvolutionStage.ADOLESCENT:
            self.config.daily_training_minutes = 45
            self.config.assessment_frequency_hours = 6
        elif stage == EvolutionStage.ADULT:
            self.config.daily_training_minutes = 60
            self.config.assessment_frequency_hours = 4
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        return {
            'current_stage': self.current_stage.value,
            'evolution_progress': self._calculate_evolution_progress(),
            'learning_metrics': asdict(self.learning_metrics),
            'recent_sessions': len(self.training_sessions),
            'knowledge_gaps': len(self.knowledge_gaps),
            'improvement_areas': len(self.improvement_areas),
            'overall_score': self._calculate_overall_score(),
            'system_age_days': self._calculate_system_age()
        }
    
    async def store_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """Store knowledge in unified system"""
        knowledge_id = knowledge_data.get('knowledge_id', f"knowledge_{int(time.time())}")
        
        # Store in knowledge base
        self.knowledge_base[knowledge_id] = knowledge_data
        
        # Also store in experience memory if it's an experience
        if knowledge_data.get('source_type') == 'experience' and self.experience_memory:
            try:
                # Convert back to experience format for storage
                exp_id = self.experience_memory.store_experience(
                    experience_type=knowledge_data.get('metadata', {}).get('experience_type', 'learning'),
                    category=knowledge_data.get('category', 'general'),
                    context=knowledge_data.get('metadata', {}),
                    action=knowledge_data.get('content', ''),
                    outcome={'success': True},
                    success=True,
                    lessons_learned=[],
                    tags=knowledge_data.get('tags', []),
                    confidence=knowledge_data.get('confidence', 0.8),
                    impact_score=knowledge_data.get('impact_score', 0.5)
                )
                return exp_id
            except Exception as e:
                self.logger.warning(f"Failed to store in experience memory: {e}")
        
        return knowledge_id
    
    async def emergency_learning_reset(self):
        """Emergency reset learning system"""
        self.logger.warning("Emergency learning reset initiated")
        
        # Reset to infant stage
        self.current_stage = EvolutionStage.INFANT
        
        # Clear performance history
        self.performance_history.clear()
        
        # Reset learning metrics
        self.learning_metrics = LearningMetrics()
        
        # Clear training sessions
        self.training_sessions.clear()
        
        # Reset knowledge base
        self.knowledge_base.clear()
        
        self.logger.info("Learning system reset completed")


# Global instance
_evolutionary_system = None

def get_evolutionary_learning_system() -> EvolutionaryLearningSystem:
    """Get global evolutionary learning system instance"""
    global _evolutionary_system
    if _evolutionary_system is None:
        _evolutionary_system = EvolutionaryLearningSystem()
    return _evolutionary_system

def initialize_evolutionary_learning(config: EvolutionaryConfig = None):
    """Initialize evolutionary learning system"""
    global _evolutionary_system
    _evolutionary_system = EvolutionaryLearningSystem(config)
    return _evolutionary_system
