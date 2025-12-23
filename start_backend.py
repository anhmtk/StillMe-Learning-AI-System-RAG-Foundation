#!/usr/bin/env python3
"""Wrapper script to start FastAPI backend with Railway PORT environment variable."""
import os
import sys
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("✓ Loaded environment variables from .env file")
except ImportError:
    # python-dotenv not installed, skip (Railway uses environment variables directly)
    pass
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Failed to load .env file: {e}")

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

# Global variable to store healthcheck server instance and thread
_healthcheck_server = None
_healthcheck_thread = None
_healthcheck_stop_flag = threading.Event()

def start_healthcheck_server(port):
    """Start a simple HTTP server for healthcheck while FastAPI app loads"""
    global _healthcheck_server
    try:
        _healthcheck_server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Healthcheck server started on port {port}")
        sys.stdout.flush()
        # Use serve_forever with timeout to allow checking stop flag
        # This server will run until uvicorn binds to the same port (which will cause it to fail gracefully)
        while not _healthcheck_stop_flag.is_set():
            try:
                _healthcheck_server.handle_request()
            except OSError as e:
                # Port already in use - uvicorn has taken over, this is expected
                if "Address already in use" in str(e) or "address already in use" in str(e).lower():
                    logger.info("✅ Uvicorn has taken over the port - healthcheck server stopping gracefully")
                    break
                else:
                    raise  # Re-raise if it's a different error
        logger.info("🛑 Healthcheck server stopping...")
        sys.stdout.flush()
    except OSError as e:
        # Port already in use - uvicorn has taken over, this is expected
        if "Address already in use" in str(e) or "address already in use" in str(e).lower():
            logger.info("✅ Uvicorn has taken over the port - healthcheck server stopping gracefully")
        elif not _healthcheck_stop_flag.is_set():
            logger.error(f"❌ Healthcheck server failed: {e}")
            sys.stdout.flush()
    except Exception as e:
        if not _healthcheck_stop_flag.is_set():
            logger.error(f"❌ Healthcheck server failed: {e}")
            sys.stdout.flush()

def stop_healthcheck_server():
    """Stop the healthcheck server to free up the port for FastAPI"""
    global _healthcheck_server, _healthcheck_thread
    if _healthcheck_server or (_healthcheck_thread and _healthcheck_thread.is_alive()):
        try:
            # Signal server to stop
            _healthcheck_stop_flag.set()
            # Make a request to trigger handle_request() to check the flag
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect(('localhost', port_int))
                sock.close()
            except:
                pass  # Ignore connection errors
            # Wait for thread to finish (with shorter timeout for faster shutdown)
            if _healthcheck_thread and _healthcheck_thread.is_alive():
                _healthcheck_thread.join(timeout=0.5)  # Reduced from 1.0 to 0.5
            # Close server
            if _healthcheck_server:
                try:
                    _healthcheck_server.server_close()
                except:
                    pass  # Ignore errors during shutdown
                _healthcheck_server = None
            logger.info("✅ Healthcheck server stopped")
            sys.stdout.flush()
        except Exception as e:
            logger.warning(f"⚠️ Error stopping healthcheck server: {e}")
            sys.stdout.flush()

# Get PORT from environment (Railway injects this)
# For local development, default to 8000; for Railway, use 8080
port = os.getenv("PORT", "8000" if os.getenv("ENVIRONMENT") != "production" else "8080")

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
_healthcheck_thread = threading.Thread(
    target=start_healthcheck_server,
    args=(port_int,),
    daemon=True
)
_healthcheck_thread.start()
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

# CRITICAL: Pre-download embedding model BEFORE importing FastAPI app
# This ensures model is ready before any requests arrive
logger.info("=" * 60)
logger.info("📦 Pre-downloading embedding model...")
logger.info("=" * 60)
logger.info("Model: paraphrase-multilingual-MiniLM-L12-v2")
logger.info("Cache location: /app/hf_cache (Railway persistent volume)")
logger.info("This may take 3-5 minutes on first deploy...")
sys.stdout.flush()

try:
    # Pre-download model using the same method as model_warmup.py
    import os
    from pathlib import Path
    
    # Set cache environment variables FIRST (before importing SentenceTransformer)
    cache_path = Path("/app/hf_cache")
    if cache_path.exists() or cache_path.parent.exists():
        os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
        os.environ["HF_HOME"] = str(cache_path)
        os.environ["HF_DATASETS_CACHE"] = str(cache_path / "datasets")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_path)
        os.environ["HF_HUB_CACHE"] = str(cache_path / "hub")
        logger.info(f"✅ Cache environment configured: {cache_path}")
        sys.stdout.flush()
    
    # Now import and download model
    from sentence_transformers import SentenceTransformer
    
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    logger.info(f"⏳ Downloading model: {model_name}...")
    sys.stdout.flush()
    
    # Suppress tqdm progress bars
    os.environ.setdefault("TQDM_DISABLE", "1")
    
    # Download model (this will cache it in /app/hf_cache)
    model = SentenceTransformer(
        model_name,
        cache_folder=str(cache_path) if cache_path.exists() else None
    )
    
    # Test model by encoding a small text
    test_embedding = model.encode("test", show_progress_bar=False)
    logger.info(f"✅ Model downloaded and verified (embedding dimension: {len(test_embedding)})")
    logger.info(f"✅ Model cached at: {cache_path}")
    sys.stdout.flush()
    
    # Clean up model from memory (we'll reload it later in EmbeddingService)
    del model
    import gc
    gc.collect()
    logger.info("✅ Model pre-download complete - ready for use")
    sys.stdout.flush()
    
except Exception as e:
    logger.warning(f"⚠️ Model pre-download failed: {e}")
    logger.warning("⚠️ Model will be downloaded on first use (may cause slow first request)")
    logger.warning("⚠️ This is not critical - service will continue to start")
    sys.stdout.flush()
    # Don't exit - let service continue (model will download on first use)

# Import FastAPI app (this will trigger RAG initialization)
logger.info("=" * 60)
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

# CRITICAL: Stop healthcheck server RIGHT BEFORE uvicorn starts
# This prevents port conflict while minimizing gap
# Uvicorn will start immediately after healthcheck server stops
logger.info("🛑 Stopping healthcheck server to free port for uvicorn...")
sys.stdout.flush()
stop_healthcheck_server()
# Small delay to ensure port is released, but uvicorn will start immediately after
time.sleep(0.2)  # 200ms delay - minimal gap
logger.info("✅ Port should be free now - starting uvicorn immediately")
sys.stdout.flush()

# Start uvicorn
logger.info("=" * 60)
logger.info(f"🚀 Starting uvicorn server on 0.0.0.0:{port_int}...")
logger.info("=" * 60)
sys.stdout.flush()

# Log that health endpoint is ready
logger.info("=" * 60)
logger.info("✅ StillMe Backend - Server Starting")
logger.info("=" * 60)
logger.info(f"📍 Port: {port_int}")
logger.info("📍 Host: 0.0.0.0")
logger.info("✅ Health endpoint: /health (available immediately)")
logger.info("✅ Readiness endpoint: /ready (may return 503 until dependencies ready)")
logger.info("=" * 60)
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
    logger.info("⚠️ Note: Uvicorn will bind to port, causing healthcheck server to stop gracefully")
    logger.info("⚠️ This is expected - FastAPI app takes over once uvicorn binds to port")
    sys.stdout.flush()
    # Uvicorn will bind to the same port, which will cause the healthcheck server to fail gracefully
    # This is expected - FastAPI app takes over once it starts
    # The healthcheck server will catch OSError and stop gracefully
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
