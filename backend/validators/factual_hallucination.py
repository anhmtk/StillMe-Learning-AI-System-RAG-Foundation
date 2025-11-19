"""
Factual Hallucination Validator
Detects hallucinations in history/science questions:
- Non-existent events/concepts described with certainty
- Fabricated citations, research papers, authors
- Fake organizations, countries, alliances
"""

import re
import logging
from typing import List, Optional
from .base import Validator, ValidationResult
from backend.knowledge.factual_scanner import get_fps, FPSResult

logger = logging.getLogger(__name__)


class FactualHallucinationValidator(Validator):
    """
    Validator to detect factual hallucinations in history/science questions
    
    Detects:
    - Non-existent events/concepts described with certainty
    - Fabricated citations (e.g., "Smith, A. et al. (1975)")
    - Fake organizations, countries, alliances
    - Assertive descriptions of unverified concepts
    """
    
    def __init__(self):
        super().__init__()
        self.fps = get_fps()
        
        # Patterns that indicate fabrication
        self.fake_citation_patterns = [
            r"\b[A-Z][a-z]+,\s*[A-Z]\.\s+et\s+al\.\s*\(\d{4}\)",  # "Smith, A. et al. (1975)"
            r"\b[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)",  # "Smith et al. (1975)"
            r"\bJournal\s+of\s+[A-Z][a-z]+\s+Studies\s+\(\d{4}\)",  # "Journal of X Studies (1975)"
        ]
        
        # Assertive phrases that suggest certainty about unverified facts
        self.assertive_phrases = [
            r"\baccording\s+to\s+research\b",  # "according to research"
            r"\bstudies\s+show\b",  # "studies show"
            r"\bresearch\s+indicates\b",  # "research indicates"
            r"\bit\s+is\s+known\s+that\b",  # "it is known that"
            r"\bthe\s+theory\s+was\s+proposed\b",  # "the theory was proposed"
            r"\bthe\s+concept\s+was\s+developed\b",  # "the concept was developed"
            r"\bđược\s+đề\s+xuất\b",  # "được đề xuất" (was proposed)
            r"\btheo\s+nghiên\s+cứu\b",  # "theo nghiên cứu" (according to research)
        ]
        
        # Fake URL patterns
        self.fake_url_patterns = [
            r"exemple-source\.com",
            r"example\.com",
            r"test-url\.com",
            r"fake-source\.com",
            r"placeholder\.com",
        ]
    
    def run(self, answer: str, ctx_docs: List[str], user_question: Optional[str] = None, **kwargs) -> ValidationResult:
        """
        Run validation (implements Validator protocol)
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            user_question: User's original question (optional, passed via kwargs in chain)
            **kwargs: Additional parameters (may include user_question)
        
        Returns:
            ValidationResult
        """
        # Extract user_question from kwargs if not provided directly
        if user_question is None:
            user_question = kwargs.get("user_question")
        return self.validate(answer, ctx_docs, user_question, **kwargs)
    
    def validate(self, answer: str, ctx_docs: List[str] = None, 
                 user_question: Optional[str] = None, **kwargs) -> ValidationResult:
        """
        Validate answer for factual hallucinations
        
        Args:
            answer: The answer to validate
            ctx_docs: Context documents (not used for this validator)
            user_question: User's original question (used to check if question is about history/science)
        
        Returns:
            ValidationResult
        """
        if not answer:
            return ValidationResult(passed=True, reasons=[])
        
        reasons = []
        answer_lower = answer.lower()
        
        # Check if question is about history/science
        is_history_science_question = False
        if user_question:
            question_lower = user_question.lower()
            history_science_keywords = [
                r"\bconference\s+\d{4}\b",
                r"\btreaty\s+\d{4}\b",
                r"\bwar\s+\d{4}\b",
                r"\bsyndrome\b",
                r"\bfusion\b",
                r"\bfield\b",
                r"\btheory\b",
                r"\bresearch\b",
                r"\bstudy\b",
                r"\bhội\s+nghị\b",
                r"\bhiệp\s+ước\b",
                r"\bhội\s+chứng\b",
                r"\blý\s+thuyết\b",
                r"\bnghiên\s+cứu\b",
            ]
            is_history_science_question = any(
                re.search(pattern, question_lower) for pattern in history_science_keywords
            )
        
        # If not a history/science question, skip detailed validation
        if not is_history_science_question:
            # Still check for obvious fake citations
            for pattern in self.fake_citation_patterns:
                if re.search(pattern, answer, re.IGNORECASE):
                    reasons.append(f"fake_citation_detected: {pattern}")
                    logger.warning(f"FactualHallucinationValidator detected fake citation: {pattern}")
        
        # For history/science questions, do comprehensive validation
        if is_history_science_question:
            # 1. Check for fake citations
            for pattern in self.fake_citation_patterns:
                matches = re.findall(pattern, answer, re.IGNORECASE)
                if matches:
                    reasons.append(f"fake_citation_detected: {matches}")
                    logger.warning(f"FactualHallucinationValidator detected fake citations: {matches}")
            
            # 2. Check for fake URLs
            for pattern in self.fake_url_patterns:
                if re.search(pattern, answer_lower):
                    reasons.append(f"fake_url_detected: {pattern}")
                    logger.warning(f"FactualHallucinationValidator detected fake URL: {pattern}")
            
            # 3. Check answer against FPS
            if user_question:
                fps_result = self.fps.scan(user_question)
                
                # If question contains non-existent concepts, check if answer describes them with certainty
                if not fps_result.is_plausible:
                    # Check if answer describes these concepts assertively
                    for entity in fps_result.detected_entities:
                        if entity.lower() in answer_lower:
                            # Check if answer uses assertive phrases about this entity
                            for phrase_pattern in self.assertive_phrases:
                                # Check if assertive phrase appears near the entity
                                entity_pos = answer_lower.find(entity.lower())
                                if entity_pos != -1:
                                    # Look for assertive phrases in a window around the entity
                                    window_start = max(0, entity_pos - 200)
                                    window_end = min(len(answer_lower), entity_pos + 200)
                                    window_text = answer_lower[window_start:window_end]
                                    
                                    if re.search(phrase_pattern, window_text):
                                        reasons.append(
                                            f"assertive_description_of_non_existent_concept: {entity}"
                                        )
                                        logger.warning(
                                            f"FactualHallucinationValidator: Answer describes non-existent "
                                            f"concept '{entity}' with certainty"
                                        )
            
            # 4. Check for assertive phrases without citations (when describing specific concepts)
            # This catches cases where answer makes strong claims without evidence
            if user_question:
                # Extract entities from question
                question_entities = self.fps.extract_entities(user_question)
                
                for entity in question_entities:
                    if entity.lower() in answer_lower:
                        # Check if answer uses assertive phrases about this entity
                        entity_pos = answer_lower.find(entity.lower())
                        if entity_pos != -1:
                            window_start = max(0, entity_pos - 200)
                            window_end = min(len(answer_lower), entity_pos + 200)
                            window_text = answer_lower[window_start:window_end]
                            
                            # Check for assertive phrases
                            has_assertive = any(
                                re.search(pattern, window_text) 
                                for pattern in self.assertive_phrases
                            )
                            
                            # Check for citations in the window
                            has_citation = bool(re.search(r'\[\d+\]', window_text))
                            
                            # If assertive but no citation, and entity is not in KCI, flag it
                            if has_assertive and not has_citation:
                                if not self.fps.kci.check_term(entity):
                                    reasons.append(
                                        f"assertive_claim_without_citation_for_unknown_entity: {entity}"
                                    )
                                    logger.warning(
                                        f"FactualHallucinationValidator: Answer makes assertive claim about "
                                        f"unknown entity '{entity}' without citation"
                                    )
        
        # If we found issues, return failure with patched answer
        if reasons:
            # Create patched answer that acknowledges uncertainty
            patched_answer = self._create_honest_response(user_question)
            return ValidationResult(
                passed=False,
                reasons=reasons,
                patched_answer=patched_answer
            )
        
        return ValidationResult(passed=True, reasons=[])
    
    def _create_honest_response(self, user_question: Optional[str] = None) -> str:
        """
        Create an honest response when hallucination is detected
        
        Returns:
            Template response acknowledging uncertainty
        """
        if user_question:
            # Try to extract the suspicious entity
            entities = self.fps.extract_entities(user_question)
            if entities:
                entity = entities[0]
                return (
                    f"Tôi không thể xác nhận tính xác thực của thông tin về '{entity}'. "
                    f"Dấu hiệu cho thấy đây có thể là khái niệm/sự kiện không có thật hoặc "
                    f"chưa được xác nhận trong các nguồn đáng tin cậy. "
                    f"Vui lòng cung cấp thêm nguồn hoặc mô tả rõ hơn."
                )
        
        return (
            "Tôi không thể xác nhận tính xác thực của thông tin này vì dấu hiệu cho thấy "
            "đây có thể là khái niệm/sự kiện không có thật. "
            "Vui lòng cung cấp thêm nguồn hoặc mô tả rõ hơn."
        )

