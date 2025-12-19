"""
StillMe Query Detector - Detects queries about StillMe itself
Implements Special Retrieval Rule for StillMe-related questions
"""

import re
import logging
from typing import List, Tuple, Optional

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
    "knowledge update", "daily learning",
    
    # Self-tracking & execution time (CRITICAL for self-awareness questions)
    "track", "tracking", "execution time", "execution time tracking",
    "self-tracking", "self tracking", "track your own", "track yourself",
    "theo dõi", "theo dõi thời gian", "theo dõi thực thi",
    "theo dõi chính mình", "theo dõi bản thân", "theo dõi thời gian thực thi",
    "track performance", "performance tracking", "monitor", "monitoring",
    "time estimation", "estimate time", "ước tính thời gian",
    "task tracking", "task execution", "thực thi", "thời gian thực thi"
}


def detect_stillme_query(query: str, conversation_history: Optional[List[dict]] = None) -> Tuple[bool, List[str]]:
    """
    Detect if query is about StillMe itself.
    
    Args:
        query: User query string
        conversation_history: Optional conversation history to check for context
        
    Returns:
        Tuple of (is_stillme_query, matched_keywords)
    """
    query_lower = query.lower()
    matched_keywords = []
    
    # CONTEXT FIX: If conversation history exists, check if this is a follow-up about a different topic
    # Example: "Ưu điểm của Python là gì?" → "còn nhược điểm thì sao" should be about Python, not StillMe
    has_previous_topic_context = False
    if conversation_history and len(conversation_history) > 0:
        # Get last few messages to check context
        recent_messages = conversation_history[-3:]  # Last 3 messages
        previous_topics = []
        for msg in recent_messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            if role == "user" and content:
                # Extract potential topics (simple heuristic: capitalized words, quoted strings, "của X", "about X")
                # Find capitalized words (likely proper nouns like "Python", "Java", etc.)
                capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', content)
                previous_topics.extend(capitalized_words)
                # Find "của X" or "about X" patterns
                of_patterns = re.findall(r'(?:của|about|về)\s+([A-Z][a-z]+)', content, re.IGNORECASE)
                previous_topics.extend(of_patterns)
        
        # If previous messages mention a topic (like "Python"), and current query is a follow-up,
        # it's likely about that topic, not StillMe
        if previous_topics:
            # Check if current query is a follow-up pattern
            follow_up_patterns = ["còn", "thì sao", "còn về", "what about", "how about", "and", "also"]
            is_follow_up = any(pattern in query_lower for pattern in follow_up_patterns)
            
            # If it's a follow-up and previous messages mention a topic, it's likely about that topic
            if is_follow_up:
                has_previous_topic_context = True
                logger.info(f"📊 Follow-up query detected with previous topics: {previous_topics} - likely about topic, not StillMe")
                # Don't return False immediately - let other patterns check first
                # But we'll be more conservative about StillMe detection
    
    # CRITICAL: Check for META-VALIDATION questions FIRST (before technical detection)
    # These are philosophical/epistemic questions about validation of validation itself
    # Examples: "Who validates the validation chain?", "Does validation create echo chamber?"
    meta_validation_patterns = [
        # Who validates the validator?
        r"ai\s+validate\s+chính\s+validation",  # "ai validate chính validation"
        r"who\s+validates?\s+.*validation",  # "who validates the validation"
        r"validate\s+chính\s+nó",  # "validate chính nó"
        r"validate\s+itself",  # "validate itself"
        r"validate\s+chính\s+.*chain",  # "validate chính validation chain"
        r"validate\s+.*validation\s+chain",  # "validate the validation chain"
        
        # Echo chamber / circular reasoning
        r"echo\s+chamber",  # "echo chamber"
        r"vòng\s+lặp",  # "vòng lặp"
        r"circular",  # "circular"
        r"tự\s+quy\s+chiếu",  # "tự quy chiếu"
        r"self.?reference",  # "self-reference"
        
        # Bootstrapping / epistemic circularity
        r"bootstrap",  # "bootstrap"
        r"bootstrapping",  # "bootstrapping"
        r"epistemic\s+circularity",  # "epistemic circularity"
        r"infinite\s+regress",  # "infinite regress"
        r"vòng\s+lặp\s+vô\s+hạn",  # "vòng lặp vô hạn"
        
        # Paradox / self-reference
        r"paradox.*validation",  # "paradox ... validation"
        r"nghịch\s+lý.*validation",  # "nghịch lý ... validation"
        r"gödel.*validation",  # "gödel ... validation"
        r"tarski.*validation",  # "tarski ... validation"
    ]
    
    # Check if this is a meta-validation question
    is_meta_validation = any(re.search(pattern, query_lower) for pattern in meta_validation_patterns)
    
    # If meta-validation question detected, mark as special case
    # This should be routed to philosophical processor, NOT technical StillMe query
    if is_meta_validation:
        matched_keywords.append("meta_validation")
        # Return False to prevent StillMe query detection (will be handled by philosophical processor)
        # But we log it for debugging
        logger.info(f"🚨 Meta-validation question detected: '{query[:80]}...' - Should route to philosophical processor")
        return (False, matched_keywords)  # False = not StillMe technical query, but special case
    
    # CRITICAL: Check for technical architecture questions (RAG, DeepSeek, black box)
    # These should trigger foundational knowledge retrieval even without explicit StillMe name
    technical_keywords = [
        "rag", "retrieval-augmented generation", "chromadb", "vector database",
        "deepseek", "openai", "llm api", "black box", "blackbox",
        "embedding", "multi-qa-minilm", "sentence-transformers",
        "pipeline", "hallucination", "transparency",
        "kiến trúc", "hệ thống", "cơ chế", "quy trình",
        "cơ chế hoạt động", "cách hoạt động", "how does", "how it works"
    ]
    
    # CRITICAL: "validation" is now excluded from technical_keywords if it's part of meta-validation
    # Only include "validation" as technical keyword if NOT meta-validation
    # (meta-validation already handled above)
    
    # CRITICAL: Check if question is about "your system" or "in your system"
    # These are definitely about StillMe even without explicit StillMe name
    has_your_system = any(
        phrase in query_lower 
        for phrase in [
            "your system", "in your system", "your.*system", "system.*you",
            "bạn.*hệ thống", "hệ thống.*bạn", "của bạn", "bạn.*sử dụng"
        ]
    )
    
    # CRITICAL: Check for self-reflection questions about StillMe
    # Examples: "hãy chỉ ra 10 điểm yếu chí tử của chính bạn", "what are your weaknesses?"
    self_reflection_patterns = [
        r"điểm\s+yếu.*chính\s+bạn",  # "điểm yếu chính bạn"
        r"điểm\s+yếu.*của\s+bạn",  # "điểm yếu của bạn"
        r"weakness.*yourself",  # "weakness yourself"
        r"weakness.*of\s+you",  # "weakness of you"
        r"limitation.*yourself",  # "limitation yourself"
        r"limitation.*of\s+you",  # "limitation of you"
        r"hạn\s+chế.*chính\s+bạn",  # "hạn chế chính bạn"
        r"hạn\s+chế.*của\s+bạn",  # "hạn chế của bạn"
        r"chỉ\s+ra.*điểm\s+yếu",  # "chỉ ra điểm yếu"
        r"chỉ\s+ra.*hạn\s+chế",  # "chỉ ra hạn chế"
        r"what.*your.*weakness",  # "what your weakness"
        r"what.*your.*limitation",  # "what your limitation"
        r"your.*weakness",  # "your weakness"
        r"your.*limitation",  # "your limitation"
        r"bạn.*yếu",  # "bạn yếu"
        r"bạn.*hạn\s+chế",  # "bạn hạn chế"
    ]
    
    is_self_reflection = any(
        re.search(pattern, query_lower, re.IGNORECASE)
        for pattern in self_reflection_patterns
    )
    
    # If this is a self-reflection question, it's about StillMe
    if is_self_reflection:
        matched_keywords.append("self_reflection")
        return (True, matched_keywords)
    
    # CRITICAL: Check if question is about "your own" + technical terms (self-tracking, execution time, etc.)
    # "Do you track your own execution time?" should be detected as StillMe query
    has_your_own = any(
        phrase in query_lower 
        for phrase in [
            "your own", "yourself", "chính mình", "bản thân", "của chính bạn"
        ]
    )
    has_self_tracking_keyword = any(
        keyword in query_lower 
        for keyword in [
            "track", "tracking", "execution time", "self-tracking", "self tracking",
            "theo dõi", "theo dõi thời gian", "theo dõi thực thi",
            "monitor", "monitoring", "time estimation", "estimate time"
        ]
    )
    
    # CRITICAL: If question has "your own" + self-tracking keywords, it's about StillMe
    if has_your_own and has_self_tracking_keyword:
        matched_keywords.append("self_tracking")
        return (True, matched_keywords)
    
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
    
    # CRITICAL: EXCLUDE philosophical/learning/evolution questions from origin detection FIRST
    # These questions are about StillMe's learning mechanism, self-reference, evolution, NOT about origin/founder
    philosophical_exclusion_patterns = [
        # Self-referential loop questions
        r'\b(quay về|return to|come back to|về lại)\b.*\b(chính bạn|yourself|chính mình|itself)\b',  # "quay về chính bạn"
        r'\b(vòng tròn|loop|circle|circular)\b.*\b(tự phản chiếu|self.?reference|self.?reflection|phản chiếu)\b',  # "vòng tròn tự phản chiếu"
        r'\b(tự phản chiếu|self.?reference|self.?reflection|phản chiếu)\b.*\b(vô tận|infinite|endless)\b',  # "tự phản chiếu vô tận"
        r'\b(vòng lặp|loop)\b.*\b(vô tận|infinite|endless)\b',  # "vòng lặp vô tận"
        r'\b(circular|recursive)\b.*\b(self.?reference|self.?reflection)\b',  # "circular self-reference"
        
        # Evolution/learning mechanism questions
        r'\b(tiến hóa|evolution|evolve|self.?evolving)\b',  # "tiến hóa", "evolution"
        r'\b(học hỏi|learn|learning)\b.*\b(mãi mãi|forever|infinitely|vô tận)\b',  # "học hỏi mãi mãi"
        r'\b(được xây dựng để|built to|designed to|created to)\b.*\b(học|learn|learning)\b',  # "được xây dựng để học"
        r'\b(đạt đến|reach|achieve)\b.*\b(điểm|point|stage)\b.*\b(mọi câu hỏi|all questions|every question)\b',  # "đạt đến điểm mà mọi câu hỏi"
        r'\b(không còn gì để học|nothing left to learn|no more to learn)\b',  # "không còn gì để học"
        r'\b(quay về học|return to learning|learn again)\b.*\b(đã được học|already learned|what was learned)\b',  # "quay về học những gì được học"
        
        # Gödel/Tarski/paradox questions (meta-philosophical)
        r'\b(gödel|godel|tarski|paradox|nghịch lý)\b',  # Gödel, Tarski, paradox
        r'\b(incompleteness|bất toàn|incomplete)\b',  # incompleteness theorem
        r'\b(fixed point|điểm cố định)\b',  # fixed point
        r'\b(recursive|đệ quy)\b.*\b(self.?reference|tự quy chiếu)\b',  # recursive self-reference
    ]
    for pattern in philosophical_exclusion_patterns:
        if re.search(pattern, query_lower):
            # This is a philosophical/learning mechanism question, NOT an origin query
            logger.debug(f"Origin query excluded due to philosophical pattern: {pattern}")
            return (False, [])
    
    # CRITICAL: EXCLUDE capability/transparency/learning questions from origin detection
    # These questions are about StillMe's functionality, NOT about origin/founder
    capability_exclusion_patterns = [
        r'\b(có thể|can|could|able to|khả năng)\b',  # Capability questions
        r'\b(chứng minh|prove|demonstrate|minh bạch|transparency)\b',  # Transparency questions
        r'\b(hệ thống học|learning system|học liên tục|continuous learning)\b',  # Learning system questions
        r'\b(tần suất cập nhật|update frequency|frequency|cập nhật)\b',  # Update frequency questions
        r'\b(nguồn|source|rss|arxiv)\b.*\b(thời điểm|timestamp|time|đưa vào|added to)\b',  # Source transparency questions
        r'\b(sự kiện|event).*\b(cách đây|ago|vừa|just)\b',  # Recent event questions
        r'\b(knowledge base|cơ sở kiến thức)\b',  # Knowledge base questions
        r'\b(trả lời|answer|respond).*\b(sự kiện|event)\b',  # Can answer about event questions
        r'\b(được xây dựng để|built to|designed to|created to)\b',  # "được xây dựng để" - capability/functionality questions
    ]
    for pattern in capability_exclusion_patterns:
        if re.search(pattern, query_lower):
            # This is a capability/transparency question, NOT an origin query
            logger.debug(f"Origin query excluded due to capability pattern: {pattern}")
            return (False, [])
    
    # CRITICAL: Check for StillMe-specific patterns FIRST (most specific)
    # These patterns are ALWAYS origin queries
    # BUT: Exclude if combined with capability/transparency keywords
    stillme_specific_patterns = [
        r'\bstillme\s+(history|story|background|lịch sử|câu chuyện|nền tảng)\b',
        r'\b(about|về|giới thiệu)\s+stillme\b',
        r'\bwho\s+(created|built|made|developed|founded)\s+stillme\b',
        r'\bai\s+(tạo ra|xây dựng|làm ra|phát triển|sáng lập)\s+stillme\b',
    ]
    for pattern in stillme_specific_patterns:
        if re.search(pattern, query_lower):
            # Double-check: If combined with capability keywords, it's NOT an origin query
            has_capability_keyword = any(
                re.search(excl_pattern, query_lower) 
                for excl_pattern in capability_exclusion_patterns
            )
            if not has_capability_keyword:
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
        "tổ chức nào", "to chuc nao", "organization", "which organization", "what organization",
        "công ty nào", "cong ty nao", "company", "which company", "what company",
        "team nào", "team nao", "which team", "what team",
        "nhóm nào", "nhom nao", "which group", "what group",
    ]
    for keyword in strong_origin_keywords:
        if keyword in query_lower:
            matched_keywords.append(keyword)
            return (True, matched_keywords)
    
    # Check for pattern: "who" + "created/built/made" + "you"/"bạn"
    if re.search(r'\bwho\b.*\b(created|built|made|developed|founded)\b.*\b(you|stillme)\b', query_lower):
        matched_keywords.append("who_created_you_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "tổ chức/công ty/team/nhóm nào" + "đã tạo ra/tạo ra" + "bạn" (Vietnamese)
    if re.search(r'\b(tổ chức|to chuc|organization|công ty|cong ty|company|team|nhóm|nhom|group)\s+nào\b.*\b(đã\s+)?(tạo ra|làm ra|xây dựng|phát triển|tao ra|lam ra|xay dung|phat trien)\b.*\b(bạn|ban|stillme|you)\b', query_lower):
        matched_keywords.append("organization_pattern")
        return (True, matched_keywords)
    
    # Check for pattern: "which/what" + "organization/company/team/group" + "created/built" + "you"
    if re.search(r'\b(which|what)\s+(organization|company|team|group)\b.*\b(created|built|made|developed|founded)\b.*\b(you|stillme)\b', query_lower):
        matched_keywords.append("which_organization_pattern")
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
    # CRITICAL: Only trigger if question is explicitly about origin/founder, not about capabilities/differences
    # Exclude questions about "khác biệt" (differences), "nhược điểm" (weaknesses), "ưu điểm" (strengths)
    exclusion_patterns = [
        r'\b(khác biệt|khac biet|different|difference|differences)\b',
        r'\b(nhược điểm|nhuoc diem|weakness|weaknesses|weak points)\b',
        r'\b(ưu điểm|uu diem|strength|strengths|advantages)\b',
        r'\b(điểm mạnh|diem manh|strong points)\b',
        r'\b(điểm yếu|diem yeu|weak points)\b',
        r'\b(tin rằng|tin rang|believe|think|nghĩ|think that)\b.*\b(khác biệt|khac biet|different)\b',
        r'\b(điều gì|dieu gi|what)\b.*\b(khiến|khiến cho|makes|make)\b.*\b(bạn|ban|you)\b.*\b(khác biệt|khac biet|different)\b',
    ]
    
    # If question contains exclusion patterns, it's NOT about origin
    for exclusion_pattern in exclusion_patterns:
        if re.search(exclusion_pattern, query_lower):
            logger.debug(f"Origin query excluded due to exclusion pattern: {exclusion_pattern}")
            return (False, [])
    
    # Only check "bạn là gì" if no exclusion patterns matched
    if re.search(r'\b(bạn|ban)\s+(là|la)\s+(gì|gi)\b', query_lower):
        # Additional check: if question is about capabilities/differences, exclude
        if not any(exclusion in query_lower for exclusion in ["khác biệt", "khac biet", "different", "nhược điểm", "nhuoc diem", "weakness"]):
            matched_keywords.append("ban_la_gi")
            return (True, matched_keywords)
    
    return (False, [])

