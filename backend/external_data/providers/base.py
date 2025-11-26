"""
Base classes for External Data Providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExternalDataResult:
    """Result from external API"""
    data: Dict[str, Any]  # Processed/structured data
    source: str  # API name (e.g., "Open-Meteo")
    timestamp: datetime  # When data was retrieved
    cached: bool  # Whether data was from cache
    cache_ttl: Optional[int] = None  # Cache TTL in seconds
    raw_response: Optional[str] = None  # Raw JSON for audit
    success: bool = True  # Whether fetch was successful
    error_message: Optional[str] = None  # Error message if failed


class ExternalDataProvider(ABC):
    """Base class for external data providers"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        Initialize provider
        
        Args:
            api_key: Optional API key for the provider
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name (e.g., 'Open-Meteo', 'GNews')"""
        pass
    
    @abstractmethod
    def supports(self, intent_type: str, params: Dict[str, Any]) -> bool:
        """
        Check if this provider supports the intent
        
        Args:
            intent_type: Type of intent (e.g., 'weather', 'news')
            params: Intent parameters
            
        Returns:
            True if provider supports this intent
        """
        pass
    
    @abstractmethod
    async def fetch(self, intent_type: str, params: Dict[str, Any]) -> ExternalDataResult:
        """
        Fetch data from external API
        
        Args:
            intent_type: Type of intent (e.g., 'weather', 'news')
            params: Intent parameters (e.g., {'location': 'Hanoi'})
            
        Returns:
            ExternalDataResult with data or error
        """
        pass
    
    def get_cache_key(self, intent_type: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key for this intent
        
        Args:
            intent_type: Type of intent
            params: Intent parameters
            
        Returns:
            Cache key string
        """
        # Default: provider_name:type:params_hash
        import hashlib
        import json
        
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{self.get_provider_name()}:{intent_type}:{params_hash}"
    
    def get_cache_ttl(self, intent_type: str) -> int:
        """
        Get cache TTL in seconds for this intent type
        
        Args:
            intent_type: Type of intent
            
        Returns:
            TTL in seconds
        """
        # Default TTLs (can be overridden by subclasses)
        ttl_map = {
            "weather": 15 * 60,  # 15 minutes
            "news": 2 * 60 * 60,  # 2 hours
            "fx_rate": 10 * 60,  # 10 minutes
            "sports": 60 * 60,  # 1 hour
        }
        return ttl_map.get(intent_type, 60 * 60)  # Default: 1 hour

