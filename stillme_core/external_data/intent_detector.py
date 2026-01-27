"""
Intent Detector for External Data Queries

Detects when a user query should be routed to external data providers
instead of RAG pipeline.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ExternalDataIntent:
    """Detected intent for external data query"""
    type: str  # "weather", "news", "fx_rate", "sports", etc.
    params: Dict[str, Any]  # Query parameters (location, query, etc.)
    confidence: float  # Confidence score (0.0-1.0)


def detect_external_data_intent(query: str) -> Optional[ExternalDataIntent]:
    """
    Detect if query should be routed to external data provider
    
    Args:
        query: User query string
        
    Returns:
        ExternalDataIntent if detected, None otherwise
    """
    if not query:
        return None
    
    query_lower = query.lower().strip()
    
    # Weather intent detection
    weather_intent = _detect_weather_intent(query, query_lower)
    if weather_intent:
        return weather_intent
    
    # News intent detection
    news_intent = _detect_news_intent(query, query_lower)
    if news_intent:
        return news_intent
    
    # Time intent detection
    time_intent = _detect_time_intent(query, query_lower)
    if time_intent:
        return time_intent
    
    return None


def _is_research_query(query_lower: str) -> bool:
    """Detect research/paper-style queries that should stay in RAG."""
    # If the user asks for analysis/summary/compare and does NOT explicitly ask for news,
    # keep it in RAG (these are not real-time news requests).
    analysis_indicators = [
        "tóm tắt",
        "tom tat",
        "so sánh",
        "so sanh",
        "phân tích",
        "phan tich",
        "đánh giá",
        "danh gia",
        "compare",
        "summarize",
        "analysis",
        "review",
    ]
    explicit_news_indicators = [
        "tin tức",
        "tin tuc",
        "thời sự",
        "thoi su",
        "bản tin",
        "ban tin",
        "headline",
        "headlines",
        "breaking news",
        "news",
    ]
    if any(ind in query_lower for ind in analysis_indicators) and not any(
        ind in query_lower for ind in explicit_news_indicators
    ):
        logger.info(
            "🧪 Analysis-style query detected - will skip news routing "
            f"(text='{query_lower[:80]}...')"
        )
        return True

    # Fast substring checks (robust for Vietnamese diacritics / word boundaries)
    research_indicators = [
        # Vietnamese (with and without diacritics)
        "nghiên cứu",
        "nghien cuu",
        "bài nghiên cứu",
        "bai nghien cuu",
        "bài báo",
        "bai bao",
        "bài viết học thuật",
        "bai viet hoc thuat",
        "tạp chí",
        "tap chi",
        "công bố",
        "cong bo",
        "hội nghị",
        "hoi nghi",
        "kỷ yếu",
        "ky yeu",
        "tiền ấn phẩm",
        "tien an pham",
        # English
        "research",
        "study",
        "paper",
        "journal",
        "publication",
        "conference",
        "proceedings",
        "preprint",
        "doi",
        # Source-specific signals
        "arxiv",
        "crossref",
        "papers with code",
        "paperswithcode",
    ]

    for indicator in research_indicators:
        if indicator in query_lower:
            logger.info(
                "🧪 Research-style query detected - will skip news routing "
                f"(indicator='{indicator}', text='{query_lower[:80]}...')"
            )
            return True

    # Regex fallback for flexible matching
    research_patterns = [
        r"nghiên\s+cứu",
        r"nghien\s+cuu",
        r"bài\s+nghiên\s+cứu",
        r"bai\s+nghien\s+cuu",
        r"bài\s+báo",
        r"bai\s+bao",
        r"bài\s+viết\s+học\s+thuật",
        r"bai\s+viet\s+hoc\s+thuat",
        r"tạp\s+chí",
        r"tap\s+chi",
        r"công\s+bố",
        r"cong\s+bo",
        r"hội\s+nghị",
        r"hoi\s+nghi",
        r"kỷ\s+yếu",
        r"ky\s+yeu",
        r"tiền\s+ấn\s+phẩm",
        r"tien\s+an\s+pham",
        r"research",
        r"study",
        r"paper",
        r"journal",
        r"publication",
        r"conference",
        r"proceedings",
        r"preprint",
        r"doi",
        r"arxiv",
        r"crossref",
        r"papers\s*with\s*code",
        r"paperswithcode",
    ]

    for pattern in research_patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.info(
                "🧪 Research-style query detected - will skip news routing "
                f"(pattern='{pattern}', text='{query_lower[:80]}...')"
            )
            return True

    return False


def _detect_weather_intent(query: str, query_lower: str) -> Optional[ExternalDataIntent]:
    """Detect weather-related queries"""
    
    # Weather keywords (English + Vietnamese)
    weather_keywords = [
        # English
        r'\bweather\b',
        r'\btemperature\b',
        r'\bforecast\b',
        r'\bhow.*weather\b',
        r'\bwhat.*weather\b',
        r'\bweather.*like\b',
        r'\bweather.*today\b',
        r'\bweather.*tomorrow\b',
        r'\bweather.*now\b',
        r'\bcurrent.*weather\b',
        r'\bweather.*in\b',
        # Vietnamese
        r'\bthời\s+tiết\b',
        r'\bnhiệt\s+độ\b',
        r'\bdự\s+báo\s+thời\s+tiết\b',
        r'\bthời\s+tiết\s+hôm\s+nay\b',
        r'\bthời\s+tiết\s+ngày\s+mai\b',
        r'\bthời\s+tiết\s+hiện\s+tại\b',
        r'\bthời\s+tiết\s+ở\b',
        r'\bthời\s+tiết\s+tại\b',
    ]
    
    # Check if query contains weather keywords
    has_weather_keyword = any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in weather_keywords)
    
    if not has_weather_keyword:
        return None
    
    # Extract location
    location = _extract_location(query, query_lower)
    
    # Calculate confidence
    confidence = 0.8  # Base confidence for weather queries
    
    # Increase confidence if location is found
    if location:
        confidence = 0.9
    
    # Decrease confidence if query seems too complex (might need RAG)
    if len(query.split()) > 15:
        confidence *= 0.8
    
    # Only return if confidence is high enough
    if confidence >= 0.7:
        return ExternalDataIntent(
            type="weather",
            params={"location": location} if location else {},
            confidence=confidence
        )
    
    return None


def _detect_news_intent(query: str, query_lower: str) -> Optional[ExternalDataIntent]:
    """Detect news-related queries"""

    # Guardrail: research/paper queries should stay in RAG, not external news
    if _is_research_query(query_lower):
        return None
    
    # First, check for simple Vietnamese patterns that are very common
    # "mới nhất về" or "thông tin mới nhất" are strong indicators
    simple_indicators = [
        'mới nhất về',
        'thông tin mới nhất',
        'thông tin mới',
        'tin tức mới nhất',
        'tin mới nhất',
    ]
    
    # Check if query contains any of these simple indicators
    has_simple_indicator = any(indicator in query_lower for indicator in simple_indicators)
    
    # News keywords (English + Vietnamese) - more specific patterns
    news_keywords = [
        # English
        r'\bnews\b',
        r'\blatest\s+news\b',
        r'\brecent\s+news\b',
        r'\bnews\s+about\b',
        r'\bnews\s+on\b',
        r'\bnews\s+regarding\b',
        r'\bwhat.*news\b',
        r'\bany.*news\b',
        r'\bheadlines\b',
        r'\bbreaking\s+news\b',
        r'\btoday.*news\b',
        r'\brecent.*news\b',
        # Vietnamese - explicit news keywords
        r'\btin\s+tức\b',
        r'\btin\s+mới\b',
        r'\btin\s+tức\s+mới\s+nhất\b',
        r'\btin\s+tức\s+về\b',
        r'\btin\s+tức\s+liên\s+quan\b',
        r'\bthời\s+sự\b',
        r'\bheadline\b',
        # Vietnamese - "thông tin mới nhất" patterns (common way to ask for latest news)
        # Note: Using simpler patterns without strict word boundaries for Vietnamese
        r'thông\s+tin\s+mới\s+nhất',
        r'thông\s+tin\s+mới',
        r'thông\s+tin\s+về',
        r'thông\s+tin\s+ngày\s+hôm\s+nay',
        r'thông\s+tin\s+mới\s+nhất\s+về',
        r'thông\s+tin\s+mới\s+nhất\s+ngày\s+hôm\s+nay',
        r'có\s+biết\s+thông\s+tin\s+mới\s+nhất',
        # Additional patterns for common Vietnamese news queries
        r'mới\s+nhất\s+về',
        r'thông\s+tin\s+.*\s+mới',
        r'tin\s+tức\s+.*\s+mới',
    ]
    
    # Check if query contains news keywords (either simple indicators or regex patterns)
    has_news_keyword = has_simple_indicator
    
    if not has_news_keyword:
        # Try regex patterns
        matched_pattern = None
        for pattern in news_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                has_news_keyword = True
                matched_pattern = pattern
                logger.debug(f"News keyword matched: pattern={pattern}, query={query[:50]}")
                break
    
    if not has_news_keyword:
        logger.debug(f"No news keyword found in query: {query[:50]}")
        return None
    
    # Extract query/topic
    news_query = _extract_news_query(query, query_lower)
    
    # Calculate confidence
    confidence = 0.75  # Base confidence for news queries
    
    # Increase confidence if specific topic is mentioned
    if news_query and len(news_query) > 3:
        confidence = 0.85
    
    # Decrease confidence if query seems too complex
    if len(query.split()) > 20:
        confidence *= 0.8
    
    # Only return if confidence is high enough
    if confidence >= 0.7:
        return ExternalDataIntent(
            type="news",
            params={"query": news_query, "max_results": 5},
            confidence=confidence
        )
    
    return None


def _extract_location(query: str, query_lower: str) -> Optional[str]:
    """Extract location from weather query"""
    
    # Common patterns
    patterns = [
        # "weather in [location]"
        r'weather\s+in\s+([a-z\s]+?)(?:\?|$|\.)',
        # "thời tiết ở [location]"
        r'thời\s+tiết\s+ở\s+([a-z\s]+?)(?:\?|$|\.)',
        # "thời tiết tại [location]"
        r'thời\s+tiết\s+tại\s+([a-z\s]+?)(?:\?|$|\.)',
        # "[location] weather"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+weather',
        # "weather [location]"
        r'weather\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Clean up common words
            location = re.sub(r'\b(in|at|the|ở|tại)\b', '', location, flags=re.IGNORECASE).strip()
            if location and len(location) > 2:
                return location
    
    # Fallback: try to extract capitalized words (likely city names)
    # This is a simple heuristic - can be improved
    words = query.split()
    capitalized_words = [w for w in words if w[0].isupper() and len(w) > 2]
    if capitalized_words:
        # Take first capitalized word/phrase
        location = ' '.join(capitalized_words[:2])  # Max 2 words
        return location
    
    return None


def _extract_news_query(query: str, query_lower: str) -> str:
    """Extract news topic/query from query"""
    
    # Remove news keywords to get the actual topic
    news_removal_patterns = [
        # English patterns
        r'\bnews\s+about\s+',
        r'\bnews\s+on\s+',
        r'\bnews\s+regarding\s+',
        r'\bwhat.*news\s+about\s+',
        r'\blatest\s+news\s+on\s+',
        r'\brecent\s+news\s+about\s+',
        # Vietnamese - explicit "tin tức" patterns
        r'\btin\s+tức\s+về\s+',
        r'\btin\s+tức\s+liên\s+quan\s+',
        r'\btin\s+tức\s+mới\s+nhất\s+về\s+',
        # Vietnamese - "thông tin mới nhất" patterns
        r'\bthông\s+tin\s+mới\s+nhất\s+về\s+',
        r'\bthông\s+tin\s+mới\s+nhất\s+ngày\s+hôm\s+nay\s+về\s+',
        r'\bthông\s+tin\s+về\s+',
        r'\bthông\s+tin\s+mới\s+nhất\s+',
        r'\bcó\s+biết\s+thông\s+tin\s+mới\s+nhất\s+về\s+',
    ]
    
    topic = query
    for pattern in news_removal_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            topic = query[match.end():].strip()
            # Remove trailing punctuation and question words
            topic = re.sub(r'[?.,!]+$', '', topic).strip()
            topic = re.sub(r'^(về|about|on|regarding)\s+', '', topic, flags=re.IGNORECASE).strip()
            # Remove common time/question words
            topic = re.sub(r'\b(ngày\s+hôm\s+nay|hôm\s+nay|today|ko|không|gì|what|mới\s+nhất|latest|recent)\b', '', topic, flags=re.IGNORECASE).strip()
            if topic:
                return topic
    
    # Try to extract topic after "về" or "about" if present
    # Pattern: "thông tin mới nhất về [topic]"
    about_patterns = [
        r'về\s+([^?.,!]+)',
        r'about\s+([^?.,!]+)',
        r'on\s+([^?.,!]+)',
    ]
    
    for pattern in about_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            # Remove common question words and time references
            topic = re.sub(r'\b(ngày\s+hôm\s+nay|hôm\s+nay|today|ko|không|gì|what|mới\s+nhất|latest|recent)\b', '', topic, flags=re.IGNORECASE).strip()
            # Remove trailing question marks and punctuation
            topic = re.sub(r'[?.,!]+$', '', topic).strip()
            if topic and len(topic) > 1:  # Allow single character topics like "AI"
                return topic
    
    # If no specific topic, return generic query
    # For "news" or "tin tức" without topic, we'll search for general news
    if re.search(r'^(news|tin\s+tức|thông\s+tin)', query_lower):
        return "technology"  # Default to technology news
    
    return query.strip()


def _detect_time_intent(query: str, query_lower: str) -> Optional[ExternalDataIntent]:
    """Detect time-related queries"""
    
    # Simple string matching for common Vietnamese patterns (more reliable than regex)
    simple_indicators = [
        'mấy giờ',
        'thời gian hiện tại',
        'thời gian hiện giờ',
        'giờ hiện tại',
        'giờ hiện giờ',
        'ngày tháng năm',
        'hôm nay là',
        'thứ mấy',
        'what time',
        'current time',
        'what date',
        'current date',
    ]
    
    # Check simple indicators first
    has_simple_indicator = any(indicator in query_lower for indicator in simple_indicators)
    
    # Time keywords (English + Vietnamese) - regex patterns
    time_keywords = [
        # English
        r'\bcurrent\s+time\b',
        r'\bwhat\s+time\b',
        r'\bwhat.*time.*now\b',
        r'\btime.*now\b',
        r'\bwhat.*date\b',
        r'\bcurrent\s+date\b',
        r'\btoday.*date\b',
        r'\bwhat.*day\b',
        r'\bwhat.*hour\b',
        # Vietnamese - simpler patterns without word boundaries
        r'thời\s+gian\s+hiện\s+tại',
        r'thời\s+gian\s+hiện\s+giờ',
        r'mấy\s+giờ',
        r'giờ\s+hiện\s+tại',
        r'giờ\s+hiện\s+giờ',
        r'ngày\s+tháng\s+năm',
        r'ngày\s+hôm\s+nay',
        r'hôm\s+nay\s+là\s+ngày',
        r'thứ\s+mấy',
    ]
    
    # Check if query contains time keywords (either simple indicators or regex patterns)
    has_time_keyword = has_simple_indicator
    
    if not has_time_keyword:
        # Try regex patterns
        for pattern in time_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                has_time_keyword = True
                break
    
    if not has_time_keyword:
        return None
    
    # Calculate confidence
    confidence = 0.85  # High confidence for time queries
    
    # Decrease confidence if query seems too complex
    if len(query.split()) > 20:
        confidence *= 0.8
    
    # Only return if confidence is high enough
    if confidence >= 0.7:
        return ExternalDataIntent(
            type="time",
            params={},
            confidence=confidence
        )
    
    return None

