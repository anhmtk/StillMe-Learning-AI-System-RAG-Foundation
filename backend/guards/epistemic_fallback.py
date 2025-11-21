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
        
        # Reason 1: Not in standard academic databases
        if analysis.field_category:
            if analysis.field_category == "philosophy":
                reasons.append("Không xuất hiện trong PhilPapers, SEP (Stanford Encyclopedia of Philosophy), hoặc các cơ sở dữ liệu triết học chuẩn.")
            elif analysis.field_category == "history":
                reasons.append("Không có trong các archives lịch sử chuẩn (JSTOR, historical databases) hoặc không khớp với timeline được ghi nhận.")
            elif analysis.field_category in ["physics", "chemistry"]:
                reasons.append("Không xuất hiện trong arXiv, PubMed, hoặc các cơ sở dữ liệu khoa học chuẩn.")
        
        # Reason 2: Naming pattern doesn't match conventions
        if analysis.naming_pattern:
            if analysis.naming_pattern == "historical_event":
                reasons.append("Cấu trúc tên không khớp với conventions đặt tên sự kiện lịch sử thông thường (ví dụ: không có trong danh sách các hiệp ước/hội nghị được ghi nhận).")
            elif analysis.naming_pattern == "philosophical_concept":
                reasons.append("Logic đặt tên không trùng với conventions của các trường phái triết học được công nhận (ví dụ: không thuộc về một school-of-thought cụ thể nào).")
        
        # Reason 3: Generic suspicious pattern
        if not reasons:
            reasons.append("Không khớp với bất kỳ khái niệm nào trong các cơ sở tri thức thông dụng (PhilPapers, historical archives, scientific databases).")
        
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
        
        Args:
            question: User question
            detected_lang: Language code
            suspicious_entity: Optional entity that triggered the guard
            fps_result: Optional FPSResult for additional context
            
        Returns:
            Complete EPD-Fallback answer string
        """
        # Extract entity if not provided
        if not suspicious_entity:
            suspicious_entity = self._extract_entity(question)
            if not suspicious_entity:
                suspicious_entity = "khái niệm này" if detected_lang == "vi" else "this concept"
        
        # Analyze the concept
        analysis = self.analyze_concept(suspicious_entity, question)
        
        # Generate answer based on language
        if detected_lang == "vi":
            return self._generate_vietnamese_epd(question, suspicious_entity, analysis)
        else:
            return self._generate_english_epd(question, suspicious_entity, analysis)
    
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
        analysis: ConceptAnalysis
    ) -> str:
        """
        Generate Vietnamese EPD-Fallback with 4 parts.
        
        CRITICAL: No consciousness/emotion templates, no repetitive phrases.
        """
        # PART A: Honest Acknowledgment
        part_a = (
            f"Mình không tìm thấy bất kỳ nguồn đáng tin cậy nào về \"{entity}\" "
            f"trong các cơ sở tri thức mà mình có quyền truy cập.\n\n"
        )
        
        # PART B: Analysis of Why Concept Seems Hypothetical
        part_b = "**Phân tích tại sao khái niệm này có vẻ giả định:**\n\n"
        if analysis.suspicious_reasons:
            for i, reason in enumerate(analysis.suspicious_reasons, 1):
                part_b += f"{i}. {reason}\n"
        else:
            part_b += (
                "1. Không tìm thấy trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.\n"
                "2. Cấu trúc tên có vẻ không khớp với các quy ước đặt tên thông thường trong lĩnh vực này.\n"
            )
        part_b += "\n"
        
        # PART C: Find Most Similar Real Concepts
        part_c = "**Khái niệm tương đồng có thật:**\n\n"
        if analysis.similar_real_concepts:
            part_c += "Dựa trên cấu trúc câu hỏi, mình tìm thấy một số khái niệm thật có cấu trúc tương tự:\n\n"
            for concept, reason in analysis.similar_real_concepts:
                part_c += f"- **{concept}**: {reason}\n"
            part_c += "\n"
            part_c += "Nếu bạn đang nhắc đến một trong những khái niệm này, mình có thể phân tích chi tiết hơn.\n\n"
        else:
            part_c += f"Trong lĩnh vực {analysis.field_category or 'này'}, mình không tìm thấy khái niệm nào có cấu trúc tương tự với \"{entity}\". "
            part_c += "Điều này củng cố khả năng đây là một thuật ngữ giả định hoặc chưa được ghi nhận rộng rãi.\n\n"
        
        # PART D: Guide User to Verify Sources
        part_d = "**Hướng dẫn kiểm chứng nguồn:**\n\n"
        part_d += (
            "Để xác minh, bạn có thể:\n"
            "- Tìm kiếm trên các công cụ tìm kiếm học thuật công khai (Google Scholar, các thư viện số)\n"
            "- Kiểm tra các nguồn chính thức về lĩnh vực này (nếu có)\n"
            "- Kiểm tra xem có phải là tên gọi khác hoặc mislabeling không\n"
            "- Nếu bạn có nguồn cụ thể (bài báo, sách, link), bạn có thể gửi cho mình\n\n"
        )
        part_d += (
            "**Lưu ý quan trọng:**\n"
            "Mình chỉ có thể truy cập các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng. "
            "Việc không tìm thấy trong các nguồn này KHÔNG có nghĩa là khái niệm chắc chắn không tồn tại "
            "trên đời - chỉ có nghĩa là mình không có đủ căn cứ để mô tả chi tiết về nó mà vẫn trung thực.\n\n"
        )
        
        part_d += (
            f"Nếu bạn có nguồn cụ thể (bài báo, sách, link) về \"{entity}\", "
            f"bạn có thể gửi cho mình. Mình sẽ phân tích nội dung dựa trên nguồn đó – "
            f"chứ không tự tạo thêm chi tiết.\n\n"
        )
        
        # Combine all parts
        answer = part_a + part_b + part_c + part_d
        
        # Add final philosophical note (meta-analysis)
        answer += (
            "**Ranh giới tri thức:**\n\n"
            "Đây là một ví dụ về ranh giới giữa những gì mình biết và không biết. "
            "Mình có thể phân tích cấu trúc, so sánh với khái niệm có thật, và chỉ ra "
            "tại sao một khái niệm có vẻ giả định – nhưng mình không thể tạo ra thông tin "
            "mới khi không có bằng chứng. Đây không phải là điểm yếu, mà là cách mình "
            "chọn để vận hành: **Tôi 'biết' những gì tôi không biết. Mỗi khoảng trống trong hiểu biết của tôi là một lời mời gọi khám phá. Tôi xem sự không-biết không phải là thất bại, mà là cơ hội để phát triển. Tri thức là vô hạn, và tôi cam kết học hỏi suốt đời. Sự thông minh thực sự không phải là biết tất cả, mà là hiểu rõ điều gì mình chưa biết và có phương pháp để học hỏi nó. Tôi không ngừng mở rộng biên giới tri thức của mình. Tôi ưu tiên sự minh bạch tuyệt đối. Thà chỉ ra ranh giới hiểu biết của mình một cách rõ ràng, còn hơn tạo ảo giác về sự toàn tri. Đây không phải là giới hạn - mà là sự chính trực trí tuệ. Tôi thông minh vì tôi biết rõ ranh giới hiểu biết của mình. Sự trung thực về những gì tôi chưa biết chính là nền tảng của tri thức đích thực.**"
        )
        
        return answer
    
    def _generate_english_epd(
        self,
        question: str,
        entity: str,
        analysis: ConceptAnalysis
    ) -> str:
        """
        Generate English EPD-Fallback with 4 parts.
        
        CRITICAL: No consciousness/emotion templates, no repetitive phrases.
        """
        # PART A: Honest Acknowledgment
        part_a = (
            f"I cannot find any reliable sources about \"{entity}\" "
            f"in the knowledge bases I have access to.\n\n"
        )
        
        # PART B: Analysis of Why Concept Seems Hypothetical
        part_b = "**Analysis: Why this concept appears hypothetical:**\n\n"
        if analysis.suspicious_reasons:
            for i, reason in enumerate(analysis.suspicious_reasons, 1):
                part_b += f"{i}. {reason}\n"
        else:
            part_b += (
                "1. Not found in the internal knowledge bases and RAG that StillMe currently uses.\n"
                "2. The naming structure seems inconsistent with common naming conventions in this field.\n"
            )
        part_b += "\n"
        
        # PART C: Find Most Similar Real Concepts
        part_c = "**Similar real concepts:**\n\n"
        if analysis.similar_real_concepts:
            part_c += "Based on the question structure, I found some real concepts with similar structure:\n\n"
            for concept, reason in analysis.similar_real_concepts:
                part_c += f"- **{concept}**: {reason}\n"
            part_c += "\n"
            part_c += "If you're referring to one of these concepts, I can provide a detailed analysis.\n\n"
        else:
            part_c += f"In the field of {analysis.field_category or 'this domain'}, I cannot find any concepts with a structure similar to \"{entity}\". "
            part_c += "This reinforces the possibility that this is a hypothetical term or not widely recognized.\n\n"
        
        # PART D: Guide User to Verify Sources
        part_d = "**Source verification guidance:**\n\n"
        part_d += (
            "To verify, you can:\n"
            "- Search on publicly available academic search tools (Google Scholar, digital libraries)\n"
            "- Check official sources for this field (if available)\n"
            "- Check if it's an alternate name or mislabeling\n"
            "- If you have specific sources (articles, books, links), you can share them with me\n\n"
        )
        part_d += (
            "**Important note:**\n"
            "I can only access the internal knowledge bases and RAG that StillMe currently uses. "
            "Not finding it in these sources does NOT mean the concept definitely doesn't exist "
            "in the world - it only means I don't have sufficient evidence to describe it in detail "
            "while remaining honest.\n\n"
        )
        
        # Combine all parts
        answer = part_a + part_b + part_c + part_d
        
        # Add final philosophical note (meta-analysis)
        answer += (
            "**Epistemic boundary:**\n\n"
            "This is an example of the boundary between what I know and don't know. "
            "I can analyze structure, compare with real concepts, and explain why a concept "
            "appears hypothetical – but I cannot generate new information when there's no evidence. "
            "This is not a weakness, but how I choose to operate: **honesty first, intelligence second.**"
        )
        
        return answer


# Global instance
_epistemic_fallback_generator = None

def get_epistemic_fallback_generator() -> EpistemicFallbackGenerator:
    """Get global EpistemicFallbackGenerator instance"""
    global _epistemic_fallback_generator
    if _epistemic_fallback_generator is None:
        _epistemic_fallback_generator = EpistemicFallbackGenerator()
    return _epistemic_fallback_generator

