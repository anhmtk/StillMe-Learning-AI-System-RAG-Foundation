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
    
    # Vietnamese
    "bao lâu",
    "mất bao lâu",
    "tốn bao lâu",
    "cần bao lâu",
    "sẽ mất",
    "sẽ tốn",
    "sẽ cần",
    "ước tính",
    "thời gian",
    "thời lượng",
    "mất thời gian",
    "tốn thời gian",
    "cần thời gian",
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
    
    # Check for time estimation keywords
    has_time_keyword = any(
        keyword in query_lower 
        for keyword in TIME_ESTIMATION_KEYWORDS
    )
    
    if not has_time_keyword:
        return (False, None)
    
    task_description = None
    
    # First, try Vietnamese patterns (more reliable without regex)
    if "bao lâu" in query_lower:
        # Pattern: "bao lâu để [task]"
        if "để" in query_lower:
            parts = query_lower.split("để", 1)
            if len(parts) > 1:
                task_description = parts[1].strip().rstrip("?")
        # Pattern: "[task] mất bao lâu"
        elif "mất bao lâu" in query_lower:
            parts = query_lower.split("mất bao lâu", 1)
            if len(parts) > 0:
                task_description = parts[0].strip()
        # Pattern: "[task] tốn bao lâu"
        elif "tốn bao lâu" in query_lower:
            parts = query_lower.split("tốn bao lâu", 1)
            if len(parts) > 0:
                task_description = parts[0].strip()
        # Pattern: "[task] cần bao lâu"
        elif "cần bao lâu" in query_lower:
            parts = query_lower.split("cần bao lâu", 1)
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
