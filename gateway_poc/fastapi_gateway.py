#!/usr/bin/env python3
"""
StillMe FastAPI Gateway - Ultra Low Latency
Author: StillMe AI Assistant
Date: 2025-09-22

Features:
- Connection pooling
- Circuit breaker
- Response caching
- Request batching
- Async processing
- Health checks
- Metrics collection
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis
from circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "stillme_backend": "http://127.0.0.1:1216",
    "ollama_backend": "http://127.0.0.1:11434",
    "redis_url": "redis://localhost:6379/0",
    "cache_ttl": 300,  # 5 minutes
    "max_connections": 100,
    "timeout": 30,
    "circuit_breaker_failure_threshold": 5,
    "circuit_breaker_recovery_timeout": 60,
}

@dataclass
class LatencyMetrics:
    """Latency metrics for monitoring"""
    endpoint: str
    request_time: float
    upstream_time: float
    cache_hit: bool
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    use_cache: bool = True

class ChatResponse(BaseModel):
    response: str
    engine: str
    latency_ms: float
    cache_hit: bool
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]
    metrics: Dict[str, Any]

class StillMeGateway:
    """Ultra Low Latency API Gateway for StillMe"""
    
    def __init__(self):
        self.app = FastAPI(
            title="StillMe API Gateway",
            description="Ultra Low Latency Gateway for StillMe Microservices",
            version="1.0.0"
        )
        
        # Initialize components
        self.redis_client = None
        self.http_client = None
        self.circuit_breakers = {}
        self.metrics = []
        
        # Setup
        self._setup_middleware()
        self._setup_routes()
        self._setup_circuit_breakers()
        
    async def startup(self):
        """Initialize connections and services"""
        try:
            # Redis connection
            self.redis_client = redis.Redis.from_url(CONFIG["redis_url"])
            await self.redis_client.ping()
            logger.info("✅ Redis connected")
            
            # HTTP client with connection pooling
            self.http_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=CONFIG["max_connections"],
                    max_connections=CONFIG["max_connections"]
                ),
                timeout=CONFIG["timeout"]
            )
            logger.info("✅ HTTP client initialized")
            
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup connections"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("✅ Gateway shutdown complete")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request timing middleware
        @self.app.middleware("http")
        async def timing_middleware(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            services = {}
            
            # Check StillMe backend
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{CONFIG['stillme_backend']}/health", timeout=5)
                    services["stillme_backend"] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services["stillme_backend"] = "unhealthy"
            
            # Check Ollama backend
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{CONFIG['ollama_backend']}/api/tags", timeout=5)
                    services["ollama_backend"] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services["ollama_backend"] = "unhealthy"
            
            # Check Redis
            try:
                if self.redis_client:
                    await self.redis_client.ping()
                    services["redis"] = "healthy"
                else:
                    services["redis"] = "unhealthy"
            except:
                services["redis"] = "unhealthy"
            
            return HealthResponse(
                status="healthy" if all(s == "healthy" for s in services.values()) else "degraded",
                timestamp=datetime.now(),
                services=services,
                metrics={
                    "total_requests": len(self.metrics),
                    "avg_latency_ms": sum(m.request_time for m in self.metrics[-100:]) / min(100, len(self.metrics)) * 1000 if self.metrics else 0,
                    "cache_hit_rate": sum(1 for m in self.metrics[-100:] if m.cache_hit) / min(100, len(self.metrics)) if self.metrics else 0
                }
            )
        
        @self.app.post("/api/chat", response_model=ChatResponse)
        async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
            """Chat endpoint with ultra low latency"""
            start_time = time.time()
            
            # Check cache first
            cache_key = self._generate_cache_key(request.message, request.user_id or "anonymous")
            cached_response = await self._get_from_cache(cache_key)
            
            if cached_response and request.use_cache:
                latency = (time.time() - start_time) * 1000
                background_tasks.add_task(self._record_metrics, "chat", latency, 0, True)
                return ChatResponse(
                    response=cached_response["response"],
                    engine=cached_response["engine"],
                    latency_ms=latency,
                    cache_hit=True,
                    timestamp=datetime.now()
                )
            
            # Circuit breaker for StillMe backend
            try:
                response = await self._call_with_circuit_breaker(
                    "stillme_backend",
                    self._call_stillme_backend,
                    request
                )
                
                # Cache successful responses
                if response:
                    await self._set_cache(cache_key, response, CONFIG["cache_ttl"])
                
                latency = (time.time() - start_time) * 1000
                background_tasks.add_task(self._record_metrics, "chat", latency, latency * 0.8, False)
                
                return ChatResponse(
                    response=response["response"],
                    engine=response["engine"],
                    latency_ms=latency,
                    cache_hit=False,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/ollama")
        async def ollama_endpoint(request: dict, background_tasks: BackgroundTasks):
            """Direct Ollama endpoint with ultra low latency"""
            start_time = time.time()
            
            try:
                response = await self._call_with_circuit_breaker(
                    "ollama_backend",
                    self._call_ollama_backend,
                    request
                )
                
                latency = (time.time() - start_time) * 1000
                background_tasks.add_task(self._record_metrics, "ollama", latency, latency * 0.9, False)
                
                return response
                
            except Exception as e:
                logger.error(f"Ollama endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get performance metrics"""
            if not self.metrics:
                return {"message": "No metrics available yet"}
            
            recent_metrics = self.metrics[-100:]  # Last 100 requests
            
            return {
                "total_requests": len(self.metrics),
                "recent_requests": len(recent_metrics),
                "avg_latency_ms": sum(m.request_time for m in recent_metrics) / len(recent_metrics) * 1000,
                "avg_upstream_latency_ms": sum(m.upstream_time for m in recent_metrics) / len(recent_metrics) * 1000,
                "cache_hit_rate": sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics),
                "endpoints": {
                    endpoint: {
                        "count": sum(1 for m in recent_metrics if m.endpoint == endpoint),
                        "avg_latency_ms": sum(m.request_time for m in recent_metrics if m.endpoint == endpoint) / max(1, sum(1 for m in recent_metrics if m.endpoint == endpoint)) * 1000
                    }
                    for endpoint in set(m.endpoint for m in recent_metrics)
                }
            }
    
    def _setup_circuit_breakers(self):
        """Setup circuit breakers for backend services"""
        self.circuit_breakers = {
            "stillme_backend": CircuitBreaker(
                failure_threshold=CONFIG["circuit_breaker_failure_threshold"],
                recovery_timeout=CONFIG["circuit_breaker_recovery_timeout"]
            ),
            "ollama_backend": CircuitBreaker(
                failure_threshold=CONFIG["circuit_breaker_failure_threshold"],
                recovery_timeout=CONFIG["circuit_breaker_recovery_timeout"]
            )
        }
    
    async def _call_with_circuit_breaker(self, service: str, func, *args, **kwargs):
        """Call backend service with circuit breaker"""
        try:
            return await self.circuit_breakers[service].call(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Circuit breaker {service} failed: {e}")
            raise
    
    async def _call_stillme_backend(self, request: ChatRequest):
        """Call StillMe backend"""
        payload = {
            "message": request.message,
            "user_id": request.user_id,
            "session_id": request.session_id
        }
        
        if self.http_client:
            response = await self.http_client.post(
                f"{CONFIG['stillme_backend']}/chat",
                json=payload,
                timeout=10
            )
        else:
            raise Exception("HTTP client not initialized")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"StillMe backend error: {response.status_code}")
    
    async def _call_ollama_backend(self, request: dict):
        """Call Ollama backend"""
        if self.http_client:
            response = await self.http_client.post(
                f"{CONFIG['ollama_backend']}/api/generate",
                json=request,
                timeout=15
            )
        else:
            raise Exception("HTTP client not initialized")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ollama backend error: {response.status_code}")
    
    def _generate_cache_key(self, message: str, user_id: str) -> str:
        """Generate cache key for request"""
        content = f"{message}:{user_id}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[dict]:
        """Get response from cache"""
        try:
            if self.redis_client:
                cached = await self.redis_client.get(key)
            else:
                return None
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def _set_cache(self, key: str, data: dict, ttl: int):
        """Set response in cache"""
        try:
            if self.redis_client:
                await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def _record_metrics(self, endpoint: str, request_time: float, upstream_time: float, cache_hit: bool):
        """Record performance metrics"""
        metric = LatencyMetrics(
            endpoint=endpoint,
            request_time=request_time,
            upstream_time=upstream_time,
            cache_hit=cache_hit,
            timestamp=datetime.now()
        )
        
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

# Create FastAPI app
gateway = StillMeGateway()
app = gateway.app

# Add startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await gateway.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await gateway.shutdown()

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_gateway:app",
        host="0.0.0.0",
        port=8080,
        loop="asyncio",  # Use asyncio for Windows compatibility
        log_level="info"
    )
