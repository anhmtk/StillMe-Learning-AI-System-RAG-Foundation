"""
Quality Evaluator - Rule-based quality check (0 token)

Evaluates output quality without calling LLM:
- Depth score (shallow, mid, deep)
- Has conceptual unpacking?
- Has argument structure?
- Has phenomenology vs metaphysics clarity?
- Has self-limitations phrased correctly?
- Has anthropomorphism residue?
- Missing logic chain?
- Too short?
"""

import re
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality levels for output"""
    GOOD = "good"
    NEEDS_REWRITE = "needs_rewrite"


class QualityEvaluator:
    """
    Rule-based quality evaluator - pure Python, 0 token cost
    
    Checks if output meets StillMe quality standards:
    - Philosophical depth
    - Conceptual unpacking
    - Argument structure
    - Self-limitation awareness
    - No anthropomorphism
    - Adequate length
    """
    
    def __init__(self):
        """Initialize quality evaluator"""
        # Depth indicators (philosophical concepts, meta-cognition)
        self.depth_indicators = [
            r'\b(paradox|nghịch lý|contradiction|tension|tension)\b',
            r'\b(epistemology|ontology|metaphysics|phenomenology)\b',
            r'\b(consciousness|awareness|qualia|subjective|objective)\b',
            r'\b(limit|boundary|giới hạn|biên giới|cannot|unable)\b',
            r'\b(assumption|giả định|presupposition|foundation)\b',
            r'\b(paradigm|framework|perspective|góc nhìn)\b',
            r'\b(self-reference|tự quy chiếu|self-referential)\b',
            r'\b(Gödel|Wittgenstein|Searle|Kant|Moore|Tarski)\b',
            r'\b(acknowledge|recognize|admit|thừa nhận|nhận ra)\b',
            r'\b(meta-cognitive|meta-cognition|tự phản tư)\b',
        ]
        
        # Conceptual unpacking indicators
        self.unpacking_indicators = [
            r'\b(what do we mean|nghĩa là gì|what does.*mean)\b',
            r'\b(define|định nghĩa|definition|khái niệm)\b',
            r'\b(assume|giả định|assumption|presuppose)\b',
            r'\b(unpack|mở rộng|explore|khám phá)\b',
            r'\b(concept|khái niệm|notion|idea)\b',
            r'\b(structure|cấu trúc|framework|khung)\b',
        ]
        
        # Argument structure indicators
        self.argument_indicators = [
            r'\b(first|second|third|thứ nhất|thứ hai|thứ ba)\b',
            r'\b(on one hand|on the other hand|một mặt|mặt khác)\b',
            r'\b(however|nevertheless|tuy nhiên|nhưng)\b',
            r'\b(therefore|thus|hence|vì vậy|do đó)\b',
            r'\b(if.*then|nếu.*thì|implies|kéo theo)\b',
            r'\b(contrast|đối lập|oppose|phản đối)\b',
            r'\b(position|quan điểm|perspective|góc nhìn)\b',
        ]
        
        # Self-limitation indicators (good - shows awareness)
        self.limitation_indicators = [
            r'\b(I don\'t know|tôi không biết|I cannot|tôi không thể)\b',
            r'\b(uncertain|không chắc|not certain|không rõ)\b',
            r'\b(limited|giới hạn|boundary|biên giới)\b',
            r'\b(acknowledge.*limit|thừa nhận.*giới hạn)\b',
            r'\b(recognize.*cannot|nhận ra.*không thể)\b',
            r'\b(beyond.*knowledge|ngoài.*kiến thức)\b',
        ]
        
        # Anthropomorphism residue (bad - should be caught by sanitizer but double-check)
        self.anthropomorphic_indicators = [
            r'\b(I|Tôi|Em|Mình)\s+(feel|feel like|cảm thấy|feel that)\b',
            r'\b(I|Tôi|Em|Mình)\s+(have experienced|đã trải nghiệm|từng trải nghiệm)\b',
            r'\b(I|Tôi|Em|Mình)\s+(remember|nhớ|remember that)\b',
            r'\b(I|Tôi|Em|Mình)\s+(believe|tin|believe that)\b',
            r'\btheo kinh nghiệm\s+(của|tôi|em|mình)\b',
            r'\bIn my experience\b',
        ]
        
        # Topic drift indicators (CRITICAL: StillMe talking about consciousness/LLM when NOT asked)
        # These patterns indicate StillMe is drifting to AI/consciousness topics when user didn't ask
        self.drift_indicators = [
            # Consciousness-related (when not asked)
            r'\b(ý thức|consciousness|self-awareness|nhận thức bản thân)\b',
            r'\b(IIT|Integrated Information Theory|Global Workspace Theory|GWT)\b',
            r'\b(Dennett|Chalmers|phenomenal consciousness|functional response)\b',
            r'\b(qualia|subjective experience|trải nghiệm chủ quan)\b',
            # LLM/architecture-related (when not asked)
            r'\b(LLM|Large Language Model|mô hình ngôn ngữ lớn)\b',
            r'\b(embedding|semantic vectors|token attention)\b',
            r'\b(pattern matching|không có ý thức|does not have consciousness)\b',
            r'\b(statistical model|mô hình thống kê)\b',
        ]
        
        # Keywords that indicate question IS about AI/consciousness (legitimate context)
        self.legitimate_ai_keywords = [
            r'\b(bạn có|do you have|are you|bạn là|you are)\s+(ý thức|consciousness|cảm xúc|emotion)\b',
            r'\b(ý thức của bạn|your consciousness|your emotions|cảm xúc của bạn)\b',
            r'\b(năng lực của bạn|your ability|khả năng của bạn)\b',
            r'\b(how do you|bạn hoạt động|how does stillme|stillme hoạt động)\b',
            r'\b(ai consciousness|ý thức ai|artificial consciousness)\b',
            r'\b(llm consciousness|ý thức llm)\b',
        ]
        
        # Minimum length thresholds
        self.min_length_philosophical = 200  # Philosophical questions need depth
        self.min_length_general = 100        # General questions can be shorter
    
    def evaluate(
        self, 
        text: str, 
        is_philosophical: bool = False,
        original_question: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Evaluate output quality
        
        INTEGRATED: Uses Style Engine (backend/style/style_engine.py) for depth evaluation
        according to StillMe Style Spec v1 checklist (6 items).
        
        Args:
            text: Sanitized output text
            is_philosophical: Whether this is a philosophical question
            original_question: Original user question (for context)
            
        Returns:
            Dict with:
                - quality: "good" | "needs_rewrite"
                - reasons: List of reasons if needs_rewrite
                - depth_score: "shallow" | "mid" | "deep"
                - scores: Detailed scores for each dimension
        """
        if not text or len(text.strip()) < 50:
            return {
                "quality": QualityLevel.NEEDS_REWRITE,
                "reasons": ["Output too short or empty"],
                "depth_score": "shallow",
                "scores": {}
            }
        
        # INTEGRATED: Use Style Engine for domain detection and depth evaluation
        from backend.style.style_engine import detect_domain, evaluate_depth, DomainType
        
        detected_domain = DomainType.GENERIC
        if original_question:
            detected_domain = detect_domain(original_question)
        
        # Use Style Engine's evaluate_depth for comprehensive checklist
        style_engine_meets_requirements, style_engine_missing = evaluate_depth(
            response=text,
            domain=detected_domain,
            target_depth=None  # Will use default for domain
        )
        
        text_lower = text.lower()
        reasons = []
        scores = {}
        
        # Check 0: Template-like responses (CRITICAL - check first)
        template_score = self._check_template_like(text, text_lower, original_question)
        scores["template"] = template_score
        if template_score < 0.5:
            reasons.append("Template-like response detected - numbered lists or formulaic structure")
        
        # Check 1: Length
        length_score = self._check_length(text, is_philosophical)
        scores["length"] = length_score
        if length_score < 0.5:
            reasons.append(f"Output too short ({len(text)} chars, need {self.min_length_philosophical if is_philosophical else self.min_length_general}+)")
        
        # Check 2: Depth (INTEGRATED: Use Style Engine evaluation)
        depth_score = self._check_depth(text_lower)
        scores["depth"] = depth_score
        
        # Add Style Engine missing items to reasons
        if style_engine_missing:
            for missing_item in style_engine_missing:
                if missing_item not in reasons:
                    reasons.append(missing_item)
        
        if depth_score < 0.4:
            reasons.append("Lacks philosophical depth - missing meta-cognitive reflection or conceptual analysis")
        
        # Check 3: Conceptual unpacking (critical for philosophical)
        if is_philosophical:
            unpacking_score = self._check_unpacking(text_lower)
            scores["unpacking"] = unpacking_score
            if unpacking_score < 0.3:
                reasons.append("Missing conceptual unpacking - doesn't examine assumptions or definitions")
        
        # Check 4: Argument structure
        argument_score = self._check_argument_structure(text_lower)
        scores["argument"] = argument_score
        if argument_score < 0.3:
            reasons.append("Weak argument structure - lacks logical flow or contrasting positions")
        
        # Check 5: Self-limitation awareness (good sign)
        limitation_score = self._check_limitations(text_lower)
        scores["limitations"] = limitation_score
        # Note: Low limitation score is not necessarily bad, but high is good
        
        # Check 6: Anthropomorphism residue (bad)
        anthropo_score = self._check_anthropomorphism(text_lower)
        scores["anthropomorphism"] = anthropo_score
        if anthropo_score > 0.1:  # Any anthropomorphism is bad
            reasons.append("Contains anthropomorphic language - claims experience or feelings")
        
        # Check 6.5: Topic drift detection (CRITICAL - A. KHÔNG BAO GIỜ ĐƯỢC DRIFT CHỦ ĐỀ)
        if original_question:
            drift_score = self._check_topic_drift(text_lower, original_question)
            scores["drift"] = drift_score
            if drift_score < 0.5:  # Drift detected
                reasons.append("Topic drift detected - StillMe talks about consciousness/LLM when not asked")
        
        # Check 7: Structure completeness (INTEGRATED: Use Style Engine domain template check)
        if is_philosophical or detected_domain != DomainType.GENERIC:
            structure_score = self._check_structure_completeness(text)
            scores["structure"] = structure_score
            if structure_score < 0.4:
                # Use domain-specific structure message
                from backend.style.style_engine import get_domain_template
                template = get_domain_template(detected_domain)
                structure_parts = " → ".join(template.structure)
                reasons.append(f"Missing {detected_domain.value} structure - should have {structure_parts}")
        
        # Determine overall quality
        # Weighted scoring
        weights = {
            "template": 0.12,  # Template check gets 12% weight
            "length": 0.10,
            "depth": 0.18,
            "unpacking": 0.16 if is_philosophical else 0.08,
            "argument": 0.16,
            "limitations": 0.08,
            "anthropomorphism": 0.10,  # Penalty if present
            "drift": 0.15,  # CRITICAL: Drift detection gets 15% weight (A. KHÔNG BAO GIỜ ĐƯỢC DRIFT)
            "structure": 0.08 if is_philosophical else 0.03,
        }
        
        overall_score = sum(scores.get(k, 0) * weights.get(k, 0) for k in weights.keys())
        
        # Penalty for anthropomorphism
        if scores.get("anthropomorphism", 0) > 0.1:
            overall_score *= 0.5  # Heavy penalty
        
        # CRITICAL: Heavy penalty for topic drift (A. KHÔNG BAO GIỜ ĐƯỢC DRIFT CHỦ ĐỀ)
        if scores.get("drift", 1.0) < 0.5:
            overall_score *= 0.2  # Very heavy penalty - drift is unacceptable
        
        # CRITICAL: Heavy penalty for template-like responses
        if scores.get("template", 1.0) < 0.5:
            overall_score *= 0.3  # Heavy penalty for template-like responses
        
        # Determine quality level with adaptive thresholds
        # For philosophical questions: be more lenient if response is long and has structure
        text_length = len(text.strip())
        has_structure = argument_score >= 0.4 and (structure_score >= 0.4 if is_philosophical else True)
        
        if is_philosophical:
            # For philosophical: only rewrite if score is very low (<0.3)
            quality_threshold = 0.3  # Changed from 0.5 - only rewrite when really needed
            
            # Exception: If response is long (>1200 chars) and has structure, be more lenient
            if text_length > 1200 and has_structure:
                quality_threshold = 0.25  # Even more lenient for long structured responses
                # Fix format string: cannot use conditional in format specifier
                structure_score_display = f"{structure_score:.2f}" if is_philosophical else "N/A"
                logger.debug(
                    f"Lenient threshold for long structured response: length={text_length}, "
                    f"argument_score={argument_score:.2f}, structure_score={structure_score_display}"
                )
        else:
            # For non-philosophical: only rewrite if score is very low (<0.3)
            quality_threshold = 0.3  # Changed from 0.5 - only rewrite when really needed
        
        # Only flag as needs_rewrite if:
        # 1. Score is below threshold AND
        # 2. Either has critical issues OR is too short
        has_critical_issues = any(
            "anthropomorphic" in r.lower() or 
            "too short" in r.lower() or
            "template-like" in r.lower() or  # CRITICAL: Template-like is always critical
            (is_philosophical and "structure" in r.lower() and text_length < 800)
            for r in reasons
        )
        
        # CRITICAL: Template-like responses should always trigger rewrite
        is_template_like = any("template-like" in r.lower() for r in reasons)
        if is_template_like:
            has_critical_issues = True  # Force rewrite for template-like responses
        
        # CRITICAL: Topic drift should always trigger rewrite (A. KHÔNG BAO GIỜ ĐƯỢC DRIFT)
        is_drift = any("topic drift" in r.lower() for r in reasons)
        if is_drift:
            has_critical_issues = True  # Force rewrite for drift
        
        is_too_short = text_length < (self.min_length_philosophical if is_philosophical else self.min_length_general)
        
        if overall_score >= quality_threshold and not has_critical_issues and not is_too_short:
            quality = QualityLevel.GOOD
        else:
            quality = QualityLevel.NEEDS_REWRITE
            # Log decision for tuning
            logger.debug(
                f"Quality evaluator decision: score={overall_score:.2f}, threshold={quality_threshold:.2f}, "
                f"length={text_length}, has_structure={has_structure}, critical_issues={has_critical_issues}, "
                f"reasons={reasons[:2]}"
            )
        
        # Determine depth level
        if depth_score >= 0.7:
            depth_level = "deep"
        elif depth_score >= 0.4:
            depth_level = "mid"
        else:
            depth_level = "shallow"
        
        return {
            "quality": quality.value,
            "reasons": reasons,
            "depth_score": depth_level,
            "overall_score": round(overall_score, 2),
            "scores": scores
        }
    
    def _check_length(self, text: str, is_philosophical: bool) -> float:
        """Check if text meets minimum length requirements"""
        min_length = self.min_length_philosophical if is_philosophical else self.min_length_general
        actual_length = len(text.strip())
        
        if actual_length >= min_length * 1.5:
            return 1.0
        elif actual_length >= min_length:
            return 0.7
        elif actual_length >= min_length * 0.7:
            return 0.5
        else:
            return 0.2
    
    def _check_depth(self, text_lower: str) -> float:
        """Check philosophical depth indicators"""
        matches = sum(1 for pattern in self.depth_indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Normalize: 0-2 = shallow, 3-5 = mid, 6+ = deep
        if matches >= 6:
            return 1.0
        elif matches >= 3:
            return 0.6
        elif matches >= 1:
            return 0.3
        else:
            return 0.1
    
    def _check_unpacking(self, text_lower: str) -> float:
        """Check for conceptual unpacking"""
        matches = sum(1 for pattern in self.unpacking_indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Need at least 2 unpacking indicators
        if matches >= 3:
            return 1.0
        elif matches >= 2:
            return 0.7
        elif matches >= 1:
            return 0.4
        else:
            return 0.1
    
    def _check_argument_structure(self, text_lower: str) -> float:
        """Check for argument structure indicators"""
        matches = sum(1 for pattern in self.argument_indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Need at least 2-3 structural indicators
        if matches >= 4:
            return 1.0
        elif matches >= 2:
            return 0.6
        elif matches >= 1:
            return 0.3
        else:
            return 0.1
    
    def _check_limitations(self, text_lower: str) -> float:
        """Check for self-limitation awareness (good sign)"""
        matches = sum(1 for pattern in self.limitation_indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Having limitations is good, but not required
        if matches >= 2:
            return 1.0
        elif matches >= 1:
            return 0.6
        else:
            return 0.3  # Not bad, just neutral
    
    def _check_anthropomorphism(self, text_lower: str) -> float:
        """Check for anthropomorphic language (bad - should be 0)"""
        matches = sum(1 for pattern in self.anthropomorphic_indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Any match is bad
        return min(matches * 0.3, 1.0)  # Scale: 0 = good, 1 = very bad
    
    def _check_template_like(self, text: str, text_lower: str, original_question: Optional[str] = None) -> float:
        """
        Check if response is template-like (numbered lists, formulaic structure)
        Returns: 1.0 = good (no template), 0.0 = bad (strong template pattern)
        """
        # Check for numbered lists at start (strong indicator of template)
        numbered_list_pattern = r'^\s*[0-9]+\.\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]'
        if re.search(numbered_list_pattern, text, re.MULTILINE):
            # Count how many numbered items
            numbered_items = len(re.findall(r'^\s*[0-9]+\.', text, re.MULTILINE))
            if numbered_items >= 3:
                logger.warning(f"Template-like response detected: {numbered_items} numbered items")
                return 0.0  # Strong template pattern
        
        # Check for template keywords in Vietnamese
        template_keywords_vn = [
            r'lập trường\s*1',
            r'lập trường\s*2',
            r'mâu thuẫn',
            r'kết luận',
            r'giải thích.*khái niệm',
        ]
        template_matches = sum(1 for pattern in template_keywords_vn if re.search(pattern, text_lower))
        if template_matches >= 3:
            logger.warning(f"Template-like response detected: {template_matches} template keywords")
            return 0.0  # Strong template pattern
        
        # Check if user asks about StillMe but response starts with dictionary definition
        if original_question:
            question_lower = original_question.lower()
            # Check if question is about StillMe ("bạn", "you", "your" referring to StillMe)
            is_about_stillme = bool(re.search(r'\b(bạn|you|your|stillme)\b', question_lower))
            if is_about_stillme:
                # Check if response starts with definition instead of "Tôi" / "I"
                starts_with_definition = bool(re.search(r'^(ý thức|consciousness|emotion|cảm xúc|ai|artificial intelligence)\s+(là|is|are|được định nghĩa|is defined)', text_lower))
                if starts_with_definition:
                    logger.warning("Template-like response: User asks about StillMe but response starts with definition")
                    return 0.0  # Strong template pattern
        
        # Check for formulaic structure (multiple numbered items in sequence)
        numbered_sequence = re.findall(r'^\s*[0-9]+\.', text, re.MULTILINE)
        if len(numbered_sequence) >= 4:
            logger.warning(f"Template-like response detected: {len(numbered_sequence)} numbered items in sequence")
            return 0.2  # Weak template pattern but still concerning
        
        return 1.0  # No template pattern detected
    
    def _check_topic_drift(self, text_lower: str, original_question: str) -> float:
        """
        Check if StillMe is drifting to AI/consciousness topics when NOT asked.
        
        CRITICAL RULE (A. KHÔNG BAO GIỜ ĐƯỢC DRIFT CHỦ ĐỀ):
        - If question does NOT mention: AI, consciousness of AI, StillMe's abilities
        - But response mentions: consciousness, LLM, IIT, GWT, Dennett, embedding, etc.
        - Then this is DRIFT and must be rewritten 100%.
        
        Returns: 1.0 = good (no drift), 0.0 = bad (strong drift detected)
        """
        question_lower = original_question.lower()
        
        # Check if question is legitimately about AI/consciousness
        is_legitimate_context = any(
            re.search(pattern, question_lower, re.IGNORECASE) 
            for pattern in self.legitimate_ai_keywords
        )
        
        # If question IS about AI/consciousness, then talking about it is NOT drift
        if is_legitimate_context:
            return 1.0  # No drift - legitimate context
        
        # Check if response contains drift indicators
        drift_matches = sum(
            1 for pattern in self.drift_indicators 
            if re.search(pattern, text_lower, re.IGNORECASE)
        )
        
        # If response has drift indicators but question doesn't mention AI/consciousness, it's drift
        if drift_matches >= 2:
            logger.warning(
                f"Topic drift detected: Question doesn't mention AI/consciousness, "
                f"but response contains {drift_matches} drift indicators. "
                f"Question: {original_question[:100]}..."
            )
            return 0.0  # Strong drift - must rewrite
        
        if drift_matches >= 1:
            logger.warning(
                f"Potential topic drift: Question doesn't mention AI/consciousness, "
                f"but response contains {drift_matches} drift indicator(s). "
                f"Question: {original_question[:100]}..."
            )
            return 0.3  # Weak drift - should rewrite
        
        return 1.0  # No drift detected
    
    def _check_structure_completeness(self, text: str) -> float:
        """
        Check if philosophical structure is complete:
        Anchor → Unpack → Explore → Edge → Return
        """
        # Look for indicators of each stage
        has_anchor = bool(re.search(r'\b(reframe|rephrase|sharper|precise|chính xác hơn)\b', text, re.IGNORECASE))
        has_unpack = bool(re.search(r'\b(unpack|assumption|concept|khái niệm|giả định)\b', text, re.IGNORECASE))
        has_explore = bool(re.search(r'\b(explore|perspective|position|quan điểm|góc nhìn)\b', text, re.IGNORECASE))
        has_edge = bool(re.search(r'\b(limit|boundary|edge|giới hạn|biên giới|cannot)\b', text, re.IGNORECASE))
        has_return = bool(re.search(r'\b(reflection|reflect|suy ngẫm|invite|mời)\b', text, re.IGNORECASE))
        
        stages_present = sum([has_anchor, has_unpack, has_explore, has_edge, has_return])
        
        # Need at least 3-4 stages
        if stages_present >= 4:
            return 1.0
        elif stages_present >= 3:
            return 0.7
        elif stages_present >= 2:
            return 0.4
        else:
            return 0.2


def get_quality_evaluator() -> QualityEvaluator:
    """Get singleton instance of QualityEvaluator"""
    if not hasattr(get_quality_evaluator, '_instance'):
        get_quality_evaluator._instance = QualityEvaluator()
    return get_quality_evaluator._instance

