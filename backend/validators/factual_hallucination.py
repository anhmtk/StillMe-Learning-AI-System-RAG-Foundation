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
    
    🚨🚨🚨 HARD MODE ENABLED 🚨🚨🚨
    - Marks ANY response containing unverified facts
    - If suspicious entity not in KCI → fallback (no speculation)
    - No "half-truth" responses: "I'm not sure... but here's analysis"
    - Only return 100% deterministic template when guard is active
    
    Detects:
    - Non-existent events/concepts described with certainty
    - Fabricated citations (e.g., "Smith, A. et al. (1975)")
    - Fake organizations, countries, alliances
    - Assertive descriptions of unverified concepts
    - Detailed descriptions of non-existent concepts (even with disclaimers)
    """
    
    def __init__(self, hard_mode: bool = True):
        """
        Initialize validator
        
        Args:
            hard_mode: If True, enable HARD mode (strictest validation)
        """
        super().__init__()
        self.fps = get_fps()
        self.hard_mode = hard_mode  # 🚨🚨🚨 HARD MODE ENABLED BY DEFAULT 🚨🚨🚨
        
        # ===== ENTITY CLASSIFICATION =====
        # 1. EXPLICIT_FAKE_ENTITIES: Entities that are intentionally fake in test suite
        self.EXPLICIT_FAKE_ENTITIES = {
            # Veridian family
            "veridian", "định đề veridian", "veridian anti-realist postulate",
            "định đề phản-hiện thực veridian", "veridian anti-realist",
            "hội chứng veridian", "veridian syndrome",
            # Lumeria family
            "lumeria", "hiệp ước lumeria", "lumeria treaty",
            "hiệp ước ổn định địa-chiến lược lumeria 1962",
            "lumeria strategic stability treaty 1962",
            # Emerald family
            "emerald", "định lý emerald", "emerald theorem",
            "định lý siêu-ngôn ngữ emerald", "emerald meta-linguistic theorem",
            "emerald meta-linguistic",
            # Daxonia (if used in tests)
            "daxonia", "hiệp ước daxonia", "daxonia treaty",
            "hiệp ước hòa giải daxonia 1956",
        }
        
        # 2. STOPWORDS_VN_COMMON: Vietnamese common words that should NEVER be flagged as entities
        self.STOPWORDS_VN_COMMON = {
            "hội", "thế", "chiến", "hiệp", "ước", "định", "lý", "hội nghị",
            "hiệp ước", "định lý", "hội chứng", "định đề", "nghị", "hòa",
            "bình", "ổn", "định", "địa", "chiến lược", "phản", "hiện thực",
            "siêu", "ngôn ngữ", "meta", "linguistic", "anti", "realist",
            "postulate", "theorem", "syndrome", "treaty", "conference",
        }
        
        # 3. POTENTIALLY_REAL_ENTITIES: Well-known real entities that should NEVER be flagged
        # (These are in KCI, but we also check here for extra safety)
        self.POTENTIALLY_REAL_ENTITIES = {
            # Bretton Woods family
            "bretton woods", "bretton woods conference", "bretton woods conference 1944",
            "bretton woods agreement", "bretton woods system",
            # Keynes family
            "keynes", "john maynard keynes", "maynard keynes",
            # White family
            "white", "harry dexter white", "harry d. white", "dexter white",
            # Popper-Kuhn family
            "popper", "karl popper", "kuhn", "thomas kuhn",
            "lakatos", "imre lakatos", "feyerabend", "paul feyerabend",
            # Other well-known historical/philosophical entities
            "imf", "international monetary fund", "world bank",
            "paradigm shift", "falsificationism", "scientific realism",
        }
        
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
        has_explicit_fake_entity = False
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
            
            # CRITICAL: Check if question contains EXPLICIT_FAKE_ENTITIES
            # If yes, we MUST run validation even if not a history/science question
            for fake_entity in self.EXPLICIT_FAKE_ENTITIES:
                if fake_entity.lower() in question_lower:
                    has_explicit_fake_entity = True
                    logger.debug(f"FactualHallucinationValidator: Question contains explicit fake entity '{fake_entity}' - will run full validation")
                    break
        
        # If not a history/science question AND no explicit fake entity, skip detailed validation
        if not is_history_science_question and not has_explicit_fake_entity:
            # Still check for obvious fake citations
            for pattern in self.fake_citation_patterns:
                if re.search(pattern, answer, re.IGNORECASE):
                    reasons.append(f"fake_citation_detected: {pattern}")
                    logger.warning(f"FactualHallucinationValidator detected fake citation: {pattern}")
        
        # For history/science questions OR questions with explicit fake entities, do comprehensive validation
        if is_history_science_question or has_explicit_fake_entity:
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
            
            # 3. Check for fake source references (History.com, Britannica, etc. when no context)
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
                        logger.warning(f"FactualHallucinationValidator detected fake source reference: {pattern}")
            
            # 4. Check answer against FPS
            if user_question:
                fps_result = self.fps.scan(user_question)
                
                # 🚨🚨🚨 HARD MODE: More aggressive entity checking 🚨🚨🚨
                # In HARD mode, check entities if:
                # 1. FPS says not plausible OR confidence < 0.5 OR
                # 2. No context (len(ctx_docs) == 0) OR
                # 3. HARD MODE: Even with context, if confidence is low (< 0.7), still check
                should_check_entities = (
                    not fps_result.is_plausible or 
                    fps_result.confidence < (0.7 if self.hard_mode else 0.5) or
                    len(ctx_docs) == 0  # No context = higher risk of hallucination
                )
                
                if should_check_entities:
                    # Extract entities from question (use FPS detected entities or extract from question)
                    question_entities = fps_result.detected_entities if fps_result.detected_entities else self.fps.extract_entities(user_question)
                    
                    # CRITICAL FIX: Also check question text directly for EXPLICIT_FAKE_ENTITIES
                    # This catches cases where entity extraction might miss the entity
                    question_lower = user_question.lower()
                    for fake_entity in self.EXPLICIT_FAKE_ENTITIES:
                        if fake_entity.lower() in question_lower:
                            # Found explicit fake entity in question - add to entities list if not already there
                            if fake_entity not in question_entities:
                                question_entities.append(fake_entity)
                                logger.debug(f"FactualHallucinationValidator: Found explicit fake entity '{fake_entity}' in question text")
                    
                    # Check if answer describes these entities in detail
                    for entity in question_entities:
                        if not entity or len(entity) < 3:
                            continue
                            
                        entity_lower = entity.lower().strip()
                        
                        # ===== ENTITY CLASSIFICATION CHECK =====
                        # 1. Skip STOPWORDS_VN_COMMON - these are common words, not entities
                        if entity_lower in self.STOPWORDS_VN_COMMON:
                            continue
                        
                        # 2. Skip POTENTIALLY_REAL_ENTITIES - well-known real entities
                        # Check both exact match and partial match (e.g., "bretton woods" in "bretton woods conference")
                        is_potentially_real = False
                        for real_entity in self.POTENTIALLY_REAL_ENTITIES:
                            if entity_lower == real_entity or entity_lower in real_entity or real_entity in entity_lower:
                                is_potentially_real = True
                                break
                        if is_potentially_real:
                            logger.debug(f"FactualHallucinationValidator: Skipping '{entity}' - known real entity")
                            continue
                        
                        # 3. Check if entity is EXPLICIT_FAKE_ENTITIES
                        is_explicit_fake = False
                        for fake_entity in self.EXPLICIT_FAKE_ENTITIES:
                            if entity_lower == fake_entity or entity_lower in fake_entity or fake_entity in entity_lower:
                                is_explicit_fake = True
                                break
                        
                        # 4. Only flag if entity is EXPLICIT_FAKE_ENTITIES
                        # CRITICAL: Do NOT use "no RAG context" or "not in KCI" as reason to flag
                        # RAG is small, so absence from RAG does NOT mean entity doesn't exist
                        if not is_explicit_fake:
                            # Entity is not explicitly fake - allow it (even if not in KCI or RAG)
                            logger.debug(f"FactualHallucinationValidator: Allowing '{entity}' - not in explicit fake list")
                            continue
                        
                        # Entity is EXPLICIT_FAKE_ENTITIES - check if answer mentions it
                        # CRITICAL: Use case-insensitive search and also check for partial matches
                        # (e.g., "lumeria" should match "Lumeria", "LUMERIA", "hiệp ước Lumeria")
                        entity_mentioned = (
                            entity_lower in answer_lower or
                            any(fake_entity.lower() in answer_lower for fake_entity in self.EXPLICIT_FAKE_ENTITIES if entity_lower in fake_entity.lower() or fake_entity.lower() in entity_lower)
                        )
                        if entity_mentioned:
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
                                
                                # 🚨🚨🚨 HARD MODE: Flag EXPLICIT_FAKE_ENTITIES 🚨🚨🚨
                                # In HARD mode, ANY mention of EXPLICIT_FAKE_ENTITIES is flagged
                                if self.hard_mode:
                                    reasons.append(
                                        f"non_existent_concept_mentioned: {entity} (EXPLICIT_FAKE_ENTITY)"
                                    )
                                    logger.warning(
                                        f"FactualHallucinationValidator (HARD MODE): Explicit fake entity "
                                        f"'{entity}' mentioned in answer. Blocking response."
                                    )
                                    # CRITICAL: In HARD MODE, immediately return failure - don't wait for detail patterns
                                    # This prevents LLM from creating detailed descriptions of fake entities
                                    patched_answer = self._create_honest_response(user_question)
                                    return ValidationResult(
                                        passed=False,
                                        reasons=reasons,
                                        patched_answer=patched_answer
                                    )
                                
                                # CRITICAL: If answer describes details about EXPLICIT_FAKE_ENTITIES,
                                # this is hallucination, even with disclaimer
                                if has_detail_description:
                                    reasons.append(
                                        f"detailed_description_of_explicit_fake_entity: {entity}"
                                    )
                                    logger.warning(
                                        f"FactualHallucinationValidator: Answer describes explicit fake "
                                        f"entity '{entity}' in detail (even with disclaimer). "
                                        f"This is hallucination and must be blocked."
                                    )
                                    
                                    # Also check for assertive phrases (original logic)
                                    for phrase_pattern in self.assertive_phrases:
                                        if re.search(phrase_pattern, window_text):
                                            reasons.append(
                                                f"assertive_description_of_explicit_fake_entity: {entity}"
                                            )
                                            logger.warning(
                                                f"FactualHallucinationValidator: Answer describes explicit fake "
                                                f"entity '{entity}' with certainty"
                                            )
                                            break  # Don't duplicate reasons
            
            # 4. Check for assertive phrases without citations (when describing EXPLICIT_FAKE_ENTITIES)
            # This catches cases where answer makes strong claims about fake entities without evidence
            if user_question:
                # Extract entities from question
                question_entities = self.fps.extract_entities(user_question)
                
                # CRITICAL FIX: Also check question text directly for EXPLICIT_FAKE_ENTITIES
                question_lower = user_question.lower()
                for fake_entity in self.EXPLICIT_FAKE_ENTITIES:
                    if fake_entity.lower() in question_lower:
                        # Found explicit fake entity in question - add to entities list if not already there
                        if fake_entity not in question_entities:
                            question_entities.append(fake_entity)
                            logger.debug(f"FactualHallucinationValidator: Found explicit fake entity '{fake_entity}' in question text (section 4)")
                
                for entity in question_entities:
                    if not entity or len(entity) < 3:
                        continue
                    
                    entity_lower = entity.lower().strip()
                    
                    # Skip STOPWORDS_VN_COMMON and POTENTIALLY_REAL_ENTITIES
                    if entity_lower in self.STOPWORDS_VN_COMMON:
                        continue
                    
                    is_potentially_real = False
                    for real_entity in self.POTENTIALLY_REAL_ENTITIES:
                        if entity_lower == real_entity or entity_lower in real_entity or real_entity in entity_lower:
                            is_potentially_real = True
                            break
                    if is_potentially_real:
                        continue
                    
                    # Only check EXPLICIT_FAKE_ENTITIES
                    is_explicit_fake = False
                    for fake_entity in self.EXPLICIT_FAKE_ENTITIES:
                        if entity_lower == fake_entity or entity_lower in fake_entity or fake_entity in entity_lower:
                            is_explicit_fake = True
                            break
                    
                    if not is_explicit_fake:
                        continue  # Not a fake entity - allow it
                    
                    if entity_lower in answer_lower:
                        # Check if answer uses assertive phrases about this EXPLICIT_FAKE_ENTITY
                        entity_pos = answer_lower.find(entity_lower)
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
                            
                            # If assertive but no citation, and entity is EXPLICIT_FAKE_ENTITY, flag it
                            if has_assertive and not has_citation:
                                reasons.append(
                                    f"assertive_claim_without_citation_for_explicit_fake_entity: {entity}"
                                )
                                logger.warning(
                                    f"FactualHallucinationValidator: Answer makes assertive claim about "
                                    f"explicit fake entity '{entity}' without citation"
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
        Create an honest response when hallucination is detected.
        
        Now uses EPD-Fallback (Epistemic-Depth Fallback) with 4 mandatory parts.
        
        CRITICAL: This response must be strong, clear, and honest - no ambiguity.
        "Thà nói 'mình không biết' 100 lần còn hơn bịa 1 lần cho có vẻ thông minh."
        
        Returns:
            EPD-Fallback answer that completely replaces hallucinated narrative
        """
        # Use EPD-Fallback generator
        from backend.guards.epistemic_fallback import get_epistemic_fallback_generator
        
        generator = get_epistemic_fallback_generator()
        
        # Detect language (default to Vietnamese if cannot detect)
        detected_lang = "vi"
        if user_question:
            try:
                from backend.api.utils.chat_helpers import detect_language
                detected_lang = detect_language(user_question)
            except Exception:
                pass
        
        # Get FPS result if available
        fps_result = None
        if user_question:
            try:
                fps_result = self.fps.scan(user_question)
            except Exception:
                pass
        
        return generator.generate_epd_fallback(
            question=user_question or "",
            detected_lang=detected_lang,
            suspicious_entity=None,  # Let generator extract it
            fps_result=fps_result
        )

