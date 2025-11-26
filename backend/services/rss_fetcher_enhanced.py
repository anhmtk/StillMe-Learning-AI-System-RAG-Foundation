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
import re
import html
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Fallback feeds mapping for failed feeds
FALLBACK_FEEDS = {
    # Removed: Reuters feeds (businessNews, technologyNews) - Permanent DNS errors
    "https://feeds.reuters.com/reuters/topNews": [
        "https://feeds.reuters.com/reuters/worldNews"  # Only keep worldNews as fallback
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
    ],
    # Removed fallback feeds for permanently broken feeds (all variants failed XML validation):
    # - https://www.sciencedaily.com/rss/matter_energy.xml (all variants failed)
    # - https://aeon.co/feed.rss (all variants failed)
    # - https://www.alignmentforum.org/feed.xml (all variants failed)
    # - https://www.lionsroar.com/feed/ (all variants failed)
    # - https://physicsworld.com/feed/ (all variants failed)
    # These feeds have been removed from the main list and replaced with reliable alternatives
    
    # Feeds with XML validation issues - add fallbacks
    "https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=PNAS": [
        "https://www.pnas.org/feed/",
        "https://www.pnas.org/rss/",
        "https://www.pnas.org/action/showFeed?type=etoc&feed=rss"
    ],
    "https://www.historytoday.com/rss.xml": [
        "https://www.historytoday.com/feed/",
        "https://www.historytoday.com/rss/",
        "https://www.historytoday.com/feed/rss"
    ],
    "https://www.firstthings.com/rss": [
        "https://www.firstthings.com/feed/",
        "https://www.firstthings.com/rss.xml",
        "https://www.firstthings.com/feed/rss"
    ],
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 10.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


def validate_xml_structure(xml_content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate XML structure before parsing.
    
    CRITICAL FIX: Use feedparser for lenient validation instead of strict ET.fromstring.
    feedparser is more tolerant of malformed XML and can handle many edge cases.
    
    Args:
        xml_content: XML content as string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First try strict validation (for well-formed XML)
    try:
        ET.fromstring(xml_content)
        return True, None
    except ET.ParseError as strict_error:
        # If strict validation fails, try feedparser (more lenient)
        # feedparser can handle many malformed XML cases
        try:
            test_feed = feedparser.parse(xml_content)
            # If feedparser can parse it (even with warnings), consider it valid
            # We'll check for bozo later, but for now, if it doesn't crash, it's parseable
            if not test_feed.bozo or (test_feed.bozo and test_feed.entries):
                # feedparser parsed it successfully (may have warnings, but has entries)
                logger.debug(f"Strict XML validation failed, but feedparser can parse: {strict_error}")
                return True, None
            else:
                # feedparser also failed
                return False, f"XML parse error: {str(strict_error)}"
        except Exception as feedparser_error:
            # Both strict and lenient parsing failed
            return False, f"XML parse error: {str(strict_error)}"
    except Exception as e:
        return False, f"XML validation error: {str(e)}"


def sanitize_xml(xml_content: str) -> str:
    """
    Sanitize XML content by removing invalid characters and fixing common issues.
    Enhanced to handle undefined entities (like &eacute; without DTD declaration).
    
    Args:
        xml_content: Raw XML content
        
    Returns:
        Sanitized XML content
    """
    # Remove null bytes and other control characters (except newlines and tabs)
    sanitized = ''.join(char for char in xml_content if ord(char) >= 32 or char in '\n\t')
    
    # STEP 1: Handle undefined XML entities (e.g., &eacute; without DTD)
    # Common HTML/XML entities that might not be declared in DTD
    # Use html.unescape to convert named entities to Unicode characters
    try:
        # First, protect already-escaped ampersands (like &amp; &lt; &gt;)
        # Replace &amp; with a temporary marker
        sanitized = sanitized.replace('&amp;', '__AMP__')
        sanitized = sanitized.replace('&lt;', '__LT__')
        sanitized = sanitized.replace('&gt;', '__GT__')
        sanitized = sanitized.replace('&quot;', '__QUOT__')
        sanitized = sanitized.replace('&apos;', '__APOS__')
        
        # Now unescape other entities (like &eacute; &nbsp; etc.)
        sanitized = html.unescape(sanitized)
        
        # Restore protected entities
        sanitized = sanitized.replace('__AMP__', '&amp;')
        sanitized = sanitized.replace('__LT__', '&lt;')
        sanitized = sanitized.replace('__GT__', '&gt;')
        sanitized = sanitized.replace('__QUOT__', '&quot;')
        sanitized = sanitized.replace('__APOS__', '&apos;')
    except Exception as unescape_error:
        logger.debug(f"HTML unescape failed, using fallback: {unescape_error}")
        # Fallback: Manual replacement of common undefined entities
        entity_replacements = {
            '&nbsp;': ' ',
            '&eacute;': 'é',
            '&egrave;': 'è',
            '&ecirc;': 'ê',
            '&agrave;': 'à',
            '&acirc;': 'â',
            '&ocirc;': 'ô',
            '&icirc;': 'î',
            '&ucirc;': 'û',
            '&uuml;': 'ü',
            '&ouml;': 'ö',
            '&auml;': 'ä',
            '&ccedil;': 'ç',
            '&ndash;': '–',
            '&mdash;': '—',
            '&lsquo;': ''',
            '&rsquo;': ''',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&hellip;': '…',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
            '&deg;': '°',
            '&frac12;': '½',
            '&frac14;': '¼',
            '&frac34;': '¾',
            '&times;': '×',
            '&divide;': '÷',
            '&amp;': '&',  # Must be last to avoid double replacement
        }
        for entity, replacement in entity_replacements.items():
            sanitized = sanitized.replace(entity, replacement)
    
    # STEP 2: Remove any remaining undefined entities (pattern: &word;)
    # This catches entities that weren't in our replacement list
    undefined_entity_pattern = r'&([a-zA-Z][a-zA-Z0-9]{1,31});'
    def replace_undefined_entity(match):
        entity_name = match.group(1)
        # Skip standard XML entities
        if entity_name in ['amp', 'lt', 'gt', 'quot', 'apos']:
            return match.group(0)
        # Try to decode using html.entities if available
        try:
            import html.entities
            if entity_name in html.entities.name2codepoint:
                codepoint = html.entities.name2codepoint[entity_name]
                return chr(codepoint)
        except (ImportError, KeyError, ValueError):
            pass
        # If we can't decode it, remove the entity (safer than leaving it undefined)
        logger.debug(f"Removing undefined entity: &{entity_name};")
        return ''
    
    sanitized = re.sub(undefined_entity_pattern, replace_undefined_entity, sanitized)
    
    # STEP 3: Fix common XML issues
    # Remove BOM and other invisible characters at start
    sanitized = sanitized.lstrip('\ufeff')  # Remove BOM
    sanitized = sanitized.lstrip()  # Remove leading whitespace
    
    # Fix "syntax error: line 2, column 0" - often caused by invalid characters before XML declaration
    # Remove any non-printable characters before <?xml
    if '<?xml' in sanitized:
        xml_start = sanitized.find('<?xml')
        if xml_start > 0:
            # Check if there are invalid characters before <?xml
            before_xml = sanitized[:xml_start]
            # Keep only printable characters and newlines
            cleaned_before = ''.join(c for c in before_xml if c.isprintable() or c in '\n\r\t')
            sanitized = cleaned_before + sanitized[xml_start:]
        # CRITICAL FIX: Also check for BOM or other invisible characters at the very start
        # Some feeds have BOM (Byte Order Mark) or other invisible characters
        if sanitized.startswith('\ufeff'):
            sanitized = sanitized[1:]  # Remove BOM
        # Remove any remaining non-printable characters at the start
        while sanitized and not sanitized[0].isprintable() and sanitized[0] not in '\n\r\t':
            sanitized = sanitized[1:]
    
    # Ensure proper XML declaration if missing
    if not sanitized.strip().startswith('<?xml'):
        # Try to find encoding declaration
        if 'encoding=' in sanitized[:200]:
            # Already has encoding, just ensure <?xml
            if not sanitized.strip().startswith('<'):
                sanitized = '<?xml version="1.0" encoding="UTF-8"?>\n' + sanitized
        else:
            # Add XML declaration with UTF-8 encoding
            sanitized = '<?xml version="1.0" encoding="UTF-8"?>\n' + sanitized
    
    # STEP 4: Fix "not well-formed (invalid token)" - often caused by invalid characters in content
    # Remove any remaining non-XML-safe characters (except in CDATA sections)
    # This is a last resort - try to preserve as much content as possible
    try:
        # Try to parse and see if it's valid now
        ET.fromstring(sanitized)
    except ET.ParseError as parse_error:
        error_msg = str(parse_error).lower()
        if "invalid token" in error_msg or "not well-formed" in error_msg or "syntax error" in error_msg:
            # CRITICAL FIX: Try to remove problematic characters around the error location
            # This is a heuristic - we try to fix common issues
            # Remove any characters that are not valid in XML 1.0
            # XML 1.0 allows: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
            import sys
            if sys.version_info >= (3, 7):
                # Use regex to remove invalid XML characters
                # Keep: tab (0x09), newline (0x0A), carriage return (0x0D), and valid Unicode ranges
                sanitized = re.sub(
                    r'[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]',
                    '',
                    sanitized,
                    flags=re.UNICODE
                )
                logger.debug("Removed invalid XML characters to fix 'invalid token' or 'syntax error'")
            
            # CRITICAL FIX: Also try to fix "line 2, column 4" errors - often caused by invalid characters in first few lines
            # Try to clean the first 100 characters more aggressively
            if "line 2" in error_msg or "column" in error_msg:
                lines = sanitized.split('\n')
                if len(lines) > 1:
                    # Clean first 2 lines more aggressively
                    for i in range(min(2, len(lines))):
                        # Remove any non-printable characters except newline
                        lines[i] = ''.join(c for c in lines[i] if c.isprintable() or c == '\n')
                    sanitized = '\n'.join(lines)
                    logger.debug("Cleaned first 2 lines to fix 'line 2, column' error")
    
    return sanitized


async def fetch_feed_with_retry(
    feed_url: str,
    max_retries: int = MAX_RETRIES,
    timeout: float = 15.0  # Increased from 10.0 to 15.0 for slow feeds
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
    
    # Standard User-Agent header to bypass bot protection (mimics Chrome browser)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                
                # CRITICAL FIX: Try feedparser first (lenient), then validate if needed
                # feedparser is more tolerant and can handle many malformed XML cases
                xml_content = response.text
                
                # Try parsing directly with feedparser (most lenient)
                feed = feedparser.parse(xml_content)
                
                # If feedparser parsed successfully (has entries), use it
                if not feed.bozo or (feed.bozo and feed.entries):
                    # feedparser parsed it successfully (may have warnings, but has entries)
                    logger.debug(f"Successfully parsed {feed_url} with feedparser (attempt {attempt + 1})")
                else:
                    # feedparser failed, try sanitizing and re-parsing
                    logger.debug(f"feedparser failed for {feed_url}, trying sanitization...")
                    sanitized_xml = sanitize_xml(xml_content)
                    feed = feedparser.parse(sanitized_xml)
                    
                    if feed.bozo and not feed.entries:
                        # Still failed after sanitization
                        error_msg = str(feed.bozo_exception) if feed.bozo_exception else "Unknown parse error"
                        logger.warning(f"XML validation failed for {feed_url} (attempt {attempt + 1}): {error_msg}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)
                            continue
                        return None
                    else:
                        logger.debug(f"Successfully parsed {feed_url} after sanitization (attempt {attempt + 1})")
                
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

