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
    
    # CRITICAL: Check if question is about "your system" or "in your system"
    # These are definitely about StillMe even without explicit StillMe name
    has_your_system = any(
        phrase in query_lower 
        for phrase in [
            "your system", "in your system", "your.*system", "system.*you",
            "bạn.*hệ thống", "hệ thống.*bạn", "của bạn", "bạn.*sử dụng"
        ]
    )
    
    # If question has technical keywords AND "your system", it's definitely about StillMe
    for keyword in technical_keywords:
        if keyword in query_lower:
            if has_your_system:
                matched_keywords.append("technical_your_system")
                return (True, matched_keywords)
            matched_keywords.append("technical")
            return (True, matched_keywords)
    
    # Check for StillMe name
    if re.search(r'\bstillme\b|\bstill\s*me\b|\bstill-me\b', query_lower):
        matched_keywords.append("stillme_name")
        return (True, matched_keywords)
    
    # Check for keyword combinations
    # Pattern 1: "StillMe" + learning/system keywords
    # CRITICAL: "your system" or "in your system" should be treated as StillMe context
    has_stillme_context = any(
        keyword in query_lower 
        for keyword in ["stillme", "still me", "still-me", "bạn", "you", "it", "your", "của bạn"]
    ) or any(
        phrase in query_lower 
        for phrase in ["your system", "in your system", "your.*system", "system.*you"]
    )
    
    has_learning_keyword = any(
        keyword in query_lower 
        for keyword in [
            "học", "learn", "learning", "học tập", "học hỏi", "tự học", 
            "học như thế nào", "how do you learn", "how does.*learn", "cách học",
            "học được gì", "hoc duoc gi", "what did you learn", "what have you learned",
            "hôm nay bạn học", "hom nay ban hoc", "today you learn", "what you learned today",
            "lý do vì sao lại học", "ly do vi sao lai hoc", "why do you learn", "why learn",
            "vì sao lại bỏ bài học", "vi sao lai bo bai hoc", "why skip", "why filter",
            "bỏ bài học", "bo bai hoc", "skip", "filter", "bỏ qua", "bo qua",
            "nguồn học", "nguon hoc", "learning source", "source of learning",
            "nguồn học nào bị lỗi", "nguon hoc nao bi loi", "which source failed", "source error",
            "lý do lỗi", "ly do loi", "reason for error", "why error", "why failed"
        ]
    )
    
    has_system_keyword = any(
        keyword in query_lower 
        for keyword in [
            "hệ thống", "system", "hoạt động", "vận hành", "work", "cách", "how", 
            "như thế nào", "how does", "how do", "how work", "how function",
            "mechanisms", "wie funktioniert", "fonctionne", "comment fonctionne",
            "cómo funciona", "如何工作", "どのように機能", "mechanism", "cơ chế",
            "triết lý hoạt động", "triet ly hoat dong", "operating philosophy", "philosophy of operation",
            "mục tiêu phát triển", "muc tieu phat trien", "development goal", "development target",
            "mục tiêu kế tiếp", "muc tieu ke tiep", "next goal", "next target", "future goal"
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
    # CRITICAL: Also detect questions about learning activity, philosophy, goals, errors
    # These are ALWAYS about StillMe even without "bạn"/"you"
    if has_learning_keyword and any(
        keyword in query_lower 
        for keyword in ["bạn", "you", "your", "như thế nào", "how", "cách", "hôm nay", "hom nay", "today", "ngày hôm nay", "ngay hom nay"]
    ):
        matched_keywords.append("learning_direct")
        return (True, matched_keywords)
    
    # Pattern 3c: Questions about StillMe's philosophy, goals, errors (self-knowledge)
    # These are ALWAYS about StillMe, even without explicit "bạn"/"you"
    # Examples: "triết lý hoạt động của bạn", "mục tiêu phát triển", "nguồn học nào bị lỗi"
    has_philosophy_goal_keyword = any(
        keyword in query_lower 
        for keyword in [
            "triết lý", "triet ly", "philosophy", "philosophy of operation",
            "mục tiêu", "muc tieu", "goal", "target", "development goal",
            "phát triển", "phat trien", "development", "next goal",
            "nguồn học", "nguon hoc", "learning source", "source",
            "bị lỗi", "bi loi", "failed", "error", "lỗi", "loi", "why error", "why failed",
            "lý do", "ly do", "reason", "why"
        ]
    )
    
    # If question has philosophy/goal/error keywords AND learning/system keywords, it's about StillMe
    if has_philosophy_goal_keyword and (has_learning_keyword or has_system_keyword):
        if has_philosophy_goal_keyword:
            matched_keywords.append("philosophy_goal_error")
        return (True, matched_keywords)
    
    # Pattern 3c-2: Questions about "why skip/filter" learning - ALWAYS about StillMe
    # "vi sao lai bo bai hoc", "why skip learning", "why filter"
    if has_learning_keyword and any(
        pattern in query_lower 
        for pattern in ["vi sao lai bo", "why skip", "why filter", "vi sao bo", "why do you skip", "why do you filter"]
    ):
        matched_keywords.append("why_skip_filter")
        return (True, matched_keywords)
    
    # Pattern 3d: Questions about "hôm nay bạn học được gì" / "what did you learn today"
    # These are ALWAYS about StillMe's learning activity
    if any(
        pattern in query_lower 
        for pattern in [
            "hôm nay bạn học", "hom nay ban hoc", "today you learn", "what did you learn today",
            "học được gì", "hoc duoc gi", "learned what", "what learned",
            "ngày hôm nay", "ngay hom nay", "today"
        ]
    ) and has_learning_keyword:
        matched_keywords.append("learning_activity_today")
        return (True, matched_keywords)
    
    # Pattern 3d: CRITICAL - Questions about StillMe's capabilities/philosophy with "bạn có thể"
    # "Bạn có thể có X mà không có Y không?" - These are about StillMe's nature/capabilities
    # Examples: "Bạn có thể có embodied cognition mà không có enactive cognition không?"
    if re.search(r'\b(bạn|you)\s+có\s+thể\b', query_lower):
        # If question asks "can you have X without Y", it's about StillMe's capabilities
        if re.search(r'\b(có|have)\s+\w+\s+mà\s+không\s+(có|have)\b', query_lower) or \
           re.search(r'\b(có|have)\s+\w+.*\bwithout\b', query_lower):
            matched_keywords.append("capability_paradox")
            return (True, matched_keywords)
        # Also catch "bạn có thể" + philosophical/cognitive terms
        philosophical_terms = [
            "cognition", "nhận thức", "consciousness", "ý thức", "mind", "tâm trí",
            "free will", "ý chí tự do", "determinism", "thuyết quyết định",
            "embodied", "nhập thể", "enactive", "hành động",
            "predictive", "dự đoán", "inference", "suy luận",
            "integration", "tích hợp", "phenomenal", "hiện tượng",
            "higher-order", "bậc cao", "thought", "tư duy", "perception", "nhận thức"
        ]
        if any(term in query_lower for term in philosophical_terms):
            matched_keywords.append("philosophical_capability")
            return (True, matched_keywords)
    
    # Pattern 3e: CRITICAL - Simple questions about StillMe with "bạn có X ko?" or "do you have X?"
    # "Bạn có ý thức ko?" / "Do you have consciousness?" - These are about StillMe's nature
    # This pattern catches direct questions about StillMe's attributes/capabilities
    if re.search(r'\b(bạn|you)\s+có\b', query_lower) or re.search(r'\bdo\s+you\s+have\b', query_lower):
        philosophical_terms = [
            "cognition", "nhận thức", "consciousness", "ý thức", "mind", "tâm trí",
            "free will", "ý chí tự do", "determinism", "thuyết quyết định",
            "embodied", "nhập thể", "enactive", "hành động",
            "predictive", "dự đoán", "inference", "suy luận",
            "integration", "tích hợp", "phenomenal", "hiện tượng",
            "higher-order", "bậc cao", "thought", "tư duy", "perception", "nhận thức",
            "experience", "trải nghiệm", "feeling", "cảm giác", "emotion", "cảm xúc",
            "awareness", "nhận biết", "self-awareness", "tự nhận thức"
        ]
        if any(term in query_lower for term in philosophical_terms):
            matched_keywords.append("philosophical_attribute")
            return (True, matched_keywords)
    
    # Pattern 3f: CRITICAL - Questions about StillMe's wishes, desires, preferences
    # "Nếu có thể ước thì bạn sẽ ước điều gì?" / "If you could wish, what would you wish for?"
    # "Bạn muốn gì?" / "What do you want?"
    # These are about StillMe's nature (it cannot have wishes/desires)
    wish_desire_patterns = [
        r'\b(bạn|you)\s+(sẽ|would|will)\s+(ước|wish)',
        r'\b(bạn|you)\s+(muốn|want|desire)',
        r'\b(bạn|you)\s+(thích|like|prefer)',
        r'\b(bạn|you)\s+(hy\s+vọng|hope)',
        r'\b(bạn|you)\s+(mong\s+muốn|aspire)',
        r'\bif\s+(you|bạn)\s+could\s+(wish|ước)',
        r'\bnếu\s+(bạn|you)\s+(có\s+thể\s+ước|could\s+wish)',
        r'\bwhat\s+(do|would|will)\s+(you|bạn)\s+(wish|want|desire|like|prefer)',
        r'\b(bạn|you)\s+(có\s+ước\s+muốn|have\s+wish|have\s+desire)',
    ]
    if any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in wish_desire_patterns):
        matched_keywords.append("wish_desire_preference")
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
            "StillMe embedding model paraphrase-multilingual-MiniLM-L12-v2 ChromaDB",
            "StillMe sentence-transformers paraphrase-multilingual-MiniLM-L12-v2 384 dimensions",
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
            "StillMe mô hình embedding paraphrase-multilingual-MiniLM-L12-v2 ChromaDB",
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
    "what are you", "what is stillme", "what is your purpose", "why were you created",
    "what is your mission", "what is your goal", "what are your goals",
    
    # Origin-related (Vietnamese - with diacritics)
    "nguồn gốc", "xuất xứ", "ai tạo ra", "ai xây dựng", "ai làm ra", "ai phát triển",
    "người tạo ra", "người sáng lập", "tác giả", "ai đứng sau", "ai đã tạo",
    "về stillme", "lịch sử stillme", "câu chuyện stillme", "background stillme",
    "người sáng lập là ai", "ai là người sáng lập", "người tạo ra stillme",
    "ai là người", "ai đã tạo ra bạn", "ai tạo ra bạn", "ai làm ra bạn",
    "người nào tạo ra", "ai đã làm ra", "ai đã xây dựng",
    "bạn là gì", "stillme là gì", "mục tiêu của bạn", "bạn ra đời để làm gì",
    "bạn được tạo ra để làm gì", "mục đích của bạn", "nhiệm vụ của bạn",
    "bạn được tạo ra như thế nào", "bạn được xây dựng như thế nào",
    
    # Origin-related (Vietnamese - without diacritics for robustness)
    "nguon goc", "xuat xu", "ai tao ra", "ai xay dung", "ai lam ra", "ai phat trien",
    "nguoi tao ra", "nguoi sang lap", "tac gia", "ai dung sau", "ai da tao",
    "ve stillme", "lich su stillme", "cau chuyen stillme",
    "nguoi sang lap la ai", "ai la nguoi sang lap", "nguoi tao ra stillme",
    "ai la nguoi", "ai da tao ra ban", "ai tao ra ban", "ai lam ra ban",
    "nguoi nao tao ra", "ai da lam ra", "ai da xay dung",
    "ban la gi", "stillme la gi", "muc tieu cua ban", "ban ra doi de lam gi",
    "ban duoc tao ra de lam gi", "muc dich cua ban", "nhiem vu cua ban",
    "ban duoc tao ra nhu the nao", "ban duoc xay dung nhu the nao",
    
    # About-related (only when combined with StillMe)
    "about stillme", "ve stillme", "gioi thieu stillme", "introduction stillme",
    
    # History-related (only when combined with StillMe)
    "stillme history", "lich su stillme", "stillme story", "cau chuyen stillme",
    "stillme background", "background stillme"
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
    
    # CRITICAL: Check for StillMe-specific patterns FIRST (most specific)
    # These patterns are ALWAYS origin queries
    stillme_specific_patterns = [
        r'\bstillme\s+(history|story|background|lịch sử|câu chuyện|nền tảng)\b',
        r'\b(about|về|giới thiệu)\s+stillme\b',
        r'\bwho\s+(created|built|made|developed|founded)\s+stillme\b',
        r'\bai\s+(tạo ra|xây dựng|làm ra|phát triển|sáng lập)\s+stillme\b',
    ]
    for pattern in stillme_specific_patterns:
        if re.search(pattern, query_lower):
            matched_keywords.append(f"stillme_specific_{pattern}")
            return (True, matched_keywords)
    
    # Check for explicit origin/founder keywords (excluding generic "about", "history", etc.)
    # These keywords are ONLY origin queries when they appear alone or with "you"/"bạn"
    strong_origin_keywords = [
        "who created", "who built", "who made", "who developed", "who is behind",
        "creator", "founder", "founders", "author", "authors", "created by",
        "built by", "made by", "developed by",
        "ai tạo ra", "ai xây dựng", "ai làm ra", "ai phát triển",
        "người tạo ra", "người sáng lập", "tác giả", "ai đứng sau",
        "ai tao ra", "ai xay dung", "ai lam ra", "ai phat trien",
        "nguoi tao ra", "nguoi sang lap", "tac gia", "ai dung sau",
        "what is your purpose", "why were you created", "what is your mission",
        "mục tiêu của bạn", "bạn ra đời", "muc tieu cua ban", "ban ra doi",
        "mục đích của bạn", "muc dich cua ban", "nhiệm vụ của bạn", "nhiem vu cua ban",
    ]
    for keyword in strong_origin_keywords:
        if keyword in query_lower:
            matched_keywords.append(keyword)
            return (True, matched_keywords)
    
    # Check for pattern: "who" + "created/built/made" + "you"/"bạn"
    if re.search(r'\bwho\b.*\b(created|built|made|developed|founded)\b.*\b(you|stillme)\b', query_lower):
        matched_keywords.append("who_created_you_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "ai" + "tạo ra/xây dựng" + "bạn" (Vietnamese)
    if re.search(r'\bai\b.*\b(tạo ra|xây dựng|làm ra|phát triển|sáng lập|tao ra|xay dung|lam ra|phat trien|sang lap)\b.*\b(bạn|ban|stillme)\b', query_lower):
        matched_keywords.append("ai_tao_ra_ban_pattern")
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
    if re.search(r'\b(about|về|giới thiệu|ve|gioi thieu)\b.*\bstillme\b', query_lower):
        matched_keywords.append("about_stillme")
        return (True, matched_keywords)
    
    # Check for "StillMe là gì" / "StillMe la gi" pattern
    if re.search(r'\bstillme\s+(là|la)\s+(gì|gi)\b', query_lower):
        matched_keywords.append("stillme_la_gi")
        return (True, matched_keywords)
    
    # Check for "bạn là gì" / "ban la gi" pattern (when asking about StillMe)
    if re.search(r'\b(bạn|ban)\s+(là|la)\s+(gì|gi)\b', query_lower):
        matched_keywords.append("ban_la_gi")
        return (True, matched_keywords)
    
    return (False, [])

