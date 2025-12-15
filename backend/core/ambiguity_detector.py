"""
Ambiguity Detector for StillMe

Detects ambiguous questions and determines when StillMe should ask for clarification
vs. answering with assumptions.

Based on StillMe Manifesto Principle 5: "EMBRACE 'I DON'T KNOW' AS INTELLECTUAL HONESTY"
- We value HONESTY over APPEARING KNOWLEDGEABLE
- But we also value USER EXPERIENCE - not asking too many questions
- Balance: Ask when truly ambiguous, answer with disclaimers when we can infer

Ambiguity Levels:
1. HIGH (0.7-1.0): Multiple valid interpretations, should ask for clarification
2. MEDIUM (0.4-0.7): Can infer intent, but should acknowledge assumptions
3. LOW (0.0-0.4): Clear intent, answer directly
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AmbiguityLevel(str, Enum):
    """Ambiguity level classification"""
    HIGH = "HIGH"      # Should ask for clarification
    MEDIUM = "MEDIUM"  # Answer with disclaimer about assumptions
    LOW = "LOW"        # Answer directly


class AmbiguityDetector:
    """
    Detects ambiguous questions and determines appropriate response strategy.
    
    Philosophy:
    - StillMe should ask for clarification when truly ambiguous (HIGH)
    - StillMe should answer with disclaimers when it can infer intent (MEDIUM)
    - StillMe should answer directly when intent is clear (LOW)
    - Balance: Not too many questions (bad UX), not too mechanical (bad UX)
    """
    
    def __init__(self, high_threshold: float = 0.7, medium_threshold: float = 0.4):
        """
        Initialize ambiguity detector.
        
        Args:
            high_threshold: Score above which we should ask for clarification (default: 0.7)
            medium_threshold: Score above which we should add disclaimers (default: 0.4)
        """
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
    
    def detect_ambiguity(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None
    ) -> Tuple[float, AmbiguityLevel, List[str]]:
        """
        Detect ambiguity in user query.
        
        Args:
            query: User query string
            conversation_history: Optional conversation history for context
            
        Returns:
            Tuple of (ambiguity_score, ambiguity_level, reasons)
            - ambiguity_score: 0.0 (clear) to 1.0 (very ambiguous)
            - ambiguity_level: HIGH, MEDIUM, or LOW
            - reasons: List of reasons why query is ambiguous
        """
        if not query or not query.strip():
            return 1.0, AmbiguityLevel.HIGH, ["Empty query"]
        
        query_lower = query.lower().strip()
        reasons = []
        score = 0.0
        
        # Factor 1: Very short queries (often ambiguous)
        word_count = len(query.split())
        if word_count <= 2:
            score += 0.3
            reasons.append("Very short query (≤2 words)")
        elif word_count <= 4:
            score += 0.15
            reasons.append("Short query (≤4 words)")
        
        # Factor 2: Pronouns without clear referent
        pronouns = ["nó", "đó", "cái đó", "điều đó", "it", "that", "this", "they", "them"]
        has_pronoun = any(pronoun in query_lower for pronoun in pronouns)
        
        # Check if pronoun has referent in conversation history
        has_referent = False
        if has_pronoun and conversation_history:
            # Check last few messages for potential referents
            recent_messages = conversation_history[-3:]
            for msg in recent_messages:
                content = msg.get("content", "")
                # Simple heuristic: if previous message mentions a topic, pronoun likely refers to it
                if len(content.split()) > 5:  # Substantive message
                    has_referent = True
                    break
        
        if has_pronoun and not has_referent:
            score += 0.25
            reasons.append("Pronoun without clear referent in conversation")
        elif has_pronoun and has_referent:
            # Pronoun has referent, but still slightly ambiguous
            score += 0.1
            reasons.append("Pronoun with possible referent (slight ambiguity)")
        
        # Factor 3: Ambiguous keywords
        ambiguous_keywords = [
            "cái gì", "gì", "what", "which", "how", "như thế nào",
            "tốt hơn", "better", "best", "tốt nhất",
            "nên", "should", "có nên", "should i",
            "có thể", "can", "could", "might",
            "về", "about", "liên quan", "related"
        ]
        ambiguous_count = sum(1 for keyword in ambiguous_keywords if keyword in query_lower)
        if ambiguous_count >= 2:
            score += 0.2
            reasons.append(f"Multiple ambiguous keywords ({ambiguous_count})")
        elif ambiguous_count == 1:
            score += 0.1
            reasons.append("Ambiguous keyword present")
        
        # Factor 4: Multiple possible interpretations
        # Check for questions that could be about different things
        multi_interpretation_patterns = [
            r"ưu\s+điểm.*nhược\s+điểm",  # "ưu điểm và nhược điểm" - could be about anything
            r"pros?\s+and\s+cons?",  # "pros and cons"
            r"so\s+sánh",  # "so sánh" - compare what?
            r"compare",  # "compare"
            r"khác\s+biệt",  # "khác biệt" - difference between what?
            r"difference",  # "difference"
        ]
        has_multi_interpretation = any(
            re.search(pattern, query_lower) for pattern in multi_interpretation_patterns
        )
        if has_multi_interpretation:
            # Check if topic is mentioned
            has_topic = any(
                word[0].isupper() for word in query.split() if len(word) > 2
            ) or any(
                keyword in query_lower for keyword in ["python", "java", "javascript", "c++", "c#"]
            )
            if not has_topic:
                score += 0.3
                reasons.append("Multi-interpretation pattern without clear topic")
            else:
                score += 0.1
                reasons.append("Multi-interpretation pattern with topic (slight ambiguity)")
        
        # Factor 5: Follow-up questions without clear context
        follow_up_patterns = ["còn", "thì sao", "còn về", "what about", "how about"]
        is_follow_up = any(pattern in query_lower for pattern in follow_up_patterns)
        
        if is_follow_up:
            # Check if conversation history provides context
            if conversation_history and len(conversation_history) > 0:
                recent_messages = conversation_history[-2:]
                has_context = False
                for msg in recent_messages:
                    content = msg.get("content", "")
                    if len(content.split()) > 10:  # Substantive message
                        has_context = True
                        break
                
                if not has_context:
                    score += 0.25
                    reasons.append("Follow-up question without clear context")
                else:
                    # Follow-up with context - still slightly ambiguous
                    score += 0.1
                    reasons.append("Follow-up question (slight ambiguity)")
            else:
                score += 0.3
                reasons.append("Follow-up question without conversation history")
        
        # Factor 6: Questions that could be about StillMe or something else
        stillme_ambiguous_patterns = [
            r"nhược\s+điểm",  # "nhược điểm" - of what?
            r"weakness",  # "weakness"
            r"ưu\s+điểm",  # "ưu điểm" - of what?
            r"advantage",  # "advantage"
            r"tính\s+năng",  # "tính năng" - features of what?
            r"features?",  # "features"
        ]
        has_stillme_ambiguous = any(
            re.search(pattern, query_lower) for pattern in stillme_ambiguous_patterns
        )
        
        if has_stillme_ambiguous:
            # Check if query explicitly mentions StillMe or a topic
            has_explicit_topic = (
                "stillme" in query_lower or
                "bạn" in query_lower or
                "you" in query_lower or
                any(word[0].isupper() for word in query.split() if len(word) > 2)
            )
            if not has_explicit_topic:
                # CRITICAL FIX: If query is very short (≤2 words) AND has ambiguous reference,
                # this is HIGH ambiguity - boost score to ensure it's classified as HIGH
                if word_count <= 2:
                    score += 0.4  # Boost from 0.25 to 0.4 to push it over HIGH threshold
                    reasons.append("Ambiguous reference (could be StillMe or topic) + very short query → HIGH ambiguity")
                else:
                    score += 0.25
                    reasons.append("Ambiguous reference (could be StillMe or topic)")
            else:
                score += 0.05
                reasons.append("Ambiguous pattern with explicit topic (minimal ambiguity)")
        
        # Normalize score to 0.0-1.0
        score = min(1.0, score)
        
        # Determine level
        if score >= self.high_threshold:
            level = AmbiguityLevel.HIGH
        elif score >= self.medium_threshold:
            level = AmbiguityLevel.MEDIUM
        else:
            level = AmbiguityLevel.LOW
        
        logger.debug(
            f"Ambiguity detection: score={score:.2f}, level={level.value}, "
            f"reasons={reasons}"
        )
        
        return score, level, reasons
    
    def should_ask_clarification(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if StillMe should ask for clarification.
        
        Args:
            query: User query string
            conversation_history: Optional conversation history for context
            
        Returns:
            Tuple of (should_ask, clarification_question)
            - should_ask: True if should ask for clarification
            - clarification_question: Suggested clarification question (if should_ask)
        """
        score, level, reasons = self.detect_ambiguity(query, conversation_history)
        
        if level == AmbiguityLevel.HIGH:
            # Generate clarification question based on ambiguity reasons
            clarification = self._generate_clarification_question(query, reasons, conversation_history)
            return True, clarification
        else:
            return False, None
    
    def _generate_clarification_question(
        self,
        query: str,
        reasons: List[str],
        conversation_history: Optional[List[dict]] = None
    ) -> str:
        """
        Generate a natural clarification question.
        
        Philosophy: StillMe should ask like a thoughtful human, not a robot.
        """
        query_lower = query.lower()
        
        # Detect language
        is_vietnamese = any(
            char in query for char in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
        )
        
        # Pattern 1: Pronoun without referent
        if "Pronoun without clear referent" in str(reasons):
            if is_vietnamese:
                return "Bạn đang nói về điều gì cụ thể? Có thể bạn muốn nói về chủ đề nào đó từ câu hỏi trước không?"
            else:
                return "Could you clarify what you're referring to? Are you asking about something from our previous conversation?"
        
        # Pattern 2: Multi-interpretation without topic
        if "Multi-interpretation pattern without clear topic" in str(reasons):
            if is_vietnamese:
                return "Bạn muốn so sánh hoặc phân tích về chủ đề nào cụ thể? Ví dụ: Python, Java, một công nghệ, hay một khái niệm nào đó?"
            else:
                return "What specific topic would you like me to compare or analyze? For example: Python, Java, a technology, or a concept?"
        
        # Pattern 3: Follow-up without context
        if "Follow-up question without clear context" in str(reasons):
            if is_vietnamese:
                return "Bạn đang hỏi về điều gì cụ thể? Có thể bạn muốn nói về chủ đề nào từ câu hỏi trước không?"
            else:
                return "What specifically are you asking about? Are you referring to something from our previous conversation?"
        
        # Pattern 4: Ambiguous reference (StillMe vs topic)
        if "Ambiguous reference" in str(reasons):
            if is_vietnamese:
                return "Bạn đang hỏi về nhược điểm/ưu điểm của StillMe (bản thân mình) hay của một chủ đề/công nghệ nào đó? Ví dụ: Python, Java, hay một khái niệm?"
            else:
                return "Are you asking about the weaknesses/advantages of StillMe (myself) or of a specific topic/technology? For example: Python, Java, or a concept?"
        
        # Pattern 5: Very short query
        if "Very short query" in str(reasons):
            if is_vietnamese:
                return "Bạn có thể diễn đạt rõ hơn câu hỏi của bạn không? Mình muốn hiểu chính xác bạn đang hỏi về điều gì."
            else:
                return "Could you elaborate on your question? I'd like to understand exactly what you're asking about."
        
        # Default clarification
        if is_vietnamese:
            return "Mình muốn đảm bảo mình hiểu đúng ý bạn. Bạn có thể làm rõ câu hỏi của bạn không? Ví dụ: bạn đang hỏi về chủ đề nào, trong bối cảnh nào?"
        else:
            return "I want to make sure I understand correctly. Could you clarify your question? For example: what topic are you asking about, in what context?"


# Global instance
_ambiguity_detector: Optional[AmbiguityDetector] = None


def get_ambiguity_detector() -> AmbiguityDetector:
    """Get global ambiguity detector instance"""
    global _ambiguity_detector
    if _ambiguity_detector is None:
        _ambiguity_detector = AmbiguityDetector()
    return _ambiguity_detector

