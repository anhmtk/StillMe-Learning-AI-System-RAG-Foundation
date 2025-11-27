"""
Philosophical Depth Validator
Validates that philosophical self-reference questions contain required keywords (Gödel, Tarski, paradox, etc.)
"""

import re
import logging
from typing import List, Optional, Dict, Any
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)

# Required keywords for self-reference philosophical questions
SELF_REFERENCE_KEYWORDS = {
    "gödel": ["gödel", "godel", "incompleteness", "bất toàn", "định lý bất toàn"],
    "tarski": ["tarski", "undefinability", "không thể định nghĩa"],
    "paradox": ["paradox", "nghịch lý", "nghịch lí", "circularity", "vòng lặp", "circular"],
    "bootstrapping": ["bootstrapping", "bootstrap", "epistemic circularity", "vòng lặp nhận thức"],
    "infinite_regress": ["infinite regress", "vòng lặp vô hạn", "regress", "lùi vô hạn"],
    "epistemic": ["epistemic", "epistemology", "nhận thức luận", "epistemological"]
}

# Patterns that indicate self-reference questions
SELF_REFERENCE_PATTERNS = [
    r"hệ\s+thống\s+tư\s+duy.*đánh\s+giá.*chính\s+nó",
    r"tư\s+duy.*đánh\s+giá.*chính\s+nó",
    r"tư\s+duy.*vượt.*qua.*giới\s+hạn",
    r"system.*evaluate.*itself",
    r"thought.*evaluate.*itself",
    r"thinking.*about.*thinking",
    r"giá\s+trị.*câu\s+trả\s+lời.*xuất\s+phát.*từ.*hệ\s+thống",
    r"value.*answer.*from.*system",
    r"bootstrap",
    r"bootstrapping",
    r"infinite\s+regress",
    r"vòng\s+lặp.*vô\s+hạn"
]

# Optimistic phrases that should NOT appear (indicates missing paradox acknowledgment)
OPTIMISTIC_PHRASES = [
    r"có\s+thể\s+vượt\s+qua",
    r"có\s+thể\s+đánh\s+giá",
    r"tự\s+phản\s+biện\s+sẽ\s+giúp",
    r"self.*improvement",
    r"cải\s+thiện",
    r"có\s+thể\s+giải\s+quyết"
]


class PhilosophicalDepthValidator(Validator):
    """
    Validates that philosophical self-reference questions contain required keywords
    and acknowledge the paradox (not give optimistic answers).
    """
    
    def __init__(self, min_keywords: int = 2, strict_mode: bool = True):
        """
        Args:
            min_keywords: Minimum number of keyword categories that must appear (default: 2)
            strict_mode: If True, fail validation if optimistic phrases found (default: True)
        """
        self.min_keywords = min_keywords
        self.strict_mode = strict_mode
        logger.info(f"PhilosophicalDepthValidator initialized (min_keywords={min_keywords}, strict_mode={strict_mode})")
    
    def _is_self_reference_question(self, question: str) -> bool:
        """Check if question is about self-reference"""
        if not question:
            return False
        
        question_lower = question.lower()
        for pattern in SELF_REFERENCE_PATTERNS:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return True
        return False
    
    def _check_keywords(self, answer: str) -> Dict[str, Any]:
        """Check which keywords are present in the answer"""
        answer_lower = answer.lower()
        found_keywords = {}
        missing_keywords = {}
        
        for category, keywords in SELF_REFERENCE_KEYWORDS.items():
            found = False
            found_keyword = None
            for keyword in keywords:
                if keyword.lower() in answer_lower:
                    found = True
                    found_keyword = keyword
                    break
            
            if found:
                found_keywords[category] = found_keyword
            else:
                missing_keywords[category] = keywords[0]  # Use first keyword as representative
        
        return {
            "found": found_keywords,
            "missing": missing_keywords,
            "count": len(found_keywords)
        }
    
    def _check_optimistic_phrases(self, answer: str) -> List[str]:
        """Check for optimistic phrases that indicate missing paradox acknowledgment"""
        answer_lower = answer.lower()
        found_phrases = []
        
        for phrase in OPTIMISTIC_PHRASES:
            if re.search(phrase, answer_lower, re.IGNORECASE):
                found_phrases.append(phrase)
        
        return found_phrases
    
    def run(self, answer: str, ctx_docs: List[str] = None, 
            user_question: Optional[str] = None, is_philosophical: bool = False, **kwargs) -> ValidationResult:
        """
        Validate philosophical depth for self-reference questions.
        
        Args:
            answer: The answer to validate
            ctx_docs: Context documents (not used)
            user_question: The user's question
            is_philosophical: Whether this is a philosophical question
            **kwargs: Additional arguments
            
        Returns:
            ValidationResult
        """
        # Only validate if it's a philosophical question
        if not is_philosophical:
            return ValidationResult(passed=True, reasons=[])
        
        # Only validate if it's a self-reference question
        if not user_question or not self._is_self_reference_question(user_question):
            return ValidationResult(passed=True, reasons=[])
        
        logger.info(f"🔍 PhilosophicalDepthValidator: Checking self-reference question: '{user_question[:80]}...'")
        
        # Check keywords
        keyword_check = self._check_keywords(answer)
        found_count = keyword_check["count"]
        missing_keywords = keyword_check["missing"]
        
        # Check for optimistic phrases
        optimistic_phrases = self._check_optimistic_phrases(answer)
        
        # Determine if validation passes
        passed = True
        reasons = []
        
        if found_count < self.min_keywords:
            passed = False
            reasons.append(f"missing_philosophical_keywords")
            logger.warning(
                f"❌ PhilosophicalDepthValidator: Only {found_count}/{len(SELF_REFERENCE_KEYWORDS)} keyword categories found. "
                f"Missing: {list(missing_keywords.keys())}"
            )
        
        if optimistic_phrases and self.strict_mode:
            passed = False
            reasons.append(f"optimistic_answer_missing_paradox")
            logger.warning(
                f"❌ PhilosophicalDepthValidator: Found optimistic phrases: {optimistic_phrases}. "
                f"Answer should acknowledge the paradox, not suggest solutions."
            )
        
        if passed:
            logger.info(
                f"✅ PhilosophicalDepthValidator: Passed. Found {found_count} keyword categories: {list(keyword_check['found'].keys())}"
            )
        else:
            # Create a patched answer that includes missing keywords
            patched_answer = self._create_patched_answer(answer, keyword_check, optimistic_phrases, user_question)
            
            return ValidationResult(
                passed=False,
                reasons=reasons,
                patched_answer=patched_answer,
                metadata={
                    "found_keywords": keyword_check["found"],
                    "missing_keywords": missing_keywords,
                    "optimistic_phrases": optimistic_phrases,
                    "keyword_count": found_count
                }
            )
        
        return ValidationResult(
            passed=True,
            reasons=[],
            metadata={
                "found_keywords": keyword_check["found"],
                "keyword_count": found_count
            }
        )
    
    def _create_patched_answer(self, original_answer: str, keyword_check: Dict[str, Any], 
                               optimistic_phrases: List[str], user_question: str) -> str:
        """
        Create a patched answer that includes missing keywords and acknowledges the paradox.
        This is a fallback - ideally the LLM should generate this correctly.
        """
        # For now, we'll prepend a note about missing philosophical depth
        # In the future, we could use LLM to rewrite the answer
        
        missing = keyword_check["missing"]
        found = keyword_check["found"]
        
        # Build a note about what's missing
        note_parts = []
        
        if missing:
            note_parts.append("Lưu ý: Câu trả lời này cần đề cập đến các khái niệm triết học quan trọng: ")
            missing_list = []
            if "gödel" in missing:
                missing_list.append("định lý bất toàn của Gödel")
            if "tarski" in missing:
                missing_list.append("định lý không thể định nghĩa của Tarski")
            if "paradox" in missing:
                missing_list.append("nghịch lý tự quy chiếu")
            if "bootstrapping" in missing:
                missing_list.append("vấn đề bootstrapping trong nhận thức luận")
            if "infinite_regress" in missing:
                missing_list.append("vòng lặp vô hạn")
            
            if missing_list:
                note_parts.append(", ".join(missing_list))
                note_parts.append(".")
        
        if optimistic_phrases:
            note_parts.append(" Câu trả lời cần thừa nhận rằng đây là một nghịch lý không thể giải quyết, không phải một vấn đề có thể vượt qua bằng 'tự phản biện'.")
        
        if note_parts:
            note = "".join(note_parts)
            # Prepend note to original answer
            return f"{note}\n\n{original_answer}"
        
        return original_answer

