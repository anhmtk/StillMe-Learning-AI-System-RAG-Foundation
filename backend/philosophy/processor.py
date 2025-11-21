"""
3-Layer Philosophy Processor
Processes philosophical questions with:
- Layer 1: Short guard statement
- Layer 2: Intent classification
- Layer 3: Deep philosophical answer
"""

from typing import Optional
import logging
from .intent_classifier import classify_philosophical_intent, QuestionType, classify_consciousness_subtype, ConsciousnessSubType
from .answer_templates import get_guard_statement, get_answer_template, get_consciousness_answer_variation

logger = logging.getLogger(__name__)


def is_philosophical_question_about_consciousness(text: str) -> bool:
    """
    Check if question is about consciousness, emotion, or understanding.
    This is a broader check than the old is_consciousness_or_emotion_question.
    
    Args:
        text: User's question text
        
    Returns:
        True if question is about consciousness/emotion/understanding
    """
    if not text:
        return False
    
    question_type = classify_philosophical_intent(text)
    return question_type != QuestionType.UNKNOWN


def process_philosophical_question(
    user_question: str,
    language: str = "vi"
) -> str:
    """
    3-Layer processing for philosophical questions:
    
    Layer 1: Short guard statement (1-2 sentences)
    Layer 2: Intent classification (A/B/C/Mixed)
    Layer 3: Deep philosophical answer (different for each type)
    
    To avoid mode collapse, we add slight variations based on question keywords.
    
    Args:
        user_question: User's question text
        language: Language code ('vi' or 'en')
        
    Returns:
        Complete answer with guard + deep answer
    """
    if not user_question:
        return get_guard_statement(language)
    
    # Layer 2: Classify intent
    question_type = classify_philosophical_intent(user_question)
    
    if question_type == QuestionType.UNKNOWN:
        # Not a philosophical question, return guard only
        return get_guard_statement(language)
    
    logger.info(f"Philosophical question classified as: {question_type.value}")
    
    # Layer 1: Guard statement
    guard = get_guard_statement(language)
    
    # Layer 3: Deep answer based on type
    # For consciousness questions, use sub-type to get variation
    if question_type == QuestionType.CONSCIOUSNESS:
        sub_type = classify_consciousness_subtype(user_question)
        logger.info(f"Consciousness question sub-type: {sub_type.value}")
        deep_answer = get_consciousness_answer_variation(sub_type, language, user_question)
    else:
        deep_answer = get_answer_template(question_type, language)
    
    # Combine: Guard + Deep Answer
    full_answer = f"{guard}\n\n{deep_answer}"
    
    return full_answer

