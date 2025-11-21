"""
StillMe Style Engine

Provides unified style and depth management based on StillMe Style Spec v1.
"""

from .style_engine import (
    DepthLevel,
    DomainType,
    get_depth_target_for_question,
    get_domain_template,
    evaluate_depth,
    build_domain_structure_guidance
)

__all__ = [
    "DepthLevel",
    "DomainType",
    "get_depth_target_for_question",
    "get_domain_template",
    "evaluate_depth",
    "build_domain_structure_guidance"
]

