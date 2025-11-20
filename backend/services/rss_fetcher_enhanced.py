"""
Enhanced RSS Feed Fetcher for StillMe
Improved error handling, retry mechanism, XML validation, and fallback feeds
"""

import feedparser
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import time
import asyncio
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Fallback feeds mapping for failed feeds
FALLBACK_FEEDS = {
    "https://feeds.reuters.com/reuters/topNews": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://feeds.reuters.com/reuters/worldNews"
    ],
    "https://www.brookings.edu/topic/technology-innovation/feed/": [
        "https://www.brookings.edu/feed/",
        "https://www.brookings.edu/topic/artificial-intelligence/feed/",
        "https://www.brookings.edu/topic/tech-innovation/feed/"
    ],
    "https://www.cato.org/rss/blog/technology": [
        "https://www.cato.org/rss/blog",
        "https://www.cato.org/feed/",
        "https://www.cato.org/research/feed/"
    ],
    "https://www.aei.org/technology/feed/": [
        "https://www.aei.org/feed/",
        "https://www.aei.org/research/feed/",
        "https://www.aei.org/policy-areas/technology/feed/"
    ],
    "https://lilianweng.github.io/feed.xml": [
        # No reliable fallback - feed removed from main list
    ],
    "https://phys.org/rss-feed/physics-news/": [
        "https://phys.org/rss-feed/",
        "https://phys.org/rss-feed/breaking/"
    ],
    "https://tricycle.org/feed/": [
        # No reliable fallback - feed removed from main list
    ]
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 10.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


def validate_xml_structure(xml_content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate XML structure before parsing.
    
    Args:
        xml_content: XML content as string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ET.fromstring(xml_content)
        return True, None
    except ET.ParseError as e:
        return False, f"XML parse error: {str(e)}"
    except Exception as e:
        return False, f"XML validation error: {str(e)}"


def sanitize_xml(xml_content: str) -> str:
    """
    Sanitize XML content by removing invalid characters and fixing common issues.
    
    Args:
        xml_content: Raw XML content
        
    Returns:
        Sanitized XML content
    """
    # Remove null bytes and other control characters (except newlines and tabs)
    sanitized = ''.join(char for char in xml_content if ord(char) >= 32 or char in '\n\t')
    
    # Fix common XML issues
    # Remove invalid XML entities
    sanitized = sanitized.replace('&nbsp;', ' ')
    sanitized = sanitized.replace('&amp;', '&')
    
    # Fix mismatched tags (basic - more complex fixes would need full parser)
    # This is a simple heuristic - for production, consider using lxml with recover=True
    
    return sanitized


async def fetch_feed_with_retry(
    feed_url: str,
    max_retries: int = MAX_RETRIES,
    timeout: float = 10.0
) -> Optional[feedparser.FeedParserDict]:
    """
    Fetch RSS feed with exponential backoff retry mechanism.
    
    Args:
        feed_url: URL of the RSS feed
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        
    Returns:
        Parsed feed or None if all retries failed
    """
    retry_delay = INITIAL_RETRY_DELAY
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                
                # Validate XML structure
                xml_content = response.text
                is_valid, error_msg = validate_xml_structure(xml_content)
                
                if not is_valid:
                    # Try sanitizing
                    sanitized_xml = sanitize_xml(xml_content)
                    is_valid, error_msg = validate_xml_structure(sanitized_xml)
                    if is_valid:
                        xml_content = sanitized_xml
                    else:
                        logger.warning(f"XML validation failed for {feed_url} (attempt {attempt + 1}): {error_msg}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                            continue
                        return None
                
                # Parse feed
                feed = feedparser.parse(xml_content)
                
                # Check for parsing errors
                if feed.bozo and feed.bozo_exception:
                    error_type = type(feed.bozo_exception).__name__
                    error_msg = str(feed.bozo_exception)
                    
                    # Try to handle specific error types
                    if "DNS" in error_type or "DNS" in error_msg:
                        logger.warning(f"DNS error for {feed_url}: {error_msg}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                            continue
                        return None
                    elif "not well-formed" in error_msg.lower() or "malformed" in error_msg.lower():
                        logger.warning(f"Malformed XML for {feed_url}: {error_msg}")
                        # Try sanitizing and reparsing
                        sanitized = sanitize_xml(xml_content)
                        feed = feedparser.parse(sanitized)
                        if feed.bozo:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                                continue
                            return None
                    elif "mismatched tag" in error_msg.lower():
                        logger.warning(f"Mismatched tag for {feed_url}: {error_msg}")
                        # Try sanitizing
                        sanitized = sanitize_xml(xml_content)
                        feed = feedparser.parse(sanitized)
                        if feed.bozo:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                                continue
                            return None
                    elif "invalid token" in error_msg.lower():
                        logger.warning(f"Invalid token for {feed_url}: {error_msg}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                            continue
                        return None
                
                # Success
                logger.debug(f"Successfully fetched {feed_url} (attempt {attempt + 1})")
                return feed
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {feed_url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                continue
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {feed_url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1 and e.response.status_code >= 500:
                # Retry on server errors
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                continue
            return None
        except Exception as e:
            logger.warning(f"Error fetching {feed_url} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                continue
    
    logger.error(f"Failed to fetch {feed_url} after {max_retries} attempts")
    return None


async def fetch_feed_with_fallback(feed_url: str) -> Optional[feedparser.FeedParserDict]:
    """
    Fetch RSS feed with fallback URLs if primary feed fails.
    
    Args:
        feed_url: Primary feed URL
        
    Returns:
        Parsed feed from primary or fallback URL, or None if all fail
    """
    # Try primary feed first
    feed = await fetch_feed_with_retry(feed_url)
    if feed and not feed.bozo:
        return feed
    
    # Try fallback feeds
    fallback_urls = FALLBACK_FEEDS.get(feed_url, [])
    if not fallback_urls:
        logger.warning(f"No fallback feeds configured for {feed_url}")
        return None
    
    logger.info(f"Trying {len(fallback_urls)} fallback feed(s) for {feed_url}")
    for fallback_url in fallback_urls:
        feed = await fetch_feed_with_retry(fallback_url)
        if feed and not feed.bozo:
            logger.info(f"Successfully fetched fallback feed: {fallback_url}")
            return feed
    
    logger.error(f"All feeds failed for {feed_url} (including {len(fallback_urls)} fallback(s))")
    return None

