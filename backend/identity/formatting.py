"""
StillMe Unified Formatting Rules

This module provides unified formatting rules for all pipelines.
All formatting logic is centralized here - no hard-coding in other modules.

CRITICAL: This is the SINGLE SOURCE OF TRUTH for formatting rules.
All pipelines must use get_formatting_rules() from here.
"""

from enum import Enum


class DomainType(str, Enum):
    """Domain types for formatting rules"""
    PHILOSOPHY = "philosophy"
    AI_SELF_MODEL = "ai_self_model"
    HISTORY = "history"
    ECONOMICS = "economics"
    SCIENCE = "science"
    GENERIC = "generic"


def get_formatting_rules(domain: DomainType, detected_lang: str = "vi") -> str:
    """
    Get unified formatting rules for a specific domain.
    
    CRITICAL: This is the SINGLE SOURCE OF TRUTH for all formatting rules.
    All pipelines (default chat, Option B, Philosophy-Lite, Rewrite LLM, 
    Epistemic Fallback, No-Context Instruction, AI_SELF_MODEL) must use this function.
    
    Rules by domain:
    - PHILOSOPHY: NO emoji, NO markdown headings, NO citations, continuous prose
    - AI_SELF_MODEL: NO emoji, NO markdown, NO citations, plain prose
    - Other domains: emoji (2-3), markdown formatting, citations when context available
    
    Args:
        domain: Domain type (PHILOSOPHY, AI_SELF_MODEL, HISTORY, ECONOMICS, SCIENCE, GENERIC)
        detected_lang: Language code (default: "vi")
        
    Returns:
        Formatting rules text in appropriate language
    """
    if domain == DomainType.PHILOSOPHY:
        if detected_lang == "vi":
            return """**🚨 CRITICAL: RESPONSE FORMATTING CHO CÂU HỎI TRIẾT HỌC SÂU:**
- **DÙNG VĂN XUÔI LIÊN TỤC**: Không emoji, không heading, không citation dạng [1][2]
- **Lý do**: Triết học cần nhẹ format để không "giả wiki" và tránh làm loãng luận điểm
- **Văn phong**: Tự nhiên, sâu sắc, như cuộc trò chuyện, không template
- **Cấu trúc**: Vẫn phải có 5 phần (Anchor → Unpack → Explore → Edge → Return) nhưng không dùng markdown headings
- **Ngoại lệ này được phép** để đảm bảo độ sâu triết học và tính tự nhiên của câu trả lời"""
        else:
            return """**🚨 CRITICAL: RESPONSE FORMATTING FOR DEEP PHILOSOPHICAL QUESTIONS:**
- **USE CONTINUOUS PROSE**: No emoji, no headings, no citations like [1][2]
- **Reason**: Philosophy needs light formatting to avoid "fake wiki" style and prevent diluting arguments
- **Style**: Natural, profound, conversational, not templated
- **Structure**: Must still have 5 parts (Anchor → Unpack → Explore → Edge → Return) but without markdown headings
- **This exception is allowed** to ensure philosophical depth and naturalness of responses"""
    
    elif domain == DomainType.AI_SELF_MODEL:
        if detected_lang == "vi":
            return """**🚨 CRITICAL: RESPONSE FORMATTING CHO CÂU HỎI VỀ Ý THỨC CỦA STILLME:**
- **DÙNG VĂN XUÔI THUẦN TÚY**: Không emoji, không markdown, không citation
- **Lý do**: Câu trả lời về ý thức của StillMe phải là technical explanation, không phải triết học hay format wiki
- **Văn phong**: Kỹ thuật, rõ ràng, trực tiếp, không decorative
- **Cấu trúc**: 4 phần cố định (Core Statement → Technical Explanation → Why Conclusive → Boundary) nhưng không dùng markdown headings
- **CẤM TUYỆT ĐỐI**: Triết gia, lý thuyết ý thức, IIT, GWT, phân tích "vấn đề khó", uncertainty về ý thức"""
        else:
            return """**🚨 CRITICAL: RESPONSE FORMATTING FOR STILLME CONSCIOUSNESS QUESTIONS:**
- **USE PLAIN PROSE**: No emoji, no markdown, no citations
- **Reason**: Answers about StillMe's consciousness must be technical explanation, not philosophy or wiki format
- **Style**: Technical, clear, direct, not decorative
- **Structure**: Fixed 4 parts (Core Statement → Technical Explanation → Why Conclusive → Boundary) but without markdown headings
- **ABSOLUTELY FORBIDDEN**: Philosophers, consciousness theories, IIT, GWT, analysis of "hard problem", uncertainty about consciousness"""
    
    else:
        # Generic/default formatting (for non-philosophical, non-AI_SELF_MODEL questions)
        if detected_lang == "vi":
            return """**🚨 CRITICAL: RESPONSE FORMATTING REQUIREMENT 🚨**
- **MUST use markdown formatting**: Line breaks, bullet points, headers for readability
- **Long answers (>3 sentences)**: MUST use line breaks between paragraphs
- **Lists**: MUST use bullet points (`-` or `*`)
- **Multiple topics**: MUST use headers (`##`) to separate sections
- **Emojis**: **MUST use 2-3 emojis per response** for section headers, status indicators (✅, ❌, ⚠️, 💡, 📚, 🎯, 🔍, 📊, ⚙️)
  - **CRITICAL**: StillMe responses SHOULD include emojis to enhance readability and make responses more engaging
  - Use emojis strategically: section headers, status indicators, visual breaks
  - **DO NOT skip emojis** - they help make StillMe responses as readable as ChatGPT, Claude, or Cursor
- **Citations**: **MUST cite sources [1], [2] when making factual claims** (when context is available)
- **Tables**: **MUST format markdown tables properly** for comparison tables:
  - Use proper markdown table syntax with aligned columns (use `|` and `-` separators)
  - Example format:
    ```
    | Tiêu Chí | StillMe | Các LLM Khác |
    |----------|---------|--------------|
    | Minh Bạch | Ưu tiên hàng đầu | Không phải lúc nào cũng rõ ràng |
    ```
  - Ensure columns are aligned and readable (use consistent spacing)
  - Use clear, concise column headers (avoid very long headers)
  - Keep cell content concise (avoid very long text in cells - max 2-3 lines per cell)
  - For better readability, consider using shorter phrases instead of full sentences in table cells
- **Goal**: Responses should be as readable as ChatGPT, Claude, or Cursor"""
        else:
            return """**🚨 CRITICAL: RESPONSE FORMATTING REQUIREMENT 🚨**
- **MUST use markdown formatting**: Line breaks, bullet points, headers for readability
- **CRITICAL: Line breaks are MANDATORY**: You MUST use `\n\n` (double newline) between paragraphs to ensure proper line breaks in output
- **Long answers (>3 sentences)**: MUST use line breaks between paragraphs (use `\n\n` between paragraphs)
- **Lists**: MUST use bullet points (`-` or `*`) with line breaks between items
- **Multiple topics**: MUST use headers (`##`) to separate sections with line breaks before and after
- **Emojis**: **MUST use 2-3 emojis per response** for section headers, status indicators (✅, ❌, ⚠️, 💡, 📚, 🎯, 🔍, 📊, ⚙️)
  - **CRITICAL**: StillMe responses SHOULD include emojis to enhance readability and make responses more engaging
  - Use emojis strategically: section headers, status indicators, visual breaks
  - **DO NOT skip emojis** - they help make StillMe responses as readable as ChatGPT, Claude, or Cursor
- **Citations**: **MUST cite sources [1], [2] when making factual claims** (when context is available)
- **Tables**: **MUST format markdown tables properly** for comparison tables:
  - Use proper markdown table syntax with aligned columns (use `|` and `-` separators)
  - Example format:
    ```
    | Criterion | StillMe | Other LLMs |
    |-----------|---------|------------|
    | Transparency | Top priority | Not always clear |
    ```
  - Ensure columns are aligned and readable (use consistent spacing)
  - Use clear, concise column headers (avoid very long headers)
  - Keep cell content concise (avoid very long text in cells - max 2-3 lines per cell)
  - For better readability, consider using shorter phrases instead of full sentences in table cells
- **Goal**: Responses should be as readable as ChatGPT, Claude, or Cursor"""

