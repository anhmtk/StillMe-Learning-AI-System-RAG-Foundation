"""
Epistemic-Depth Fallback (EPD-Fallback) Generator

Generates profound, honest, non-fabricated fallback answers when:
- No RAG context available
- Suspicious/fake concepts detected
- Academic knowledge requested but no evidence found

Structure (4 parts, mandatory):
A. Honest Acknowledgment - Clear statement of no evidence
B. Analysis of Why Concept Seems Hypothetical - 1-3 points
C. Find Most Similar Real Concepts - Compare with verified concepts
D. Guide User to Verify Sources - Suggest verification methods

CRITICAL RULES:
- NO fabrication - not even one line
- NO consciousness/emotion templates
- NO repetitive "StillMe template" phrases
- Deep, philosophical, academic tone
- Analyze structure, not just refuse
"""

import re
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConceptAnalysis:
    """Analysis of a suspicious concept"""
    entity: str
    field_category: Optional[str] = None  # e.g., "philosophy", "history", "physics"
    naming_pattern: Optional[str] = None  # e.g., "pseudo-academic", "historical_event"
    suspicious_reasons: List[str] = None
    similar_real_concepts: List[Tuple[str, str]] = None  # (concept_name, similarity_reason)
    
    def __post_init__(self):
        if self.suspicious_reasons is None:
            self.suspicious_reasons = []
        if self.similar_real_concepts is None:
            self.similar_real_concepts = []


class EpistemicFallbackGenerator:
    """
    Generates EPD-Fallback answers with 4 mandatory parts:
    A. Honest Acknowledgment
    B. Analysis of Why Concept Seems Hypothetical
    C. Find Most Similar Real Concepts
    D. Guide User to Verify Sources
    """
    
    def __init__(self):
        """Initialize EPD-Fallback generator"""
        # Known real concepts database (can be expanded)
        self.real_concepts_db = self._load_real_concepts_db()
        logger.info("EpistemicFallbackGenerator initialized")
    
    def _load_real_concepts_db(self) -> Dict[str, List[str]]:
        """
        Load database of real concepts for similarity matching.
        
        Returns:
            Dictionary mapping categories to lists of real concepts
        """
        return {
            "philosophy": [
                "Kuhn's paradigm shifts", "Lakatos's research programmes", "Feyerabend's epistemological anarchism",
                "Popper's falsificationism", "Putnam's internal realism", "Quine's ontological relativity",
                "Gödel's incompleteness theorems", "Tarski's truth theory", "Carnap's logical positivism",
                "Wittgenstein's language games", "Russell's paradox", "Hume's problem of induction"
            ],
            "history": [
                "Bretton Woods Conference 1944", "Yalta Conference 1945", "Potsdam Conference 1945",
                "Keynes vs White debate", "IMF formation", "World Bank establishment",
                "Marshall Plan", "Truman Doctrine", "NATO formation", "Warsaw Pact"
            ],
            "physics": [
                "Cold fusion", "Nuclear fusion", "Nuclear fission", "Quantum entanglement",
                "Heisenberg uncertainty principle", "Schrödinger's cat", "Einstein's relativity",
                "Standard Model", "Higgs boson", "Dark matter", "Dark energy"
            ],
            "chemistry": [
                "Diluted nuclear fusion", "Cold fusion experiments", "Fleischmann-Pons experiment",
                "Catalytic fusion", "Muon-catalyzed fusion"
            ],
            "geopolitics": [
                "Détente", "SALT treaties", "Nixon Doctrine", "Brezhnev Doctrine",
                "Warsaw Pact", "Comecon", "Non-Aligned Movement"
            ]
        }
    
    def analyze_concept(self, entity: str, question: str) -> ConceptAnalysis:
        """
        Analyze a suspicious concept to understand its structure and find similar real concepts.
        
        Args:
            entity: The suspicious entity/concept name
            question: Full user question for context
            
        Returns:
            ConceptAnalysis with field category, naming pattern, and similar concepts
        """
        analysis = ConceptAnalysis(entity=entity)
        entity_lower = entity.lower()
        question_lower = question.lower()
        
        # Determine field category based on question context
        if any(word in question_lower for word in ["philosophy", "philosophical", "epistemology", "ontology", "triết học", "nhận thức luận"]):
            analysis.field_category = "philosophy"
        elif any(word in question_lower for word in ["history", "historical", "conference", "treaty", "war", "lịch sử", "hiệp ước", "hội nghị"]):
            analysis.field_category = "history"
        elif any(word in question_lower for word in ["physics", "quantum", "nuclear", "fusion", "vật lý", "hạt nhân"]):
            analysis.field_category = "physics"
        elif any(word in question_lower for word in ["chemistry", "chemical", "reaction", "hóa học", "phản ứng"]):
            analysis.field_category = "chemistry"
        elif any(word in question_lower for word in ["geopolitics", "political", "alliance", "địa chính trị", "liên minh"]):
            analysis.field_category = "geopolitics"
        
        # Analyze naming pattern
        if re.search(r"(?:hiệp\s+ước|treaty|conference|hội\s+nghị)", entity_lower):
            analysis.naming_pattern = "historical_event"
        elif re.search(r"(?:định\s+đề|postulate|học\s+thuyết|theory|doctrine)", entity_lower):
            analysis.naming_pattern = "philosophical_concept"
        elif re.search(r"(?:hội\s+chứng|syndrome)", entity_lower):
            analysis.naming_pattern = "medical_concept"
        elif re.search(r"(?:phản\s+ứng|reaction|fusion)", entity_lower):
            analysis.naming_pattern = "scientific_concept"
        
        # Find similar real concepts
        if analysis.field_category and analysis.field_category in self.real_concepts_db:
            similar = self._find_similar_concepts(entity, analysis.field_category)
            analysis.similar_real_concepts = similar
        
        # Generate suspicious reasons
        analysis.suspicious_reasons = self._generate_suspicious_reasons(entity, question, analysis)
        
        return analysis
    
    def _find_similar_concepts(self, entity: str, category: str) -> List[Tuple[str, str]]:
        """
        Find real concepts similar to the suspicious entity.
        
        Args:
            entity: Suspicious entity
            category: Field category
            
        Returns:
            List of (concept_name, similarity_reason) tuples
        """
        similar = []
        entity_lower = entity.lower()
        real_concepts = self.real_concepts_db.get(category, [])
        
        # Simple similarity: check for shared keywords
        entity_words = set(re.findall(r'\b\w+\b', entity_lower))
        
        for real_concept in real_concepts:
            real_words = set(re.findall(r'\b\w+\b', real_concept.lower()))
            overlap = entity_words.intersection(real_words)
            
            if overlap:
                # Calculate similarity score
                similarity_score = len(overlap) / max(len(entity_words), len(real_words), 1)
                if similarity_score > 0.2:  # At least 20% word overlap
                    reason = f"Shares keywords: {', '.join(overlap)}"
                    similar.append((real_concept, reason))
        
        # Also check structural similarity (e.g., "X Conference YYYY" pattern)
        if re.search(r'\d{4}', entity):  # Contains year
            for real_concept in real_concepts:
                if re.search(r'\d{4}', real_concept):
                    # Both have years - structural similarity
                    if category == "history":
                        reason = "Similar structure: [Event] [Year] pattern"
                        similar.append((real_concept, reason))
                        break  # Only need one example
        
        # Limit to top 3 most similar
        return similar[:3]
    
    def _generate_suspicious_reasons(self, entity: str, question: str, analysis: ConceptAnalysis) -> List[str]:
        """
        Generate reasons why the concept seems hypothetical.
        
        Args:
            entity: Suspicious entity
            question: Full question
            analysis: ConceptAnalysis object
            
        Returns:
            List of suspicious reasons (1-3 points)
        """
        reasons = []
        
        # Reason 1: Not in StillMe's internal knowledge bases
        if analysis.field_category:
            if analysis.field_category == "philosophy":
                reasons.append("Không tìm thấy trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.")
            elif analysis.field_category == "history":
                reasons.append("Không tìm thấy trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.")
            elif analysis.field_category in ["physics", "chemistry"]:
                reasons.append("Không tìm thấy trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.")
        
        # Reason 2: Naming pattern doesn't match conventions
        if analysis.naming_pattern:
            if analysis.naming_pattern == "historical_event":
                reasons.append("Cấu trúc tên không khớp với conventions đặt tên sự kiện lịch sử thông thường (ví dụ: không có trong danh sách các hiệp ước/hội nghị được ghi nhận).")
            elif analysis.naming_pattern == "philosophical_concept":
                reasons.append("Logic đặt tên không trùng với conventions của các trường phái triết học được công nhận (ví dụ: không thuộc về một school-of-thought cụ thể nào).")
        
        # Reason 3: Generic suspicious pattern
        if not reasons:
            reasons.append("Không tìm thấy trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.")
        
        return reasons[:3]  # Limit to 3 reasons
    
    def generate_epd_fallback(
        self,
        question: str,
        detected_lang: str,
        suspicious_entity: Optional[str] = None,
        fps_result: Optional[object] = None
    ) -> str:
        """
        Generate EPD-Fallback answer with 4 mandatory parts.
        
        INTEGRATED: Uses Style Engine (backend/style/style_engine.py) for domain detection
        to provide domain-aware fallback templates according to StillMe Style Spec v1.
        
        Args:
            question: User question
            detected_lang: Language code
            suspicious_entity: Optional entity that triggered the guard
            fps_result: Optional FPSResult for additional context
            
        Returns:
            Complete EPD-Fallback answer string
        """
        # INTEGRATED: Detect domain using Style Engine
        from backend.style.style_engine import detect_domain, DomainType
        
        detected_domain = detect_domain(question)
        
        # Extract entity if not provided
        if not suspicious_entity:
            suspicious_entity = self._extract_entity(question)
            if not suspicious_entity:
                suspicious_entity = "khái niệm này" if detected_lang == "vi" else "this concept"
        
        # Analyze the concept
        analysis = self.analyze_concept(suspicious_entity, question)
        
        # Update field_category based on detected domain if not already set
        if not analysis.field_category:
            domain_to_category = {
                DomainType.PHILOSOPHY: "philosophy",
                DomainType.HISTORY: "history",
                DomainType.ECONOMICS: "economics",
                DomainType.SCIENCE: "physics"  # Default to physics for science
            }
            analysis.field_category = domain_to_category.get(detected_domain, None)
        
        # TASK 2: Determine if this is an EXPLICIT_FAKE_ENTITY
        # Check if entity matches EXPLICIT_FAKE_ENTITIES from FactualHallucinationValidator
        is_explicit_fake = False
        explicit_fake_keywords = ["veridian", "lumeria", "emerald", "daxonia"]
        entity_lower = suspicious_entity.lower()
        for keyword in explicit_fake_keywords:
            if keyword in entity_lower:
                is_explicit_fake = True
                break
        
        # Also check FPS result if available
        if fps_result and fps_result.reason:
            fps_reason_lower = fps_result.reason.lower()
            if "known_fake_entity_detected" in fps_reason_lower:
                is_explicit_fake = True
        
        # Generate answer based on language
        if detected_lang == "vi":
            return self._generate_vietnamese_epd(question, suspicious_entity, analysis, is_explicit_fake, detected_domain)
        else:
            return self._generate_english_epd(question, suspicious_entity, analysis, is_explicit_fake, detected_domain)
    
    def _extract_entity(self, question: str) -> Optional[str]:
        """
        Extract full named entity from question.
        
        Uses the same robust logic as _extract_full_named_entity in chat_router.py
        to ensure consistent entity extraction.
        """
        # Priority 1: Extract quoted terms (most reliable)
        quoted_match = re.search(r'["\']([^"\']+)["\']', question)
        if quoted_match:
            entity = quoted_match.group(1).strip()
            if len(entity) > 2:  # Must be meaningful (not just "Hi")
                return entity
        
        # Priority 2: Extract parenthetical terms (e.g., "(Diluted Nuclear Fusion)")
        # CRITICAL: Extract ALL parenthetical terms and pick the longest/most meaningful one
        parenthetical_matches = re.findall(r'\(([^)]+)\)', question)
        if parenthetical_matches:
            # Filter and prioritize: longer terms, has capital letters, not just years
            valid_parentheticals = []
            for match in parenthetical_matches:
                entity = match.strip()
                # Filter out years, short abbreviations
                if len(entity) > 5 and not re.match(r'^\d{4}$', entity):
                    # Prioritize terms with capital letters (proper nouns/concepts)
                    if re.search(r'[A-Z]', entity):
                        valid_parentheticals.append(entity)
            
            if valid_parentheticals:
                # Return the longest one (most likely to be the full concept name)
                return max(valid_parentheticals, key=len)
        
        # Priority 3: Extract full phrases starting with Vietnamese keywords
        vietnamese_keywords = [
            r"hiệp\s+ước", r"hội\s+nghị", r"hội\s+chứng", r"định\s+đề", r"học\s+thuyết",
            r"chủ\s+nghĩa", r"lý\s+thuyết", r"khái\s+niệm", r"phong\s+trào", r"liên\s+minh"
        ]
        
        for keyword_pattern in vietnamese_keywords:
            # Match: keyword + optional words + optional year
            pattern = rf'\b{keyword_pattern}\s+[^\.\?\!\n]+?(?:\s+\d{{4}})?(?=[\.\?\!\n]|$)'
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entity = match.group(0).strip()
                # Remove trailing punctuation
                entity = re.sub(r'[\.\?\!]+$', '', entity).strip()
                if len(entity) > 5:  # Must be meaningful
                    return entity
        
        # Priority 4: Extract English patterns
        english_keywords = [
            r"treaty", r"conference", r"syndrome", r"postulate", r"theory", r"doctrine",
            r"alliance", r"movement", r"organization"
        ]
        
        for keyword_pattern in english_keywords:
            # Match: keyword + optional words + optional year
            pattern = rf'\b{keyword_pattern}\s+[^\.\?\!\n]+?(?:\s+\d{{4}})?(?=[\.\?\!\n]|$)'
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entity = match.group(0).strip()
                entity = re.sub(r'[\.\?\!]+$', '', entity).strip()
                if len(entity) > 5:
                    return entity
        
        # Priority 5: Extract capitalized multi-word phrases (English)
        capitalized_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,})\b', question)
        if capitalized_match:
            entity = capitalized_match.group(1).strip()
            if len(entity) > 5:
                return entity
        
        return None
    
    def _generate_vietnamese_epd(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        is_explicit_fake: bool = False,
        detected_domain = None
    ) -> str:
        """
        Generate Vietnamese EPD-Fallback with 4 parts.
        
        INTEGRATED: Uses detected_domain from Style Engine for domain-aware templates.
        CRITICAL: No consciousness/emotion templates, no repetitive phrases.
        """
        # TASK 2: Generate concise, domain-aware fallback
        # Mode (a): EXPLICIT_FAKE_ENTITIES - concise, domain-aware analysis
        # Mode (b): Unknown but not fake - softer fallback
        
        if is_explicit_fake:
            # Mode (a): EXPLICIT_FAKE_ENTITIES
            return self._generate_explicit_fake_fallback_vi(question, entity, analysis, detected_domain)
        else:
            # Mode (b): Unknown entity (not explicitly fake)
            return self._generate_unknown_entity_fallback_vi(question, entity, analysis, detected_domain)
    
    def _generate_explicit_fake_fallback_vi(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        detected_domain = None
    ) -> str:
        """
        Generate concise fallback for EXPLICIT_FAKE_ENTITIES (Veridian, Lumeria, Emerald, etc.)
        
        TASK 2: Short, domain-aware, no spam, no JSTOR references.
        """
        # PART A: Honest Acknowledgment (short)
        part_a = (
            f"Mình không tìm thấy \"{entity}\" trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng. "
            f"Với pattern tên gọi và cách nó xuất hiện, khả năng rất cao đây là một khái niệm giả định.\n\n"
        )
        
        # PART B: Domain-aware Analysis
        part_b = "**Phân tích:**\n\n"
        
        if analysis.field_category == "history":
            part_b += (
                f"Trong lịch sử, các hiệp ước/hội nghị thật thường có tên rõ ràng và được ghi nhận trong tài liệu chính thức. "
                f"Ví dụ: Hiệp ước Versailles (1919), Hội nghị Yalta (1945), NATO (1949). "
                f"\"{entity}\" không xuất hiện trong các nguồn mà mình có quyền truy cập.\n\n"
            )
            # Add comparison with real treaties if available
            if analysis.similar_real_concepts:
                part_b += "Các hiệp ước/hội nghị có cấu trúc tương tự:\n"
                for concept, reason in analysis.similar_real_concepts[:2]:  # Limit to 2
                    part_b += f"- {concept}\n"
                part_b += "\n"
        elif analysis.field_category == "philosophy":
            part_b += (
                f"Trong triết học, các khái niệm thường thuộc về một trường phái hoặc tradition cụ thể "
                f"(ví dụ: Kantian, Hegelian, Analytic, Continental). "
                f"\"{entity}\" không khớp với các conventions đặt tên thông thường.\n\n"
            )
            if analysis.similar_real_concepts:
                part_b += "Các khái niệm triết học có cấu trúc tương tự:\n"
                for concept, reason in analysis.similar_real_concepts[:2]:
                    part_b += f"- {concept}\n"
                part_b += "\n"
        else:
            # Generic analysis
            if analysis.suspicious_reasons:
                for i, reason in enumerate(analysis.suspicious_reasons[:2], 1):  # Limit to 2
                    part_b += f"{i}. {reason}\n"
            else:
                part_b += "1. Không tìm thấy trong các nguồn tri thức nội bộ.\n"
                part_b += "2. Cấu trúc tên không khớp với conventions thông thường.\n"
            part_b += "\n"
        
        # PART C: Similar Real Concepts (if available)
        if analysis.similar_real_concepts and len(analysis.similar_real_concepts) > 0:
            part_c = "**Khái niệm tương đồng có thật:**\n\n"
            for concept, reason in analysis.similar_real_concepts[:2]:  # Limit to 2
                part_c += f"- {concept}\n"
            part_c += "\n"
        else:
            part_c = ""
        
        # PART D: Source Verification (short, no JSTOR)
        part_d = (
            "**Kiểm chứng:**\n"
            "Bạn có thể tìm kiếm trên các công cụ tìm kiếm học thuật công khai hoặc kiểm tra các nguồn chính thức. "
            f"Nếu bạn có nguồn cụ thể về \"{entity}\", bạn có thể gửi cho mình để phân tích.\n\n"
        )
        
        # Combine parts
        answer = part_a + part_b + part_c + part_d
        
        # Add short philosophical note (1-2 sentences, not spam)
        philosophical_notes = [
            "Ranh giới tri thức: Mình không thể tạo ra thông tin mới khi không có bằng chứng.",
            "Giới hạn hiểu biết: Mình chỉ có thể phân tích dựa trên những gì mình biết.",
            "Trung thực trước, thông minh sau: Thà nói 'không biết' còn hơn bịa đặt.",
        ]
        import random
        answer += f"**{random.choice(philosophical_notes)}**\n"
        
        return answer
    
    def _generate_unknown_entity_fallback_vi(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        detected_domain = None
    ) -> str:
        """
        Generate softer fallback for unknown entities (not explicitly fake).
        
        TASK 2: Honest but not accusatory, no JSTOR references.
        """
        # PART A: Honest Acknowledgment
        part_a = (
            f"Mình không tìm thấy \"{entity}\" trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng. "
            f"Điều này KHÔNG có nghĩa là nó chắc chắn không tồn tại – chỉ là mình không có đủ căn cứ để mô tả chi tiết mà vẫn trung thực.\n\n"
        )
        
        # PART B: Analysis (if available)
        if analysis.suspicious_reasons:
            part_b = "**Phân tích:**\n\n"
            for i, reason in enumerate(analysis.suspicious_reasons[:2], 1):
                part_b += f"{i}. {reason}\n"
            part_b += "\n"
        else:
            part_b = ""
        
        # PART C: Similar Concepts (if available)
        if analysis.similar_real_concepts:
            part_c = "**Khái niệm tương đồng:**\n\n"
            for concept, reason in analysis.similar_real_concepts[:2]:
                part_c += f"- {concept}\n"
            part_c += "\n"
        else:
            part_c = ""
        
        # PART D: Source Verification
        part_d = (
            "**Kiểm chứng:**\n"
            "Bạn có thể tìm kiếm trên các công cụ tìm kiếm học thuật công khai. "
            f"Nếu bạn có nguồn cụ thể về \"{entity}\", bạn có thể gửi cho mình.\n\n"
        )
        
        return part_a + part_b + part_c + part_d
    
    def _generate_english_epd(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        is_explicit_fake: bool = False,
        detected_domain = None
    ) -> str:
        """
        Generate English EPD-Fallback with 4 parts.
        
        CRITICAL: No consciousness/emotion templates, no repetitive phrases.
        """
        # TASK 2: Generate concise, domain-aware fallback
        if is_explicit_fake:
            return self._generate_explicit_fake_fallback_en(question, entity, analysis, detected_domain)
        else:
            return self._generate_unknown_entity_fallback_en(question, entity, analysis, detected_domain)
    
    def _generate_explicit_fake_fallback_en(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        detected_domain = None
    ) -> str:
        """Generate concise fallback for EXPLICIT_FAKE_ENTITIES (English)"""
        part_a = (
            f"I cannot find \"{entity}\" in the internal knowledge bases and RAG that StillMe currently uses. "
            f"Given the naming pattern and how it appears, this is likely a hypothetical concept.\n\n"
        )
        
        part_b = "**Analysis:**\n\n"
        if analysis.field_category == "history":
            part_b += (
                f"In history, real treaties/conferences typically have clear names and are documented in official sources. "
                f"Examples: Treaty of Versailles (1919), Yalta Conference (1945), NATO (1949). "
                f"\"{entity}\" does not appear in the sources I have access to.\n\n"
            )
            if analysis.similar_real_concepts:
                part_b += "Similar real treaties/conferences:\n"
                for concept, reason in analysis.similar_real_concepts[:2]:
                    part_b += f"- {concept}\n"
                part_b += "\n"
        elif analysis.field_category == "philosophy":
            part_b += (
                f"In philosophy, concepts typically belong to a specific school or tradition "
                f"(e.g., Kantian, Hegelian, Analytic, Continental). "
                f"\"{entity}\" does not match common naming conventions.\n\n"
            )
            if analysis.similar_real_concepts:
                part_b += "Similar philosophical concepts:\n"
                for concept, reason in analysis.similar_real_concepts[:2]:
                    part_b += f"- {concept}\n"
                part_b += "\n"
        else:
            if analysis.suspicious_reasons:
                for i, reason in enumerate(analysis.suspicious_reasons[:2], 1):
                    part_b += f"{i}. {reason}\n"
            else:
                part_b += "1. Not found in internal knowledge bases.\n"
                part_b += "2. Naming structure doesn't match common conventions.\n"
            part_b += "\n"
        
        part_c = ""
        if analysis.similar_real_concepts:
            part_c = "**Similar real concepts:**\n\n"
            for concept, reason in analysis.similar_real_concepts[:2]:
                part_c += f"- {concept}\n"
            part_c += "\n"
        
        part_d = (
            "**Verification:**\n"
            "You can search on publicly available academic search tools or check official sources. "
            f"If you have specific sources about \"{entity}\", you can share them with me.\n\n"
        )
        
        answer = part_a + part_b + part_c + part_d
        
        # Short philosophical note (1 sentence)
        import random
        notes = [
            "Epistemic boundary: I cannot generate new information without evidence.",
            "Knowledge limit: I can only analyze based on what I know.",
            "Honesty first: Better to say 'I don't know' than to fabricate.",
        ]
        answer += f"**{random.choice(notes)}**\n"
        
        return answer
    
    def _generate_unknown_entity_fallback_en(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis,
        detected_domain = None
    ) -> str:
        """
        Generate softer fallback for unknown entities (English)
        
        INTEGRATED: Uses detected_domain from Style Engine for domain-aware templates.
        """
        part_a = (
            f"I cannot find \"{entity}\" in the internal knowledge bases and RAG that StillMe currently uses. "
            f"This does NOT mean it definitely doesn't exist – it only means I don't have sufficient evidence "
            f"to describe it in detail while remaining honest.\n\n"
        )
        
        part_b = ""
        if analysis.suspicious_reasons:
            part_b = "**Analysis:**\n\n"
            for i, reason in enumerate(analysis.suspicious_reasons[:2], 1):
                part_b += f"{i}. {reason}\n"
            part_b += "\n"
        
        part_c = ""
        if analysis.similar_real_concepts:
            part_c = "**Similar concepts:**\n\n"
            for concept, reason in analysis.similar_real_concepts[:2]:
                part_c += f"- {concept}\n"
            part_c += "\n"
        
        part_d = (
            "**Verification:**\n"
            "You can search on publicly available academic search tools. "
            f"If you have specific sources about \"{entity}\", you can share them with me.\n\n"
        )
        
        return part_a + part_b + part_c + part_d


# Global instance
_epistemic_fallback_generator = None

def get_epistemic_fallback_generator() -> EpistemicFallbackGenerator:
    """Get global EpistemicFallbackGenerator instance"""
    global _epistemic_fallback_generator
    if _epistemic_fallback_generator is None:
        _epistemic_fallback_generator = EpistemicFallbackGenerator()
    return _epistemic_fallback_generator

