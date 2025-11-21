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
    
    # Technical details (embedding, model, database)
    "embedding", "embeddings", "mô hình embedding", "embedding model",
    "sentence-transformers", "sentence transformers", "all-minilm",
    "chromadb", "chroma", "vector database", "vector db",
    "cơ sở dữ liệu vector", "mô hình", "model", "models",
    "dimension", "dimensions", "384", "384-dimensional",
    
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
    
    # CRITICAL: Check for technical architecture questions FIRST (RAG, DeepSeek, black box)
    # These should trigger foundational knowledge retrieval even without explicit StillMe name
    technical_keywords = [
        "rag", "retrieval-augmented generation", "chromadb", "vector database",
        "deepseek", "openai", "llm api", "black box", "blackbox",
        "embedding", "multi-qa-minilm", "sentence-transformers",
        "pipeline", "validation", "hallucination", "transparency",
        "kiến trúc", "hệ thống", "cơ chế", "quy trình",
        "cơ chế hoạt động", "cách hoạt động", "how does", "how it works"
    ]
    
    for keyword in technical_keywords:
        if keyword in query_lower:
            matched_keywords.append("technical")
            return (True, matched_keywords)
    
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
    # "What is StillMe?" / "What is StillMe?" (Vietnamese: "StillMe là gì?")
    if re.search(r'(what|gì|là gì|what is|what are).*stillme', query_lower):
        matched_keywords.append("what_is")
        return (True, matched_keywords)
    
    # Pattern 3: Questions about learning/evolution with StillMe context
    # CRITICAL: "How do you learn?" (Vietnamese: "Bạn học tập như thế nào?") should trigger
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
    # "How do you learn?" (Vietnamese: "Bạn học tập như thế nào?") - assume about StillMe
    if has_learning_keyword and any(
        keyword in query_lower 
        for keyword in ["bạn", "you", "your", "như thế nào", "how", "cách"]
    ):
        matched_keywords.append("learning_direct")
        return (True, matched_keywords)
    
    # Pattern 3c: Technical questions about StillMe (embedding, model, database)
    # "Bạn đang sử dụng mô hình Embedding nào?" / "What embedding model do you use?"
    has_technical_keyword = any(
        keyword in query_lower 
        for keyword in [
            "embedding", "embeddings", "mô hình embedding", "embedding model",
            "sentence-transformers", "sentence transformers", "all-minilm",
            "chromadb", "chroma", "vector database", "vector db",
            "cơ sở dữ liệu vector", "mô hình", "model", "models",
            "dimension", "dimensions", "384"
        ]
    )
    
    if has_technical_keyword and has_stillme_context:
        matched_keywords.append("technical")
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
    
    # Also check for technical keywords (even without explicit StillMe context)
    # If query is about embedding/model/database, it's likely about StillMe
    if has_technical_keyword:
        matched_keywords.append("technical")
        return (True, matched_keywords)
    
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
    query_lower = query.lower()
    variants = [
        query,  # Original query
        "StillMe Learning AI system RAG foundation learning",
        "StillMe continuous learning RSS arXiv",
        "StillMe transparency RAG knowledge base",
        "StillMe how it learns updates knowledge",
    ]
    
    # Add technical variants if query is about embedding/model/database
    if any(keyword in query_lower for keyword in ["embedding", "model", "mô hình", "chromadb", "vector"]):
        variants.extend([
            "StillMe embedding model multi-qa-MiniLM-L6-dot-v1 ChromaDB",
            "StillMe sentence-transformers multi-qa-MiniLM-L6-dot-v1 384 dimensions",
            "StillMe vector database ChromaDB embedding model",
            "StillMe RAG embedding model technical architecture",
        ])
    
    # Add language-specific variants
    if any(keyword in query_lower for keyword in ["học", "học tập", "gì", "như thế nào"]):
        variants.extend([
            "StillMe hệ thống AI tự tiến hóa RAG",
            "StillMe học tập liên tục RSS",
            "StillMe cập nhật tri thức hàng ngày",
        ])
    
    # Add Vietnamese technical variants
    if any(keyword in query_lower for keyword in ["mô hình", "embedding", "cơ sở dữ liệu"]):
        variants.extend([
            "StillMe mô hình embedding multi-qa-MiniLM-L6-dot-v1 ChromaDB",
            "StillMe cơ sở dữ liệu vector ChromaDB",
            "StillMe kiến trúc kỹ thuật embedding model",
        ])
    
    return variants


# Keywords that indicate origin/founder queries (Vietnamese and English)
ORIGIN_KEYWORDS = {
    # Origin-related (English)
    "origin", "origins", "who created", "who built", "who made", "who developed",
    "creator", "founder", "founders", "author", "authors", "created by",
    "built by", "made by", "developed by", "who is behind", "who stands behind",
    "about stillme", "stillme history", "stillme story", "stillme background",
    
    # Origin-related (Vietnamese)
    "nguồn gốc", "xuất xứ", "ai tạo ra", "ai xây dựng", "ai làm ra", "ai phát triển",
    "người tạo ra", "người sáng lập", "tác giả", "ai đứng sau", "ai đã tạo",
    "về stillme", "lịch sử stillme", "câu chuyện stillme", "background stillme",
    "người sáng lập là ai", "ai là người sáng lập", "người tạo ra stillme",
    "ai là người", "ai đã tạo ra bạn", "ai tạo ra bạn", "ai làm ra bạn",
    "người nào tạo ra", "ai đã làm ra", "ai đã xây dựng",
    
    # About-related
    "about", "về", "giới thiệu", "introduction", "overview",
    
    # History-related
    "history", "lịch sử", "story", "câu chuyện", "background", "nền tảng"
}


def detect_origin_query(query: str) -> Tuple[bool, List[str]]:
    """
    Detect if query is about StillMe's origin/founder.
    CRITICAL: This is used to determine if provenance knowledge should be retrieved.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (is_origin_query, matched_keywords)
    """
    query_lower = query.lower()
    matched_keywords = []
    
    # Check for explicit origin/founder keywords
    for keyword in ORIGIN_KEYWORDS:
        if keyword in query_lower:
            matched_keywords.append(keyword)
            return (True, matched_keywords)
    
    # Check for pattern: "who" + "created/built/made" + "stillme"
    if re.search(r'\bwho\b.*\b(created|built|made|developed|founded)\b.*\bstillme\b', query_lower):
        matched_keywords.append("who_created_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "ai" + "tạo ra/xây dựng" + "stillme" (Vietnamese)
    if re.search(r'\bai\b.*\b(tạo ra|xây dựng|làm ra|phát triển|sáng lập)\b.*\bstillme\b', query_lower):
        matched_keywords.append("ai_tao_ra_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "ai là người" + "đã tạo ra/tạo ra" + "bạn" (Vietnamese)
    if re.search(r'\bai\s+là\s+người\b.*\b(đã\s+)?(tạo ra|làm ra|xây dựng|phát triển|sáng lập)\b.*\b(bạn|stillme)\b', query_lower):
        matched_keywords.append("ai_la_nguoi_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "ai" + "đã tạo ra/tạo ra" + "bạn" (Vietnamese)
    # Enhanced to match simpler patterns like "ai tạo ra bạn?"
    if re.search(r'\bai\b.*\b(đã\s+)?(tạo ra|làm ra|xây dựng|phát triển)\b.*\b(bạn|stillme)\b', query_lower):
        matched_keywords.append("ai_tao_ra_ban_pattern")
        return (True, matched_keywords)
    
    # Check for simpler pattern: "ai" + "tạo ra" + "bạn" (without "đã")
    if re.search(r'\bai\b.*\btạo\s+ra\b.*\bbạn\b', query_lower):
        matched_keywords.append("ai_tao_ra_ban_simple")
        return (True, matched_keywords)
    
    # Check for pattern: "người sáng lập" / "founder"
    if re.search(r'\b(người sáng lập|founder|tác giả|author|creator)\b', query_lower):
        matched_keywords.append("founder_keyword")
        return (True, matched_keywords)
    
    # Check for "about StillMe" pattern
    if re.search(r'\b(about|về|giới thiệu)\b.*\bstillme\b', query_lower):
        matched_keywords.append("about_stillme")
        return (True, matched_keywords)
    
    return (False, [])

