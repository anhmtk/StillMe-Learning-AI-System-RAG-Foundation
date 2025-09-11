# StillMe Gateway - Development Version
"""
DEVELOPMENT GATEWAY - NOT FOR PRODUCTION USE

This is a simplified gateway for development and testing purposes.
For production, use main.py with full security and features.

Features:
- Basic WebSocket support
- Simple message forwarding
- StillMe AI integration
- Development-friendly CORS settings

Security Note: This gateway uses permissive CORS for development.
DO NOT use in production environments.
"""

import asyncio
import logging
import httpx
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from cors_config import cors_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StillMe Gateway - Simple",
    description="Simple Gateway for testing",
    version="1.0.0"
)

# Add CORS middleware with environment-based configuration
cors_settings = cors_config.get_cors_config()
logger.info(f"🔒 CORS Configuration: {cors_config.get_security_warning()}")
logger.info(f"🌐 Allowed Origins: {cors_settings['allow_origins']}")

app.add_middleware(
    CORSMiddleware,
    **cors_settings
)

# Add CORS validation middleware
@app.middleware("http")
async def cors_validation_middleware(request, call_next):
    """Validate CORS requests and log security events"""
    origin = request.headers.get("origin")
    
    if origin and not cors_config.is_origin_allowed(origin):
        logger.warning(f"🚨 BLOCKED CORS request from unauthorized origin: {origin}")
        return JSONResponse(
            status_code=403,
            content={"error": "CORS: Origin not allowed", "origin": origin}
        )
    
    response = await call_next(request)
    return response

# WebSocket connections storage
active_connections: dict = {}

# Store messages for each client
client_messages: dict = {}

# StillMe AI configuration
STILLME_AI_URL = "http://127.0.0.1:2377"  # Stable AI Server port
STILLME_AI_AVAILABLE = False

async def check_stillme_ai():
    """Check if StillMe AI is available"""
    global STILLME_AI_AVAILABLE
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STILLME_AI_URL}/health/ai", timeout=5.0)
            if response.status_code == 200:
                STILLME_AI_AVAILABLE = True
                logger.info("✅ StillMe AI is available")
                return True
    except Exception as e:
        logger.warning(f"⚠️ StillMe AI not available: {e}")
        STILLME_AI_AVAILABLE = False
        return False

async def send_to_stillme_ai(message: str, client_id: str) -> str:
    """Send message to StillMe AI and get response"""
    try:
        async with httpx.AsyncClient() as client:
            # Prepare the request data for API Server
            data = {
                "prompt": message,
                "locale": "vi",
                "safety_mode": "maximum"
            }
            
            response = await client.post(
                f"{STILLME_AI_URL}/inference",
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "text" in result:
                    ai_response = result["text"]
                    logger.info(f"🤖 StillMe AI response: {ai_response}")
                    return ai_response
                else:
                    return "Xin lỗi, tôi không thể xử lý tin nhắn này lúc này."
            else:
                logger.error(f"StillMe AI API error: {response.status_code}")
                return "Xin lỗi, có lỗi xảy ra khi kết nối với StillMe AI."
                
    except Exception as e:
        logger.error(f"Error calling StillMe AI: {e}")
        return "Xin lỗi, StillMe AI hiện không khả dụng."

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Simple WebSocket endpoint"""
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"Client {client_id} connected")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            logger.info(f"Received from {client_id}: {data}")
            
            # Check if message has target
            target = data.get('target')
            if target and target in active_connections:
                # Forward message to target client
                await active_connections[target].send_json({
                    "type": "message",
                    "data": data,
                    "from": client_id,
                    "timestamp": data.get('timestamp', '')
                })
                logger.info(f"Forwarded message from {client_id} to {target}")
            else:
                # Echo back to sender
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "from": client_id
                })
            
    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")

@app.get("/")
async def root():
    """Root endpoint"""
    await check_stillme_ai()  # Check StillMe AI status
    
    return {
        "message": "StillMe Gateway - Simple Version",
        "version": "1.0.0",
        "status": "running",
        "connections": len(active_connections),
        "stillme_ai": {
            "available": STILLME_AI_AVAILABLE,
            "url": STILLME_AI_URL
        },
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "health": "/health",
            "send_message": "/send-message",
            "get_messages": "/messages/{client_id}"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "connections": len(active_connections)
    }

@app.get("/health/ai")
async def health_ai():
    """AI-specific health check endpoint for VS Code Tasks"""
    return {
        "ok": True,
        "status": "healthy",
        "timestamp": "2025-01-11T12:00:00Z",
        "server": "StillMe Gateway",
        "version": "1.0.0",
        "connections": len(active_connections),
        "stillme_ai_available": STILLME_AI_AVAILABLE
    }

@app.post("/send-message")
async def send_message(message_data: dict):
    """Send message between clients or to StillMe AI"""
    target = message_data.get('target')
    from_client = message_data.get('from', 'unknown')
    message_text = message_data.get('message', '')
    
    # Check if target is StillMe AI
    if target == 'stillme-ai':
        logger.info(f"🤖 Sending message to StillMe AI from {from_client}: {message_text}")
        
        # Check if StillMe AI is available
        await check_stillme_ai()
        
        if STILLME_AI_AVAILABLE:
            # Send to StillMe AI
            ai_response = await send_to_stillme_ai(message_text, from_client)
            
            # Store AI response for the sender
            if from_client not in client_messages:
                client_messages[from_client] = []
            
            client_messages[from_client].append({
                "from": "stillme-ai",
                "message": ai_response,
                "timestamp": message_data.get('timestamp', ''),
                "data": {"message": ai_response, "from": "stillme-ai"}
            })
            
            logger.info(f"✅ StillMe AI response sent to {from_client}")
            return {"status": "success", "message": "Message sent to StillMe AI"}
        else:
            # StillMe AI not available
            if from_client not in client_messages:
                client_messages[from_client] = []
            
            client_messages[from_client].append({
                "from": "system",
                "message": "StillMe AI hiện không khả dụng. Vui lòng thử lại sau.",
                "timestamp": message_data.get('timestamp', ''),
                "data": {"message": "StillMe AI unavailable", "from": "system"}
            })
            
            return {"status": "error", "message": "StillMe AI not available"}
    
    # Regular client-to-client messaging
    elif target and target in active_connections:
        # Forward message to target client via WebSocket
        await active_connections[target].send_json({
            "type": "message",
            "data": message_data,
            "from": from_client,
            "timestamp": message_data.get('timestamp', '')
        })
        logger.info(f"Forwarded message from {from_client} to {target}")
        return {"status": "success", "message": "Message sent"}
    else:
        # Store message for later retrieval (HTTP polling)
        if target not in client_messages:
            client_messages[target] = []
        
        client_messages[target].append({
            "from": from_client,
            "message": message_text,
            "timestamp": message_data.get('timestamp', ''),
            "data": message_data
        })
        
        logger.info(f"Stored message from {from_client} for {target} (client not connected)")
        return {"status": "success", "message": "Message stored for later delivery"}

@app.get("/messages/{client_id}")
async def get_messages(client_id: str):
    """Get messages for a specific client"""
    if client_id in client_messages:
        messages = client_messages[client_id]
        # Clear messages after retrieval
        client_messages[client_id] = []
        return {"messages": messages}
    else:
        return {"messages": []}

if __name__ == "__main__":
    logger.info("🚀 Starting StillMe Gateway - Simple Version...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
