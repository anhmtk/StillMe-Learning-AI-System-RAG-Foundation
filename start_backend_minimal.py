#!/usr/bin/env python3
"""
Minimal startup script for Railway - starts FastAPI with immediate /health endpoint
This ensures service is available even during RAG initialization
"""
import os
import sys
import logging

# Configure logging to stdout (Railway captures stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

try:
    port_int = int(port)
except ValueError:
    logger.error(f"Invalid PORT value '{port}'. Using default 8080.")
    port_int = 8080

logger.info("=" * 60)
logger.info("StillMe Backend - Starting FastAPI Server")
logger.info("=" * 60)
logger.info(f"Port: {port_int}")
logger.info(f"Host: 0.0.0.0")
logger.info(f"Python: {sys.executable}")
logger.info(f"Python Version: {sys.version}")
logger.info("=" * 60)

# Import uvicorn
try:
    import uvicorn
    logger.info("✓ uvicorn imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import uvicorn: {e}")
    sys.exit(1)

# Import FastAPI app (this will trigger RAG initialization)
logger.info("Importing FastAPI application...")
logger.info("Note: RAG components initialization may take 10-30 seconds")
logger.info("The /health endpoint will be available immediately")

try:
    from backend.api.main import app
    logger.info("✓ FastAPI app imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import FastAPI app: {e}", exc_info=True)
    logger.error("This may be due to RAG initialization errors")
    sys.exit(1)

# Start uvicorn
logger.info("=" * 60)
logger.info(f"Starting uvicorn server on 0.0.0.0:{port_int}...")
logger.info("=" * 60)

try:
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port_int,
        log_level="info",
        access_log=True
    )
except KeyboardInterrupt:
    logger.info("Server stopped by user")
except Exception as e:
    logger.error(f"❌ Server crashed: {e}", exc_info=True)
    sys.exit(1)

