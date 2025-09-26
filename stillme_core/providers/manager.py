"""
Provider manager for StillMe AI Framework.
Handles provider initialization, health monitoring, and fallback.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .llm_base import LLMProviderManager, LLMRequest, LLMResponse, FallbackStrategy
from .factory import ProviderFactory
from .llm_base import ProviderConfig

logger = logging.getLogger(__name__)


class StillMeProviderManager:
    """High-level provider manager for StillMe AI Framework."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._manager: Optional[LLMProviderManager] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the provider manager."""
        try:
            # Get provider configurations
            provider_configs = self.config.get("providers", [])
            if not provider_configs:
                logger.warning("No provider configurations found")
                return False
            
            # Create providers
            providers = ProviderFactory.create_providers_from_config(provider_configs)
            if not providers:
                logger.error("No providers could be created")
                return False
            
            # Create manager
            fallback_strategy = FallbackStrategy(
                self.config.get("fallback_strategy", "round_robin")
            )
            self._manager = LLMProviderManager(providers, fallback_strategy)
            
            # Initialize all providers
            if not await self._manager.initialize_all():
                logger.error("Failed to initialize any providers")
                return False
            
            # Start health monitoring
            self._start_health_monitoring()
            
            self._initialized = True
            logger.info(f"Provider manager initialized with {len(providers)} providers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize provider manager: {e}")
            return False
    
    async def generate(self, request: LLMRequest, preferred_provider: Optional[str] = None) -> LLMResponse:
        """Generate a response using the best available provider."""
        if not self._initialized or not self._manager:
            raise RuntimeError("Provider manager not initialized")
        
        return await self._manager.generate(request, preferred_provider)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        if not self._initialized or not self._manager:
            return {"error": "Provider manager not initialized"}
        
        return await self._manager.health_check_all()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        if not self._initialized or not self._manager:
            return {"error": "Provider manager not initialized"}
        
        return self._manager.get_provider_status()
    
    def _start_health_monitoring(self):
        """Start background health monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            return
        
        self._health_check_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Started health monitoring")
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while True:
            try:
                if self._manager:
                    await self._manager.health_check_all()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def cleanup(self):
        """Cleanup the provider manager."""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._manager:
            await self._manager.cleanup_all()
        
        self._initialized = False
        logger.info("Provider manager cleaned up")


# Global provider manager instance
_provider_manager: Optional[StillMeProviderManager] = None


async def get_provider_manager() -> StillMeProviderManager:
    """Get the global provider manager instance."""
    global _provider_manager
    
    if _provider_manager is None:
        _provider_manager = StillMeProviderManager()
        await _provider_manager.initialize()
    
    return _provider_manager


async def cleanup_provider_manager():
    """Cleanup the global provider manager."""
    global _provider_manager
    
    if _provider_manager:
        await _provider_manager.cleanup()
        _provider_manager = None
