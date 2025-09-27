"""
StillMe RSS Registry
Allowlist-based RSS connector registry for trusted sources.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

log = logging.getLogger(__name__)

@dataclass
class RSSSource:
    """Represents an RSS source configuration."""
    name: str
    url: str
    domain: str
    category: str
    reputation_score: float
    description: str
    enabled: bool = True
    max_items: int = 20
    update_frequency: str = "daily"  # daily, weekly, monthly
    content_type: str = "research"  # research, blog, news, documentation

class RSSRegistry:
    """Registry of allowed RSS sources."""
    
    def __init__(self):
        self.sources: Dict[str, RSSSource] = {}
        self._initialize_default_sources()
    
    def _initialize_default_sources(self):
        """Initialize default allowlist sources."""
        default_sources = [
            # Academic Sources
            RSSSource(
                name="arXiv AI Papers",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending",
                domain="arxiv.org",
                category="academic",
                reputation_score=0.95,
                description="Latest AI research papers from arXiv",
                content_type="research"
            ),
            RSSSource(
                name="arXiv Machine Learning",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending",
                domain="arxiv.org",
                category="academic",
                reputation_score=0.95,
                description="Latest ML research papers from arXiv",
                content_type="research"
            ),
            RSSSource(
                name="arXiv NLP Papers",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.CL&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending",
                domain="arxiv.org",
                category="academic",
                reputation_score=0.95,
                description="Latest NLP research papers from arXiv",
                content_type="research"
            ),
            
            # Industry Research
            RSSSource(
                name="OpenAI Blog",
                url="https://openai.com/blog/rss.xml",
                domain="openai.com",
                category="industry",
                reputation_score=0.90,
                description="OpenAI research blog and announcements",
                content_type="blog"
            ),
            RSSSource(
                name="DeepMind Blog",
                url="https://deepmind.com/blog/feed/basic/",
                domain="deepmind.com",
                category="industry",
                reputation_score=0.90,
                description="DeepMind research blog and publications",
                content_type="blog"
            ),
            
            # Technical Documentation
            RSSSource(
                name="Hugging Face Blog",
                url="https://huggingface.co/blog/feed.xml",
                domain="huggingface.co",
                category="technical",
                reputation_score=0.80,
                description="Hugging Face technical blog and tutorials",
                content_type="blog"
            ),
            RSSSource(
                name="PyTorch Blog",
                url="https://pytorch.org/blog/feed.xml",
                domain="pytorch.org",
                category="technical",
                reputation_score=0.85,
                description="PyTorch development blog and tutorials",
                content_type="blog"
            ),
            
            # AI Ethics and Safety
            RSSSource(
                name="AI Safety Papers",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+all:safety&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending",
                domain="arxiv.org",
                category="ethics",
                reputation_score=0.95,
                description="AI safety and ethics research papers",
                content_type="research"
            ),
            RSSSource(
                name="AI Ethics Papers",
                url="http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+all:ethics&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending",
                domain="arxiv.org",
                category="ethics",
                reputation_score=0.95,
                description="AI ethics and fairness research papers",
                content_type="research"
            )
        ]
        
        for source in default_sources:
            self.sources[source.name] = source
        
        log.info(f"Initialized RSS registry with {len(self.sources)} sources")
    
    def get_source(self, name: str) -> Optional[RSSSource]:
        """Get a source by name."""
        return self.sources.get(name)
    
    def get_sources_by_domain(self, domain: str) -> List[RSSSource]:
        """Get all sources for a domain."""
        return [source for source in self.sources.values() 
                if source.domain == domain and source.enabled]
    
    def get_sources_by_category(self, category: str) -> List[RSSSource]:
        """Get all sources for a category."""
        return [source for source in self.sources.values() 
                if source.category == category and source.enabled]
    
    def get_enabled_sources(self) -> List[RSSSource]:
        """Get all enabled sources."""
        return [source for source in self.sources.values() if source.enabled]
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is in the allowlist."""
        return any(source.domain == domain and source.enabled 
                  for source in self.sources.values())
    
    def get_domains(self) -> List[str]:
        """Get all allowed domains."""
        return list(set(source.domain for source in self.sources.values() 
                       if source.enabled))
    
    def add_source(self, source: RSSSource) -> bool:
        """Add a new source to the registry."""
        try:
            # Validate domain
            parsed = urlparse(source.url)
            if not parsed.netloc:
                log.error(f"Invalid URL for source {source.name}: {source.url}")
                return False
            
            # Check if domain is already allowed
            if not self.is_domain_allowed(parsed.netloc):
                log.warning(f"Domain {parsed.netloc} not in allowlist for {source.name}")
                return False
            
            self.sources[source.name] = source
            log.info(f"Added source: {source.name} ({source.domain})")
            return True
            
        except Exception as e:
            log.error(f"Failed to add source {source.name}: {e}")
            return False
    
    def remove_source(self, name: str) -> bool:
        """Remove a source from the registry."""
        if name in self.sources:
            del self.sources[name]
            log.info(f"Removed source: {name}")
            return True
        return False
    
    def enable_source(self, name: str) -> bool:
        """Enable a source."""
        if name in self.sources:
            self.sources[name].enabled = True
            log.info(f"Enabled source: {name}")
            return True
        return False
    
    def disable_source(self, name: str) -> bool:
        """Disable a source."""
        if name in self.sources:
            self.sources[name].enabled = False
            log.info(f"Disabled source: {name}")
            return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get registry statistics."""
        enabled_sources = self.get_enabled_sources()
        
        stats = {
            "total_sources": len(self.sources),
            "enabled_sources": len(enabled_sources),
            "domains": len(self.get_domains()),
            "categories": len(set(source.category for source in enabled_sources)),
            "avg_reputation": sum(source.reputation_score for source in enabled_sources) / len(enabled_sources) if enabled_sources else 0,
            "sources_by_category": {},
            "sources_by_domain": {}
        }
        
        # Count by category
        for source in enabled_sources:
            category = source.category
            if category not in stats["sources_by_category"]:
                stats["sources_by_category"][category] = 0
            stats["sources_by_category"][category] += 1
        
        # Count by domain
        for source in enabled_sources:
            domain = source.domain
            if domain not in stats["sources_by_domain"]:
                stats["sources_by_domain"][domain] = 0
            stats["sources_by_domain"][domain] += 1
        
        return stats
    
    def validate_allowlist(self, policy_domains: List[str]) -> Dict:
        """Validate registry against policy allowlist."""
        registry_domains = set(self.get_domains())
        policy_domains_set = set(policy_domains)
        
        return {
            "valid": registry_domains.issubset(policy_domains_set),
            "registry_domains": list(registry_domains),
            "policy_domains": policy_domains,
            "extra_domains": list(registry_domains - policy_domains_set),
            "missing_domains": list(policy_domains_set - registry_domains)
        }

# Global registry instance
_registry = None

def get_rss_registry() -> RSSRegistry:
    """Get global RSS registry instance."""
    global _registry
    if _registry is None:
        _registry = RSSRegistry()
    return _registry

def validate_source_url(url: str) -> bool:
    """Validate if a URL is from an allowed domain."""
    try:
        parsed = urlparse(url)
        registry = get_rss_registry()
        return registry.is_domain_allowed(parsed.netloc)
    except Exception:
        return False
