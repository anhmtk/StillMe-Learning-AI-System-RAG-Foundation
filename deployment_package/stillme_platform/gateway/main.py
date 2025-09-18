#!/usr/bin/env python3
"""
🌐 STILLME GATEWAY - PRODUCTION SERVER
🌐 STILLME GATEWAY - SERVER PRODUCTION

PURPOSE / MỤC ĐÍCH:
- Production gateway server with full enterprise features
- Server gateway production với đầy đủ tính năng doanh nghiệp
- Unified communication hub for multi-platform system
- Trung tâm giao tiếp thống nhất cho hệ thống đa nền tảng
- Handles WebSocket, REST API, and message routing
- Xử lý WebSocket, REST API và routing tin nhắn

FUNCTIONALITY / CHỨC NĂNG:
- WebSocket connections management
- Quản lý kết nối WebSocket
- Authentication and authorization (JWT)
- Xác thực và phân quyền (JWT)
- Database integration (PostgreSQL/SQLite)
- Tích hợp database (PostgreSQL/SQLite)
- Redis caching and session management
- Cache Redis và quản lý session
- Rate limiting and security middleware
- Rate limiting và security middleware
- Health monitoring and logging
- Giám sát sức khỏe và logging

RELATED FILES / FILES LIÊN QUAN:
- dev_gateway.py - Development version (simplified)
- cors_config.py - CORS configuration
- core/ - Core gateway modules
- api/ - API route handlers
- services/ - Business logic services

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- FastAPI with WebSocket support
- Database: PostgreSQL/SQLite with async support
- Redis: Session storage and caching
- Security: JWT tokens, CORS, rate limiting
- Port: 8001 (configurable via environment)
"""

import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from api.routes import auth, devices, health, messages
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from services.notification_service import NotificationService
from services.notification_manager import NotificationManager, NotificationChannel, AlertSeverity
from services.stillme_integration import StillMeIntegration

from core.config import Settings
from core.database import init_db
from core.message_protocol import MessageProtocol, MessageType
from core.redis_client import RedisClient
from core.websocket_manager import WebSocketManager

# Import common utilities
# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common import (
    AsyncHttpClient,
    ConfigManager,
    FileManager,
    StillMeException,
    get_logger,
)

# Initialize common utilities
config_manager = ConfigManager("config/gateway_config.json", {})
logger = get_logger("StillMe.Gateway", log_file="logs/gateway.log", json_format=True)
http_client = AsyncHttpClient()
file_manager = FileManager()

# Global instances
settings = Settings()
websocket_manager = WebSocketManager()
redis_client = RedisClient()
stillme_integration = StillMeIntegration()
notification_service = NotificationService()
notification_manager = NotificationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting StillMe Gateway...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Initialize Redis
    await redis_client.connect()
    logger.info("✅ Redis connected")

    # Initialize StillMe integration
    await stillme_integration.initialize()
    logger.info("✅ StillMe integration ready")

    # Initialize notification service
    await notification_service.initialize()
    logger.info("✅ Notification service ready")
    
    # Initialize notification manager
    await notification_manager.start()
    logger.info("✅ Notification manager ready")

    logger.info("🎉 StillMe Gateway started successfully!")

    yield

    # Cleanup
    logger.info("🔄 Shutting down StillMe Gateway...")
    await redis_client.disconnect()
    await stillme_integration.cleanup()
    await notification_service.cleanup()
    await notification_manager.stop()
    logger.info("✅ StillMe Gateway shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="StillMe Gateway",
    description="Unified communication hub for StillMe multi-platform system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])


# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = MessageProtocol.parse(data)

            # Process message based on type
            if message.type == MessageType.COMMAND:
                # Route command to StillMe Core
                result = await stillme_integration.process_command(message)
                await websocket_manager.send_to_client(client_id, result)

            elif message.type == MessageType.STATUS:
                # Handle status updates
                status_dict = {
                    "id": message.id,
                    "type": message.type.value,
                    "content": message.content,
                    "timestamp": message.timestamp,
                    "metadata": message.metadata,
                }
                await websocket_manager.broadcast_status(status_dict)

            elif message.type == MessageType.HEARTBEAT:
                # Handle heartbeat
                await websocket_manager.send_to_client(
                    client_id, {"type": "heartbeat_ack", "timestamp": message.timestamp}
                )
                
                # Send health notification if needed
                await notification_manager.send_notification(
                    title="Gateway Health Check",
                    body=f"Client {client_id} heartbeat received",
                    severity=AlertSeverity.INFO,
                    channels=[NotificationChannel.INTERNAL]
                )

    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
        
        # Send disconnection notification
        await notification_manager.send_notification(
            title="Client Disconnected",
            body=f"Client {client_id} disconnected from Gateway",
            severity=AlertSeverity.LOW,
            channels=[NotificationChannel.INTERNAL]
        )
        
    except StillMeException as e:
        logger.error(f"StillMe error for client {client_id}: {e}")
        await websocket_manager.disconnect(client_id)
        
        # Send error notification
        await notification_manager.send_notification(
            title="StillMe Integration Error",
            body=f"StillMe error for client {client_id}: {str(e)}",
            severity=AlertSeverity.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.INTERNAL]
        )
        
    except Exception as e:
        logger.error(f"Unexpected error for client {client_id}: {e}")
        await websocket_manager.disconnect(client_id)
        
        # Send critical error notification
        await notification_manager.send_notification(
            title="Gateway Critical Error",
            body=f"Unexpected error for client {client_id}: {str(e)}",
            severity=AlertSeverity.CRITICAL,
            channels=[NotificationChannel.EMAIL, NotificationChannel.INTERNAL]
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StillMe Gateway - Multi-Platform Communication Hub",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "api": "/api",
            "health": "/api/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
