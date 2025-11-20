"""
Question Classifier V2 - Enhanced classification for Option B pipeline

Classifies questions into:
- factual_academic: History, economics, science, treaties, conferences, papers, events
- factual_technical: Code, system architecture, algorithms
- philosophical_meta: Consciousness, reality, subjective/objective, knowledge, logic
- imaginative/creative: Fiction, fantasy, roleplay

CRITICAL: This classifier is used to route questions through the appropriate
pipeline path in Option B (zero-tolerance hallucination, deep philosophical analysis).
"""

import re
import logging
from typing import Optional, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Question type classification"""
    FACTUAL_ACADEMIC = "factual_academic"  # History, science, economics, treaties, conferences
    FACTUAL_TECHNICAL = "factual_technical"  # Code, architecture, algorithms
    PHILOSOPHICAL_META = "philosophical_meta"  # Consciousness, reality, knowledge, logic
    IMAGINATIVE_CREATIVE = "imaginative_creative"  # Fiction, fantasy, roleplay
    UNKNOWN = "unknown"  # Cannot classify


class QuestionClassifierV2:
    """
    Enhanced question classifier for Option B pipeline
    
    Classifies questions to determine:
    1. Which pipeline path to use
    2. Whether to apply strict hallucination guard
    3. Whether to apply deep philosophical analysis
    4. Whether to skip RAG (for certain question types)
    """
    
    def __init__(self):
        """Initialize classifier"""
        # Factual academic indicators (history, science, economics, treaties, conferences)
        self.factual_academic_patterns = [
            # History
            r"\b(năm|year|thế kỷ|century|thập niên|decade|thời kỳ|period|era)\s+\d{4}",
            r"\b(chiến tranh|war|battle|trận|conflict|cuộc|event|sự kiện)",
            r"\b(hiệp ước|treaty|hiệp định|agreement|conference|hội nghị)",
            r"\b(đế chế|empire|vương quốc|kingdom|quốc gia|nation|country)",
            r"\b(tổng thống|president|vua|king|hoàng đế|emperor|chính trị gia|politician)",
            
            # Science & Research
            r"\b(lý thuyết|theory|định luật|law|nguyên lý|principle)",
            r"\b(nghiên cứu|research|study|thí nghiệm|experiment|quan sát|observation)",
            r"\b(phát minh|invention|khám phá|discovery|bằng sáng chế|patent)",
            r"\b(hội chứng|syndrome|bệnh|disease|phản ứng|reaction|mechanism)",
            r"\b(tiến sĩ|dr\.|doctor|professor|giáo sư|scientist|nhà khoa học)",
            r"\b(paper|bài báo|journal|tạp chí|publication|công bố)",
            r"\b(volume|vol\.|tập|issue|số)",
            
            # Economics & Politics
            r"\b(kinh tế|economy|economic|tài chính|finance|financial)",
            r"\b(chính sách|policy|chính trị|politics|political)",
            r"\b(tổ chức|organization|liên minh|alliance|phong trào|movement)",
            
            # Specific entities
            r"\b(hiện tượng|phenomenon|khái niệm|concept|thực thể|entity)",
        ]
        
        # Factual technical indicators (code, architecture, algorithms)
        self.factual_technical_patterns = [
            r"\b(code|mã|programming|program|function|hàm|class|lớp)",
            r"\b(algorithm|thuật toán|data structure|cấu trúc dữ liệu)",
            r"\b(architecture|kiến trúc|system design|thiết kế hệ thống)",
            r"\b(api|endpoint|database|cơ sở dữ liệu|database)",
            r"\b(framework|library|thư viện|package|gói)",
            r"\b(debug|fix|sửa lỗi|error|lỗi|bug)",
            r"\b(implementation|triển khai|deploy|deployment)",
        ]
        
        # Philosophical meta indicators (consciousness, reality, knowledge, logic)
        self.philosophical_meta_patterns = [
            r"\b(ý thức|consciousness|self-awareness|nhận thức bản thân)",
            r"\b(thực tại|reality|thực tế|existence|tồn tại)",
            r"\b(chủ quan|subjective|khách quan|objective)",
            r"\b(tri thức|knowledge|epistemology|nhận thức luận)",
            r"\b(logic|logic|paradox|nghịch lý|contradiction)",
            r"\b(truth|chân lý|truth|certainty|chắc chắn)",
            r"\b(meaning|ý nghĩa|meaning|purpose|mục đích)",
            r"\b(free will|ý chí tự do|determinism|quyết định luận)",
            r"\b(ethics|đạo đức|morality|moral|đạo đức học)",
            r"\b(metaphysics|siêu hình học|ontology|bản thể luận)",
            r"\b(phenomenology|hiện tượng học|qualia|subjective experience)",
        ]
        
        # Imaginative/creative indicators (fiction, fantasy, roleplay)
        self.imaginative_patterns = [
            r"\b(truyện|story|fiction|tiểu thuyết|novel)",
            r"\b(fantasy|giả tưởng|magic|phép thuật)",
            r"\b(roleplay|đóng vai|pretend|giả vờ)",
            r"\b(imagine|tưởng tượng|what if|nếu như)",
            r"\b(character|nhân vật|protagonist|nhân vật chính)",
        ]
        
        # Suspicious patterns that suggest fabricated concepts
        self.suspicious_patterns = [
            # Fake academic patterns
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+Postulate\b",  # "Veridian Anti-Realist Postulate"
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+Theorem\b",  # "Emerald Meta-Linguistic Theorem"
            r"\b[A-Z][a-z]+\s+Syndrome\b",  # "Veridian Syndrome"
            r"\bHội\s+chứng\s+[A-Z][a-z]+\b",  # "Hội chứng Veridian"
            r"\b[A-Z][a-z]+\s+Conference\s+\d{4}\b",  # "Lisbon Peace Conference 1943" (if not in KCI)
            r"\b[A-Z][a-z]+\s+Treaty\s+\d{4}\b",  # "Daxonia Treaty 1956" (if not in KCI)
            r"\bHiệp\s+ước\s+[A-Z][a-z]+\s+\d{4}\b",  # "Hiệp ước Daxonia 1956"
        ]
    
    def classify(self, question: str) -> Tuple[QuestionType, float, List[str]]:
        """
        Classify question into one of the types
        
        Args:
            question: User question text
            
        Returns:
            Tuple of (question_type, confidence, detected_patterns)
            - question_type: QuestionType enum
            - confidence: 0.0 to 1.0 (how confident we are in the classification)
            - detected_patterns: List of patterns that matched
        """
        question_lower = question.lower()
        detected_patterns = []
        scores = {
            QuestionType.FACTUAL_ACADEMIC: 0.0,
            QuestionType.FACTUAL_TECHNICAL: 0.0,
            QuestionType.PHILOSOPHICAL_META: 0.0,
            QuestionType.IMAGINATIVE_CREATIVE: 0.0,
        }
        
        # Check factual academic patterns
        for pattern in self.factual_academic_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                scores[QuestionType.FACTUAL_ACADEMIC] += 0.1
                detected_patterns.append(f"factual_academic: {pattern}")
        
        # Check factual technical patterns
        for pattern in self.factual_technical_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                scores[QuestionType.FACTUAL_TECHNICAL] += 0.1
                detected_patterns.append(f"factual_technical: {pattern}")
        
        # Check philosophical meta patterns
        for pattern in self.philosophical_meta_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                scores[QuestionType.PHILOSOPHICAL_META] += 0.1
                detected_patterns.append(f"philosophical_meta: {pattern}")
        
        # Check imaginative patterns
        for pattern in self.imaginative_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                scores[QuestionType.IMAGINATIVE_CREATIVE] += 0.1
                detected_patterns.append(f"imaginative: {pattern}")
        
        # Find the type with highest score
        max_score = max(scores.values())
        if max_score == 0.0:
            return QuestionType.UNKNOWN, 0.0, []
        
        # Get the type with highest score
        question_type = max(scores.items(), key=lambda x: x[1])[0]
        
        # Calculate confidence (normalize to 0.0-1.0)
        total_score = sum(scores.values())
        confidence = min(1.0, max_score / max(total_score, 1.0))
        
        # Check for suspicious patterns (fabricated concepts)
        suspicious_patterns_found = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                suspicious_patterns_found.append(pattern)
        
        # If suspicious patterns found, mark as suspected fabricated
        if suspicious_patterns_found:
            detected_patterns.append(f"suspicious_patterns: {suspicious_patterns_found}")
            logger.warning(
                f"QuestionClassifierV2: Suspicious patterns detected in question: {suspicious_patterns_found}"
            )
        
        return question_type, confidence, detected_patterns
    
    def is_suspected_fabricated(self, question: str) -> Tuple[bool, List[str]]:
        """
        Check if question contains suspected fabricated concepts
        
        Args:
            question: User question text
            
        Returns:
            Tuple of (is_suspected, suspicious_patterns)
        """
        suspicious_patterns_found = []
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            if matches:
                suspicious_patterns_found.extend(matches)
        
        return len(suspicious_patterns_found) > 0, suspicious_patterns_found


# Singleton instance
_classifier_instance: Optional[QuestionClassifierV2] = None


def get_question_classifier_v2() -> QuestionClassifierV2:
    """Get singleton instance of QuestionClassifierV2"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = QuestionClassifierV2()
    return _classifier_instance


def classify_question(question: str) -> Tuple[QuestionType, float, List[str]]:
    """
    Convenience function to classify a question
    
    Args:
        question: User question text
        
    Returns:
        Tuple of (question_type, confidence, detected_patterns)
    """
    classifier = get_question_classifier_v2()
    return classifier.classify(question)

