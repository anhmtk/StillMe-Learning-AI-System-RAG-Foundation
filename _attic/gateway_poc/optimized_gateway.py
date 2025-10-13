#!/usr/bin/env python3
"""
Optimized Gateway for StillMe - Without Redis (for testing)
"""

import time

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="StillMe Optimized Gateway")

# HTTP client with connection pooling
http_client = httpx.AsyncClient(
    timeout=30.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

# Simple in-memory cache
cache = {}
CACHE_TTL = 300  # 5 minutes


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Optimized Gateway is healthy"}


@app.post("/chat")
async def chat_proxy(request: Request):
    try:
        body = await request.json()
        user_message = body.get("message", "")

        # Simple cache key
        cache_key = f"chat:{hash(user_message)}"

        # Check cache first
        if cache_key in cache:
            cached_data, timestamp = cache[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                print(f"Cache hit for: {user_message[:50]}...")
                return JSONResponse(cached_data, status_code=200)

        print(f"Gateway processing: {user_message[:50]}...")

        # Forward to StillMe backend
        start_time = time.monotonic()
        stillme_response = await http_client.post(
            "http://localhost:1216/chat", json=body
        )
        stillme_response.raise_for_status()
        response_data = stillme_response.json()

        latency = (time.monotonic() - start_time) * 1000
        print(f"Gateway response: {latency:.1f}ms")

        # Cache the response
        cache[cache_key] = (response_data, time.time())

        return JSONResponse(response_data, status_code=200)

    except httpx.RequestError as e:
        print(f"StillMe backend request failed: {e}")
        return JSONResponse(
            {"error": "StillMe backend is unavailable"}, status_code=503
        )
    except Exception as e:
        print(f"Gateway error: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)


@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()


if __name__ == "__main__":
    print("Starting StillMe Optimized Gateway on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080, loop="asyncio")
