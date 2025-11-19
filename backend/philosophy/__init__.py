"""
Philosophy Module - Handles consciousness, emotion, and understanding questions
with 3-layer processing to avoid mode collapse.
"""

from .intent_classifier import classify_philosophical_intent, QuestionType
from .answer_templates import get_answer_template
from .processor import process_philosophical_question

__all__ = [
    "classify_philosophical_intent",
    "QuestionType",
    "get_answer_template",
    "process_philosophical_question",
]

