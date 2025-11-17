"""
Ego-Neutrality Validator - Detects and flags anthropomorphic language

This validator addresses a critical blindspot in AI transparency:
"Hallucination of Experience" - when AI uses language that falsely attributes
subjective qualities (experience, emotions, personal opinions) to itself.

This is a novel contribution to AI transparency research, identifying a
philosophical risk that existing validators miss.
"""

import re
from typing import List, Optional
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)


class EgoNeutralityValidator:
    """
    Validator that detects anthropomorphic language in AI responses
    
    Detects phrases that falsely attribute subjective qualities to AI:
    - "theo kinh nghiệm" / "in my experience" / "based on my experience"
    - "tôi nghĩ" / "I think" / "I believe"
    - "tôi cảm thấy" / "I feel" / "I sense"
    - "theo quan điểm của tôi" / "in my opinion"
    - "tôi thấy" / "I see" / "I notice"
    
    This addresses the "Hallucination of Experience" - a subtle but critical
    form of linguistic hallucination that undermines transparency.
    """
    
    def __init__(self, strict_mode: bool = True, auto_patch: bool = False):
        """
        Initialize Ego-Neutrality validator
        
        Args:
            strict_mode: If True, flag all anthropomorphic phrases. If False, only flag obvious ones.
            auto_patch: If True, automatically replace anthropomorphic phrases with neutral alternatives
        """
        self.strict_mode = strict_mode
        self.auto_patch = auto_patch
        
        # Anthropomorphic phrases to detect (Vietnamese and English)
        # These phrases falsely attribute subjective qualities to AI
        self.anthropomorphic_patterns = [
            # Vietnamese patterns
            r"\btheo\s+kinh\s+nghiệm\b",
            r"\btheo\s+kinh\s+nghiệm\s+của\s+tôi\b",
            r"\btheo\s+kinh\s+nghiệm\s+thấy\b",
            r"\btôi\s+nghĩ\b",
            r"\btôi\s+cảm\s+thấy\b",
            r"\btheo\s+quan\s+điểm\s+của\s+tôi\b",
            r"\btôi\s+thấy\b",
            r"\btôi\s+tin\s+rằng\b",
            r"\btôi\s+cho\s+rằng\b",
            r"\btheo\s+ý\s+kiến\s+của\s+tôi\b",
            
            # English patterns
            r"\bin\s+my\s+experience\b",
            r"\bbased\s+on\s+my\s+experience\b",
            r"\bfrom\s+my\s+experience\b",
            r"\bI\s+think\b",
            r"\bI\s+believe\b",
            r"\bI\s+feel\b",
            r"\bI\s+sense\b",
            r"\bin\s+my\s+opinion\b",
            r"\bI\s+see\b",
            r"\bI\s+notice\b",
            r"\bI\s+find\b",
            r"\bI\s+consider\b",
            r"\bI\s+would\s+say\b",
            r"\bI\s+have\s+found\b",
            r"\bI\s+have\s+seen\b",
            r"\bI\s+have\s+noticed\b",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.anthropomorphic_patterns
        ]
        
        # Neutral alternatives for common phrases
        self.neutral_replacements = {
            # Vietnamese
            "theo kinh nghiệm": "dựa trên dữ liệu",
            "theo kinh nghiệm của tôi": "dựa trên dữ liệu",
            "theo kinh nghiệm thấy": "dữ liệu cho thấy",
            "tôi nghĩ": "phân tích cho thấy",
            "tôi cảm thấy": "dữ liệu chỉ ra",
            "theo quan điểm của tôi": "dựa trên phân tích",
            "tôi thấy": "dữ liệu cho thấy",
            "tôi tin rằng": "dữ liệu cho thấy",
            
            # English
            "in my experience": "based on data",
            "based on my experience": "based on data",
            "from my experience": "based on data",
            "I think": "analysis shows",
            "I believe": "data indicates",
            "I feel": "data suggests",
            "in my opinion": "based on analysis",
            "I see": "data shows",
            "I notice": "data indicates",
        }
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check for anthropomorphic language in answer
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (not used for this validator)
            
        Returns:
            ValidationResult with passed status and detected phrases
        """
        if not answer:
            return ValidationResult(passed=True)
        
        detected_phrases = []
        answer_lower = answer.lower()
        
        # Check for anthropomorphic patterns
        for pattern in self.compiled_patterns:
            matches = pattern.findall(answer_lower)
            if matches:
                detected_phrases.extend(matches)
        
        if not detected_phrases:
            return ValidationResult(passed=True)
        
        # Remove duplicates while preserving order
        unique_phrases = []
        seen = set()
        for phrase in detected_phrases:
            phrase_lower = phrase.lower()
            if phrase_lower not in seen:
                unique_phrases.append(phrase)
                seen.add(phrase_lower)
        
        logger.warning(
            f"Ego-Neutrality Validator detected anthropomorphic language: {unique_phrases}. "
            f"This is a 'Hallucination of Experience' - AI should not claim personal experience."
        )
        
        # Auto-patch if enabled
        patched_answer = None
        if self.auto_patch:
            patched_answer = self._patch_anthropomorphic_language(answer, unique_phrases)
            logger.info("Ego-Neutrality Validator auto-patched anthropomorphic language")
        
        return ValidationResult(
            passed=False,  # Flag as failed to track the issue
            reasons=[f"anthropomorphic_language: {', '.join(unique_phrases)}"],
            patched_answer=patched_answer
        )
    
    def _patch_anthropomorphic_language(self, answer: str, detected_phrases: List[str]) -> str:
        """
        Replace anthropomorphic phrases with neutral alternatives
        
        Args:
            answer: Original answer
            detected_phrases: List of detected anthropomorphic phrases
            
        Returns:
            Answer with anthropomorphic language replaced
        """
        patched = answer
        
        # Replace each detected phrase with neutral alternative
        for phrase in detected_phrases:
            phrase_lower = phrase.lower()
            if phrase_lower in self.neutral_replacements:
                replacement = self.neutral_replacements[phrase_lower]
                # Use case-insensitive replacement
                patched = re.sub(
                    re.escape(phrase),
                    replacement,
                    patched,
                    flags=re.IGNORECASE
                )
            else:
                # Generic replacement for unmatched phrases
                # Try to extract the core meaning and replace with neutral alternative
                if "experience" in phrase_lower or "kinh nghiệm" in phrase_lower:
                    patched = re.sub(
                        re.escape(phrase),
                        "dựa trên dữ liệu" if "kinh nghiệm" in phrase_lower else "based on data",
                        patched,
                        flags=re.IGNORECASE
                    )
                elif "think" in phrase_lower or "nghĩ" in phrase_lower:
                    patched = re.sub(
                        re.escape(phrase),
                        "phân tích cho thấy" if "nghĩ" in phrase_lower else "analysis shows",
                        patched,
                        flags=re.IGNORECASE
                    )
                elif "feel" in phrase_lower or "cảm thấy" in phrase_lower:
                    patched = re.sub(
                        re.escape(phrase),
                        "dữ liệu chỉ ra" if "cảm thấy" in phrase_lower else "data indicates",
                        patched,
                        flags=re.IGNORECASE
                    )
        
        # Add transparency note if we made replacements
        if patched != answer:
            transparency_note = "\n\n[Note: StillMe does not have personal experiences. The above response is based on data analysis, not personal experience.]"
            patched = patched + transparency_note
        
        return patched

