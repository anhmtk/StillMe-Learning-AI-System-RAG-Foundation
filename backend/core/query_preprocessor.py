"""
Query Preprocessing for Better RAG Retrieval
Extracts key terms and improves cross-lingual matching
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Vietnamese-English keyword mapping for historical/factual queries
VI_EN_KEYWORD_MAP = {
    # Historical events
    "hiệp ước": "treaty",
    "hội nghị": "conference",
    "chiến tranh": "war",
    "trận đánh": "battle",
    "cuộc cách mạng": "revolution",
    "phân chia": "partition",
    "độc lập": "independence",
    
    # Countries/Regions
    "việt nam": "Vietnam",
    "trung quốc": "China",
    "nhật bản": "Japan",
    "hàn quốc": "Korea",
    "mỹ": "USA",
    "hoa kỳ": "USA",
    "liên xô": "Soviet Union",
    "anh": "UK",
    "pháp": "France",
    
    # Organizations
    "imf": "IMF",
    "ngân hàng thế giới": "World Bank",
    "nato": "NATO",
    "liên hợp quốc": "UN",
    
    # Historical figures
    "hồ chí minh": "Ho Chi Minh",
    "bảo đại": "Bao Dai",
    "võ nguyên giáp": "Vo Nguyen Giap",
}

# Well-known historical events (Vietnamese -> English)
HISTORICAL_EVENTS_MAP = {
    "geneva 1954": "Geneva Conference 1954",
    "hội nghị geneva 1954": "Geneva Conference 1954",
    "hiệp ước geneva 1954": "Geneva Conference 1954",
    "hiệp ước geneva": "Geneva Conference",
    "geneva conference": "Geneva Conference",
    "bretton woods 1944": "Bretton Woods Conference 1944",
    "hội nghị bretton woods 1944": "Bretton Woods Conference 1944",
    "bretton woods": "Bretton Woods",
    "điện biên phủ 1954": "Dien Bien Phu 1954",
    "trận điện biên phủ": "Dien Bien Phu",
}


def extract_key_terms(query: str) -> List[str]:
    """
    Extract key terms from query (years, names, locations, events).
    Useful for improving RAG retrieval by adding English keywords to Vietnamese queries.
    
    Args:
        query: User query string
        
    Returns:
        List of key terms (years, names, locations, events)
    """
    key_terms = []
    query_lower = query.lower()
    
    # Extract years (4 digits)
    years = re.findall(r'\b\d{4}\b', query)
    key_terms.extend(years)
    
    # Extract capitalized words (likely names, places, events)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
    key_terms.extend(capitalized)
    
    # Extract well-known historical events (Vietnamese)
    for vi_event, en_event in HISTORICAL_EVENTS_MAP.items():
        if vi_event in query_lower:
            # Add both Vietnamese and English versions
            key_terms.append(vi_event)
            key_terms.append(en_event)
            # Extract key words from English version
            key_terms.extend(en_event.split())
            # Also add partial matches (e.g., "Geneva" from "Geneva Conference 1954")
            if " " in en_event:
                parts = en_event.split()
                # Add first word (e.g., "Geneva", "Bretton")
                if len(parts) > 0:
                    key_terms.append(parts[0])
                # Add year if present
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        key_terms.append(part)
    
    # Extract Vietnamese keywords and map to English
    for vi_keyword, en_keyword in VI_EN_KEYWORD_MAP.items():
        if vi_keyword in query_lower:
            key_terms.append(en_keyword)
    
    # Remove duplicates and empty strings
    key_terms = list(set([term.strip() for term in key_terms if term.strip()]))
    
    return key_terms


def enhance_query_for_retrieval(query: str) -> str:
    """
    Enhance query by adding English keywords for better cross-lingual matching.
    
    Strategy:
    1. Extract key terms (years, names, events)
    2. Add English keywords for Vietnamese queries
    3. Preserve original query + add keywords
    
    Args:
        query: Original user query
        
    Returns:
        Enhanced query with English keywords appended
    """
    key_terms = extract_key_terms(query)
    
    if not key_terms:
        return query
    
    # Build enhanced query: original + English keywords
    # Format: "original query | keyword1 keyword2 keyword3"
    # This helps embedding model match better
    enhanced = f"{query} | {' '.join(key_terms)}"
    
    logger.debug(f"Enhanced query: '{query}' -> '{enhanced}' (added {len(key_terms)} key terms)")
    
    return enhanced


def is_historical_question(question: str) -> bool:
    """
    Detect if question is about historical events/facts.
    
    Args:
        question: User question text
        
    Returns:
        True if question is about historical topics
    """
    question_lower = question.lower()
    
    # Historical indicators
    historical_patterns = [
        # Years/dates
        r'\b(năm|year|thế kỷ|century|thập niên|decade)\s+\d+',
        r'\b\d{4}\b',  # 4-digit years
        
        # Historical events
        r'\b(hiệp ước|treaty|hiệp định|agreement|conference|hội nghị)',
        r'\b(chiến tranh|war|battle|trận|conflict|cuộc)',
        r'\b(cách mạng|revolution|độc lập|independence)',
        
        # Historical figures
        r'\b(hồ chí minh|ho chi minh|bảo đại|bao dai|võ nguyên giáp)',
        
        # Historical places/events (improved patterns)
        r'\b(geneva|bretton\s+woods|điện biên phủ|dien bien phu)',
        r'\b(việt nam|vietnam|trung quốc|china|pháp|france)',
        r'\b(17th\s+parallel|17th\s+paralell|vĩ tuyến 17)',  # 17th parallel for Vietnam partition
        
        # Historical organizations
        r'\b(imf|world\s+bank|nato|un|liên hợp quốc)',
        
        # Historical keywords in Vietnamese
        r'\b(quyết định|decided|đã quyết định|decisions?)\s+(về|about|regarding)',
    ]
    
    for pattern in historical_patterns:
        if re.search(pattern, question_lower):
            return True
    
    return False

