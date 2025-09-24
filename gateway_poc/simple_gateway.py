#!/usr/bin/env python3
"""
Simple Gateway for StillMe - Quick Performance Test
"""
import asyncio
import httpx
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="StillMe Simple Gateway")

# HTTP client for upstream requests
http_client = httpx.AsyncClient(timeout=30.0)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Simple Gateway is healthy"}

@app.post("/chat")
async def chat_proxy(request: Request):
    try:
        body = await request.json()
        user_message = body.get("message", "")
        
        print(f"Gateway processing: {user_message[:50]}...")
        
        # Forward to StillMe backend
        start_time = time.monotonic()
        stillme_response = await http_client.post("http://localhost:1216/chat", json=body)
        stillme_response.raise_for_status()
        response_data = stillme_response.json()
        
        latency = (time.monotonic() - start_time) * 1000
        print(f"Gateway response: {latency:.1f}ms")
        
        return JSONResponse(response_data, status_code=200)
        
    except httpx.RequestError as e:
        print(f"StillMe backend request failed: {e}")
        return JSONResponse(
            {"error": "StillMe backend is unavailable"},
            status_code=503
        )
    except Exception as e:
        print(f"Gateway error: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

if __name__ == "__main__":
    print("Starting StillMe Simple Gateway on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080, loop="asyncio")
