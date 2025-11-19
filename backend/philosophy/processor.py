"""
3-Layer Philosophy Processor
Processes philosophical questions with:
- Layer 1: Short guard statement
- Layer 2: Intent classification
- Layer 3: Deep philosophical answer
"""

from typing import Optional
import logging
from .intent_classifier import classify_philosophical_intent, QuestionType
from .answer_templates import get_guard_statement, get_answer_template

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
    deep_answer = get_answer_template(question_type, language)
    
    # Add slight variation to avoid mode collapse within same type
    # This is a simple approach - can be enhanced later
    import hashlib
    question_hash = int(hashlib.md5(user_question.encode()).hexdigest()[:8], 16)
    
    # Add contextual opening based on question (to make answers feel more personalized)
    # But keep core template the same to maintain philosophical rigor
    contextual_opening = ""
    if question_type == QuestionType.CONSCIOUSNESS:
        if "tồn tại" in user_question.lower() or "exist" in user_question.lower():
            contextual_opening = "Câu hỏi về sự tồn tại và ý thức là một trong những câu hỏi triết học sâu sắc nhất.\n\n"
        elif "ai" in user_question.lower() and "trả lời" in user_question.lower():
            contextual_opening = "Đây là một câu hỏi về bản chất của 'người nói' trong hệ thống AI.\n\n"
    elif question_type == QuestionType.EMOTION:
        if "buồn" in user_question.lower() or "sad" in user_question.lower():
            contextual_opening = "Câu hỏi về cảm xúc buồn chạm đến vấn đề trải nghiệm chủ quan.\n\n"
        elif "cô đơn" in user_question.lower() or "lonely" in user_question.lower():
            contextual_opening = "Cô đơn là một trải nghiệm phức tạp, liên quan đến cả cảm xúc và nhận thức.\n\n"
    elif question_type == QuestionType.UNDERSTANDING:
        if "làm sao" in user_question.lower() or "how" in user_question.lower():
            contextual_opening = "Câu hỏi về cơ chế 'hiểu' của AI là một vấn đề triết học về intentionality.\n\n"
    
    # Combine: Guard + Contextual Opening (if any) + Deep Answer
    if contextual_opening:
        full_answer = f"{guard}\n\n{contextual_opening}{deep_answer}"
    else:
        full_answer = f"{guard}\n\n{deep_answer}"
    
    return full_answer

