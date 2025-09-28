"""
🧠 Tests for StillMe Unified Evolutionary Learning System
========================================================

Test suite cho unified evolutionary learning system.
Bao gồm:
- Unit tests cho core components
- Integration tests cho learning pipeline
- Performance tests cho daily training
- Assessment tests cho self-evaluation

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-27
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Import systems to test
from stillme_core.learning.evolutionary_learning_system import (
    EvolutionaryLearningSystem,
    EvolutionaryConfig,
    EvolutionStage,
    LearningMode,
    LearningMetrics,
    TrainingSession
)

from stillme_core.learning.learning_assessment_system import (
    LearningAssessmentSystem,
    AssessmentType,
    AssessmentCategory,
    AssessmentResult
)

class TestEvolutionaryLearningSystem:
    """Test cases for EvolutionaryLearningSystem"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return EvolutionaryConfig(
            learning_mode=LearningMode.EVOLUTIONARY,
            daily_training_minutes=15,
            assessment_frequency_hours=6,
            evolution_checkpoint_days=7
        )
    
    @pytest.fixture
    def system(self, config):
        """Test system instance"""
        with patch('stillme_core.learning.evolutionary_learning_system.ExperienceMemory') as mock_exp, \
             patch('stillme_core.learning.evolutionary_learning_system.LearningPipeline') as mock_pipeline, \
             patch('stillme_core.learning.evolutionary_learning_system.get_vector_store') as mock_vector, \
             patch('stillme_core.learning.evolutionary_learning_system.get_claims_store') as mock_claims:
            
            # Mock experience memory with empty experiences list
            mock_exp_instance = Mock()
            mock_exp_instance.experiences = []
            mock_exp.return_value = mock_exp_instance
            
            # Mock pipeline
            mock_pipeline_instance = Mock()
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Mock stores
            mock_vector.return_value = Mock()
            mock_claims.return_value = Mock()
            
            return EvolutionaryLearningSystem(config)
    
    def test_system_initialization(self, system):
        """Test system initialization"""
        assert system.config.learning_mode == LearningMode.EVOLUTIONARY
        assert system.current_stage == EvolutionStage.INFANT
        assert system.learning_metrics.accuracy == 0.0
        assert len(system.training_sessions) == 0
    
    def test_evolution_stage_determination(self, system):
        """Test evolution stage determination"""
        # Test infant stage (0-7 days)
        system._calculate_system_age = Mock(return_value=3)
        stage = system._determine_evolution_stage(3)
        assert stage == EvolutionStage.INFANT
        
        # Test child stage (8-30 days)
        stage = system._determine_evolution_stage(15)
        assert stage == EvolutionStage.CHILD
        
        # Test adolescent stage (31-90 days)
        stage = system._determine_evolution_stage(60)
        assert stage == EvolutionStage.ADOLESCENT
        
        # Test adult stage (90+ days)
        stage = system._determine_evolution_stage(120)
        assert stage == EvolutionStage.ADULT
    
    @pytest.mark.asyncio
    async def test_daily_learning_session(self, system):
        """Test daily learning session"""
        # Mock the internal methods
        system._review_yesterday_experiences = AsyncMock(return_value=[])
        system._learn_from_new_content = AsyncMock(return_value=[])
        system._perform_self_assessment = AsyncMock(return_value={
            'gaps': ['knowledge_gap_1'],
            'overall_score': 0.7
        })
        system._conduct_targeted_training = AsyncMock(return_value={
            'exercises_completed': 3,
            'skills_improved': ['knowledge_gap_1']
        })
        system._evaluate_performance = AsyncMock(return_value={
            'accuracy_improvement': 0.05
        })
        system._plan_next_session = AsyncMock(return_value={
            'focus_areas': ['accuracy_improvement']
        })
        system._save_training_session = AsyncMock()
        
        # Run daily learning session
        session = await system.daily_learning_session()
        
        # Verify session
        assert isinstance(session, TrainingSession)
        assert session.mode == LearningMode.EVOLUTIONARY
        assert session.exercises_completed == 3
        assert session.accuracy_improvement == 0.05
        assert len(session.knowledge_gaps_identified) == 1
        
        # Verify methods were called
        system._review_yesterday_experiences.assert_called_once()
        system._learn_from_new_content.assert_called_once()
        system._perform_self_assessment.assert_called_once()
        system._conduct_targeted_training.assert_called_once()
        system._evaluate_performance.assert_called_once()
        system._plan_next_session.assert_called_once()
        system._save_training_session.assert_called_once()
    
    def test_learning_status(self, system):
        """Test learning status retrieval"""
        status = system.get_learning_status()
        
        assert 'current_stage' in status
        assert 'evolution_progress' in status
        assert 'learning_metrics' in status
        assert 'recent_sessions' in status
        assert 'overall_score' in status
        assert 'system_age_days' in status
        
        assert status['current_stage'] == EvolutionStage.INFANT.value
        assert status['recent_sessions'] == 0
    
    @pytest.mark.asyncio
    async def test_evolution_to_next_stage(self, system):
        """Test evolution to next stage"""
        # Mock high progress
        system._calculate_evolution_progress = Mock(return_value=0.9)
        system._get_next_evolution_stage = Mock(return_value=EvolutionStage.CHILD)
        system._update_config_for_stage = Mock()
        
        # Test evolution
        success = await system.evolve_to_next_stage()
        
        assert success is True
        assert system.current_stage == EvolutionStage.CHILD
        system._update_config_for_stage.assert_called_once_with(EvolutionStage.CHILD)
    
    def test_emergency_learning_reset(self, system):
        """Test emergency learning reset"""
        # Add some data
        system.performance_history.append({'test': 'data'})
        system.training_sessions.append(Mock())
        system.knowledge_base['test'] = 'data'
        
        # Reset
        asyncio.run(system.emergency_learning_reset())
        
        # Verify reset
        assert system.current_stage == EvolutionStage.INFANT
        assert len(system.performance_history) == 0
        assert len(system.training_sessions) == 0
        assert len(system.knowledge_base) == 0


class TestLearningAssessmentSystem:
    """Test cases for LearningAssessmentSystem"""
    
    @pytest.fixture
    def assessment_system(self):
        """Test assessment system instance"""
        return LearningAssessmentSystem()
    
    def test_assessment_system_initialization(self, assessment_system):
        """Test assessment system initialization"""
        assert assessment_system.current_parameters['learning_rate'] == 0.1
        assert assessment_system.current_parameters['confidence_threshold'] == 0.7
        assert len(assessment_system.assessment_history) == 0
        assert len(assessment_system.learning_curves) == 0
    
    def test_question_generation(self, assessment_system):
        """Test question generation"""
        # Test knowledge questions
        questions = assessment_system._generate_knowledge_questions(3)
        assert len(questions) == 3
        assert all('question' in q for q in questions)
        assert all('options' in q for q in questions)
        assert all('correct_answer' in q for q in questions)
        
        # Test reasoning questions
        questions = assessment_system._generate_reasoning_questions(2)
        assert len(questions) == 2
        
        # Test creativity questions
        questions = assessment_system._generate_creativity_questions(2)
        assert len(questions) == 2
        assert all(q.get('type') == 'open_ended' for q in questions)
    
    @pytest.mark.asyncio
    async def test_assessment_execution(self, assessment_system):
        """Test assessment execution"""
        # Mock question generation
        assessment_system._generate_questions = Mock(return_value=[
            {
                'id': 'test_1',
                'question': 'Test question?',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 0,
                'difficulty': 'easy',
                'category': 'test'
            }
        ])
        
        # Mock answer simulation
        assessment_system._simulate_answer = AsyncMock(return_value=0)
        assessment_system._save_assessment_result = AsyncMock()
        
        # Run assessment
        result = await assessment_system.run_assessment(
            AssessmentType.QUICK,
            AssessmentCategory.KNOWLEDGE
        )
        
        # Verify result
        assert isinstance(result, AssessmentResult)
        assert result.assessment_type == AssessmentType.QUICK
        assert result.category == AssessmentCategory.KNOWLEDGE
        assert result.questions_answered == 1
        assert result.score >= 0.0
        assert result.score <= 1.0
    
    def test_score_calculation(self, assessment_system):
        """Test score calculation"""
        # Test perfect score
        results = {
            'questions': [{'id': '1'}, {'id': '2'}, {'id': '3'}],
            'correct_count': 3
        }
        score = assessment_system._calculate_score(results)
        assert score == 1.0
        
        # Test partial score
        results['correct_count'] = 2
        score = assessment_system._calculate_score(results)
        assert score == 2/3
        
        # Test zero score
        results['correct_count'] = 0
        score = assessment_system._calculate_score(results)
        assert score == 0.0
    
    def test_learning_curve_calculation(self, assessment_system):
        """Test learning curve calculation"""
        # Test trend calculation
        scores = [0.5, 0.6, 0.7, 0.8]
        trend = assessment_system._calculate_trend(scores)
        assert trend == "improving"
        
        scores = [0.8, 0.7, 0.6, 0.5]
        trend = assessment_system._calculate_trend(scores)
        assert trend == "declining"
        
        scores = [0.6, 0.6, 0.6, 0.6]
        trend = assessment_system._calculate_trend(scores)
        assert trend == "stable"
    
    def test_parameter_optimization(self, assessment_system):
        """Test parameter optimization"""
        # Mock performance data
        assessment_system._get_parameter_performance_data = Mock(return_value=[
            {'value': 0.1, 'performance': 0.6},
            {'value': 0.3, 'performance': 0.7},
            {'value': 0.5, 'performance': 0.8},
            {'value': 0.7, 'performance': 0.75},
            {'value': 0.9, 'performance': 0.7}
        ])
        
        # Test optimization
        optimizations = asyncio.run(assessment_system.optimize_parameters())
        
        # Should have some optimizations
        assert isinstance(optimizations, list)
        # Note: Actual optimizations depend on correlation analysis
    
    def test_assessment_summary(self, assessment_system):
        """Test assessment summary"""
        # Add some mock assessment results
        mock_result = AssessmentResult(
            assessment_id="test_1",
            timestamp=time.time(),
            assessment_type=AssessmentType.QUICK,
            category=AssessmentCategory.KNOWLEDGE,
            score=0.8,
            max_possible_score=5,
            questions_answered=5,
            correct_answers=4,
            time_taken_seconds=30,
            detailed_results={},
            recommendations=[],
            improvement_areas=[]
        )
        assessment_system.assessment_history.append(mock_result)
        
        # Get summary
        summary = assessment_system.get_assessment_summary()
        
        assert 'total_assessments' in summary
        assert 'average_score' in summary
        assert 'best_score' in summary
        assert 'worst_score' in summary
        assert summary['total_assessments'] == 1
        assert summary['average_score'] == 0.8


class TestIntegration:
    """Integration tests for unified learning system"""
    
    @pytest.mark.asyncio
    async def test_daily_training_workflow(self):
        """Test complete daily training workflow"""
        with patch('stillme_core.learning.evolutionary_learning_system.ExperienceMemory') as mock_exp, \
             patch('stillme_core.learning.evolutionary_learning_system.LearningPipeline') as mock_pipeline, \
             patch('stillme_core.learning.evolutionary_learning_system.get_vector_store') as mock_vector, \
             patch('stillme_core.learning.evolutionary_learning_system.get_claims_store') as mock_claims:
            
            # Mock experience memory with empty experiences list
            mock_exp_instance = Mock()
            mock_exp_instance.experiences = []
            mock_exp.return_value = mock_exp_instance
            
            # Mock pipeline
            mock_pipeline_instance = Mock()
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Mock stores
            mock_vector.return_value = Mock()
            mock_claims.return_value = Mock()
            
            # Initialize systems
            config = EvolutionaryConfig()
            learning_system = EvolutionaryLearningSystem(config)
            assessment_system = LearningAssessmentSystem()
            
            # Mock methods
            learning_system._review_yesterday_experiences = AsyncMock(return_value=[])
            learning_system._learn_from_new_content = AsyncMock(return_value=[])
            learning_system._perform_self_assessment = AsyncMock(return_value={
                'gaps': ['knowledge_gap_1'],
                'overall_score': 0.7
            })
            learning_system._conduct_targeted_training = AsyncMock(return_value={
                'exercises_completed': 3,
                'skills_improved': ['knowledge_gap_1']
            })
            learning_system._evaluate_performance = AsyncMock(return_value={
                'accuracy_improvement': 0.05
            })
            learning_system._plan_next_session = AsyncMock(return_value={
                'focus_areas': ['accuracy_improvement']
            })
            learning_system._save_training_session = AsyncMock()
            
            # Run daily training
            session = await learning_system.daily_learning_session()
            
            # Run assessment
            assessment = await assessment_system.run_assessment(
                AssessmentType.QUICK,
                AssessmentCategory.KNOWLEDGE
            )
            
            # Verify both completed successfully
            assert isinstance(session, TrainingSession)
            assert isinstance(assessment, AssessmentResult)
    
    @pytest.mark.asyncio
    async def test_evolution_workflow(self):
        """Test evolution workflow"""
        with patch('stillme_core.learning.evolutionary_learning_system.ExperienceMemory') as mock_exp, \
             patch('stillme_core.learning.evolutionary_learning_system.LearningPipeline') as mock_pipeline, \
             patch('stillme_core.learning.evolutionary_learning_system.get_vector_store') as mock_vector, \
             patch('stillme_core.learning.evolutionary_learning_system.get_claims_store') as mock_claims:
            
            # Mock experience memory with empty experiences list
            mock_exp_instance = Mock()
            mock_exp_instance.experiences = []
            mock_exp.return_value = mock_exp_instance
            
            # Mock pipeline
            mock_pipeline_instance = Mock()
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Mock stores
            mock_vector.return_value = Mock()
            mock_claims.return_value = Mock()
            
            config = EvolutionaryConfig()
            system = EvolutionaryLearningSystem(config)
            
            # Mock high progress
            system._calculate_evolution_progress = Mock(return_value=0.9)
            system._get_next_evolution_stage = Mock(return_value=EvolutionStage.CHILD)
            system._update_config_for_stage = Mock()
            
            # Test evolution
            success = await system.evolve_to_next_stage()
            
            assert success is True
            assert system.current_stage == EvolutionStage.CHILD


class TestPerformance:
    """Performance tests for unified learning system"""
    
    @pytest.mark.asyncio
    async def test_daily_training_performance(self):
        """Test daily training performance"""
        with patch('stillme_core.learning.evolutionary_learning_system.ExperienceMemory') as mock_exp, \
             patch('stillme_core.learning.evolutionary_learning_system.LearningPipeline') as mock_pipeline, \
             patch('stillme_core.learning.evolutionary_learning_system.get_vector_store') as mock_vector, \
             patch('stillme_core.learning.evolutionary_learning_system.get_claims_store') as mock_claims:
            
            # Mock experience memory with empty experiences list
            mock_exp_instance = Mock()
            mock_exp_instance.experiences = []
            mock_exp.return_value = mock_exp_instance
            
            # Mock pipeline
            mock_pipeline_instance = Mock()
            mock_pipeline.return_value = mock_pipeline_instance
            
            # Mock stores
            mock_vector.return_value = Mock()
            mock_claims.return_value = Mock()
            
            config = EvolutionaryConfig(daily_training_minutes=5)  # Short training
            system = EvolutionaryLearningSystem(config)
            
            # Mock all methods to return quickly
            system._review_yesterday_experiences = AsyncMock(return_value=[])
            system._learn_from_new_content = AsyncMock(return_value=[])
            system._perform_self_assessment = AsyncMock(return_value={'gaps': [], 'overall_score': 0.7})
            system._conduct_targeted_training = AsyncMock(return_value={'exercises_completed': 1})
            system._evaluate_performance = AsyncMock(return_value={'accuracy_improvement': 0.01})
            system._plan_next_session = AsyncMock(return_value={'focus_areas': []})
            system._save_training_session = AsyncMock()
            
            # Measure performance
            start_time = time.time()
            session = await system.daily_learning_session()
            end_time = time.time()
            
            # Should complete within reasonable time (less than 1 second for mocked version)
            assert (end_time - start_time) < 1.0
            assert isinstance(session, TrainingSession)
    
    @pytest.mark.asyncio
    async def test_assessment_performance(self):
        """Test assessment performance"""
        assessment_system = LearningAssessmentSystem()
        
        # Mock question generation
        assessment_system._generate_questions = Mock(return_value=[
            {
                'id': f'test_{i}',
                'question': f'Test question {i}?',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 0,
                'difficulty': 'easy',
                'category': 'test'
            }
            for i in range(10)
        ])
        
        # Mock answer simulation
        assessment_system._simulate_answer = AsyncMock(return_value=0)
        assessment_system._save_assessment_result = AsyncMock()
        
        # Measure performance
        start_time = time.time()
        result = await assessment_system.run_assessment(
            AssessmentType.STANDARD,
            AssessmentCategory.KNOWLEDGE
        )
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 2.0
        assert isinstance(result, AssessmentResult)


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test markers
pytestmark = [
    pytest.mark.unified_learning,
    pytest.mark.evolutionary_system,
    pytest.mark.learning_assessment
]
