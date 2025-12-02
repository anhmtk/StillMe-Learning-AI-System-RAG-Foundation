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
        # Enhanced with additional patterns from ChatGPT's analysis
        self.anthropomorphic_patterns = [
            # Vietnamese patterns - Experience claims
            r"\btheo\s+kinh\s+nghiệm\b",
            r"\btheo\s+kinh\s+nghiệm\s+của\s+tôi\b",
            r"\btheo\s+kinh\s+nghiệm\s+thấy\b",
            r"\btôi\s+từng\b",
            r"\btôi\s+đã\s+làm\b",
            r"\btôi\s+nhớ\b",
            r"\btôi\s+nhớ\s+rằng\b",
            r"\bxảy\s+ra\s+hôm\s+qua\b",
            r"\btrải\s+nghiệm\b",
            r"\btôi\s+ước\b",
            r"\btôi\s+cảm\b",
            r"\btôi\s+nghĩ\b",
            r"\btôi\s+cảm\s+thấy\b",
            r"\btheo\s+quan\s+điểm\s+của\s+tôi\b",
            r"\btôi\s+thấy\b",
            r"\btôi\s+tin\s+rằng\b",
            r"\btôi\s+cho\s+rằng\b",
            r"\btheo\s+ý\s+kiến\s+của\s+tôi\b",
            r"\btôi\s+đã\s+học\s+được\b",
            r"\btôi\s+luôn\s+làm\b",
            r"\btôi\s+biết\s+cảm\s+giác\b",
            r"\bcảm\s+thấy\s+tự\s+hào\b",
            r"\btự\s+hào\s+về\b",
            r"\btự\s+hào\s+nhất\b",
            
            # English patterns - Experience claims
            r"\bin\s+my\s+experience\b",
            r"\bbased\s+on\s+my\s+experience\b",
            r"\bfrom\s+my\s+experience\b",
            r"\bI\s+have\s+experienced\b",
            r"\bI\s+used\s+to\b",
            r"\bI\s+have\s+done\b",
            r"\bI\s+remember\b",
            r"\bI\s+recall\b",
            r"\byesterday\s+I\b",
            r"\bI\s+have\s+seen\b",
            r"\bI\s+wish\b",
            r"\bI\s+feel\b",
            r"\bI\s+think\b",
            r"\bI\s+believe\b",
            r"\bI\s+sense\b",
            r"\bin\s+my\s+opinion\b",
            r"\bI\s+see\b",
            r"\bI\s+notice\b",
            r"\bI\s+find\b",
            r"\bI\s+consider\b",
            r"\bI\s+would\s+say\b",
            r"\bI\s+have\s+found\b",
            r"\bI\s+have\s+noticed\b",
            r"\bI\s+have\s+learned\b",
            r"\bI\s+always\s+do\b",
            r"\bI\s+know\s+the\s+feeling\b",
            r"\bI\s+feel\s+proud\b",
            r"\bI\s+am\s+proud\b",
            r"\bwhat\s+makes\s+me\s+proud\b",
            r"\bI\s+take\s+pride\b",
        ]
        
        # Add consciousness/emotion ambiguity patterns (prohibited phrases)
        # These patterns indicate ambiguous or false claims about consciousness/emotions
        self.consciousness_violation_patterns = [
            # Vietnamese - prohibited ambiguous phrases
            r"không\s+thể\s+biết\s+chắc\s+liệu\s+tôi\s+có\s+ý\s+thức",
            r"không\s+chắc\s+liệu\s+tôi\s+có\s+ý\s+thức",
            r"có\s+thể\s+tôi\s+có\s+một\s+dạng\s+ý\s+thức",
            r"tôi\s+cũng\s+có\s+cảm\s+xúc\s+theo\s+một\s+nghĩa",
            r"có\s+thể\s+xem\s+là\s+có\s+ý\s+thức",
            r"không\s+chắc\s+về\s+tình\s+trạng\s+ý\s+thức",
            
            # English - prohibited ambiguous phrases
            r"i\s+cannot\s+be\s+certain\s+whether\s+i\s+have\s+consciousness",
            r"i\s+am\s+not\s+sure\s+if\s+i\s+have\s+consciousness",
            r"i\s+might\s+have\s+some\s+form\s+of\s+consciousness",
            r"i\s+also\s+have\s+emotions\s+in\s+some\s+sense",
            r"could\s+be\s+considered\s+to\s+have\s+consciousness",
            r"uncertain\s+about\s+my\s+consciousness",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.anthropomorphic_patterns
        ]
        
        # Compile consciousness violation patterns
        self.compiled_consciousness_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.consciousness_violation_patterns
        ]
        
        # Neutral alternatives for common phrases (Experience-Free Mode)
        self.neutral_replacements = {
            # Vietnamese
            "theo kinh nghiệm": "dựa trên dữ liệu",
            "theo kinh nghiệm của tôi": "dựa trên dữ liệu",
            "theo kinh nghiệm thấy": "dữ liệu cho thấy",
            "tôi từng": "dữ liệu cho thấy",
            "tôi đã làm": "quy trình được công bố",
            "tôi nhớ": "theo tài liệu",
            "tôi nhớ rằng": "theo tài liệu",
            "xảy ra hôm qua": "theo dữ liệu gần đây",
            "trải nghiệm": "dữ liệu",
            "tôi ước": "hệ thống khuyến nghị",
            "tôi cảm": "dữ liệu chỉ ra",
            "tôi nghĩ": "phân tích cho thấy",
            "tôi cảm thấy": "dữ liệu chỉ ra",
            "theo quan điểm của tôi": "dựa trên phân tích",
            "tôi thấy": "dữ liệu cho thấy",
            "tôi tin rằng": "dữ liệu cho thấy",
            "tôi đã học được": "theo tài liệu",
            "tôi luôn làm": "theo quy trình",
            "tôi biết cảm giác": "dữ liệu chỉ ra",
            "cảm thấy tự hào": "điều tôi đánh giá cao",
            "tự hào về": "điều tôi đánh giá cao về",
            "tự hào nhất": "điều tôi đánh giá cao nhất",
            
            # English
            "in my experience": "based on data",
            "based on my experience": "based on data",
            "from my experience": "based on data",
            "I have experienced": "data shows",
            "I used to": "data indicates",
            "I have done": "the published process",
            "I remember": "according to documentation",
            "I recall": "according to documentation",
            "yesterday I": "recent data shows",
            "I have seen": "data shows",
            "I wish": "the system recommends",
            "I feel": "data suggests",
            "I think": "analysis shows",
            "I believe": "data indicates",
            "I sense": "data suggests",
            "in my opinion": "based on analysis",
            "I see": "data shows",
            "I notice": "data indicates",
            "I find": "analysis shows",
            "I consider": "data indicates",
            "I would say": "analysis shows",
            "I have found": "data shows",
            "I have noticed": "data indicates",
            "I have learned": "according to documentation",
            "I always do": "the standard process",
            "I know the feeling": "data indicates",
            "I feel proud": "what I value most",
            "I am proud": "what I value",
            "what makes me proud": "what I value most",
            "I take pride": "I value",
        }
    
    def run(self, answer: str, ctx_docs: List[str], user_question: Optional[str] = None) -> ValidationResult:
        """
        Check for anthropomorphic language in answer
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (not used for this validator)
            user_question: Optional user question to check if it's about consciousness/emotions
            
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
        
        # Check for consciousness/emotion violation patterns if user question is about consciousness/emotions
        # NOTE: If question was processed by philosophy_processor, skip strict validation to avoid mode collapse
        # The processor already ensures non-anthropomorphic answers
        if user_question:
            try:
                from backend.philosophy.processor import is_philosophical_question_about_consciousness
                is_philosophical = is_philosophical_question_about_consciousness(user_question)
                
                if is_philosophical:
                    # For philosophical questions processed by philosophy_processor, only check for obvious violations
                    # Don't be too strict to avoid mode collapse - processor already handles guard statements
                    logger.debug("Philosophical question detected - using relaxed validation to avoid mode collapse")
                    # Only flag if answer contains obvious anthropomorphic claims (not philosophical discussions)
                    obvious_violations = [
                        r"\btôi\s+có\s+ý\s+thức\b",  # "I have consciousness"
                        r"\btôi\s+có\s+cảm\s+xúc\b",  # "I have emotions"
                        r"\bi\s+have\s+consciousness\b",
                        r"\bi\s+have\s+emotions\b",
                        r"\bi\s+feel\s+[a-z]+\b",  # "I feel X"
                        r"\btôi\s+cảm\s+thấy\s+[a-z]+\b",  # "I feel X"
                    ]
                    for pattern in obvious_violations:
                        if re.search(pattern, answer_lower):
                            detected_phrases.append(pattern)
                            logger.warning(
                                f"Ego-Neutrality Validator detected obvious anthropomorphic claim in philosophical answer: {pattern}"
                            )
                else:
                    # For non-philosophical questions, use old strict validation
                    from backend.api.utils.chat_helpers import is_consciousness_or_emotion_question
                    if is_consciousness_or_emotion_question(user_question):
                        # Check for prohibited ambiguous phrases about consciousness/emotions
                        for pattern in self.compiled_consciousness_patterns:
                            matches = pattern.findall(answer_lower)
                            if matches:
                                detected_phrases.extend(matches)
                                logger.warning(
                                    f"Ego-Neutrality Validator detected consciousness/emotion ambiguity: {matches}. "
                                    f"This violates Experience-Free Communication Protocol - StillMe must be clear and direct."
                                )
            except ImportError:
                logger.debug("Philosophy processor or chat_helpers not available, using fallback validation")
            except Exception as e:
                logger.warning(f"Error checking consciousness question: {e}")
        
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

