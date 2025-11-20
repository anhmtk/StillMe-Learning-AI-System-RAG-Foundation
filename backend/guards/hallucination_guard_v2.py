"""
Hallucination Guard V2 - Enhanced detection for Option B pipeline

Detects hallucinations in LLM responses:
- Non-existent entities (people, treaties, conferences, papers, journals)
- Fabricated citations (e.g., "Smith, A. et al. (1975)")
- Fake organizations, countries, alliances
- Assertive descriptions of unverified concepts
- Detailed descriptions of non-existent concepts (even with disclaimers)
- Academic-style fabrication patterns

CRITICAL: This guard is MANDATORY for Option B pipeline.
It must run on ALL responses before Rewrite 1.
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HallucinationDetection:
    """Result of hallucination detection"""
    is_hallucination: bool  # True if hallucination detected
    confidence: float  # 0.0 to 1.0 (how confident we are)
    reasons: List[str]  # List of reasons why it's hallucination
    detected_entities: List[str]  # Entities that are suspicious
    suspicious_patterns: List[str]  # Patterns that suggest fabrication
    has_contradiction: bool  # True if response contradicts itself (e.g., "I don't know" + detailed explanation)


class HallucinationGuardV2:
    """
    Enhanced hallucination guard for Option B pipeline
    
    Detects:
    1. Non-existent entities (not in KCI)
    2. Fabricated citations
    3. Fake source references
    4. Assertive descriptions of unverified concepts
    5. Detailed descriptions of non-existent concepts (even with disclaimers)
    6. Self-contradictory responses (e.g., "I don't know" + detailed explanation)
    """
    
    def __init__(self):
        """Initialize hallucination guard"""
        # Load FPS and KCI
        from backend.knowledge.factual_scanner import get_fps
        self.fps = get_fps()
        
        # Patterns that indicate fabrication
        self.fake_citation_patterns = [
            r"\b[A-Z][a-z]+,\s*[A-Z]\.\s+et\s+al\.\s*\(\d{4}\)",  # "Smith, A. et al. (1975)"
            r"\b[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)",  # "Smith et al. (1975)"
            r"\bJournal\s+of\s+[A-Z][a-z]+\s+Studies\s+\(\d{4}\)",  # "Journal of X Studies (1975)"
            r"\bVolume\s+\d+\s+\(\d{4}\)",  # "Volume 12 (1975)"
            r"\b[A-Z][a-z]+,\s*[A-Z]\.\s+\(\d{4}\)\.\s*\"[^\"]+\"",  # "Smith, A. (1975). \"Title\""
        ]
        
        # Assertive phrases that suggest certainty about unverified facts
        self.assertive_phrases = [
            r"\baccording\s+to\s+research\b",
            r"\bstudies\s+show\b",
            r"\bresearch\s+indicates\b",
            r"\bit\s+is\s+known\s+that\b",
            r"\bthe\s+theory\s+was\s+proposed\b",
            r"\bthe\s+concept\s+was\s+developed\b",
            r"\bđược\s+đề\s+xuất\b",
            r"\btheo\s+nghiên\s+cứu\b",
            r"\btheo\s+tài\s+liệu\b",
            r"\btham\s+khảo\s+nguồn\b",
        ]
        
        # Phrases that indicate uncertainty/acknowledgment of lack of knowledge
        self.uncertainty_phrases = [
            r"\bI\s+don'?t\s+know\b",
            r"\btôi\s+không\s+biết\b",
            r"\bkhông\s+có\s+đủ\s+thông\s+tin\b",
            r"\bnot\s+enough\s+information\b",
            r"\bkhông\s+tìm\s+thấy\s+nguồn\b",
            r"\bno\s+sources\s+found\b",
            r"\bkhông\s+chắc\s+chắn\b",
            r"\bnot\s+certain\b",
            r"\bnguồn\s+liên\s+quan\s+thấp\b",
            r"\blow\s+confidence\b",
        ]
        
        # Detail description keywords (if these appear near a suspicious entity, it's likely hallucination)
        self.detail_keywords = [
            r"\btác\s+động\b",  # "tác động" (impact)
            r"\blập\s+luận\b",  # "lập luận" (arguments)
            r"\bhậu\s+quả\b",  # "hậu quả" (consequences)
            r"\bảnh\s+hưởng\b",  # "ảnh hưởng" (influence)
            r"\bkết\s+quả\b",  # "kết quả" (results)
            r"\bnguyên\s+nhân\b",  # "nguyên nhân" (causes)
            r"\bimpact\b",
            r"\beffect\b",
            r"\bconsequence\b",
            r"\bresult\b",
            r"\bcause\b",
            r"\bargument\b",
            r"\bhelped\b",
            r"\breduced\b",
            r"\bcreated\b",
            r"\bgiúp\b",
            r"\bgiảm\b",
            r"\btạo\b",
        ]
    
    def detect(
        self,
        answer: str,
        user_question: str,
        ctx_docs: List[str],
        question_type: str,
        fps_result: Optional[object] = None
    ) -> HallucinationDetection:
        """
        Detect hallucinations in answer
        
        Args:
            answer: LLM-generated answer
            user_question: Original user question
            ctx_docs: Context documents from RAG
            question_type: Question type (from QuestionClassifierV2)
            fps_result: FPS scan result (optional)
            
        Returns:
            HallucinationDetection with detection results
        """
        if not answer:
            return HallucinationDetection(
                is_hallucination=False,
                confidence=0.0,
                reasons=[],
                detected_entities=[],
                suspicious_patterns=[],
                has_contradiction=False
            )
        
        reasons = []
        detected_entities = []
        suspicious_patterns = []
        has_contradiction = False
        
        answer_lower = answer.lower()
        question_lower = user_question.lower()
        
        # Only apply strict guard for factual_academic questions
        if question_type == "factual_academic":
            # 1. Check for fake citations
            for pattern in self.fake_citation_patterns:
                matches = re.findall(pattern, answer, re.IGNORECASE)
                if matches:
                    reasons.append(f"fake_citation_detected: {matches}")
                    suspicious_patterns.append(f"citation_pattern: {pattern}")
                    logger.warning(f"HallucinationGuardV2: Fake citations detected: {matches}")
            
            # 2. Check for fake source references (when no context)
            if len(ctx_docs) == 0:
                fake_source_patterns = [
                    r"History\.com",
                    r"Britannica",
                    r"theo\s+nghiên\s+cứu",
                    r"theo\s+tài\s+liệu",
                    r"tham\s+khảo\s+nguồn",
                ]
                for pattern in fake_source_patterns:
                    if re.search(pattern, answer_lower):
                        reasons.append(f"fake_source_reference_detected: {pattern}")
                        suspicious_patterns.append(f"source_pattern: {pattern}")
                        logger.warning(f"HallucinationGuardV2: Fake source reference detected: {pattern}")
            
            # 3. Check entities against FPS/KCI
            if fps_result:
                question_entities = fps_result.detected_entities if fps_result.detected_entities else []
                
                for entity in question_entities:
                    if not entity or len(entity) < 3:
                        continue
                    
                    entity_lower = entity.lower()
                    if entity_lower in answer_lower:
                        # Check if entity is in KCI
                        entity_in_kci = self.fps.kci.check_term(entity)
                        
                        if not entity_in_kci:
                            # Entity not in KCI - check if answer describes it in detail
                            entity_pos = answer_lower.find(entity_lower)
                            if entity_pos != -1:
                                # Look for detail keywords in window around entity
                                window_start = max(0, entity_pos - 300)
                                window_end = min(len(answer_lower), entity_pos + 300)
                                window_text = answer_lower[window_start:window_end]
                                
                                # Check if any detail keyword appears near the entity
                                has_detail = any(
                                    re.search(pattern, window_text) for pattern in self.detail_keywords
                                )
                                
                                if has_detail:
                                    reasons.append(
                                        f"detailed_description_of_non_existent_concept: {entity}"
                                    )
                                    detected_entities.append(entity)
                                    logger.warning(
                                        f"HallucinationGuardV2: Answer describes non-existent "
                                        f"concept '{entity}' in detail"
                                    )
                                else:
                                    # Even without detail, if entity is mentioned and not in KCI, it's suspicious
                                    reasons.append(f"non_existent_concept_mentioned: {entity}")
                                    detected_entities.append(entity)
            
            # 4. Check for self-contradiction
            # Pattern: "I don't know" / "không tìm thấy nguồn" + detailed explanation
            has_uncertainty_phrase = any(
                re.search(pattern, answer_lower) for pattern in self.uncertainty_phrases
            )
            
            if has_uncertainty_phrase:
                # Check if answer also contains detailed descriptions
                has_assertive = any(
                    re.search(pattern, answer_lower) for pattern in self.assertive_phrases
                )
                
                # Check if answer contains detail keywords (suggesting detailed explanation)
                has_detail = any(
                    re.search(pattern, answer_lower) for pattern in self.detail_keywords
                )
                
                # If answer says "I don't know" but then provides detailed explanation, it's contradictory
                if has_assertive or has_detail:
                    has_contradiction = True
                    reasons.append("self_contradiction: uncertainty_phrase_with_detailed_explanation")
                    logger.warning(
                        "HallucinationGuardV2: Self-contradiction detected: "
                        "answer claims uncertainty but provides detailed explanation"
                    )
        
        # Determine if hallucination detected
        is_hallucination = len(reasons) > 0 or has_contradiction
        
        # Calculate confidence
        confidence = min(1.0, len(reasons) * 0.3 + (0.5 if has_contradiction else 0.0))
        
        return HallucinationDetection(
            is_hallucination=is_hallucination,
            confidence=confidence,
            reasons=reasons,
            detected_entities=detected_entities,
            suspicious_patterns=suspicious_patterns,
            has_contradiction=has_contradiction
        )


# Singleton instance
_guard_instance: Optional[HallucinationGuardV2] = None


def get_hallucination_guard_v2() -> HallucinationGuardV2:
    """Get singleton instance of HallucinationGuardV2"""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = HallucinationGuardV2()
    return _guard_instance

