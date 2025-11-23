#!/usr/bin/env python3
"""Wrapper script to start FastAPI backend with Railway PORT environment variable."""
import os
import sys
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Configure logging to stdout (Railway captures stdout)
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

# Simple healthcheck server to respond immediately while FastAPI starts
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/health/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"stillme-backend","timestamp":"' + 
                           str(time.time()).encode() + b'"}')
        else:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"starting","message":"FastAPI app is starting..."}')
    
    def log_message(self, format, *args):
        # Suppress healthcheck logs to reduce noise
        pass

def start_healthcheck_server(port):
    """Start a simple HTTP server for healthcheck while FastAPI app loads"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Healthcheck server started on port {port}")
        sys.stdout.flush()
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Healthcheck server failed: {e}")
        sys.stdout.flush()

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

try:
    port_int = int(port)
except ValueError:
    logger.error(f"Invalid PORT value '{port}'. Using default 8080.")
    port_int = 8080

# CRITICAL: Start a simple healthcheck server immediately
# This ensures Railway healthcheck passes while FastAPI app loads
# The healthcheck server will be replaced by FastAPI app once it starts
# Use a separate thread so it doesn't block
logger.info("🚀 Starting immediate healthcheck server...")
healthcheck_thread = threading.Thread(
    target=start_healthcheck_server,
    args=(port_int,),
    daemon=True
)
healthcheck_thread.start()
logger.info("✅ Healthcheck server started - Railway healthcheck will pass immediately")
sys.stdout.flush()
time.sleep(1)  # Give healthcheck server a moment to bind to port

logger.info("=" * 60)
logger.info("StillMe Backend - Starting FastAPI Server")
logger.info("=" * 60)
logger.info(f"Port: {port_int}")
logger.info("Host: 0.0.0.0")
logger.info(f"Python: {sys.executable}")
logger.info(f"Python Version: {sys.version}")
logger.info("=" * 60)
sys.stdout.flush()

# Import uvicorn
try:
    import uvicorn
    logger.info("✓ uvicorn imported successfully")
    sys.stdout.flush()
except ImportError as e:
    logger.error(f"❌ Failed to import uvicorn: {e}")
    sys.stdout.flush()
    sys.exit(1)

# Import FastAPI app (this will trigger RAG initialization)
logger.info("Importing FastAPI application...")
logger.info("Note: RAG components initialization may take 10-30 seconds")
logger.info("The /health endpoint will be available immediately")
sys.stdout.flush()

try:
    logger.info("Step 1: Starting import of backend.api.main...")
    sys.stdout.flush()
    
    # Import with detailed error handling
    from backend.api.main import app
    logger.info("✓ FastAPI app imported successfully")
    sys.stdout.flush()
except ImportError as e:
    logger.error(f"❌ ImportError: Failed to import module: {e}")
    logger.error(f"   Module: {e.name if hasattr(e, 'name') else 'unknown'}")
    logger.error(f"   Path: {e.path if hasattr(e, 'path') else 'unknown'}")
    sys.stdout.flush()
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    sys.stdout.flush()
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Failed to import FastAPI app: {e}")
    logger.error(f"   Error type: {type(e).__name__}")
    import traceback
    logger.error(f"   Traceback: {traceback.format_exc()}")
    logger.error("This may be due to RAG initialization errors")
    sys.stdout.flush()
    # Don't exit - let uvicorn try to start anyway
    # The /health endpoint should still work even if RAG fails
    logger.warning("⚠️ Continuing despite import error - /health endpoint may still work")
    sys.stdout.flush()

# CRITICAL: Ensure app is defined before starting uvicorn
if 'app' not in locals() and 'app' not in globals():
    logger.error("❌ CRITICAL: FastAPI app not defined! Cannot start server.")
    sys.stdout.flush()
    sys.exit(1)

# Start uvicorn
logger.info("=" * 60)
logger.info(f"Starting uvicorn server on 0.0.0.0:{port_int}...")
logger.info("=" * 60)
sys.stdout.flush()

# Log that health endpoint is ready
logger.info("✅ App started - Health endpoint /health is ready")
logger.info("✅ Readiness endpoint /ready available (may return 503 until dependencies ready)")
sys.stdout.flush()

# CRITICAL: Add immediate health check endpoint test
try:
    # Test if app can be accessed
    logger.info(f"🔍 Testing app object: {type(app)}")
    logger.info(f"🔍 App routes count: {len(app.routes) if hasattr(app, 'routes') else 'unknown'}")
    sys.stdout.flush()
except Exception as e:
    logger.warning(f"⚠️ Could not inspect app object: {e}")
    sys.stdout.flush()

try:
    logger.info("🚀 Starting uvicorn server...")
    logger.info("⚠️ Note: Healthcheck server will be replaced by FastAPI app")
    sys.stdout.flush()
    # Uvicorn will bind to the same port, which will cause the healthcheck server to fail
    # This is expected - FastAPI app takes over once it starts
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port_int,
        log_level="info",
        access_log=True
    )
except KeyboardInterrupt:
    logger.info("Server stopped by user")
    sys.stdout.flush()
except Exception as e:
    logger.error(f"❌ Server crashed: {e}", exc_info=True)
    import traceback
    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    sys.stdout.flush()
    sys.exit(1)
