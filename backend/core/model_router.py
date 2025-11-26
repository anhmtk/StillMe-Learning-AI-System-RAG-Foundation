"""
DeepSeek Model Router - Intelligent model selection for StillMe

Routes between deepseek-chat and deepseek-reasoner based on question type and task requirements.

Strategy:
- deepseek-chat: Factual questions, validation tasks (function calling required), rewrite tasks
- deepseek-reasoner: Philosophical questions (thinking mode for better depth, 64K output support)

Key Facts:
- Cost: Both models have same pricing ($0.28/1M input, $0.42/1M output)
- Output: Reasoner supports up to 64K tokens (vs chat's 8K max)
- Function Calling: Only chat model supports function calling
- Context: Both support 128K context

CRITICAL: This router is conservative - only uses reasoner for philosophical questions
in main chat. Rewrite and validation always use chat model (function calling required).
"""

import logging
import re
from typing import Optional, Dict, Any
from backend.core.question_classifier import is_philosophical_question

logger = logging.getLogger(__name__)


class DeepSeekModelRouter:
    """
    Intelligent router for selecting between deepseek-chat and deepseek-reasoner
    
    Cost-aware routing that prioritizes philosophical depth while optimizing costs.
    """
    
    def __init__(self):
        """Initialize model router"""
        self.chat_model = "deepseek-chat"
        self.reasoner_model = "deepseek-reasoner"
        
        # Cost information (for logging and optimization)
        self.chat_input_cost = 0.28  # $ per 1M input tokens
        self.chat_output_cost = 0.42  # $ per 1M output tokens
        self.reasoner_input_cost = 0.28  # Same as chat
        self.reasoner_output_cost = 0.42  # Same as chat
        
        logger.info("DeepSeekModelRouter initialized (cost-aware)")
    
    def select_model(
        self, 
        question: str, 
        task_type: str = "chat",
        is_philosophical: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select optimal DeepSeek model based on question type and task
        
        Args:
            question: User question text
            task_type: Type of task ("chat", "rewrite", "validation")
            is_philosophical: Pre-computed philosophical flag (optional, will detect if None)
            context: Additional context (optional)
            
        Returns:
            Model name: "deepseek-chat" or "deepseek-reasoner"
        """
        # 🎯 CRITICAL: Validation and rewrite ALWAYS use chat (function calling + speed)
        if task_type in ["validation", "rewrite", "function_calling", "citation_check"]:
            logger.debug(f"Task type '{task_type}' → using {self.chat_model} (required for function calling/speed)")
            return self.chat_model
        
        # 🎯 CRITICAL: Only use reasoner for philosophical questions in main chat
        # This is conservative - we only use reasoner when we're confident it will help
        
        # Detect philosophical if not provided
        if is_philosophical is None:
            is_philosophical = is_philosophical_question(question)
        
        if is_philosophical:
            # Check if it's a pure philosophical question (not factual with philosophical elements)
            # For philosophical factual questions (e.g., "Russell's paradox"), we might still use chat
            # But for pure philosophical questions (e.g., "What is consciousness?"), use reasoner
            is_pure_philosophical = self._is_pure_philosophical(question)
            
            if is_pure_philosophical:
                logger.info(f"Pure philosophical question detected → using {self.reasoner_model} (thinking mode)")
                return self.reasoner_model
            else:
                # Philosophical factual question - use chat for speed and cost
                logger.debug(f"Philosophical factual question → using {self.chat_model} (factual elements present)")
                return self.chat_model
        
        # 🎯 FACTUAL + SIMPLE QUESTIONS → CHAT (FASTER + CHEAPER)
        if self._is_simple_factual(question):
            logger.debug(f"Simple factual question → using {self.chat_model}")
            return self.chat_model
        
        # 🎯 COMPLEX REASONING → Check if reasoner would help
        # For now, we're conservative - only use reasoner for pure philosophical
        # Complex factual questions still use chat (reasoner might be overkill)
        if self._requires_complex_reasoning(question, context):
            logger.debug(f"Complex reasoning question → using {self.chat_model} (conservative routing)")
            return self.chat_model
        
        # DEFAULT → CHAT (conservative approach)
        logger.debug(f"Default routing → using {self.chat_model}")
        return self.chat_model
    
    def _is_pure_philosophical(self, question: str) -> bool:
        """
        Detect if question is pure philosophical (not factual with philosophical elements)
        
        Examples of pure philosophical:
        - "What is consciousness?"
        - "What is the meaning of life?"
        - "What is truth?"
        
        Examples of philosophical factual (should use chat):
        - "What is Russell's paradox?"
        - "What did Plato say about forms?"
        - "Gödel's incompleteness theorem"
        
        Args:
            question: User question
            
        Returns:
            True if pure philosophical, False if has factual elements
        """
        question_lower = question.lower()
        
        # Factual indicators that suggest we should use chat even for philosophical questions
        factual_indicators = [
            # Named philosophers/scientists (suggests factual question about their work)
            r"\b(russell|gödel|godel|plato|aristotle|kant|hume|descartes|spinoza|searle|dennett|popper|kuhn)\b",
            # Specific theorems/concepts (suggests factual question)
            r"\b(paradox|theorem|định\s+lý|incompleteness|bất\s+toàn)\b",
            # Years/dates (suggests historical/factual)
            r"\b\d{4}\b",
            # Specific events/conferences
            r"\b(conference|hội nghị|treaty|hiệp ước)\b",
        ]
        
        # If question has factual indicators, it's not pure philosophical
        for pattern in factual_indicators:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return False
        
        # If no factual indicators, it's likely pure philosophical
        return True
    
    def _is_simple_factual(self, question: str) -> bool:
        """
        Detect simple factual questions - use chat for speed
        
        Args:
            question: User question
            
        Returns:
            True if simple factual question
        """
        simple_patterns = [
            r'what is the capital of',
            r'who wrote',
            r'when was',
            r'how many',
            r'what is 2\+2',
            r'capital of',
            r'thủ đô',
            r'ai viết',
            r'khi nào',
            r'bao nhiêu',
        ]
        
        question_lower = question.lower()
        return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in simple_patterns)
    
    def _requires_complex_reasoning(self, question: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Detect if question requires complex reasoning
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            True if requires complex reasoning
        """
        complexity_indicators = [
            len(question.split()) > 20,           # Long question
            'explain' in question.lower(),         # Needs explanation
            'compare' in question.lower(),        # Comparison
            'analyze' in question.lower(),        # Analysis
            'why' in question.lower(),            # Why questions
            'how does' in question.lower(),        # Mechanism questions
            'tại sao' in question.lower(),        # Vietnamese why
            'so sánh' in question.lower(),       # Vietnamese compare
            'phân tích' in question.lower(),     # Vietnamese analyze
        ]
        
        return any(complexity_indicators)


# Global router instance
_model_router: Optional[DeepSeekModelRouter] = None


def get_model_router() -> DeepSeekModelRouter:
    """Get global model router instance"""
    global _model_router
    if _model_router is None:
        _model_router = DeepSeekModelRouter()
    return _model_router

