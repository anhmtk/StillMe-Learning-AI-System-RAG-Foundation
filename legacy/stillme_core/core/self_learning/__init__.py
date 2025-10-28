# stillme_core/self_learning/__init__.py
"""
Self-Learning Mechanism for AgentDev
"""

from .experience_memory import Experience, ExperienceMemory, LearningPattern

try:
    from .optimization_engine import OptimizationEngine, OptimizationResult
except ImportError:
    pass

try:
    from .knowledge_sharing import KnowledgeArticle, KnowledgeSharing
except ImportError:
    pass

__all__ = [
    "ExperienceMemory",
    "Experience",
    "LearningPattern",
    "OptimizationEngine",
    "OptimizationResult",
    "KnowledgeSharing",
    "KnowledgeArticle",
]
