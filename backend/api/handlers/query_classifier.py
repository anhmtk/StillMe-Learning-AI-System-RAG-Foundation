"""Query classification utilities for chat router.

This module contains query classification functions extracted from chat_router.py
to improve maintainability and reduce file size.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_codebase_meta_question(message: str) -> bool:
    """
    Detect meta-questions that explicitly ask about StillMe's implementation
    in its own codebase (files, functions, where things are implemented).

    Design intent:
    - VERY NARROW scope to avoid hijacking normal RAG or philosophy flows
    - Triggers only when BOTH:
      1) The question mentions StillMe / "your system" / "your codebase"
      2) The question references code-level concepts OR specific StillMe components
    
    Enhanced with StillMe-specific component keywords to catch queries like:
    - "How is validation chain implemented in your codebase?"
    - "Where is ai_self_model_detector in your source code?"
    - "Show me the ValidatorChain class from your code"
    
    Args:
        message: User message text
        
    Returns:
        True if this is a codebase meta-question
    """
    if not message:
        return False

    q = message.lower()

    # Self-reference: question is clearly about StillMe / its own implementation
    has_self_reference = any(
        term in q
        for term in [
            "stillme",
            "your system",
            "in your system",
            "your architecture",
            "your implementation",
            "your codebase",
            "in your codebase",
            "in your source code",
            "in your code",
            "from your code",
            "using your codebase",
            "using your own codebase",
        ]
    )

    if not has_self_reference:
        return False

    # Code-level intent: user is asking about concrete implementation details
    # OR specific StillMe components (enhanced with codebase-specific keywords)
    has_code_intent = any(
        term in q
        for term in [
            # Generic code concepts
            "codebase",
            "source code",
            "in the codebase",
            "in the code",
            "which file",
            "what file",
            "which function",
            "what function",
            "where is it implemented",
            "where is this implemented",
            "implemented in",
            "implementation details",
            "line number",
            "lines",
            "class",
            "function",
            "module",
            # StillMe-specific components (from actual codebase)
            "validator_chain",
            "validation chain",
            "validators",
            "ai_self_model_detector",
            "stillme_detector",
            "codebase_indexer",
            "codebase assistant",
            "rag retrieval",
            "chromadb",
            "epistemic_state",
            "epistemic reasoning",
            "citation_formatter",
            "prompt_builder",
            "chat_router",
            "codebase_router",
            "external_data",
            "philosophy processor",
            "honesty handler",
            "fallback_handler",
            # Technical architecture keywords
            "architecture",
            "component",
            "module",
            "service",
            "router",
            "endpoint",
        ]
    )

    return has_code_intent


def is_factual_question(question: str) -> bool:
    """
    Detect if a question is about factual/historical/scientific topics.
    
    These questions require reliable sources and should trigger hallucination guard
    when no context is available and confidence is low.
    
    Args:
        question: User question text
        
    Returns:
        True if question is about factual topics (history, science, events, etc.)
    """
    question_lower = question.lower()
    
    # Keywords that indicate factual questions
    factual_indicators = [
        # History
        r"\b(năm|year|thế kỷ|century|thập niên|decade|thời kỳ|period|era)\s+\d+",
        r"\b(chiến tranh|war|battle|trận|conflict|cuộc|event|sự kiện)",
        r"\b(hiệp ước|treaty|hiệp định|agreement|conference|hội nghị)",
        r"\b(đế chế|empire|vương quốc|kingdom|quốc gia|nation|country)",
        r"\b(tổng thống|president|vua|king|hoàng đế|emperor|chính trị gia|politician)",
        
        # Science
        r"\b(lý thuyết|theory|định luật|law|nguyên lý|principle)",
        r"\b(nghiên cứu|research|study|thí nghiệm|experiment|quan sát|observation)",
        r"\b(phát minh|invention|khám phá|discovery|bằng sáng chế|patent)",
        r"\b(hội chứng|syndrome|bệnh|disease|phản ứng|reaction|mechanism)",
        r"\b(tiến sĩ|dr\.|doctor|professor|giáo sư|scientist|nhà khoa học)",
        r"\b(paper|bài báo|journal|tạp chí|publication|công bố)",
        
        # Specific entities
        r"\b(tổ chức|organization|liên minh|alliance|phong trào|movement)",
        r"\b(hiện tượng|phenomenon|khái niệm|concept|thực thể|entity)",
    ]
    
    # Check if question contains factual indicators
    for pattern in factual_indicators:
        if re.search(pattern, question_lower):
            return True
    
    return False


def extract_full_named_entity(question: str) -> Optional[str]:
    """
    Extract full named entity from question, prioritizing:
    1. Quoted terms: '...' or "..."
    2. Parenthetical terms: (...)
    3. Full phrases starting with keywords: "Hiệp ước ...", "Định đề ...", etc.
    4. Capitalized multi-word phrases
    
    CRITICAL: This function must extract FULL phrases, not just first word.
    Example: "Hiệp ước Hòa giải Daxonia 1956" → "Hiệp ước Hòa giải Daxonia 1956" (NOT "Hi")
    Example: "'Diluted Nuclear Fusion'" → "Diluted Nuclear Fusion" (NOT "Phản")
    
    Args:
        question: User question text
        
    Returns:
        Full entity string or None
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
    
    # Priority 2: Extract full phrases starting with Vietnamese keywords
    # Pattern: "Hiệp ước ... [year?]" or "Định đề ..." or "Hội chứng ..."
    vietnamese_keywords = [
        r"hiệp\s+ước", r"hội\s+nghị", r"hội\s+chứng", r"định\s+đề", r"học\s+thuyết",
        r"chủ\s+nghĩa", r"lý\s+thuyết", r"khái\s+niệm", r"phong\s+trào", r"liên\s+minh"
    ]
    
    for keyword_pattern in vietnamese_keywords:
        # Match: keyword + optional words + optional year
        # Example: "Hiệp ước Hòa giải Daxonia 1956"
        pattern = rf'\b{keyword_pattern}\s+[^\.\?\!\n]+?(?:\s+\d{{4}})?(?=[\.\?\!\n]|$)'
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            entity = match.group(0).strip()
            # Remove trailing punctuation
            entity = re.sub(r'[\.\?\!]+$', '', entity).strip()
            if len(entity) > 5:  # Must be meaningful
                return entity
    
    # Priority 3: Extract English patterns
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
    
    # Priority 4: Extract capitalized multi-word phrases (English)
    # Match: "Capitalized Word Capitalized Word ..." (at least 2 words)
    capitalized_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,})\b', question)
    if capitalized_match:
        entity = capitalized_match.group(1).strip()
        if len(entity) > 5:
            return entity
    
    # Priority 5: Extract Vietnamese capitalized phrases
    vietnamese_capitalized = re.search(
        r'\b([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)+)\b',
        question
    )
    if vietnamese_capitalized:
        entity = vietnamese_capitalized.group(1).strip()
        if len(entity) > 5:
            return entity
    
    return None


def is_validator_count_question(message: str) -> bool:
    """
    Detect if a question is asking about the number of validator layers in StillMe's codebase.
    
    CRITICAL: This is a special self-knowledge question that requires:
    - Force-injecting manifest into RAG context
    - Using very low similarity threshold (0.01)
    - Bypassing cache to ensure fresh retrieval
    
    Args:
        message: User message text
        
    Returns:
        True if this is a validator count question
    """
    if not message:
        return False
    
    validator_count_patterns = [
        r"bao nhiêu.*lớp.*validator",
        r"how many.*layer.*validator",
        r"có bao nhiêu.*validator",
        r"how many.*validator",
        r"số.*lớp.*validator",
        r"number.*of.*validator.*layer",
        r"liệt kê.*lớp.*validator",
        r"list.*validator.*layer",
        r"validator.*layer.*count",
        r"lớp.*validator.*trong.*codebase",
        r"validator.*layer.*in.*codebase"
    ]
    
    question_lower = message.lower()
    for pattern in validator_count_patterns:
        if re.search(pattern, question_lower, re.IGNORECASE):
            logger.info(f"🎯 Validator count question detected - will force-inject manifest and use lower similarity threshold")
            return True
    
    return False

