"""
External Data Orchestrator

Routes external data intents to appropriate providers and manages caching.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    logging.getLogger(__name__).warning("pytz not available, using UTC timezone only")

from .intent_detector import ExternalDataIntent
from .cache import ExternalDataCache
from .retry import retry_with_backoff
from .rate_limit_tracker import get_rate_limit_tracker
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
        self.rate_limit_tracker = get_rate_limit_tracker()
        self.logger = logging.getLogger(__name__)
        
        # Register default providers
        self._register_default_providers()
        
        # Initialize metrics tracking
        self._init_metrics()
    
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
            self._record_metrics(provider_name=None, success=False, cached=False)
            return None
        
        provider_name = provider.get_provider_name()
        
        # Check rate limit
        can_make_request, rate_limit_error = self.rate_limit_tracker.can_make_request(provider_name)
        if not can_make_request:
            self.logger.warning(f"Rate limit exceeded for {provider_name}: {rate_limit_error}")
            self._record_metrics(provider_name, success=False, cached=False, rate_limited=True)
            return ExternalDataResult(
                data={},
                source=provider_name,
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=rate_limit_error
            )
        
        # Fetch from provider with retry
        try:
            # Record API call
            self.rate_limit_tracker.record_call(provider_name)
            
            # Fetch with retry logic
            result = await retry_with_backoff(
                provider.fetch,
                max_retries=2,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                exceptions=(Exception,),
                intent_type=intent.type,
                params=intent.params
            )
            
            if not result:
                # Retry failed
                self._record_metrics(provider_name, success=False, cached=False)
                return ExternalDataResult(
                    data={},
                    source=provider_name,
                    timestamp=datetime.utcnow(),
                    cached=False,
                    success=False,
                    error_message="All retry attempts failed"
                )
            
            # Cache successful results
            if result.success:
                ttl = provider.get_cache_ttl(intent.type)
                self.cache.set(cache_key, result, ttl)
                self.logger.info(f"Fetched data from {provider_name}, cached with TTL: {ttl}s")
                self._record_metrics(provider_name, success=True, cached=False)
            else:
                self.logger.warning(f"Provider {provider_name} returned error: {result.error_message}")
                self._record_metrics(provider_name, success=False, cached=False)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching from provider {provider_name}: {e}", exc_info=True)
            self._record_metrics(provider_name, success=False, cached=False)
            return ExternalDataResult(
                data={},
                source=provider_name,
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
    
    def format_response(self, result: ExternalDataResult, query: str, detected_lang: str = "en") -> str:
        """
        Format API result into StillMe response format
        
        Args:
            result: ExternalDataResult from provider
            query: Original user query
            detected_lang: Detected language code (default: 'en')
            
        Returns:
            Formatted response string with source attribution
        """
        if not result.success:
            # Return error message with transparency (in user's language)
            if detected_lang == "vi":
                return (
                    f"StillMe không thể truy cập {result.source} API ngay bây giờ. "
                    f"Lỗi: {result.error_message}. "
                    f"Bạn có thể thử lại sau, hoặc StillMe có thể cố gắng trả lời bằng kiến thức RAG."
                )
            else:
                return (
                    f"StillMe cannot access {result.source} API right now. "
                    f"Error: {result.error_message}. "
                    f"You can try again later, or StillMe can attempt to answer using RAG knowledge."
                )
        
        # Format based on intent type
        if result.data.get("location"):  # Weather
            return self._format_weather_response(result, detected_lang)
        elif result.data.get("articles"):  # News
            return self._format_news_response(result, detected_lang)
        else:
            # Generic format
            return self._format_generic_response(result, detected_lang)
    
    def _format_weather_response(self, result: ExternalDataResult, detected_lang: str = "en") -> str:
        """Format weather data response"""
        
        data = result.data
        location = data.get("location", "Unknown location")
        temp = data.get("temperature")
        humidity = data.get("humidity")
        description = data.get("weather_description", "Unknown")
        
        # Convert UTC to local timezone
        if PYTZ_AVAILABLE:
            try:
                local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                local_time = result.timestamp.replace(tzinfo=timezone.utc).astimezone(local_tz)
                timestamp_str_local = local_time.strftime("%Y-%m-%d %H:%M")
                timestamp_str_utc = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
                timestamp_display = f"{timestamp_str_local} ({timestamp_str_utc})"
            except Exception:
                timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        else:
            timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        
        cache_status = " (đã cache)" if result.cached else "" if detected_lang == "vi" else " (cached)" if result.cached else ""
        
        if detected_lang == "vi":
            response = f"Theo {result.source} API (lấy lúc {timestamp_display}){cache_status}:\n\n"
            response += f"**Thời tiết ở {location}:**\n"
            response += f"- Nhiệt độ: {temp}°C\n" if temp is not None else ""
            response += f"- Điều kiện: {description}\n"
            response += f"- Độ ẩm: {humidity}%\n" if humidity is not None else ""
            response += f"\n[Nguồn: {result.source} | Thời gian: {result.timestamp.isoformat()}Z"
            if result.cached:
                response += f" | Đã cache: Có"
            response += " | Đã xác thực: Có (dữ liệu từ API)]"
        else:
            response = f"According to {result.source} API (retrieved at {timestamp_display}){cache_status}:\n\n"
            response += f"**Weather in {location}:**\n"
            response += f"- Temperature: {temp}°C\n" if temp is not None else ""
            response += f"- Condition: {description}\n"
            response += f"- Humidity: {humidity}%\n" if humidity is not None else ""
            response += f"\n[Source: {result.source} | Timestamp: {result.timestamp.isoformat()}Z"
            if result.cached:
                response += f" | Cached: Yes"
            response += " | Validated: Yes (data from API)]"
        
        return response
    
    def _init_metrics(self):
        """Initialize metrics tracking for external data"""
        try:
            from backend.api.metrics_collector import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
        except ImportError:
            self.metrics_collector = None
            self.logger.debug("Metrics collector not available")
    
    def _record_metrics(
        self,
        provider_name: Optional[str],
        success: bool,
        cached: bool,
        rate_limited: bool = False
    ):
        """Record metrics for external data API calls"""
        if not self.metrics_collector:
            return
        
        try:
            # Track external data calls
            endpoint = f"external_data:{provider_name or 'unknown'}"
            status_code = 200 if success else (429 if rate_limited else 500)
            self.metrics_collector.increment_request("EXTERNAL", endpoint, status_code)
            
            # Track cache hits/misses
            if cached:
                # Cache hit - no API call needed
                pass
            else:
                # API call made
                if not success:
                    # Track errors
                    error_key = f"external_data:{provider_name or 'unknown'}:error"
                    self.metrics_collector._error_counters[error_key] = \
                        self.metrics_collector._error_counters.get(error_key, 0) + 1
        except Exception as e:
            self.logger.warning(f"Error recording metrics: {e}")
    
    def _format_news_response(self, result: ExternalDataResult, detected_lang: str = "en") -> str:
        """Format news data response"""
        data = result.data
        query = data.get("query", "news")
        articles = data.get("articles", [])
        total = data.get("total_results", len(articles))
        
        # Convert UTC to local timezone
        if PYTZ_AVAILABLE:
            try:
                local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                local_time = result.timestamp.replace(tzinfo=timezone.utc).astimezone(local_tz)
                timestamp_str_local = local_time.strftime("%Y-%m-%d %H:%M")
                timestamp_str_utc = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
                timestamp_display = f"{timestamp_str_local} ({timestamp_str_utc})"
            except Exception:
                timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        else:
            timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        
        cache_status = " (đã cache)" if result.cached else "" if detected_lang == "vi" else " (cached)" if result.cached else ""
        
        if detected_lang == "vi":
            response = f"Theo {result.source} API (lấy lúc {timestamp_display}){cache_status}:\n\n"
            response += f"**Tin tức về '{query}'** ({total} kết quả tổng cộng):\n\n"
            
            for i, article in enumerate(articles[:5], 1):
                title = article.get("title", "Không có tiêu đề")
                description = article.get("description", "")
                source = article.get("source", "Nguồn không xác định")
                published = article.get("published_at", "")
                url = article.get("url", "")
                
                response += f"{i}. **{title}**\n"
                if description:
                    response += f"   {description[:150]}{'...' if len(description) > 150 else ''}\n"
                response += f"   Nguồn: {source}"
                if published:
                    response += f" | Đăng lúc: {published}"
                if url:
                    response += f"\n   [Đọc thêm]({url})"
                response += "\n\n"
            
            response += f"[Nguồn: {result.source} | Thời gian: {result.timestamp.isoformat()}Z"
            if result.cached:
                response += f" | Đã cache: Có"
            response += " | Đã xác thực: Có (dữ liệu từ API)]"
        else:
            response = f"According to {result.source} API (retrieved at {timestamp_display}){cache_status}:\n\n"
            response += f"**News about '{query}'** ({total} total results):\n\n"
            
            for i, article in enumerate(articles[:5], 1):
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
            response += " | Validated: Yes (data from API)]"
        
        return response
    
    def _init_metrics(self):
        """Initialize metrics tracking for external data"""
        try:
            from backend.api.metrics_collector import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
        except ImportError:
            self.metrics_collector = None
            self.logger.debug("Metrics collector not available")
    
    def _record_metrics(
        self,
        provider_name: Optional[str],
        success: bool,
        cached: bool,
        rate_limited: bool = False
    ):
        """Record metrics for external data API calls"""
        if not self.metrics_collector:
            return
        
        try:
            # Track external data calls
            endpoint = f"external_data:{provider_name or 'unknown'}"
            status_code = 200 if success else (429 if rate_limited else 500)
            self.metrics_collector.increment_request("EXTERNAL", endpoint, status_code)
            
            # Track cache hits/misses
            if cached:
                # Cache hit - no API call needed
                pass
            else:
                # API call made
                if not success:
                    # Track errors
                    error_key = f"external_data:{provider_name or 'unknown'}:error"
                    self.metrics_collector._error_counters[error_key] = \
                        self.metrics_collector._error_counters.get(error_key, 0) + 1
        except Exception as e:
            self.logger.warning(f"Error recording metrics: {e}")
    
    def _format_generic_response(self, result: ExternalDataResult, detected_lang: str = "en") -> str:
        """Format generic response"""
        if PYTZ_AVAILABLE:
            try:
                local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                local_time = result.timestamp.replace(tzinfo=timezone.utc).astimezone(local_tz)
                timestamp_str_local = local_time.strftime("%Y-%m-%d %H:%M")
                timestamp_str_utc = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
                timestamp_display = f"{timestamp_str_local} ({timestamp_str_utc})"
            except Exception:
                timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        else:
            timestamp_display = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        
        cache_status = " (đã cache)" if result.cached else "" if detected_lang == "vi" else " (cached)" if result.cached else ""
        
        if detected_lang == "vi":
            response = f"Theo {result.source} API (lấy lúc {timestamp_display}){cache_status}:\n\n"
            response += f"Dữ liệu: {result.data}\n\n"
            response += f"[Nguồn: {result.source} | Thời gian: {result.timestamp.isoformat()}Z"
            if result.cached:
                response += f" | Đã cache: Có"
            response += " | Đã xác thực: Có (dữ liệu từ API)]"
        else:
            response = f"According to {result.source} API (retrieved at {timestamp_display}){cache_status}:\n\n"
            response += f"Data: {result.data}\n\n"
            response += f"[Source: {result.source} | Timestamp: {result.timestamp.isoformat()}Z"
            if result.cached:
                response += f" | Cached: Yes"
            response += " | Validated: Yes (data from API)]"
        
        return response
    
    def _init_metrics(self):
        """Initialize metrics tracking for external data"""
        try:
            from backend.api.metrics_collector import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
        except ImportError:
            self.metrics_collector = None
            self.logger.debug("Metrics collector not available")
    
    def _record_metrics(
        self,
        provider_name: Optional[str],
        success: bool,
        cached: bool,
        rate_limited: bool = False
    ):
        """Record metrics for external data API calls"""
        if not self.metrics_collector:
            return
        
        try:
            # Track external data calls
            endpoint = f"external_data:{provider_name or 'unknown'}"
            status_code = 200 if success else (429 if rate_limited else 500)
            self.metrics_collector.increment_request("EXTERNAL", endpoint, status_code)
            
            # Track cache hits/misses
            if cached:
                # Cache hit - no API call needed
                pass
            else:
                # API call made
                if not success:
                    # Track errors
                    error_key = f"external_data:{provider_name or 'unknown'}:error"
                    self.metrics_collector._error_counters[error_key] = \
                        self.metrics_collector._error_counters.get(error_key, 0) + 1
        except Exception as e:
            self.logger.warning(f"Error recording metrics: {e}")

