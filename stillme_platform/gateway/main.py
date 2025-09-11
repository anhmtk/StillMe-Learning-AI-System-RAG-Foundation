# StillMe Gateway - Main Application
"""
StillMe Gateway - Core Infrastructure
Unified communication hub for StillMe multi-platform system
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import Settings
from core.database import get_db, init_db
from core.auth import verify_token, get_current_user
from core.websocket_manager import WebSocketManager
from core.message_protocol import MessageProtocol, MessageType
from core.redis_client import RedisClient
from api.routes import auth, messages, devices, health
from services.stillme_integration import StillMeIntegration
from services.notification_service import NotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gateway.log")
    ]
)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
websocket_manager = WebSocketManager()
redis_client = RedisClient()
stillme_integration = StillMeIntegration()
notification_service = NotificationService()

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
    
    logger.info("🎉 StillMe Gateway started successfully!")
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down StillMe Gateway...")
    await redis_client.disconnect()
    await stillme_integration.cleanup()
    await notification_service.cleanup()
    logger.info("✅ StillMe Gateway shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="StillMe Gateway",
    description="Unified communication hub for StillMe multi-platform system",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

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
                await websocket_manager.broadcast_status(message)
                
            elif message.type == MessageType.HEARTBEAT:
                # Handle heartbeat
                await websocket_manager.send_to_client(client_id, {
                    "type": "heartbeat_ack",
                    "timestamp": message.timestamp
                })
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await websocket_manager.disconnect(client_id)

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
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

