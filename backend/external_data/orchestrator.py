"""
External Data Orchestrator

Routes external data intents to appropriate providers and manages caching.
"""

import logging
from typing import List, Optional
from datetime import datetime

from .intent_detector import ExternalDataIntent
from .cache import ExternalDataCache
from .providers.base import ExternalDataProvider, ExternalDataResult
from .providers.weather import WeatherProvider
from .providers.news import NewsProvider

logger = logging.getLogger(__name__)


class ExternalDataOrchestrator:
    """Orchestrates multiple external data providers"""
    
    def __init__(self):
        """Initialize orchestrator with providers and cache"""
        self.providers: List[ExternalDataProvider] = []
        self.cache = ExternalDataCache()
        self.logger = logging.getLogger(__name__)
        
        # Register default providers
        self._register_default_providers()
    
    def _register_default_providers(self):
        """Register default providers"""
        # Weather provider (no API key needed)
        weather_provider = WeatherProvider()
        self.register_provider(weather_provider)
        
        # News provider (needs GNEWS_API_KEY)
        news_provider = NewsProvider()
        self.register_provider(news_provider)
        
        self.logger.info(f"Registered {len(self.providers)} external data providers")
    
    def register_provider(self, provider: ExternalDataProvider):
        """Register a provider"""
        self.providers.append(provider)
        self.logger.debug(f"Registered provider: {provider.get_provider_name()}")
    
    async def route(self, intent: ExternalDataIntent) -> Optional[ExternalDataResult]:
        """
        Route intent to appropriate provider
        
        Args:
            intent: ExternalDataIntent with type and params
            
        Returns:
            ExternalDataResult if successful, None if no provider supports or error
        """
        if not intent:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(intent)
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            self.logger.info(f"Cache hit for intent: {intent.type}")
            return cached_result
        
        # Find provider that supports this intent
        provider = self._find_provider(intent)
        
        if not provider:
            self.logger.warning(f"No provider found for intent type: {intent.type}")
            return None
        
        # Fetch from provider
        try:
            result = await provider.fetch(intent.type, intent.params)
            
            # Cache successful results
            if result.success:
                ttl = provider.get_cache_ttl(intent.type)
                self.cache.set(cache_key, result, ttl)
                self.logger.info(f"Fetched data from {provider.get_provider_name()}, cached with TTL: {ttl}s")
            else:
                self.logger.warning(f"Provider {provider.get_provider_name()} returned error: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching from provider {provider.get_provider_name()}: {e}", exc_info=True)
            return ExternalDataResult(
                data={},
                source=provider.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Exception: {str(e)}"
            )
    
    def _find_provider(self, intent: ExternalDataIntent) -> Optional[ExternalDataProvider]:
        """Find provider that supports the intent"""
        for provider in self.providers:
            if provider.supports(intent.type, intent.params):
                return provider
        return None
    
    def _get_cache_key(self, intent: ExternalDataIntent) -> str:
        """Generate cache key for intent"""
        # Use first provider that supports this intent to generate cache key
        provider = self._find_provider(intent)
        if provider:
            return provider.get_cache_key(intent.type, intent.params)
        
        # Fallback: simple key
        import hashlib
        import json
        params_str = json.dumps(intent.params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{intent.type}:{params_hash}"
    
    def format_response(self, result: ExternalDataResult, query: str) -> str:
        """
        Format API result into StillMe response format
        
        Args:
            result: ExternalDataResult from provider
            query: Original user query
            
        Returns:
            Formatted response string with source attribution
        """
        if not result.success:
            # Return error message with transparency
            return (
                f"StillMe cannot access {result.source} API right now. "
                f"Error: {result.error_message}. "
                f"You can try again later, or StillMe can attempt to answer using RAG knowledge."
            )
        
        # Format based on intent type
        if result.data.get("location"):  # Weather
            return self._format_weather_response(result)
        elif result.data.get("articles"):  # News
            return self._format_news_response(result)
        else:
            # Generic format
            return self._format_generic_response(result)
    
    def _format_weather_response(self, result: ExternalDataResult) -> str:
        """Format weather data response"""
        data = result.data
        location = data.get("location", "Unknown location")
        temp = data.get("temperature")
        humidity = data.get("humidity")
        description = data.get("weather_description", "Unknown")
        
        # Format timestamp
        timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        cache_status = " (cached)" if result.cached else ""
        
        response = f"According to {result.source} API (retrieved at {timestamp_str}){cache_status}:\n\n"
        response += f"**Weather in {location}:**\n"
        response += f"- Temperature: {temp}°C\n" if temp is not None else ""
        response += f"- Condition: {description}\n"
        response += f"- Humidity: {humidity}%\n" if humidity is not None else ""
        response += f"\n[Source: {result.source} | Timestamp: {result.timestamp.isoformat()}Z"
        if result.cached:
            response += f" | Cached: Yes"
        response += "]"
        
        return response
    
    def _format_news_response(self, result: ExternalDataResult) -> str:
        """Format news data response"""
        data = result.data
        query = data.get("query", "news")
        articles = data.get("articles", [])
        total = data.get("total_results", len(articles))
        
        # Format timestamp
        timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        cache_status = " (cached)" if result.cached else ""
        
        response = f"According to {result.source} API (retrieved at {timestamp_str}){cache_status}:\n\n"
        response += f"**News about '{query}'** ({total} total results):\n\n"
        
        for i, article in enumerate(articles[:5], 1):  # Show max 5 articles
            title = article.get("title", "No title")
            description = article.get("description", "")
            source = article.get("source", "Unknown source")
            published = article.get("published_at", "")
            url = article.get("url", "")
            
            response += f"{i}. **{title}**\n"
            if description:
                response += f"   {description[:150]}{'...' if len(description) > 150 else ''}\n"
            response += f"   Source: {source}"
            if published:
                response += f" | Published: {published}"
            if url:
                response += f"\n   [Read more]({url})"
            response += "\n\n"
        
        response += f"[Source: {result.source} | Timestamp: {result.timestamp.isoformat()}Z"
        if result.cached:
            response += f" | Cached: Yes"
        response += "]"
        
        return response
    
    def _format_generic_response(self, result: ExternalDataResult) -> str:
        """Format generic response"""
        timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        cache_status = " (cached)" if result.cached else ""
        
        response = f"According to {result.source} API (retrieved at {timestamp_str}){cache_status}:\n\n"
        response += f"Data: {result.data}\n\n"
        response += f"[Source: {result.source} | Timestamp: {result.timestamp.isoformat()}Z"
        if result.cached:
            response += f" | Cached: Yes"
        response += "]"
        
        return response

