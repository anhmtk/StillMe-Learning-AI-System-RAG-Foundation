#!/usr/bin/env python3
"""
Simple Gateway for Testing
Gateway đơn giản để test kết nối
"""

import json
from datetime import datetime

import httpx
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="StillMe Simple Gateway",
    description="Simple gateway for testing desktop/mobile connections",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections: dict[str, WebSocket] = {}

# AI Server Configuration
AI_SERVER_URL = "http://192.168.1.8:14725"


# Pydantic models
class MessageRequest(BaseModel):
    message: str
    language: str | None = "vi"
    timestamp: str | None = None


class MessageResponse(BaseModel):
    response: str
    timestamp: str
    ai_server: str


async def send_to_ai_server(message: str, language: str = "vi") -> str:
    """Send message to real AI server and get response"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try different AI server endpoints
            endpoints = [
                f"{AI_SERVER_URL}/inference",
                f"{AI_SERVER_URL}/chat",
                f"{AI_SERVER_URL}/message",
                f"{AI_SERVER_URL}/api/message",
            ]

            for endpoint in endpoints:
                try:
                    payload = {
                        "message": message,
                        "locale": language,
                        "timestamp": datetime.now().isoformat(),
                    }

                    response = await client.post(endpoint, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        # Extract response from different possible formats
                        if isinstance(data, dict):
                            return data.get(
                                "text",
                                data.get(
                                    "response",
                                    data.get("message", data.get("content", str(data))),
                                ),
                            )
                        else:
                            return str(data)

                except Exception as e:
                    print(f"Failed to connect to {endpoint}: {e}")
                    continue

            # If all endpoints fail, return fallback response
            return f"Xin chào! Tôi là StillMe AI. Bạn đã nói: '{message}'. Tôi đang hoạt động qua Gateway! (AI Server tạm thời không khả dụng)"

    except Exception as e:
        print(f"Error connecting to AI server: {e}")
        return f"Xin chào! Tôi là StillMe AI. Bạn đã nói: '{message}'. Tôi đang hoạt động qua Gateway! (Lỗi kết nối AI Server: {e!s})"


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Web Chat Interface"""
    try:
        with open("web_chat_interface.html", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback to JSON if HTML file not found
        return {
            "message": "StillMe Gateway - Simple Version",
            "version": "1.0.0",
            "status": "running",
            "connections": len(active_connections),
            "stillme_ai": {"available": True, "url": "http://192.168.1.8:14725"},
            "endpoints": {
                "websocket": "/ws/{client_id}",
                "health": "/health",
                "version": "/version",
            },
        }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "StillMe Gateway - Simple Version",
        "version": "1.0.0",
        "status": "running",
        "connections": len(active_connections),
        "stillme_ai": {"available": True, "url": "http://192.168.1.8:4729"},
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "health": "/health",
            "version": "/version",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": len(active_connections),
    }


@app.get("/version")
async def version():
    """Version endpoint"""
    return {
        "name": "stillme-gateway",
        "version": "1.0.0",
        "build_time": datetime.now().isoformat(),
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections"""
    await websocket.accept()
    active_connections[client_id] = websocket

    try:
        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection",
                    "status": "connected",
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Keep connection alive
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "chat":
                    # Send to real AI server
                    user_message = message.get("message", "")
                    language = message.get("language", "vi")

                    # Get response from AI server
                    ai_response = await send_to_ai_server(user_message, language)

                    response = {
                        "type": "ai_response",
                        "message": ai_response,
                        "timestamp": datetime.now().isoformat(),
                        "ai_server": "real_ai_server",
                    }
                else:
                    # Echo back other messages
                    response = {
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat(),
                    }

                await websocket.send_text(json.dumps(response))

            except WebSocketDisconnect:
                break
            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        pass
    finally:
        # Remove connection when client disconnects
        active_connections.pop(client_id, None)


@app.post("/api/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Send message to StillMe AI"""
    try:
        # Send to real AI server
        user_message = request.message
        language = request.language or "vi"

        # Get response from AI server
        ai_response = await send_to_ai_server(user_message, language)

        return MessageResponse(
            response=ai_response,
            timestamp=datetime.now().isoformat(),
            ai_server="real_ai_server",
        )

    except Exception as e:
        return MessageResponse(
            response=f"Lỗi: {e!s}",
            timestamp=datetime.now().isoformat(),
            ai_server="error",
        )


@app.post("/send-message", response_model=MessageResponse)
async def send_message_alt(request: Request):
    """Alternative send message endpoint"""
    try:
        # Debug: log raw request
        body = await request.body()
        print(f"Raw request body: {body}")

        # Try to parse JSON
        try:
            # Try different encodings
            try:
                data = json.loads(body.decode("utf-8"))
            except UnicodeDecodeError:
                try:
                    data = json.loads(body.decode("utf-8-sig"))
                except UnicodeDecodeError:
                    data = json.loads(body.decode("latin-1"))
            print(f"Parsed JSON: {data}")

            # Create MessageRequest from dict
            message_req = MessageRequest(
                message=data.get("message", ""),
                language=data.get("language", "vi"),
                timestamp=data.get("timestamp"),
            )

            return await send_message(message_req)

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return MessageResponse(
                response=f"Lỗi JSON: {e!s}",
                timestamp=datetime.now().isoformat(),
                ai_server="error",
            )

    except Exception as e:
        print(f"General error: {e}")
        return MessageResponse(
            response=f"Lỗi: {e!s}",
            timestamp=datetime.now().isoformat(),
            ai_server="error",
        )


@app.get("/messages/{client_id}")
async def get_messages(client_id: str):
    """Get messages for a specific client"""
    return {
        "client_id": client_id,
        "messages": [],
        "status": "no_messages",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    print("🚀 Starting StillMe Simple Gateway...")
    print("🌐 Server will be available at: http://0.0.0.0:8000")
    print("📱 Desktop/Mobile apps can connect to: http://192.168.1.8:8000")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
