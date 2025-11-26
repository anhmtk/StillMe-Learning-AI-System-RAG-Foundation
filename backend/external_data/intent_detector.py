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
    
    return None


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
    
    # News keywords (English + Vietnamese)
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
        # Vietnamese
        r'\btin\s+tức\b',
        r'\btin\s+mới\b',
        r'\btin\s+tức\s+mới\s+nhất\b',
        r'\btin\s+tức\s+về\b',
        r'\btin\s+tức\s+liên\s+quan\b',
        r'\bthời\s+sự\b',
        r'\bheadline\b',
    ]
    
    # Check if query contains news keywords
    has_news_keyword = any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in news_keywords)
    
    if not has_news_keyword:
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
        r'\bnews\s+about\s+',
        r'\bnews\s+on\s+',
        r'\bnews\s+regarding\s+',
        r'\btin\s+tức\s+về\s+',
        r'\btin\s+tức\s+liên\s+quan\s+',
        r'\bwhat.*news\s+about\s+',
        r'\blatest\s+news\s+on\s+',
        r'\brecent\s+news\s+about\s+',
    ]
    
    topic = query
    for pattern in news_removal_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            topic = query[match.end():].strip()
            # Remove trailing punctuation
            topic = re.sub(r'[?.,!]+$', '', topic).strip()
            if topic:
                return topic
    
    # If no specific topic, return generic query
    # For "news" or "tin tức" without topic, we'll search for general news
    if re.search(r'^(news|tin\s+tức)', query_lower):
        return "technology"  # Default to technology news
    
    return query.strip()

