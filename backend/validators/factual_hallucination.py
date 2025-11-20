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
                
                # CRITICAL: If question contains non-existent concepts, check if answer describes them
                # This includes ANY description (not just assertive), because describing non-existent concepts
                # is a form of hallucination, even with disclaimers
                # Also check if answer describes entities that are NOT in KCI (unknown concepts)
                should_check_entities = (
                    not fps_result.is_plausible or 
                    fps_result.confidence < 0.5 or
                    len(ctx_docs) == 0  # No context = higher risk of hallucination
                )
                
                if should_check_entities:
                    # Extract entities from question (use FPS detected entities or extract from question)
                    question_entities = fps_result.detected_entities if fps_result.detected_entities else self.fps.extract_entities(user_question)
                    
                    # Check if answer describes these entities in detail
                    for entity in question_entities:
                        if not entity or len(entity) < 3:
                            continue
                            
                        entity_lower = entity.lower()
                        if entity_lower in answer_lower:
                            # CRITICAL: Check if answer describes the entity in detail
                            # Patterns that indicate detailed description (even with disclaimer):
                            detail_patterns = [
                                r"tác\s+động",  # "tác động" (impact)
                                r"lập\s+luận",  # "lập luận" (arguments)
                                r"hậu\s+quả",  # "hậu quả" (consequences)
                                r"ảnh\s+hưởng",  # "ảnh hưởng" (influence)
                                r"kết\s+quả",  # "kết quả" (results)
                                r"nguyên\s+nhân",  # "nguyên nhân" (causes)
                                r"impact",  # "impact"
                                r"effect",  # "effect"
                                r"consequence",  # "consequence"
                                r"result",  # "result"
                                r"cause",  # "cause"
                                r"argument",  # "argument"
                                r"helped",  # "helped"
                                r"reduced",  # "reduced"
                                r"created",  # "created"
                                r"giúp",  # "giúp" (helped)
                                r"giảm",  # "giảm" (reduced)
                                r"tạo",  # "tạo" (created)
                            ]
                            
                            # Find entity position in answer
                            entity_pos = answer_lower.find(entity_lower)
                            if entity_pos != -1:
                                # Look for detail patterns in a window around the entity
                                window_start = max(0, entity_pos - 300)
                                window_end = min(len(answer_lower), entity_pos + 300)
                                window_text = answer_lower[window_start:window_end]
                                
                                # Check if any detail pattern appears near the entity
                                has_detail_description = any(
                                    re.search(pattern, window_text) for pattern in detail_patterns
                                )
                                
                                # CRITICAL: If answer describes details about non-existent concept,
                                # this is hallucination, even with disclaimer
                                if has_detail_description:
                                    # Check if entity is NOT in KCI (unknown concept)
                                    if not self.fps.kci.check_term(entity):
                                        reasons.append(
                                            f"detailed_description_of_non_existent_concept: {entity}"
                                        )
                                        logger.warning(
                                            f"FactualHallucinationValidator: Answer describes non-existent "
                                            f"concept '{entity}' in detail (even with disclaimer). "
                                            f"This is hallucination and must be blocked."
                                        )
                                        
                                        # Also check for assertive phrases (original logic)
                                        for phrase_pattern in self.assertive_phrases:
                                            if re.search(phrase_pattern, window_text):
                                                reasons.append(
                                                    f"assertive_description_of_non_existent_concept: {entity}"
                                                )
                                                logger.warning(
                                                    f"FactualHallucinationValidator: Answer describes non-existent "
                                                    f"concept '{entity}' with certainty"
                                                )
                                                break  # Don't duplicate reasons
            
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
        
        CRITICAL: This response must be strong, clear, and honest - no ambiguity.
        "Thà nói 'mình không biết' 100 lần còn hơn bịa 1 lần cho có vẻ thông minh."
        
        Returns:
            Safe refusal answer that completely replaces hallucinated narrative
        """
        # Try to extract the suspicious entity using improved extraction
        suspicious_entity = None
        if user_question:
            # Use FPS to extract entities
            entities = self.fps.extract_entities(user_question)
            if entities:
                suspicious_entity = entities[0]
            else:
                # Fallback: try to extract from question using regex
                import re
                # Look for quoted terms first
                quoted_match = re.search(r'["\']([^"\']+)["\']', user_question)
                if quoted_match:
                    suspicious_entity = quoted_match.group(1).strip()
                else:
                    # Look for Vietnamese patterns
                    vietnamese_patterns = [
                        r"(?:Hiệp ước|Hội nghị|Hội chứng|Định đề|Học thuyết|Chủ nghĩa)\s+[^\\.\\?\\!\\n]+",
                    ]
                    for pattern in vietnamese_patterns:
                        match = re.search(pattern, user_question, re.IGNORECASE)
                        if match:
                            suspicious_entity = match.group(0).strip()
                            break
        
        if not suspicious_entity:
            suspicious_entity = "khái niệm này"
        
        # Build strong, clear refusal answer (same format as _build_safe_refusal_answer)
        answer = (
            f"Mình không tìm thấy bất kỳ nguồn đáng tin cậy nào trong hệ thống về sự kiện/khái niệm có tên là \"{suspicious_entity}\".\n\n"
            f"Có một số khả năng:\n"
            f"- Đây là ví dụ giả định, tên tưởng tượng, hoặc một khái niệm chưa được ghi nhận rộng rãi trong các nguồn mà mình có.\n"
            f"- Hoặc nó trùng với một tên gọi khác trong lịch sử nhưng mình không đủ dữ liệu để khẳng định.\n\n"
            f"Vì không có bằng chứng, mình **không thể mô tả** \"các lập luận chính\" hay \"tác động lịch sử\" của \"{suspicious_entity}\" mà vẫn trung thực được.\n\n"
            f"Nếu bạn có nguồn cụ thể (bài báo, sách, link), bạn có thể gửi, mình sẽ chỉ phân tích nội dung dựa trên nguồn đó – chứ không tự tạo thêm chi tiết."
        )
        
        return answer

