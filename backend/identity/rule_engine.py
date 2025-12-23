"""
Rule Engine for Pattern Matching

Matches user questions against instruction patterns to determine which instructions to apply.
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from backend.identity.instruction_loader import get_instruction_loader, InstructionLoader

logger = logging.getLogger(__name__)


class RuleEngine:
    """Rule engine for matching questions to instructions"""
    
    def __init__(self, instruction_loader: Optional[InstructionLoader] = None):
        """
        Initialize rule engine
        
        Args:
            instruction_loader: InstructionLoader instance (default: singleton)
        """
        self.loader = instruction_loader or get_instruction_loader()
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
    
    def match_instruction(self, question: str, instruction_name: str) -> bool:
        """
        Check if question matches instruction patterns
        
        Args:
            question: User question text
            instruction_name: Name of instruction to check
            
        Returns:
            True if question matches any pattern for this instruction
        """
        patterns = self.loader.get_detection_patterns(instruction_name)
        if not patterns:
            return False
        
        # Compile patterns if not already compiled
        if instruction_name not in self._compiled_patterns:
            compiled = []
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}' for {instruction_name}: {e}")
            self._compiled_patterns[instruction_name] = compiled
        
        # Check if question matches any pattern
        question_lower = question.lower()
        for pattern in self._compiled_patterns[instruction_name]:
            if pattern.search(question_lower):
                logger.debug(f"Question matches pattern for {instruction_name}")
                return True
        
        return False
    
    def find_matching_instructions(self, question: str, instruction_names: List[str]) -> List[Tuple[str, str]]:
        """
        Find all matching instructions for a question
        
        Args:
            question: User question text
            instruction_names: List of instruction names to check
            
        Returns:
            List of (instruction_name, priority) tuples, sorted by priority (P1 first)
        """
        matches = []
        
        for instruction_name in instruction_names:
            if self.match_instruction(question, instruction_name):
                priority = self.loader.get_priority(instruction_name)
                matches.append((instruction_name, priority))
        
        # Sort by priority (P1_CRITICAL first, P4_LOW last)
        priority_order = {"P1_CRITICAL": 1, "P2_HIGH": 2, "P3_MEDIUM": 3, "P4_LOW": 4}
        matches.sort(key=lambda x: priority_order.get(x[1], 99))
        
        return matches
    
    def get_highest_priority_instruction(self, question: str, instruction_names: List[str]) -> Optional[str]:
        """
        Get highest priority matching instruction
        
        Args:
            question: User question text
            instruction_names: List of instruction names to check
            
        Returns:
            Instruction name with highest priority, or None if no match
        """
        matches = self.find_matching_instructions(question, instruction_names)
        if matches:
            return matches[0][0]  # Return instruction name
        return None


# Singleton instance
_engine_instance: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """Get singleton rule engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RuleEngine()
    return _engine_instance

