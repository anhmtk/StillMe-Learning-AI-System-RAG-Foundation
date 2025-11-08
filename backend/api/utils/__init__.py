"""
API Utilities for StillMe
Shared helper functions and utilities
"""

from .chat_helpers import (
    generate_ai_response,
    detect_language,
    build_system_prompt_with_language,
    call_deepseek_api,
    call_openai_api
)

__all__ = [
    "generate_ai_response",
    "detect_language",
    "build_system_prompt_with_language",
    "call_deepseek_api",
    "call_openai_api"
]

