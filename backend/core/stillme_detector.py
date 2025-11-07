"""
StillMe Query Detector - Detects queries about StillMe itself
Implements Special Retrieval Rule for StillMe-related questions
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Keywords that indicate StillMe-related queries (Vietnamese and English)
STILLME_KEYWORDS = {
    # StillMe name variations
    "stillme", "still me", "still-me",
    
    # Learning-related (Vietnamese)
    "học", "học tập", "học hỏi", "tự học", "học liên tục",
    "cách học", "quá trình học", "học như thế nào",
    
    # Learning-related (English)
    "learn", "learning", "how do you learn", "how does it learn",
    "continuous learning", "self-learning", "learning process",
    
    # System-related (Vietnamese)
    "hệ thống", "cách hoạt động", "hoạt động như thế nào", "vận hành",
    "quá trình", "cơ chế", "kiến trúc", "hoạt động", "vận hành như thế nào",
    
    # System-related (English)
    "system", "how does it work", "how do you work", "architecture",
    "mechanism", "process", "how it works", "how work", "how function",
    "mechanisms", "functioning", "operate", "operation",
    
    # System-related (German)
    "wie funktioniert", "wie arbeitet", "funktionsweise", "mechanismus",
    "system", "prozess", "architektur",
    
    # System-related (French)
    "fonctionne", "comment fonctionne", "mécanisme", "mécanismes",
    "système", "processus", "architecture", "fonctionnement",
    
    # System-related (Spanish)
    "cómo funciona", "cómo trabaja", "mecanismo", "mecanismos",
    "sistema", "proceso", "arquitectura", "funcionamiento",
    
    # System-related (Chinese)
    "如何工作", "如何运作", "机制", "系统", "过程", "架构", "运作方式",
    
    # System-related (Japanese)
    "どのように機能", "どのように動作", "メカニズム", "システム", "プロセス", "アーキテクチャ",
    
    # RAG-related
    "rag", "retrieval", "vector", "knowledge base", "cơ sở tri thức",
    
    # Evolution-related
    "tiến hóa", "evolution", "evolve", "self-evolving",
    
    # Transparency-related
    "minh bạch", "transparency", "transparent",
    
    # Update-related
    "cập nhật", "update", "updates", "cập nhật tri thức",
    "knowledge update", "daily learning"
}


def detect_stillme_query(query: str) -> Tuple[bool, List[str]]:
    """
    Detect if query is about StillMe itself.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (is_stillme_query, matched_keywords)
    """
    query_lower = query.lower()
    matched_keywords = []
    
    # Check for StillMe name
    if re.search(r'\bstillme\b|\bstill\s*me\b|\bstill-me\b', query_lower):
        matched_keywords.append("stillme_name")
        return (True, matched_keywords)
    
    # Check for keyword combinations
    # Pattern 1: "StillMe" + learning/system keywords
    has_stillme_context = any(
        keyword in query_lower 
        for keyword in ["stillme", "still me", "still-me", "bạn", "you", "it", "your", "của bạn"]
    )
    
    has_learning_keyword = any(
        keyword in query_lower 
        for keyword in ["học", "learn", "learning", "học tập", "học hỏi", "tự học", "học như thế nào", "how do you learn", "how does.*learn", "cách học"]
    )
    
    has_system_keyword = any(
        keyword in query_lower 
        for keyword in [
            "hệ thống", "system", "hoạt động", "vận hành", "work", "cách", "how", 
            "như thế nào", "how does", "how do", "how work", "how function",
            "mechanisms", "wie funktioniert", "fonctionne", "comment fonctionne",
            "cómo funciona", "如何工作", "どのように機能", "mechanism", "cơ chế"
        ]
    )
    
    # If query has StillMe context + learning/system keywords, it's about StillMe
    if has_stillme_context and (has_learning_keyword or has_system_keyword):
        if has_learning_keyword:
            matched_keywords.append("learning")
        if has_system_keyword:
            matched_keywords.append("system")
        return (True, matched_keywords)
    
    # Pattern 2: Direct questions about StillMe (even without name)
    # "What is StillMe?" / "StillMe là gì?"
    if re.search(r'(what|gì|là gì|what is|what are).*stillme', query_lower):
        matched_keywords.append("what_is")
        return (True, matched_keywords)
    
    # Pattern 3: Questions about learning/evolution with StillMe context
    # CRITICAL: "Bạn học tập như thế nào?" / "How do you learn?" should trigger
    if (has_learning_keyword or has_system_keyword) and any(
        keyword in query_lower 
        for keyword in ["bạn", "you", "your", "it", "stillme", "hệ thống", "system", "của bạn"]
    ):
        if has_learning_keyword:
            matched_keywords.append("learning")
        if has_system_keyword:
            matched_keywords.append("system")
        return (True, matched_keywords)
    
    # Pattern 3b: Direct learning questions (even without explicit StillMe name)
    # "Bạn học tập như thế nào?" / "How do you learn?" - assume about StillMe
    if has_learning_keyword and any(
        keyword in query_lower 
        for keyword in ["bạn", "you", "your", "như thế nào", "how", "cách"]
    ):
        matched_keywords.append("learning_direct")
        return (True, matched_keywords)
    
    # Pattern 4: RAG/transparency/evolution keywords (likely about StillMe)
    has_rag_keyword = any(
        keyword in query_lower 
        for keyword in ["rag", "retrieval", "vector", "knowledge base", "cơ sở tri thức"]
    )
    
    has_transparency_keyword = any(
        keyword in query_lower 
        for keyword in ["minh bạch", "transparency", "transparent"]
    )
    
    has_evolution_keyword = any(
        keyword in query_lower 
        for keyword in ["tiến hóa", "evolution", "evolve", "self-evolving"]
    )
    
    if has_rag_keyword or has_transparency_keyword or has_evolution_keyword:
        if has_rag_keyword:
            matched_keywords.append("rag")
        if has_transparency_keyword:
            matched_keywords.append("transparency")
        if has_evolution_keyword:
            matched_keywords.append("evolution")
        return (True, matched_keywords)
    
    return (False, [])


def get_foundational_query_variants(query: str) -> List[str]:
    """
    Generate query variants optimized for retrieving StillMe foundational knowledge.
    
    Args:
        query: Original user query
        
    Returns:
        List of query variants optimized for StillMe knowledge retrieval
    """
    variants = [
        query,  # Original query
        "StillMe Learning AI system RAG foundation learning",
        "StillMe continuous learning RSS arXiv",
        "StillMe transparency RAG knowledge base",
        "StillMe how it learns updates knowledge",
    ]
    
    # Add language-specific variants
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in ["học", "học tập", "gì", "như thế nào"]):
        variants.extend([
            "StillMe hệ thống AI tự tiến hóa RAG",
            "StillMe học tập liên tục RSS",
            "StillMe cập nhật tri thức hàng ngày",
        ])
    
    return variants

