#!/usr/bin/env python3
"""
Optimized StillMe API Server for High Throughput
Tối ưu cho performance với workers, uvloop, httptools, orjson
"""

import asyncio
import logging
import time
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global HTTP client for external API calls (if needed)
http_client: Optional[httpx.AsyncClient] = None

app = FastAPI(
    title="StillMe Clarification Core API",
    description="Optimized API for high throughput testing",
    version="1.0.0",
    default_response_class=ORJSONResponse
)

@app.on_event("startup")
async def startup_event():
    """Initialize global resources"""
    global http_client
    http_client = httpx.AsyncClient(
        timeout=5.0,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=50
        )
    )
    logger.info("🚀 StillMe Optimized API Server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup global resources"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("🛑 StillMe API Server stopped")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "StillMe Optimized API is running",
        "service": "clarification_core",
        "timestamp": time.time()
    }

@app.post("/chat")
async def chat(request: Request):
    """
    Optimized chat endpoint for high throughput
    """
    try:
        # Parse request body
        body = await request.json()
        prompt = body.get('prompt', 'No prompt provided')

        # Simulate clarification processing (replace with actual logic)
        await asyncio.sleep(0.001)  # Minimal processing time

        # Generate response
        response = {
            "response": f"Hello! You said: {prompt}. This is StillMe AI responding.",
            "status": "success",
            "service": "clarification_core",
            "clarification": "Your message was processed successfully",
            "suggestion": "You can ask me anything!",
            "timestamp": time.time(),
            "processing_time_ms": 1.0
        }

        return response

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ORJSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e),
                "status": "error"
            }
        )

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "uptime": time.time(),
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Optimized Uvicorn configuration
    uvicorn.run(
        "optimized_main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Use multiple workers
        loop="uvloop",  # Use uvloop for better performance
        http="httptools",  # Use httptools for better HTTP parsing
        access_log=False,  # Disable access logs for performance
        log_level="warning"  # Reduce log verbosity
    )
