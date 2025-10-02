#!/usr/bin/env python3
"""
🚀 Enhanced StillMe Gateway - POC Version
Enhanced FastAPI Gateway with improved performance, security, and monitoring
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from middleware.circuit_breaker import CircuitBreakerMiddleware
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.request_logger import RequestLoggerMiddleware
from prometheus_client import generate_latest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import existing modules
from api.routes import auth, devices, health, messages

# Import enhanced modules
from config import EnhancedSettings
from core.message_protocol import MessageProtocol, MessageType
from core.websocket_manager import WebSocketManager
from monitoring.health import HealthChecker
from monitoring.metrics import MetricsCollector
from security.auth import AuthManager
from security.validator import RequestValidator

# Initialize enhanced settings
settings = EnhancedSettings()

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
auth_manager = AuthManager()
request_validator = RequestValidator()
websocket_manager = WebSocketManager()

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

# Database connection
database_engine = None
database_session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager"""
    global redis_pool, redis_client, database_engine, database_session

    print("🚀 Starting Enhanced StillMe Gateway...")

    # Initialize Redis connection pool
    redis_pool = redis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_POOL_SIZE,
        retry_on_timeout=True,
    )
    redis_client = redis.Redis(connection_pool=redis_pool)

    # Test Redis connection
    await redis_client.ping()
    print("✅ Redis connection pool initialized")

    # Initialize database connection pool
    database_engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    database_session = sessionmaker(
        database_engine, class_=AsyncSession, expire_on_commit=False
    )
    print("✅ Database connection pool initialized")

    # Initialize monitoring
    await metrics_collector.initialize()
    await health_checker.initialize()
    print("✅ Monitoring initialized")

    # Initialize security
    await auth_manager.initialize()
    await request_validator.initialize()
    print("✅ Security initialized")

    print("🎉 Enhanced StillMe Gateway started successfully!")

    yield

    # Cleanup
    print("🔄 Shutting down Enhanced StillMe Gateway...")

    if redis_client:
        await redis_client.close()
    if redis_pool:
        await redis_pool.disconnect()

    if database_engine:
        await database_engine.dispose()

    await metrics_collector.cleanup()
    await health_checker.cleanup()
    await auth_manager.cleanup()
    await request_validator.cleanup()

    print("✅ Enhanced StillMe Gateway shutdown complete")


# Create enhanced FastAPI app
app = FastAPI(
    title="Enhanced StillMe Gateway",
    description="Enhanced communication hub with improved performance, security, and monitoring",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add enhanced middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CircuitBreakerMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(RequestLoggerMiddleware)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = f"req_{int(time.time() * 1000)}_{id(request)}"
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Response time middleware
@app.middleware("http")
async def add_response_time(request: Request, call_next):
    """Add response time to headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Response-Time"] = str(process_time)
    return response


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])


# Enhanced WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Enhanced WebSocket endpoint with monitoring and security"""
    # Validate client ID
    if not request_validator.validate_client_id(client_id):
        await websocket.close(code=4004, reason="Invalid client ID")
        return

    # Authenticate WebSocket connection
    if not await auth_manager.authenticate_websocket(websocket, client_id):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Connect with monitoring
    await websocket_manager.connect(websocket, client_id)
    metrics_collector.increment_websocket_connections()

    try:
        while True:
            # Receive message with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=settings.WS_MESSAGE_TIMEOUT
                )
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {"type": "error", "message": "Message timeout"}
                )
                continue

            # Validate message
            if not request_validator.validate_websocket_message(data):
                await websocket.send_json(
                    {"type": "error", "message": "Invalid message format"}
                )
                continue

            # Process message
            message = MessageProtocol.parse(data)
            metrics_collector.increment_websocket_messages()

            # Route message based on type
            if message.type == MessageType.COMMAND:
                result = await process_command_with_monitoring(message, client_id)
                await websocket_manager.send_to_client(client_id, result)

            elif message.type == MessageType.STATUS:
                await process_status_with_monitoring(message, client_id)

            elif message.type == MessageType.HEARTBEAT:
                await process_heartbeat_with_monitoring(message, client_id)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id)
        metrics_collector.decrement_websocket_connections()
        print(f"Client {client_id} disconnected")

    except Exception as e:
        await websocket_manager.disconnect(client_id)
        metrics_collector.decrement_websocket_connections()
        metrics_collector.increment_websocket_errors()
        print(f"WebSocket error for client {client_id}: {e}")


async def process_command_with_monitoring(
    message: MessageProtocol, client_id: str
) -> dict[str, Any]:
    """Process command with monitoring and error handling"""
    start_time = time.time()

    try:
        # Add to Redis for persistence
        await redis_client.setex(
            f"command:{client_id}:{message.id}",
            3600,  # 1 hour TTL
            message.to_json(),
        )

        # Process command (simplified for POC)
        result = {
            "id": message.id,
            "type": "command_response",
            "content": f"Processed command: {message.content}",
            "timestamp": time.time(),
            "client_id": client_id,
        }

        # Record metrics
        processing_time = time.time() - start_time
        metrics_collector.record_command_processing_time(processing_time)
        metrics_collector.increment_commands_processed()

        return result

    except Exception as e:
        metrics_collector.increment_command_errors()
        return {
            "id": message.id,
            "type": "error",
            "content": f"Command processing failed: {str(e)}",
            "timestamp": time.time(),
        }


async def process_status_with_monitoring(message: MessageProtocol, client_id: str):
    """Process status update with monitoring"""
    try:
        # Store status in Redis
        await redis_client.setex(
            f"status:{client_id}",
            300,  # 5 minutes TTL
            message.to_json(),
        )

        # Broadcast status
        status_dict = {
            "id": message.id,
            "type": message.type.value,
            "content": message.content,
            "timestamp": message.timestamp,
            "metadata": message.metadata,
            "client_id": client_id,
        }
        await websocket_manager.broadcast_status(status_dict)

        metrics_collector.increment_status_updates()

    except Exception as e:
        metrics_collector.increment_status_errors()
        print(f"Status processing error: {e}")


async def process_heartbeat_with_monitoring(message: MessageProtocol, client_id: str):
    """Process heartbeat with monitoring"""
    try:
        # Update last seen timestamp
        await redis_client.setex(
            f"heartbeat:{client_id}",
            60,  # 1 minute TTL
            str(time.time()),
        )

        # Send heartbeat acknowledgment
        await websocket_manager.send_to_client(
            client_id,
            {
                "type": "heartbeat_ack",
                "timestamp": message.timestamp,
                "server_time": time.time(),
            },
        )

        metrics_collector.increment_heartbeats()

    except Exception as e:
        metrics_collector.increment_heartbeat_errors()
        print(f"Heartbeat processing error: {e}")


# Enhanced root endpoint
@app.get("/")
async def root():
    """Enhanced root endpoint with system information"""
    return {
        "message": "Enhanced StillMe Gateway - Multi-Platform Communication Hub",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Enhanced Performance",
            "Advanced Security",
            "Comprehensive Monitoring",
            "Circuit Breaker",
            "Rate Limiting",
            "Connection Pooling",
        ],
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "api": "/api",
            "health": "/api/health",
            "metrics": "/metrics",
            "docs": "/docs" if settings.DEBUG else "disabled",
        },
        "timestamp": time.time(),
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


# Enhanced health check
@app.get("/health")
async def health_check():
    """Enhanced health check with detailed status"""
    health_status = await health_checker.get_comprehensive_health()

    if health_status["status"] == "healthy":
        return JSONResponse(content=health_status, status_code=200)
    else:
        return JSONResponse(content=health_status, status_code=503)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
        server_header=False,
        date_header=False,
    )
