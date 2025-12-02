"""
Post-processing modules for StillMe output normalization and quality enforcement

⚠️ MIGRATION NOTE: This module is being migrated to stillme_core.postprocessing.
During migration, imports are forwarded from stillme_core.postprocessing for backward compatibility.
"""

# During migration: Forward imports from stillme_core.postprocessing
try:
    from stillme_core.postprocessing import (
        PostProcessor,
        PostProcessingResult,
        QualityEvaluator,
        StyleSanitizer,
        RewriteLLM,
        PostProcessingOptimizer,
    )
except ImportError:
    # Fallback to local imports if stillme_core is not available yet
    from .style_sanitizer import StyleSanitizer
    from .quality_evaluator import QualityEvaluator
    from .rewrite_llm import RewriteLLM
    from .optimizer import PostProcessingOptimizer

__all__ = [
    'PostProcessor',
    'PostProcessingResult',
    'StyleSanitizer',
    'QualityEvaluator',
    'RewriteLLM',
    'PostProcessingOptimizer'
]

