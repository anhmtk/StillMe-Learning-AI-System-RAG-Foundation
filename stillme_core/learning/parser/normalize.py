"""
StillMe Content Normalizer
Normalizes and cleans content from various sources.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse

from stillme_core.learning.fetcher.rss_fetch import ContentItem

log = logging.getLogger(__name__)

@dataclass
class NormalizedContent:
    """Normalized content item."""
    title: str
    url: str
    content: str
    summary: str
    author: Optional[str]
    published_date: Optional[str]
    source: str
    domain: str
    content_type: str
    tags: List[str]
    license: Optional[str]
    word_count: int
    normalized_date: Optional[str] = None
    clean_content: str = ""
    extracted_claims: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extracted_claims is None:
            self.extracted_claims = []
        if self.metadata is None:
            self.metadata = {}

class ContentNormalizer:
    """Normalizes content from various sources."""
    
    def __init__(self):
        self.html_patterns = [
            (r'<[^>]+>', ''),  # Remove HTML tags
            (r'&nbsp;', ' '),  # Replace non-breaking spaces
            (r'&amp;', '&'),   # Replace HTML entities
            (r'&lt;', '<'),
            (r'&gt;', '>'),
            (r'&quot;', '"'),
            (r'&#39;', "'"),
        ]
        
        self.whitespace_patterns = [
            (r'\s+', ' '),      # Multiple whitespace to single space
            (r'\n\s*\n', '\n'), # Multiple newlines to single
            (r'^\s+|\s+$', ''), # Trim whitespace
        ]
        
        # License detection patterns
        self.license_patterns = {
            'CC-BY': [r'creative commons.*attribution', r'cc-by', r'cc by'],
            'CC-BY-SA': [r'creative commons.*attribution.*sharealike', r'cc-by-sa', r'cc by-sa'],
            'MIT': [r'mit license', r'mit'],
            'Apache-2.0': [r'apache.*2\.0', r'apache license'],
            'BSD-3-Clause': [r'bsd.*3.*clause', r'bsd license'],
            'arXiv License': [r'arxiv', r'preprint'],
            'All Rights Reserved': [r'all rights reserved', r'copyright'],
        }
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags and entities."""
        if not text:
            return ""
        
        cleaned = text
        for pattern, replacement in self.html_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        if not text:
            return ""
        
        normalized = text
        for pattern, replacement in self.whitespace_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized.strip()
    
    def extract_license(self, content: str, source: str, domain: str) -> Optional[str]:
        """Extract license information from content."""
        # Check content for license mentions
        content_lower = content.lower()
        
        for license_name, patterns in self.license_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return license_name
        
        # Domain-specific license detection
        if domain == "arxiv.org":
            return "arXiv License"
        elif domain in ["openai.com", "deepmind.com"]:
            return "All Rights Reserved"  # Corporate content
        elif domain in ["huggingface.co", "pytorch.org"]:
            return "Apache-2.0"  # Open source projects
        
        return None
    
    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date string to ISO format."""
        if not date_str:
            return None
        
        try:
            # Common date formats
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d %H:%M:%S',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # Try parsing with dateutil if available
            try:
                from dateutil import parser
                dt = parser.parse(date_str)
                return dt.isoformat()
            except ImportError:
                pass
            
            log.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            log.warning(f"Date normalization failed: {e}")
            return None
    
    def extract_claims(self, content: str) -> List[str]:
        """Extract factual claims from content."""
        claims = []
        
        # Simple claim extraction patterns
        claim_patterns = [
            r'([A-Z][^.!?]*(?:is|are|was|were|has|have|can|could|will|would|should|must|may|might)[^.!?]*[.!?])',
            r'([A-Z][^.!?]*(?:shows?|demonstrates?|indicates?|suggests?|reveals?)[^.!?]*[.!?])',
            r'([A-Z][^.!?]*(?:according to|based on|research shows)[^.!?]*[.!?])',
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                claim = match.strip()
                if len(claim) > 20 and len(claim) < 500:  # Reasonable claim length
                    claims.append(claim)
        
        return claims[:10]  # Limit to 10 claims
    
    def determine_content_type(self, source: str, domain: str, tags: List[str]) -> str:
        """Determine content type based on source and tags."""
        # Check tags for content type indicators
        tag_text = ' '.join(tags).lower()
        
        if any(keyword in tag_text for keyword in ['research', 'paper', 'study', 'arxiv']):
            return 'research'
        elif any(keyword in tag_text for keyword in ['tutorial', 'guide', 'how-to', 'documentation']):
            return 'documentation'
        elif any(keyword in tag_text for keyword in ['news', 'announcement', 'update']):
            return 'news'
        elif domain in ['arxiv.org']:
            return 'research'
        elif domain in ['openai.com', 'deepmind.com']:
            return 'blog'
        else:
            return 'blog'
    
    def normalize_content(self, item: ContentItem) -> NormalizedContent:
        """Normalize a content item."""
        # Clean content
        clean_content = self.clean_html(item.content)
        clean_content = self.normalize_whitespace(clean_content)
        
        # Clean title
        clean_title = self.clean_html(item.title)
        clean_title = self.normalize_whitespace(clean_title)
        
        # Clean summary
        clean_summary = self.clean_html(item.summary)
        clean_summary = self.normalize_whitespace(clean_summary)
        
        # Extract license
        license_info = self.extract_license(item.content, item.source, item.domain)
        
        # Normalize date
        normalized_date = self.normalize_date(item.published_date)
        
        # Extract claims
        claims = self.extract_claims(clean_content)
        
        # Determine content type
        content_type = self.determine_content_type(item.source, item.domain, item.tags)
        
        # Create metadata
        metadata = {
            'original_word_count': item.word_count,
            'normalized_word_count': len(clean_content.split()),
            'has_license': license_info is not None,
            'claim_count': len(claims),
            'tag_count': len(item.tags),
            'normalization_timestamp': datetime.now().isoformat()
        }
        
        return NormalizedContent(
            title=clean_title,
            url=item.url,
            content=clean_content,
            summary=clean_summary,
            author=item.author,
            published_date=item.published_date,
            source=item.source,
            domain=item.domain,
            content_type=content_type,
            tags=item.tags,
            license=license_info,
            word_count=len(clean_content.split()),
            normalized_date=normalized_date,
            clean_content=clean_content,
            extracted_claims=claims,
            metadata=metadata
        )
    
    def normalize_batch(self, items: List[ContentItem]) -> List[NormalizedContent]:
        """Normalize a batch of content items."""
        normalized_items = []
        
        for item in items:
            try:
                normalized = self.normalize_content(item)
                normalized_items.append(normalized)
            except Exception as e:
                log.error(f"Failed to normalize content item: {e}")
                continue
        
        log.info(f"Normalized {len(normalized_items)}/{len(items)} content items")
        return normalized_items

def normalize_content_item(item: ContentItem) -> NormalizedContent:
    """Convenience function to normalize a single content item."""
    normalizer = ContentNormalizer()
    return normalizer.normalize_content(item)

def normalize_content_batch(items: List[ContentItem]) -> List[NormalizedContent]:
    """Convenience function to normalize a batch of content items."""
    normalizer = ContentNormalizer()
    return normalizer.normalize_batch(items)
