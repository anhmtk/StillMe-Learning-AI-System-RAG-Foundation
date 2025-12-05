"""
Time Estimation Intent Detector

Detects when user asks about time estimation or duration questions.
"""

import re
from typing import Optional, Tuple

# Time estimation keywords (English + Vietnamese)
TIME_ESTIMATION_KEYWORDS = {
    # English
    "how long",
    "how much time",
    "how long will",
    "how long does",
    "how long to",
    "duration",
    "estimate",
    "estimation",
    "time estimate",
    "how much time will",
    "how much time does",
    "how much time to",
    "take to",
    "will take",
    "takes to",
    "time to",
    "time it takes",
    "time needed",
    "time required",
    
    # Vietnamese (with and without tone marks)
    "bao lâu",
    "bao lau",
    "mất bao lâu",
    "mat bao lau",
    "tốn bao lâu",
    "ton bao lau",
    "cần bao lâu",
    "can bao lau",
    "sẽ mất",
    "se mat",
    "sẽ tốn",
    "se ton",
    "sẽ cần",
    "se can",
    "ước tính",
    "uoc tinh",
    "thời gian",
    "thoi gian",
    "thời lượng",
    "thoi luong",
    "mất thời gian",
    "mat thoi gian",
    "tốn thời gian",
    "ton thoi gian",
    "cần thời gian",
    "can thoi gian",
}


def detect_time_estimation_intent(query: str) -> Tuple[bool, Optional[str]]:
    """
    Detect if user is asking about time estimation or duration.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (is_time_estimation, task_description)
        - is_time_estimation: True if query is about time estimation
        - task_description: Extracted task description if detected, None otherwise
    """
    query_lower = query.lower()
    
    # NEGATIVE PATTERNS: Exclude capability questions
    # These patterns indicate the user is asking about capability/feature, not time estimation
    negative_patterns = [
        r'do you (track|have|support|can|use|provide)',
        r'can you (track|have|support|use|provide)',
        r'does (stillme|it|the system) (track|have|support|use|provide)',
        r'bạn (có|đã) (theo dõi|có|hỗ trợ|sử dụng|cung cấp)',
        r'stillme (có|đã) (theo dõi|có|hỗ trợ|sử dụng|cung cấp)',
        r'hệ thống (có|đã) (theo dõi|có|hỗ trợ|sử dụng|cung cấp)',
        r'what (features|capabilities|functions)',
        r'tính năng (nào|gì)',
        r'khả năng (nào|gì)',
        # CRITICAL: Exclude validation/capability questions
        r'validation.*warning|cảnh báo.*validation',
        r'non-critical.*failure|lỗi.*không.*nghiêm.*trọng',
        r'low overlap.*citation|trùng lặp.*thấp.*trích dẫn',
        r'stillme.*hiển thị|stillme.*cung cấp|stillme.*sẽ',
        r'stillme.*tuyên bố|stillme.*duy trì',
        r'learning.*frequency|tần suất.*cập nhật|tần suất.*học',
        r'6 lần.*ngày|6 cycles.*day',
        r'timestamp.*added|thời điểm.*đưa vào',
        r'source.*knowledge base|nguồn.*cơ sở.*kiến thức',
        r'how.*stillme.*display|stillme.*hiển thị.*như thế nào',
        r'what.*information.*stillme|thông tin.*stillme.*cung cấp',
    ]
    
    # If query matches negative patterns, it's NOT a time estimation question
    for pattern in negative_patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return (False, None)
    
    # Check for time estimation keywords
    has_time_keyword = any(
        keyword in query_lower 
        for keyword in TIME_ESTIMATION_KEYWORDS
    )
    
    if not has_time_keyword:
        return (False, None)
    
    task_description = None
    
    # First, try Vietnamese patterns (more reliable without regex)
    # Handle both "bao lâu" (with tone) and "bao lau" (without tone)
    if "bao lâu" in query_lower or "bao lau" in query_lower:
        # Pattern: "bao lâu để [task]" or "bao lau de [task]"
        if "để" in query_lower or "de" in query_lower:
            # Try with tone mark first
            if "để" in query_lower:
                parts = query_lower.split("để", 1)
            else:
                parts = query_lower.split("de", 1)
            if len(parts) > 1:
                task_description = parts[1].strip().rstrip("?")
        # Pattern: "[task] mất bao lâu" or "[task] mat bao lau"
        elif "mất bao lâu" in query_lower or "mat bao lau" in query_lower:
            if "mất bao lâu" in query_lower:
                parts = query_lower.split("mất bao lâu", 1)
            else:
                parts = query_lower.split("mat bao lau", 1)
            if len(parts) > 0:
                task_description = parts[0].strip()
        # Pattern: "[task] tốn bao lâu" or "[task] ton bao lau"
        elif "tốn bao lâu" in query_lower or "ton bao lau" in query_lower:
            if "tốn bao lâu" in query_lower:
                parts = query_lower.split("tốn bao lâu", 1)
            else:
                parts = query_lower.split("ton bao lau", 1)
            if len(parts) > 0:
                task_description = parts[0].strip()
        # Pattern: "[task] cần bao lâu" or "[task] can bao lau"
        elif "cần bao lâu" in query_lower or "can bao lau" in query_lower:
            if "cần bao lâu" in query_lower:
                parts = query_lower.split("cần bao lâu", 1)
            else:
                parts = query_lower.split("can bao lau", 1)
            if len(parts) > 0:
                task_description = parts[0].strip()
    
    # If Vietnamese pattern didn't match, try regex patterns
    if not task_description:
        patterns = [
            r'how\s+long\s+(?:will\s+it\s+)?(?:take\s+)?(?:to\s+)?(.+?)(?:\?|$)',
            r'how\s+much\s+time\s+(?:will\s+it\s+)?(?:take\s+)?(?:to\s+)?(.+?)(?:\?|$)',
            r'bao\s+lâu\s+(?:để\s+)?(.+?)(?:\?|$)',
            r'mất\s+bao\s+lâu\s+(?:để\s+)?(.+?)(?:\?|$)',
            r'tốn\s+bao\s+lâu\s+(?:để\s+)?(.+?)(?:\?|$)',
            r'cần\s+bao\s+lâu\s+(?:để\s+)?(.+?)(?:\?|$)',
            r'ước\s+tính\s+(?:thời\s+gian\s+)?(?:cho\s+)?(.+?)(?:\?|$)',
            r'(.+?)\s+(?:mất|tốn|cần)\s+bao\s+lâu',  # "[task] mất bao lâu"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                task_description = match.group(1).strip()
                # Clean up common trailing words
                task_description = re.sub(r'\s+(?:to|for|để|cho)\s*$', '', task_description)
                break
    
    # If no specific task found, use query as task description
    if not task_description:
        task_description = query.strip()
    
    return (True, task_description)
