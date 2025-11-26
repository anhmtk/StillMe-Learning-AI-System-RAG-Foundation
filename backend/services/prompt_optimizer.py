"""
Philosophical Prompt Optimizer for StillMe

Optimizes prompts to reduce tokens WITHOUT compromising philosophical depth.
"""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PhilosophicalPromptOptimizer:
    """
    Optimizes prompts while preserving philosophical instructions
    
    Strategy:
    - NEVER optimize philosophical instructions
    - Optimize verbose system prompts
    - Remove redundant language
    - Keep all core principles intact
    """
    
    def __init__(self):
        """Initialize prompt optimizer"""
        # Verbose phrases to optimize (but NOT philosophical content)
        self.verbose_optimizations = {
            "it is very important that": "ensure",
            "it is crucial that": "ensure",
            "you must always": "always",
            "under any circumstances": "always",
            "it is essential that": "ensure",
            "it is critical that": "ensure",
            "please note that": "",
            "kindly note that": "",
            "it should be noted that": "",
            "it is worth noting that": "",
            "it is important to note that": "",
            "as a reminder": "",
            "just to remind you": "",
            "to reiterate": "",
            "once again": "",
            "again": "",
        }
        
        # Phrases to preserve (philosophical content)
        self.preserve_phrases = [
            "transparency",
            "philosophical",
            "intellectual humility",
            "acknowledge uncertainty",
            "paradox",
            "epistemology",
            "ontology",
            "ethics",
            "consciousness",
            "reality",
            "truth",
            "knowledge",
            "uncertainty",
            "limitations",
            "paradigm",
            "perspective",
            "framework",
            "principle",
            "doctrine",
            "tradition",
            "school of thought",
            "philosopher",
            "philosophical question",
            "philosophical depth",
            "philosophical inquiry",
            "philosophical analysis",
            "philosophical perspective",
            "philosophical tradition",
            "philosophical framework",
            "philosophical principle",
            "philosophical doctrine",
            "philosophical school",
        ]
    
    def _contains_philosophical_content(self, text: str) -> bool:
        """Check if text contains philosophical content"""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in self.preserve_phrases)
    
    def _is_philosophical_instruction_block(self, text: str) -> bool:
        """Check if text is a philosophical instruction block"""
        philo_markers = [
            "PHILOSOPHICAL FRAMING INSTRUCTION",
            "PHILOSOPHICAL QUESTION DETECTED",
            "MANDATORY OUTPUT RULES",
            "MANDATORY: MINIMUM 2 CONTRASTING POSITIONS",
            "PARADOX HANDLING",
            "DEEP CONCEPTUAL UNPACKING",
            "Answer Shape",
            "Anchor",
            "Unpack",
            "Explore",
            "Edge of knowledge",
            "Return to the user",
        ]
        
        return any(marker in text for marker in philo_markers)
    
    def optimize_prompt(self, messages: List[Dict[str, Any]], question_type: str = "general") -> List[Dict[str, Any]]:
        """
        Optimize prompt messages while preserving philosophical content
        
        Args:
            messages: List of message dicts (role, content)
            question_type: Type of question ("philosophical", "factual", "general")
            
        Returns:
            Optimized messages list
        """
        optimized_messages = []
        
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")
            
            # 🎯 NEVER optimize philosophical instructions
            if self._is_philosophical_instruction_block(content):
                logger.debug("🔒 Preserving philosophical instructions (no optimization)")
                optimized_messages.append(msg)
                continue
            
            # 🎯 NEVER optimize if contains philosophical content
            if self._contains_philosophical_content(content):
                logger.debug("🔒 Preserving philosophical content (no optimization)")
                optimized_messages.append(msg)
                continue
            
            # 🎯 OPTIMIZE system prompts (reduce verbose language)
            if role == "system":
                optimized_content = self.optimize_system_prompt(content)
                optimized_messages.append({
                    "role": role,
                    "content": optimized_content
                })
                continue
            
            # 🎯 PRESERVE user questions (never optimize)
            if role == "user":
                optimized_messages.append(msg)
                continue
            
            # Default: preserve as-is
            optimized_messages.append(msg)
        
        return optimized_messages
    
    def optimize_system_prompt(self, content: str) -> str:
        """
        Optimize system prompt by removing verbose language
        
        Args:
            content: System prompt content
            
        Returns:
            Optimized content
        """
        # NEVER optimize if contains philosophical content
        if self._contains_philosophical_content(content):
            return content
        
        optimized = content
        
        # Apply verbose optimizations (case-insensitive)
        for verbose, concise in self.verbose_optimizations.items():
            # Use word boundaries to avoid partial matches
            pattern = re.compile(r'\b' + re.escape(verbose) + r'\b', re.IGNORECASE)
            if concise:
                optimized = pattern.sub(concise, optimized)
            else:
                # Remove phrase entirely
                optimized = pattern.sub('', optimized)
        
        # Remove redundant whitespace
        optimized = re.sub(r'\s+', ' ', optimized)
        optimized = re.sub(r'\n\s*\n\s*\n', '\n\n', optimized)
        optimized = optimized.strip()
        
        # Log optimization if significant
        original_length = len(content)
        optimized_length = len(optimized)
        if optimized_length < original_length * 0.9:  # More than 10% reduction
            reduction = ((original_length - optimized_length) / original_length) * 100
            logger.info(f"📉 Optimized system prompt: {reduction:.1f}% reduction ({original_length} → {optimized_length} chars)")
        
        return optimized
    
    def estimate_token_savings(self, original: str, optimized: str) -> int:
        """
        Estimate token savings from optimization
        
        Args:
            original: Original text
            optimized: Optimized text
            
        Returns:
            Estimated token savings
        """
        # Rough token estimation (1 token ≈ 4 characters)
        original_tokens = len(original) // 4
        optimized_tokens = len(optimized) // 4
        
        return original_tokens - optimized_tokens


# Global optimizer instance
_prompt_optimizer: Optional[PhilosophicalPromptOptimizer] = None


def get_prompt_optimizer() -> PhilosophicalPromptOptimizer:
    """Get global prompt optimizer instance (singleton)"""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PhilosophicalPromptOptimizer()
    return _prompt_optimizer

