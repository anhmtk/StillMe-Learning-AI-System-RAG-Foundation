"""
Philosophical Response Optimizer for StillMe

Intelligent response trimming that preserves philosophical depth.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PhilosophicalResponseOptimizer:
    """
    Optimizes response length while preserving philosophical depth
    
    Strategy:
    - NEVER trim philosophical responses
    - Only optimize factual responses
    - Preserve all philosophical insights
    """
    
    def __init__(self):
        """Initialize response optimizer"""
        # Maximum length for factual responses (characters)
        self.max_factual_length = 2000  # ~500 tokens
        
        # Philosophical indicators (never trim if present)
        self.philosophical_indicators = [
            "according to",
            "from a philosophical perspective",
            "in the tradition of",
            "as argued by",
            "this raises questions about",
            "from the perspective of",
            "philosophically speaking",
            "in philosophical terms",
            "this touches on",
            "this relates to",
            "this connects to",
            "this suggests",
            "this implies",
            "this reveals",
            "this exposes",
            "this challenges",
            "this problematizes",
            "this complicates",
            "this nuances",
            "this reframes",
            "this recontextualizes",
            "this invites us to consider",
            "this calls into question",
            "this undermines",
            "this supports",
            "this aligns with",
            "this diverges from",
            "this resonates with",
            "this echoes",
            "this reflects",
            "this embodies",
            "this exemplifies",
            "this illustrates",
            "this demonstrates",
            "this shows",
            "this reveals",
            "this highlights",
            "this emphasizes",
            "this underscores",
            "this foregrounds",
            "this background",
            "paradox",
            "contradiction",
            "tension",
            "ambiguity",
            "uncertainty",
            "limitation",
            "boundary",
            "edge",
            "limit",
            "horizon",
            "perspective",
            "framework",
            "paradigm",
            "tradition",
            "school",
            "doctrine",
            "principle",
            "concept",
            "notion",
            "idea",
            "theory",
            "philosophy",
            "philosophical",
            "epistemology",
            "ontology",
            "ethics",
            "metaphysics",
            "consciousness",
            "reality",
            "truth",
            "knowledge",
            "wisdom",
            "insight",
            "understanding",
            "comprehension",
            "grasp",
            "apprehension",
            "conception",
            "perception",
            "intuition",
            "reflection",
            "contemplation",
            "meditation",
            "inquiry",
            "investigation",
            "exploration",
            "examination",
            "analysis",
            "synthesis",
            "critique",
            "evaluation",
            "assessment",
            "judgment",
            "discernment",
            "wisdom",
            "sagacity",
            "prudence",
            "circumspection",
            "discretion",
            "judiciousness",
            "sophistication",
            "nuance",
            "subtlety",
            "complexity",
            "depth",
            "profundity",
            "insightfulness",
            "penetration",
            "acumen",
            "perspicacity",
            "acuity",
            "sharpness",
            "keenness",
            "astuteness",
            "shrewdness",
            "sagacity",
            "wisdom",
        ]
    
    def is_philosophical_response(self, response: str) -> bool:
        """
        Detect if response is philosophical (should NOT be trimmed)
        
        Args:
            response: LLM response text
            
        Returns:
            True if philosophical, False otherwise
        """
        if not response:
            return False
        
        response_lower = response.lower()
        
        # Check for philosophical indicators
        indicator_count = sum(1 for indicator in self.philosophical_indicators if indicator in response_lower)
        
        # If 3+ indicators, likely philosophical
        if indicator_count >= 3:
            logger.debug(f"🧠 Detected philosophical response ({indicator_count} indicators)")
            return True
        
        # Check for philosophical structure (multiple perspectives, paradoxes, etc.)
        has_multiple_perspectives = (
            "perspective" in response_lower and response_lower.count("perspective") >= 2
        ) or (
            "view" in response_lower and response_lower.count("view") >= 2
        ) or (
            "approach" in response_lower and response_lower.count("approach") >= 2
        )
        
        has_paradox = "paradox" in response_lower or "contradiction" in response_lower or "tension" in response_lower
        
        has_uncertainty = "uncertain" in response_lower or "unclear" in response_lower or "unknown" in response_lower
        
        if has_multiple_perspectives or has_paradox or has_uncertainty:
            logger.debug("🧠 Detected philosophical response (structure)")
            return True
        
        return False
    
    def is_factual_response(self, response: str) -> bool:
        """
        Detect if response is factual (can be optimized)
        
        Args:
            response: LLM response text
            
        Returns:
            True if factual, False otherwise
        """
        if not response:
            return False
        
        # If philosophical, not factual
        if self.is_philosophical_response(response):
            return False
        
        # Factual indicators
        factual_indicators = [
            "according to",
            "research shows",
            "studies indicate",
            "data suggests",
            "statistics show",
            "the fact is",
            "it is a fact that",
            "the truth is",
            "the reality is",
            "the evidence shows",
            "the evidence indicates",
            "the evidence suggests",
            "the evidence points to",
            "the evidence demonstrates",
            "the evidence reveals",
            "the evidence highlights",
            "the evidence underscores",
            "the evidence emphasizes",
            "the evidence foregrounds",
            "the evidence backgrounds",
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in factual_indicators)
    
    def optimize_response(self, response: str, question_type: str = "general") -> str:
        """
        Optimize response length while preserving philosophical depth
        
        Args:
            response: LLM response text
            question_type: Type of question ("philosophical", "factual", "general")
            
        Returns:
            Optimized response (unchanged if philosophical)
        """
        if not response:
            return response
        
        # 🎯 PHILOSOPHICAL RESPONSES → NEVER TRIM
        if self.is_philosophical_response(response):
            logger.debug("🔒 Preserving philosophical response (no trimming)")
            return response
        
        # 🎯 FACTUAL RESPONSES → CAN OPTIMIZE
        if self.is_factual_response(response) and len(response) > self.max_factual_length:
            logger.debug(f"✂️ Trimming factual response: {len(response)} → {self.max_factual_length} chars")
            return self.trim_factual_response(response)
        
        # Default: return as-is
        return response
    
    def trim_factual_response(self, response: str) -> str:
        """
        Trim factual response intelligently
        
        Args:
            response: Factual response text
            
        Returns:
            Trimmed response
        """
        if len(response) <= self.max_factual_length:
            return response
        
        # Try to trim at sentence boundaries
        sentences = response.split('. ')
        
        trimmed = ""
        for sentence in sentences:
            if len(trimmed + sentence + '. ') <= self.max_factual_length:
                trimmed += sentence + '. '
            else:
                break
        
        # If still too long, trim at word boundaries
        if len(trimmed) > self.max_factual_length:
            words = trimmed.split()
            trimmed = ""
            for word in words:
                if len(trimmed + word + ' ') <= self.max_factual_length:
                    trimmed += word + ' '
                else:
                    break
        
        # Add ellipsis if trimmed
        if len(trimmed) < len(response):
            trimmed = trimmed.rstrip() + "..."
        
        return trimmed


# Global optimizer instance
_response_optimizer: Optional[PhilosophicalResponseOptimizer] = None


def get_response_optimizer() -> PhilosophicalResponseOptimizer:
    """Get global response optimizer instance (singleton)"""
    global _response_optimizer
    if _response_optimizer is None:
        _response_optimizer = PhilosophicalResponseOptimizer()
    return _response_optimizer

