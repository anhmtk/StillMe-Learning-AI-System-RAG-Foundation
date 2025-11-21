"""
StillMe Style Engine

Provides unified style and depth management based on StillMe Style Spec v1.
Reference: docs/STILLME_STYLE_SPEC.md

This module implements:
- Depth Levels (0-5)
- Domain Templates (Philosophy, History/IR, Economics, Science)
- Depth evaluation checklist
- Domain structure guidance

CRITICAL: This is a lightweight utility module - not a complex framework.
It provides helpers that other pipelines can use.

---

MAPPING GIỮA 2 HỆ CẤU TRÚC (3-TIER ↔ 5-PART):

**3-tier (Reframing / Conceptual Map / Boundary of Knowledge):**
- Đây là view high-level, mô tả 3 tầng phân tích triết học
- Reframing: Đặt lại câu hỏi, xác định loại câu hỏi (epistemology, ontology, etc.)
- Conceptual Map: Bản đồ khái niệm học thuật (Kant/Husserl, Popper/Kuhn, etc.)
- Boundary of Knowledge: Ranh giới tri thức của StillMe

**5-part (Anchor / Unpack / Explore / Edge / Return):**
- Đây là implementation chi tiết, cấu trúc cụ thể cho câu trả lời
- Anchor ~= Reframing (đặt lại câu hỏi, định nghĩa khái niệm)
- Unpack + Explore ~= Conceptual Map (mổ xẻ cấu trúc nội tại + phân tích hệ quả)
- Edge + Return ~= Boundary of Knowledge (chỉ ra giới hạn + tóm tắt)

**Quan hệ:**
- 3-tier = abstraction level (high-level view)
- 5-part = concrete implementation (detailed structure)
- Chúng KHÔNG mâu thuẫn mà là 2 level abstraction khác nhau
- 3-tier giúp hiểu "phải có gì" (what)
- 5-part giúp hiểu "làm thế nào" (how)

**Ví dụ:**
- 3-tier nói: "Phải có Conceptual Map (Kant/Husserl)"
- 5-part nói: "Làm bằng cách Unpack (cảm năng, giác tính) + Explore (phenomena/noumena)"
"""

import re
import logging
from enum import Enum
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DepthLevel(int, Enum):
    """
    Levels of Depth according to StillMe Style Spec v1
    
    Level 0: Surface / Wikipedia-level
    Level 1: Single-Factor Analysis
    Level 2: Multi-Factor Analysis
    Level 3: Structural / Architectural Analysis (default for Option B)
    Level 4: Meta-Cognitive & Cross-Tradition Analysis
    Level 5: Synthesis / Model-Building
    """
    SURFACE = 0
    SINGLE_FACTOR = 1
    MULTI_FACTOR = 2
    STRUCTURAL = 3
    META_COGNITIVE = 4
    SYNTHESIS = 5


class DomainType(str, Enum):
    """Domain types for template selection"""
    PHILOSOPHY = "philosophy"
    HISTORY = "history"
    ECONOMICS = "economics"
    SCIENCE = "science"
    GENERIC = "generic"


@dataclass
class DomainTemplate:
    """Domain template structure"""
    domain: DomainType
    structure: List[str]  # e.g., ["Anchor", "Unpack", "Explore", "Edge", "Return"]
    description: str


# Domain Templates from Style Spec v1
DOMAIN_TEMPLATES: Dict[DomainType, DomainTemplate] = {
    DomainType.PHILOSOPHY: DomainTemplate(
        domain=DomainType.PHILOSOPHY,
        structure=["Anchor", "Unpack", "Explore", "Edge", "Return"],
        description="Philosophy template: Anchor → Unpack → Explore → Edge → Return"
    ),
    DomainType.HISTORY: DomainTemplate(
        domain=DomainType.HISTORY,
        structure=["Context", "Mechanism", "Actors", "Dynamics", "Impact"],
        description="History/IR template: Context → Mechanism → Actors → Dynamics → Impact"
    ),
    DomainType.ECONOMICS: DomainTemplate(
        domain=DomainType.ECONOMICS,
        structure=["Problem", "Model", "Tension", "Failure Modes", "Legacy"],
        description="Economics template: Problem → Model → Tension → Failure Modes → Legacy"
    ),
    DomainType.SCIENCE: DomainTemplate(
        domain=DomainType.SCIENCE,
        structure=["Hypothesis", "Mechanism", "Evidence", "Limits", "Open Questions"],
        description="Science template: Hypothesis → Mechanism → Evidence → Limits → Open Questions"
    ),
    DomainType.GENERIC: DomainTemplate(
        domain=DomainType.GENERIC,
        structure=["Introduction", "Analysis", "Implications", "Limitations", "Conclusion"],
        description="Generic template: Introduction → Analysis → Implications → Limitations → Conclusion"
    ),
}


def detect_domain(question: str, question_type: Optional[str] = None) -> DomainType:
    """
    Detect domain type from question text and optional question_type.
    
    Args:
        question: User question text
        question_type: Optional question type from QuestionClassifierV2
        
    Returns:
        DomainType
    """
    question_lower = question.lower()
    
    # Use question_type if available
    if question_type:
        if "philosophy" in question_type.lower() or "meta" in question_type.lower():
            return DomainType.PHILOSOPHY
        if "factual" in question_type.lower() and "academic" in question_type.lower():
            # Check for history/economics keywords
            if any(word in question_lower for word in ["history", "historical", "conference", "treaty", "war", "lịch sử", "hiệp ước", "hội nghị"]):
                return DomainType.HISTORY
            if any(word in question_lower for word in ["economic", "finance", "keynes", "imf", "world bank", "kinh tế", "tài chính"]):
                return DomainType.ECONOMICS
            if any(word in question_lower for word in ["physics", "quantum", "nuclear", "fusion", "vật lý", "hạt nhân"]):
                return DomainType.SCIENCE
    
    # Fallback to keyword detection
    if any(word in question_lower for word in ["philosophy", "philosophical", "epistemology", "ontology", "triết học", "nhận thức luận"]):
        return DomainType.PHILOSOPHY
    
    if any(word in question_lower for word in ["history", "historical", "conference", "treaty", "war", "lịch sử", "hiệp ước", "hội nghị"]):
        return DomainType.HISTORY
    
    if any(word in question_lower for word in ["economic", "finance", "keynes", "imf", "world bank", "bretton woods", "kinh tế", "tài chính"]):
        return DomainType.ECONOMICS
    
    if any(word in question_lower for word in ["physics", "quantum", "nuclear", "fusion", "hypothesis", "experiment", "vật lý", "hạt nhân", "giả thuyết"]):
        return DomainType.SCIENCE
    
    return DomainType.GENERIC


def get_depth_target_for_question(
    domain: DomainType,
    option_b_enabled: bool = False,
    is_fake_entity: bool = False
) -> DepthLevel:
    """
    Get target depth level for a question.
    
    According to Style Spec v1:
    - Real questions + Option B → Level 3-4
    - Fake entities → Level 2 max (fallback, no need for deep analysis)
    
    Args:
        domain: Domain type
        option_b_enabled: Whether Option B is enabled
        is_fake_entity: Whether this is a fake entity (fallback case)
        
    Returns:
        Target DepthLevel
    """
    if is_fake_entity:
        # Fake entities: fallback, no need for deep analysis
        return DepthLevel.MULTI_FACTOR  # Level 2 max
    
    if option_b_enabled:
        # Option B: target Level 3-4 (Structural or Meta-Cognitive)
        if domain == DomainType.PHILOSOPHY:
            return DepthLevel.META_COGNITIVE  # Level 4 for philosophy
        return DepthLevel.STRUCTURAL  # Level 3 for others
    
    # Default: Level 2-3 depending on domain
    if domain == DomainType.PHILOSOPHY:
        return DepthLevel.STRUCTURAL  # Level 3
    return DepthLevel.MULTI_FACTOR  # Level 2


def get_domain_template(domain: DomainType) -> DomainTemplate:
    """
    Get domain template structure.
    
    Args:
        domain: Domain type
        
    Returns:
        DomainTemplate
    """
    return DOMAIN_TEMPLATES.get(domain, DOMAIN_TEMPLATES[DomainType.GENERIC])


def build_domain_structure_guidance(
    domain: DomainType,
    detected_lang: str = "vi"
) -> str:
    """
    Build system prompt segment for domain structure guidance.
    
    Args:
        domain: Domain type
        detected_lang: Language code
        
    Returns:
        Guidance text for system prompt
    """
    template = get_domain_template(domain)
    
    if domain == DomainType.PHILOSOPHY:
        if detected_lang == "vi":
            return f"""**CẤU TRÚC TRẢ LỜI TRIẾT HỌC (MANDATORY - 5 PHẦN):**

**1. ANCHOR (Đặt lại câu hỏi):**
- Đặt lại câu hỏi bằng ngôn ngữ rõ ràng, định nghĩa khái niệm chính
- Ví dụ: "Câu hỏi về sự phân biệt giữa hiện tượng (phenomena) và vật tự thân (noumena) trong triết học Kant..."

**2. UNPACK (Mổ xẻ cấu trúc nội tại):**
- Phân tích cấu trúc nội tại của khái niệm
- Ví dụ với Kant: cảm năng, giác tính, không-thời-gian tiên nghiệm, phạm trù
- Giải thích tại sao cấu trúc này dẫn đến phân biệt phenomena/noumena

**3. EXPLORE (Phân tích hệ quả):**
- Con người biết gì, không biết gì, tại sao
- Ví dụ với Kant: Vì sao ta chỉ biết phenomena? Vai trò của noumena như giới hạn?
- Phân tích khả năng nhận thức "thực tại khách quan"

**4. EDGE (Chỉ ra giới hạn, tranh luận, phê phán):**
- Chỉ ra giới hạn của lập luận
- Tham chiếu các nhà phê phán: Hegel, Husserl, chủ nghĩa hiện tượng, chủ nghĩa thực chứng
- Tranh luận và phản biện

**5. RETURN (Tóm tắt cho người đọc bình thường):**
- 1 đoạn ngắn dễ hiểu, tóm tắt điểm chính
- Không quá kỹ thuật, nhưng vẫn chính xác"""
        else:
            return f"""**PHILOSOPHICAL ANSWER STRUCTURE (MANDATORY - 5 PARTS):**

**1. ANCHOR (Reframe the question):**
- Reframe the question clearly, define key concepts
- Example: "The question about the distinction between phenomena and noumena in Kant's philosophy..."

**2. UNPACK (Unpack internal structure):**
- Analyze the internal structure of the concept
- Example with Kant: sensibility, understanding, space-time a priori, categories
- Explain why this structure leads to the phenomena/noumena distinction

**3. EXPLORE (Analyze consequences):**
- What humans know, don't know, and why
- Example with Kant: Why do we only know phenomena? Role of noumena as limit?
- Analyze the possibility of knowing "objective reality"

**4. EDGE (Point out limits, debates, critiques):**
- Point out limits of the argument
- Reference critics: Hegel, Husserl, phenomenology, positivism
- Debates and counterarguments

**5. RETURN (Summarize for general reader):**
- 1 short paragraph, easy to understand, summarizes key points
- Not too technical, but still accurate"""
    
    elif domain == DomainType.HISTORY:
        if detected_lang == "vi":
            return f"""**CẤU TRÚC TRẢ LỜI LỊCH SỬ/QUAN HỆ QUỐC TẾ (5 PHẦN):**

**1. CONTEXT (Bối cảnh):**
- Bối cảnh lịch sử: thời điểm, chiến tranh, khủng hoảng, cấu trúc quyền lực

**2. MECHANISM (Thiết chế/Cơ chế):**
- Hiệp ước, liên minh, thể chế, điều khoản chính (nếu có thật)

**3. ACTORS (Các chủ thể):**
- Quốc gia, khối, lãnh tụ, lợi ích và mục tiêu của họ

**4. DYNAMICS (Động lực):**
- Cách cơ chế này vận hành trong thời gian: xung đột, hợp tác, khủng hoảng, turning points

**5. IMPACT (Tác động):**
- Tác động dài hạn: lên cấu trúc an ninh, lên trật tự quốc tế, di sản lâu dài"""
        else:
            return f"""**HISTORY/IR ANSWER STRUCTURE (5 PARTS):**

**1. CONTEXT:**
- Historical context: time period, wars, crises, power structure

**2. MECHANISM:**
- Treaties, alliances, institutions, key provisions (if real)

**3. ACTORS:**
- Nations, blocs, leaders, their interests and goals

**4. DYNAMICS:**
- How the mechanism operated over time: conflicts, cooperation, crises, turning points

**5. IMPACT:**
- Long-term impact: on security structure, international order, lasting legacy"""
    
    elif domain == DomainType.ECONOMICS:
        if detected_lang == "vi":
            return f"""**CẤU TRÚC TRẢ LỜI KINH TẾ/TÀI CHÍNH (5 PHẦN):**

**1. PROBLEM (Vấn đề):**
- Vấn đề kinh tế cần giải quyết: khủng hoảng, bất ổn tỷ giá, nợ, thất nghiệp

**2. MODEL (Mô hình):**
- Thiết kế chính sách/mô hình: hệ thống tỷ giá, quỹ, ngân hàng, chuẩn vàng/USD

**3. TENSION (Căng thẳng):**
- Căng thẳng giữa các bên/tư tưởng: ví dụ Keynes vs White (Bancor vs USD-centric)

**4. FAILURE MODES (Cách hệ thống bộc lộ giới hạn):**
- Bất cân xứng, moral hazard, vấn đề thanh khoản, khủng hoảng

**5. LEGACY (Di sản):**
- Thể chế còn tồn tại (IMF, World Bank), các cải cách sau này, cách nó định hình kinh tế toàn cầu"""
        else:
            return f"""**ECONOMICS/FINANCE ANSWER STRUCTURE (5 PARTS):**

**1. PROBLEM:**
- Economic problem to solve: crisis, exchange rate instability, debt, unemployment

**2. MODEL:**
- Policy/model design: exchange rate system, funds, banks, gold/USD standard

**3. TENSION:**
- Tension between parties/ideologies: e.g., Keynes vs White (Bancor vs USD-centric)

**4. FAILURE MODES:**
- How system reveals limits: asymmetry, moral hazard, liquidity issues, crises

**5. LEGACY:**
- Surviving institutions (IMF, World Bank), later reforms, how it shaped global economy"""
    
    elif domain == DomainType.SCIENCE:
        if detected_lang == "vi":
            return f"""**CẤU TRÚC TRẢ LỜI KHOA HỌC/KỸ THUẬT (5 PHẦN):**

**1. HYPOTHESIS (Giả thuyết):**
- Giả thuyết/câu hỏi khoa học

**2. MECHANISM (Cơ chế):**
- Cơ chế hoạt động (ở mức khái niệm)

**3. EVIDENCE (Dữ liệu):**
- Dữ liệu/thí nghiệm ủng hộ

**4. LIMITS (Giới hạn):**
- Giới hạn hiện tại, nơi mô hình chưa giải thích được

**5. OPEN QUESTIONS (Câu hỏi mở):**
- Câu hỏi mở, hướng nghiên cứu tiếp theo"""
        else:
            return f"""**SCIENCE/TECHNICAL ANSWER STRUCTURE (5 PARTS):**

**1. HYPOTHESIS:**
- Scientific hypothesis/question

**2. MECHANISM:**
- Operating mechanism (at conceptual level)

**3. EVIDENCE:**
- Supporting data/experiments

**4. LIMITS:**
- Current limits, where model doesn't explain

**5. OPEN QUESTIONS:**
- Open questions, future research directions"""
    
    else:  # GENERIC
        if detected_lang == "vi":
            return f"""**CẤU TRÚC TRẢ LỜI (5 PHẦN):**

**1. INTRODUCTION (Giới thiệu):**
- Đặt lại câu hỏi, định nghĩa khái niệm chính

**2. ANALYSIS (Phân tích):**
- Phân tích đa chiều, nhiều yếu tố tương tác

**3. IMPLICATIONS (Hệ quả):**
- Hệ quả và tác động

**4. LIMITATIONS (Giới hạn):**
- Giới hạn, tranh luận, phê phán

**5. CONCLUSION (Kết luận):**
- Tóm tắt ngắn gọn, dễ hiểu"""
        else:
            return f"""**ANSWER STRUCTURE (5 PARTS):**

**1. INTRODUCTION:**
- Reframe question, define key concepts

**2. ANALYSIS:**
- Multi-dimensional analysis, multiple interacting factors

**3. IMPLICATIONS:**
- Consequences and impacts

**4. LIMITATIONS:**
- Limits, debates, critiques

**5. CONCLUSION:**
- Short, easy-to-understand summary"""


def evaluate_depth(
    response: str,
    domain: DomainType,
    target_depth: DepthLevel
) -> Tuple[bool, List[str]]:
    """
    Evaluate if response meets depth requirements based on Style Spec v1 checklist.
    
    Checklist (6 items):
    1. Rõ cấu trúc (Clear structure)
    2. Trả lời trực tiếp câu hỏi (Direct answer)
    3. Đa chiều (Multi-dimensional)
    4. Có Edge/Critique (Has critique/limits)
    5. Return dễ hiểu (Clear summary)
    6. Không topic drift (No topic drift)
    
    Args:
        response: Response text to evaluate
        domain: Domain type
        target_depth: Target depth level
        
    Returns:
        Tuple of (meets_requirements, missing_items)
    """
    response_lower = response.lower()
    missing_items = []
    
    # Get template structure
    template = get_domain_template(domain)
    structure_parts = template.structure
    
    # 1. Check for clear structure (template parts present)
    has_structure = False
    if domain == DomainType.PHILOSOPHY:
        # Check for philosophy structure keywords
        structure_keywords = {
            "anchor": ["anchor", "đặt lại", "reframe", "định nghĩa"],
            "unpack": ["unpack", "mổ xẻ", "cấu trúc nội tại", "internal structure"],
            "explore": ["explore", "phân tích hệ quả", "biết gì", "không biết gì"],
            "edge": ["edge", "giới hạn", "phê phán", "critique", "hegel", "husserl"],
            "return": ["return", "tóm tắt", "summary", "nếu nói đơn giản"]
        }
    elif domain == DomainType.HISTORY:
        structure_keywords = {
            "context": ["context", "bối cảnh", "background"],
            "mechanism": ["mechanism", "thiết chế", "cơ chế", "treaty", "hiệp ước"],
            "actors": ["actors", "chủ thể", "quốc gia", "nations"],
            "dynamics": ["dynamics", "động lực", "vận hành", "operated"],
            "impact": ["impact", "tác động", "legacy", "di sản"]
        }
    elif domain == DomainType.ECONOMICS:
        structure_keywords = {
            "problem": ["problem", "vấn đề", "crisis", "khủng hoảng"],
            "model": ["model", "mô hình", "system", "hệ thống"],
            "tension": ["tension", "căng thẳng", "conflict", "keynes", "white"],
            "failure": ["failure", "giới hạn", "limits", "crisis"],
            "legacy": ["legacy", "di sản", "imf", "world bank"]
        }
    else:
        structure_keywords = {}
    
    # Check if at least 3 structure parts are present
    found_parts = 0
    for part in structure_parts:
        part_lower = part.lower()
        if part_lower in structure_keywords:
            keywords = structure_keywords[part_lower]
            if any(keyword in response_lower for keyword in keywords):
                found_parts += 1
    
    if found_parts >= 3:
        has_structure = True
    else:
        missing_items.append("Rõ cấu trúc (Clear structure matching domain template)")
    
    # 2. Check for direct answer (domain-specific)
    has_direct_answer = False
    if domain == DomainType.PHILOSOPHY:
        # Should have "biết gì / không biết gì / tại sao"
        if any(phrase in response_lower for phrase in ["biết gì", "không biết gì", "tại sao", "know what", "don't know what", "why"]):
            has_direct_answer = True
    elif domain == DomainType.HISTORY:
        # Should have "vai trò", "tác động dài hạn"
        if any(phrase in response_lower for phrase in ["vai trò", "tác động", "role", "impact", "legacy"]):
            has_direct_answer = True
    elif domain == DomainType.ECONOMICS:
        # Should have "tension", "conflict", "keynes", "white"
        if any(phrase in response_lower for phrase in ["tension", "căng thẳng", "keynes", "white", "conflict"]):
            has_direct_answer = True
    else:
        has_direct_answer = True  # Generic: assume OK
    
    if not has_direct_answer:
        missing_items.append("Trả lời trực tiếp câu hỏi (Direct answer to question)")
    
    # 3. Check for multi-dimensional (multiple factors/actors/aspects)
    has_multi_dimensional = False
    multi_dimensional_indicators = [
        r'\b(nhiều|multiple|various|several)\s+(yếu tố|factors|aspects|nguyên nhân)',
        r'\b(first|second|third|thứ nhất|thứ hai|thứ ba)',
        r'\b(on one hand|on the other hand|một mặt|mặt khác)',
        r'\b(actors|chủ thể|nations|quốc gia).*and.*(actors|chủ thể)',
    ]
    if any(re.search(pattern, response_lower) for pattern in multi_dimensional_indicators):
        has_multi_dimensional = True
    else:
        # Check for multiple entities mentioned
        entity_count = len(re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', response))
        if entity_count >= 3:  # At least 3 named entities
            has_multi_dimensional = True
    
    if not has_multi_dimensional:
        missing_items.append("Đa chiều (Multi-dimensional analysis)")
    
    # 4. Check for Edge/Critique
    has_edge = False
    edge_indicators = [
        r'\b(phê phán|critique|criticism|limit|giới hạn|boundary)',
        r'\b(hegel|husserl|positivism|thực chứng|phenomenology|hiện tượng luận)',
        r'\b(debate|tranh luận|oppose|phản đối|challenge|thách thức)',
        r'\b(however|nevertheless|tuy nhiên|nhưng|but)',
    ]
    if any(re.search(pattern, response_lower) for pattern in edge_indicators):
        has_edge = True
    
    if not has_edge:
        missing_items.append("Có Edge/Critique (Has critique/limits/debates)")
    
    # 5. Check for Return (clear summary)
    has_return = False
    return_indicators = [
        r'\b(tóm tắt|summary|nếu nói đơn giản|in summary|to summarize)',
        r'\b(kết luận|conclusion|tổng kết)',
        r'\b(nói chung|generally|overall)',
    ]
    if any(re.search(pattern, response_lower) for pattern in return_indicators):
        has_return = True
    else:
        # Check if last paragraph is shorter and summarizes
        paragraphs = response.split('\n\n')
        if paragraphs:
            last_para = paragraphs[-1].lower()
            if len(last_para) < 200:  # Short summary paragraph
                has_return = True
    
    if not has_return:
        missing_items.append("Return dễ hiểu (Clear summary/return)")
    
    # 6. Check for topic drift (AI/LLM when not asked)
    has_topic_drift = False
    topic_drift_indicators = [
        r'\b(ý thức của (llm|mô hình|ai)|consciousness of (llm|model|ai))',
        r'\b(tôi (chỉ|được) (hiểu|train)|I (only|was) (understand|trained))',
        r'\b(embedding|semantic vectors|token attention|pattern matching)',
        r'\b(iit|global workspace|dennett).*(llm|ai|model)',
    ]
    # Only flag if question doesn't mention AI/consciousness
    # (This check should be done by caller with question context)
    # For now, we'll be lenient - only flag if very obvious drift
    
    # Determine if meets requirements
    # If missing >= 2 items, needs rewrite
    meets_requirements = len(missing_items) < 2
    
    return meets_requirements, missing_items


def get_philosophy_structure_prompt_segment(detected_lang: str = "vi") -> str:
    """
    Get the philosophy structure prompt segment (Anchor → Unpack → Explore → Edge → Return).
    
    This is a convenience function that returns the same content as
    build_domain_structure_guidance(DomainType.PHILOSOPHY, detected_lang).
    
    Args:
        detected_lang: Language code
        
    Returns:
        Philosophy structure guidance text
    """
    return build_domain_structure_guidance(DomainType.PHILOSOPHY, detected_lang)

