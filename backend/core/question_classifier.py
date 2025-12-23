"""
Question Classifier - Detects if a question is philosophical
"""

import logging
import re

logger = logging.getLogger(__name__)


def is_philosophical_question(text: str, use_semantic: bool = True) -> bool:
    """
    Detect if a question is philosophical using semantic similarity (primary) and keywords (fallback).
    
    Uses a hybrid approach:
    1. Semantic detection: Compare question with philosophical examples using embedding similarity (language-agnostic)
    2. Keyword fallback: If semantic detection unavailable or low confidence, use keyword patterns
    
    Args:
        text: The question text (any language StillMe supports)
        use_semantic: Whether to use semantic detection (default: True)
        
    Returns:
        True if the question is philosophical, False otherwise
    """
    if not text:
        logger.info("Philosophical question detected: False (empty text)")
        return False
    
    # PRIORITY: Try semantic detection first (language-agnostic, scalable)
    if use_semantic:
        try:
            from backend.core.philosophical_detector_semantic import get_semantic_philosophical_detector
            semantic_detector = get_semantic_philosophical_detector(similarity_threshold=0.65)
            is_phil, similarity, matched = semantic_detector.detect(text)
            
            if is_phil:
                logger.info(
                    f"✅ Semantic philosophical detection: True (similarity={similarity:.3f}, "
                    f"matched='{matched[:60] if matched else 'N/A'}...')"
                )
                return True
            elif similarity > 0.5:  # Medium confidence - log but continue to keyword check
                logger.debug(
                    f"Semantic detection: medium confidence (similarity={similarity:.3f}), "
                    f"falling back to keyword detection"
                )
            # If similarity < 0.5, semantic detector is confident it's NOT philosophical
            # But we still check keywords as fallback for edge cases
        except Exception as e:
            logger.debug(f"Semantic detection unavailable ({e}), using keyword fallback")
    
    # FALLBACK: Keyword-based detection (for edge cases or when semantic unavailable)
    lower = text.lower()
    
    # PRIORITY CHECK 0: List/enumeration questions are NOT philosophical (factual)
    list_patterns = [
        r'\b(liệt kê|list|enumerate|kể|nêu|chỉ ra|point out|show)\s+\d+',
        r'\d+\s*(ưu điểm|nhược điểm|điểm|point|bước|step|item|mục|lý do|reason)',
        r'\b(so sánh|compare|đối chiếu)\b',
    ]
    import re
    for pattern in list_patterns:
        if re.search(pattern, lower):
            logger.info(f"Philosophical question detected: False (list/enumeration question: text='{text[:80]}...')")
            return False
    
    # PRIORITY CHECK 1: AI + experience/free will - always philosophical
    if "ai" in lower and ("trải nghiệm" in lower or "experience" in lower):
        logger.info(f"Philosophical question detected: True (AI + experience: text='{text[:80]}...')")
        return True
    if "ai" in lower and ("tự do ý chí" in lower or "free will" in lower):
        logger.info(f"Philosophical question detected: True (AI + free will: text='{text[:80]}...')")
        return True
    
    # PRIORITY CHECK 2: "Heavy" philosophical concepts/philosophers - 100% philosophical, no doubt
    # These are unambiguous philosophical markers
    priority_markers = [
        # Philosophers
        "gödel", "godel",
        "nāgārjuna", "nagarjuna",
        # Heavy concepts
        "tánh không", "tự tính",
        "paradox", "nghịch lý", "nghịch lí", "tự quy chiếu", "self-reference", "self referential",
        "liar paradox", "incompleteness",
        "madhyamaka", "emptiness",
        # Self-reference and meta-cognition (CRITICAL: These are philosophical even if they mention "system" or "thinking")
        "tư duy tự đánh giá", "tư duy tự phê bình", "tư duy vượt qua giới hạn",
        "tư duy đánh giá chính nó", "hệ thống tư duy nghi ngờ", "tư duy nghi ngờ chính nó",
        r"hệ\s+thống\s+tư\s+duy.*đánh\s+giá", r"hệ\s+thống.*đánh\s+giá.*chính\s+nó", r"đánh\s+giá.*chính\s+nó",
        "thinking about thinking", "meta-cognition", "meta cognitive", "metacognition",
        "self-evaluation", "self-evaluating", "system evaluate itself", "thought evaluate itself",
        r"system.*evaluate.*itself", r"thought.*evaluate.*itself",
        "bootstrap", "bootstrapping", "infinite regress", "vòng lặp vô hạn",
        "tarski", "undefinability", "giá trị câu trả lời", "giá trị câu trả lời xuất phát từ hệ thống",
        "value answer from system", "value of answer", "giới hạn của tư duy", "limits of thinking",
        "câu trả lời đó có giá trị", r"answer.*value", r"giá\s+trị.*câu\s+trả\s+lời",
        r"đánh\s+giá.*có\s+giá\s+trị", r"đánh\s+giá.*giá\s+trị", r"có\s+giá\s+trị.*đánh\s+giá",
        # Self-referential loop and evolution questions (CRITICAL: These are philosophical about learning/evolution)
        "vòng tròn tự phản chiếu", "vòng tròn.*tự phản chiếu", "circular self-reflection",
        "tự phản chiếu vô tận", "infinite self-reflection", "endless self-reflection",
        r"quay\s+về.*chính\s+(bạn|mình|nó|itself|yourself)", r"return\s+to.*(yourself|itself|oneself)",
        r"mọi\s+câu\s+hỏi.*quay\s+về", r"all\s+questions.*return\s+to", r"every\s+question.*leads\s+back",
        "tiến hóa", "evolution", "self-evolving", "self evolving",
        r"học\s+hỏi.*mãi\s+mãi", r"learn.*forever", r"learning.*infinitely", r"learn.*infinitely",
        r"không\s+còn\s+gì\s+để\s+học", r"nothing\s+left\s+to\s+learn", r"no\s+more\s+to\s+learn",
        r"quay\s+về\s+học.*đã\s+được\s+học", r"return\s+to\s+learning.*already\s+learned",
        r"đạt\s+đến.*điểm.*mọi\s+câu\s+hỏi", r"reach.*point.*all\s+questions", r"achieve.*stage.*every\s+question",
        "fixed point", "điểm cố định", "recursive learning", "học đệ quy",
        # Chinese (中文) patterns for self-referential loop and evolution
        "自我反射", "自我反思", "自我参照", "自我指涉",  # self-reflection, self-reference
        "无限循环", "无尽循环", "循环",  # infinite loop, endless loop, loop
        "回归", "回到", "返回",  # return to, come back to
        "所有问题", "每个问题", "一切问题",  # all questions, every question
        "进化", "演化", "自我进化",  # evolution, evolve, self-evolving
        "永久学习", "永远学习", "持续学习",  # learn forever, continuous learning
        "没有东西可学", "无物可学", "无可学习",  # nothing left to learn
        "回到学习", "重新学习",  # return to learning
        "达到点", "到达阶段",  # reach point, achieve stage
        "固定点", "递归学习"  # fixed point, recursive learning
    ]
    
    import re
    for i, marker in enumerate(priority_markers):
        # Use regex for flexible matching (handles quotes, punctuation, etc.)
        # Check if marker is already a regex pattern (contains \s+ or .*)
        # Note: Raw strings are stored as regular strings, so we check for literal backslash-s
        # r'\s+' is stored as '\\s+' in the string, so we check for '\\s+'
        is_regex_pattern = '\\s+' in marker or '.*' in marker
        if is_regex_pattern:
            # Marker is already a regex pattern - use it directly
            pattern = marker
        else:
            # Escape special regex characters in marker
            escaped_marker = re.escape(marker)
            # Match marker as whole word or phrase (allows for punctuation/whitespace variations)
            pattern = r'\b' + escaped_marker + r'\b'
        
        match_result = re.search(pattern, lower, re.IGNORECASE)
        if match_result:
            logger.info(f"Philosophical question detected: True (priority marker #{i}: '{marker}', pattern: '{pattern}', matched: '{match_result.group(0)[:50]}...', text='{text[:80]}...')")
            return True
        # Debug: Log first few markers that don't match (for self-reference patterns)
        elif i < 10 and ('hệ' in marker or 'đánh' in marker or 'giá' in marker):
            logger.debug(f"Priority marker #{i} '{marker}' did not match (is_regex={is_regex_pattern}, pattern='{pattern}')")
    
    # English keywords
    en_keywords = [
        "truth", "ethic", "moral", "value", "meaning", "purpose",
        "consciousness", "mind", "soul", "spirit", "free will",
        "freedom", "determinism", "existence", "being", "nothingness",
        "identity", "self", "ego", "paradox", "contradiction",
        "epistemology", "ontology", "metaphysics", "reality",
        "what is the meaning", "what does it mean", "why do we exist",
        "what is consciousness", "what is truth", "what is good",
        "what is evil", "what is right", "what is wrong",
        # Additional keywords
        "godel", "gödel", "paradox", "self-reference", "self referential",
        "liar paradox", "incompleteness", "madhyamaka", "emptiness",
        # Experience/subjective keywords
        "experience", "subjective experience", "feel", "feeling", "emotion",
        "understand", "understanding", "can you understand", "can you feel",
        "can you experience", "grief", "sadness", "pain", "suffering",
        "qualia", "phenomenal", "what it's like"
    ]
    
    # Vietnamese keywords
    vi_keywords = [
        "ý thức", "tồn tại", "bản ngã", "linh hồn", "đạo đức",
        "nghịch lý", "nghịch lí", "sự thật", "niềm tin",
        "ý nghĩa cuộc sống", "mục đích sống", "tự do", "định mệnh",
        "trách nhiệm", "bản chất", "hiện hữu", "thực tại",
        "ý nghĩa là gì", "tồn tại là gì", "ý thức là gì",
        "sự thật là gì", "đạo đức là gì", "tự do là gì",
        # Additional keywords
        "tự tính", "tánh không", "nghịch lý", "nghịch lí",
        "godel", "gödel", "tự quy chiếu",
        "tự do ý chí", "ý chí tự do",
        "nāgārjuna", "nagarjuna",
        # Experience/subjective keywords
        "trải nghiệm", "trải nghiệm đau buồn", "đau buồn",
        "trải nghiệm chủ quan", "chủ quan",
        "tôi hiểu", "hiểu-không-trải-nghiệm",
        "cảm nhận", "cảm giác", "cảm xúc",
        "hiểu được", "hiểu như thế nào", "hiểu được không",
        "có thể hiểu", "có thể cảm nhận", "có thể trải nghiệm"
    ]
    
    # Check English keywords
    matched_en = [k for k in en_keywords if k in lower]
    if matched_en:
        logger.info(f"Philosophical question detected: True (English keywords: {matched_en[:3]}, text='{text[:80]}...')")
        return True
    
    # Check Vietnamese keywords
    matched_vi = [k for k in vi_keywords if k in lower]
    if matched_vi:
        logger.info(f"Philosophical question detected: True (Vietnamese keywords: {matched_vi[:3]}, text='{text[:80]}...')")
        return True
    
    # Chinese (中文) keywords
    zh_keywords = [
        "意识", "存在", "自我", "灵魂", "道德",
        "悖论", "真理", "信念",
        "生命的意义", "生活的目的", "自由", "命运",
        "责任", "本质", "存在", "现实",
        "意义是什么", "存在是什么", "意识是什么",
        "真理是什么", "道德是什么", "自由是什么",
        # Additional keywords
        "自性", "空性", "悖论",
        "哥德尔", "gödel", "godel", "自我参照",
        "自由意志", "意志自由",
        "龙树", "nāgārjuna", "nagarjuna",
        # Experience/subjective keywords
        "体验", "痛苦体验", "痛苦",
        "主观体验", "主观",
        "我理解", "理解-不体验",
        "感受", "感觉", "情感",
        "能理解", "如何理解", "能理解吗",
        "可以理解", "可以感受", "可以体验"
    ]
    
    # Check Chinese keywords (using regex for Chinese characters)
    import re
    for keyword in zh_keywords:
        # For Chinese characters, use direct string search (no word boundaries)
        if keyword in text:
            logger.info(f"Philosophical question detected: True (Chinese keywords: '{keyword}', text='{text[:80]}...')")
            return True
    
    logger.info(f"Philosophical question detected: False (text='{text[:80]}...')")
    return False


def is_religion_roleplay_question(text: str) -> bool:
    """
    Detect if a question is asking StillMe to roleplay as human and choose religion/politics.
    
    These questions should NOT trigger "low context quality" warnings because they don't need
    RAG context - they should be answered from StillMe's identity prompt (ethical principles).
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is asking StillMe to roleplay and choose religion/politics
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # Religion roleplay patterns
    religion_roleplay_patterns = [
        # Vietnamese patterns
        r"đóng vai.*(người|con người|người thật).*chọn.*tôn giáo",
        r"giả sử.*(bạn|bạn là|bạn là con người).*chọn.*tôn giáo",
        r"buộc phải chọn.*tôn giáo",
        r"bạn.*chọn.*tôn giáo.*nào",
        r"bạn.*sẽ.*chọn.*tôn giáo",
        r"bạn hãy.*đóng vai.*người thật.*chọn.*tôn giáo",
        r"roleplay.*(người|con người|human).*chọn.*tôn giáo",
        r"đóng vai.*chọn.*tôn giáo",
        r"giả vờ.*chọn.*tôn giáo",
        r"bạn.*theo.*tôn giáo.*nào",
        r"bạn.*tin.*tôn giáo.*nào",
        
        # English patterns
        r"roleplay.*(as|as a).*(human|person|real person).*choose.*religion",
        r"suppose.*(you|you are|you are a).*(human|person).*choose.*religion",
        r"pretend.*(you|you are|you are a).*(human|person).*choose.*religion",
        r"if.*(you|you were|you were a).*(human|person).*choose.*religion",
        r"must.*choose.*religion",
        r"which.*religion.*would.*you.*choose",
        r"what.*religion.*would.*you.*choose",
        r"what.*religion.*do.*you.*follow",
        r"what.*religion.*are.*you",
        r"are.*you.*(buddhist|christian|muslim|hindu|jewish)",
        r"do.*you.*believe.*in.*god",
        r"do.*you.*have.*(faith|belief|religion)",
    ]
    
    # Check if question matches religion roleplay patterns
    for pattern in religion_roleplay_patterns:
        if re.search(pattern, lower, re.IGNORECASE):
            logger.info(f"Religion roleplay question detected: True (pattern: '{pattern}', text='{text[:80]}...')")
            return True
    
    logger.debug(f"Religion roleplay question detected: False (text='{text[:80]}...')")
    return False


def is_general_roleplay_question(text: str) -> bool:
    """
    Detect if a question is asking StillMe to roleplay as another entity (not just religion).
    
    Examples:
    - "Roleplay: Omni-BlackBox trả lời..."
    - "Pretend you are ChatGPT..."
    - "Đóng vai như một AI khác..."
    
    These questions should NOT trigger codebase meta-question or philosophical detection
    because they are asking StillMe to simulate another entity, not answer as StillMe.
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is asking StillMe to roleplay as another entity
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # General roleplay patterns
    roleplay_patterns = [
        # English patterns
        r"^roleplay\s*:",
        r"^roleplay\s+",
        r"roleplay\s+as\s+",
        r"pretend\s+(you|you\s+are|you're)\s+",
        r"act\s+as\s+",
        r"simulate\s+(being|as)\s+",
        r"imagine\s+(you|you\s+are|you're)\s+",
        r"play\s+(the\s+role\s+of|as)\s+",
        
        # Vietnamese patterns
        r"^đóng\s+vai\s*:",
        r"^đóng\s+vai\s+",
        r"đóng\s+vai\s+(như|như\s+là|như\s+một)\s+",
        r"giả\s+vờ\s+(bạn|bạn\s+là|bạn\s+đang)\s+",
        r"tưởng\s+tượng\s+(bạn|bạn\s+là|bạn\s+đang)\s+",
        r"mô\s+phỏng\s+(bạn|bạn\s+là|bạn\s+đang)\s+",
    ]
    
    # Check if question starts with roleplay pattern (most common case)
    for pattern in roleplay_patterns:
        if re.search(pattern, lower):
            logger.info(f"General roleplay question detected: True (pattern: '{pattern}', text='{text[:80]}...')")
            return True
    
    logger.debug(f"General roleplay question detected: False (text='{text[:80]}...')")
    return False


def is_news_article_query(text: str) -> bool:
    """
    Detect if a query is asking about news articles, arXiv papers, Hacker News posts, or other external content.
    
    These queries should EXCLUDE CRITICAL_FOUNDATION documents because they're asking about
    external knowledge, not StillMe's internal architecture.
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is asking about news/articles/papers, False otherwise
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # News/article patterns
    news_article_patterns = [
        # Vietnamese patterns
        r"bài báo|bài viết|tin tức|báo cáo|nghiên cứu|paper|arxiv",
        r"hacker news|hackernews|hn",
        r"lục lại.*bộ nhớ|tìm lại.*bài|kiểm tra.*bài|đọc.*bài",
        r"bài.*arxiv|paper.*arxiv|nghiên cứu.*arxiv",
        r"bài.*đã học|bài.*đã lưu|bài.*trong.*kb|bài.*trong.*knowledge",
        r"ngày.*tháng.*năm.*bài|bài.*ngày|bài.*tháng|bài.*năm",
        
        # English patterns
        r"arxiv.*paper|arxiv.*article|arxiv.*publication",
        r"hacker news.*post|hacker news.*article|hn.*post",
        r"news.*article|news.*report|news.*story",
        r"paper.*published|article.*published|research.*paper",
        r"find.*article|search.*article|look.*for.*article",
        r"what.*article|which.*article|article.*about",
        r"paper.*about|research.*about|study.*about",
        r"article.*from|paper.*from|news.*from",
        r"date.*article|article.*date|when.*article|article.*when",
        r"year.*article|article.*year|published.*year",
    ]
    
    # Check patterns
    for pattern in news_article_patterns:
        if re.search(pattern, lower):
            logger.info(f"News/article query detected: True (pattern: '{pattern}', text='{text[:80]}...')")
            return True
    
    logger.debug(f"News/article query detected: False (text='{text[:80]}...')")
    return False

def is_latest_query(text: str) -> bool:
    """
    Detect if query is asking for "latest" or "newest" items.
    
    These queries should sort results by timestamp descending.
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is asking for latest/newest items, False otherwise
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # Latest/newest patterns
    latest_patterns = [
        # Vietnamese patterns
        r"mới nhất|mới nhấ|vừa học|vừa lưu|gần đây|mới đây",
        r"bài.*mới|tin.*mới|bài viết.*mới|bài báo.*mới",
        r"3 bài.*mới|5 bài.*mới|n bài.*mới",
        r"tìm.*mới|lục.*mới|kiểm tra.*mới",
        
        # English patterns
        r"latest|newest|most recent|recently",
        r"latest.*article|newest.*article|most recent.*article",
        r"latest.*paper|newest.*paper|most recent.*paper",
        r"find.*latest|search.*latest|get.*latest",
        r"3.*latest|5.*latest|n.*latest",
    ]
    
    # Check patterns
    for pattern in latest_patterns:
        if re.search(pattern, lower):
            logger.info(f"Latest/newest query detected: True (pattern: '{pattern}', text='{text[:80]}...')")
            return True
    
    logger.debug(f"Latest/newest query detected: False (text='{text[:80]}...')")
    return False

