#!/usr/bin/env python3
"""Wrapper script to start FastAPI backend with Railway PORT environment variable."""
import os
import sys
import logging

# Configure logging to stdout (Railway captures stdout)
 refactor/routerization
# Force flush immediately to ensure Railway sees logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Force stdout to be unbuffered for Railway
sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
 main

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

try:
    port_int = int(port)
except ValueError:
    logger.error(f"Invalid PORT value '{port}'. Using default 8080.")
    port_int = 8080

 refactor/routerization

 refactor/routerization
 main
logger.info("=" * 60)
logger.info("StillMe Backend - Starting FastAPI Server")
logger.info("=" * 60)
logger.info(f"Port: {port_int}")
logger.info(f"Host: 0.0.0.0")
logger.info(f"Python: {sys.executable}")
logger.info(f"Python Version: {sys.version}")
logger.info("=" * 60)
 refactor/routerization
sys.stdout.flush()

 main

# Import uvicorn
try:
    import uvicorn
    logger.info("✓ uvicorn imported successfully")
 refactor/routerization
    sys.stdout.flush()
except ImportError as e:
    logger.error(f"❌ Failed to import uvicorn: {e}")
    sys.stdout.flush()

except ImportError as e:
    logger.error(f"❌ Failed to import uvicorn: {e}")
 main
    sys.exit(1)

# Import FastAPI app (this will trigger RAG initialization)
logger.info("Importing FastAPI application...")
logger.info("Note: RAG components initialization may take 10-30 seconds")
logger.info("The /health endpoint will be available immediately")
 refactor/routerization
sys.stdout.flush()

 main

try:
    from backend.api.main import app
    logger.info("✓ FastAPI app imported successfully")
 refactor/routerization
    sys.stdout.flush()
except Exception as e:
    logger.error(f"❌ Failed to import FastAPI app: {e}", exc_info=True)
    logger.error("This may be due to RAG initialization errors")
    sys.stdout.flush()

except Exception as e:
    logger.error(f"❌ Failed to import FastAPI app: {e}", exc_info=True)
    logger.error("This may be due to RAG initialization errors")
 main
    sys.exit(1)

# Start uvicorn
logger.info("=" * 60)
logger.info(f"Starting uvicorn server on 0.0.0.0:{port_int}...")
logger.info("=" * 60)
 refactor/routerization
sys.stdout.flush()

 main

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
 refactor/routerization
    sys.stdout.flush()
except Exception as e:
    logger.error(f"❌ Server crashed: {e}", exc_info=True)
    sys.stdout.flush()
    sys.exit(1)

except Exception as e:
    logger.error(f"❌ Server crashed: {e}", exc_info=True)
    sys.exit(1)

# Log startup information
print("=" * 60)
print("StillMe Backend - Starting FastAPI Server")
print("=" * 60)
print(f"Port: {port_int}")
print(f"Host: 0.0.0.0")
print(f"Python: {sys.executable}")
print(f"Python Version: {sys.version}")
print("=" * 60)

# Start uvicorn with the port
# Note: RAG components initialization happens during module import
# This may take 10-30 seconds, but /health endpoint will return 200 immediately
cmd = [
    sys.executable, "-m", "uvicorn",
    "backend.api.main:app",
    "--host", "0.0.0.0",
    "--port", str(port_int),
    "--log-level", "info"
]

print(f"Starting FastAPI backend on port {port_int}...")
print("Note: RAG components initialization may take 10-30 seconds.")
print("The /health endpoint will return 200 immediately, even during initialization.")
print("=" * 60)

# Run uvicorn (this will block until server stops)
sys.exit(subprocess.run(cmd).returncode)
 main
 main

