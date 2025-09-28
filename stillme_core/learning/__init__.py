"""
StillMe Learning Module
Unified Evolutionary Learning System for AI self-improvement.
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Framework"

# Import unified evolutionary learning system
from .evolutionary_learning_system import (
    EvolutionaryLearningSystem,
    EvolutionaryConfig,
    EvolutionStage,
    LearningMode,
    LearningMetrics,
    TrainingSession,
    get_evolutionary_learning_system,
    initialize_evolutionary_learning
)

# Import learning assessment system
from .learning_assessment_system import (
    LearningAssessmentSystem,
    AssessmentType,
    AssessmentCategory,
    AssessmentResult,
    LearningCurve,
    ParameterOptimization,
    get_assessment_system,
    initialize_assessment_system
)

__all__ = [
    # Evolutionary Learning System
    'EvolutionaryLearningSystem',
    'EvolutionaryConfig',
    'EvolutionStage',
    'LearningMode',
    'LearningMetrics',
    'TrainingSession',
    'get_evolutionary_learning_system',
    'initialize_evolutionary_learning',
    
    # Learning Assessment System
    'LearningAssessmentSystem',
    'AssessmentType',
    'AssessmentCategory',
    'AssessmentResult',
    'LearningCurve',
    'ParameterOptimization',
    'get_assessment_system',
    'initialize_assessment_system'
]
