"""
StillMe Identity Module
Injects StillMe identity and persona into prompts
"""

from .injector import inject_identity, STILLME_IDENTITY
from .prompt_builder import (
    UnifiedPromptBuilder,
    PromptContext,
    FPSResult,
    InstructionType,
    InstructionPriority
)

__all__ = [
    "inject_identity",
    "STILLME_IDENTITY",
    "UnifiedPromptBuilder",
    "PromptContext",
    "FPSResult",
    "InstructionType",
    "InstructionPriority"
]

