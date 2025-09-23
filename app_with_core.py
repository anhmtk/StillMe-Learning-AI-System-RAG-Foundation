#!/usr/bin/env python3
"""
StillMe AI Backend - Using Core Framework
Backend sử dụng Core Framework để enforce StillMe persona
"""
import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import Core Framework
try:
    from stillme_core.framework import StillMeFramework
    CORE_FRAMEWORK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Core Framework not available: {e}")
    CORE_FRAMEWORK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_PORT = 1216

class StillMeBackendHandler(BaseHTTPRequestHandler):
    """HTTP request handler using Core Framework"""
    
    def __init__(self, *args, **kwargs):
        # Initialize Core Framework
        if CORE_FRAMEWORK_AVAILABLE:
            try:
                self.framework = StillMeFramework()
                logger.info("✅ Core Framework initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Core Framework: {e}")
                self.framework = None
        else:
            self.framework = None
            logger.warning("⚠️ Core Framework not available, using fallback")
        
        super().__init__(*args, **kwargs)
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._send_json_response(200, {})
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._handle_health()
        elif self.path == '/':
            self._handle_root()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat':
            self._handle_chat()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _handle_root(self):
        """Handle root endpoint"""
        response_data = {
            "service": "StillMe AI Backend (Core Framework)",
            "status": "running",
            "framework": "Core Framework" if self.framework else "Fallback",
            "message": "Welcome to StillMe AI Backend! Using Core Framework for persona enforcement.",
            "endpoints": {
                "/": "Service information",
                "/health": "Health check",
                "/chat": "AI chat inference (POST)"
            }
        }
        self._send_json_response(200, response_data)
    
    def _handle_health(self):
        """Handle health check"""
        if self.framework:
            # Get framework status
            try:
                framework_status = self.framework.get_framework_status()
                response_data = {
                    "service": "StillMe AI Backend (Core Framework)",
                    "status": "healthy",
                    "framework": "Core Framework",
                    "modules": framework_status,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                response_data = {
                    "service": "StillMe AI Backend (Core Framework)",
                    "status": "degraded",
                    "framework": "Core Framework (Error)",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        else:
            response_data = {
                "service": "StillMe AI Backend",
                "status": "fallback",
                "framework": "Fallback Mode",
                "timestamp": datetime.now().isoformat()
            }
        
        self._send_json_response(200, response_data)
    
    def _handle_chat(self):
        """Handle chat requests using Core Framework"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            user_id = data.get('user_id', 'anonymous')
            
            if not message:
                self._send_json_response(400, {"error": "Message is required"})
                return
            
            logger.info(f"Processing message from user {user_id}: message_length={len(message)}")
            
            start_time = time.perf_counter()
            
            if self.framework and hasattr(self.framework, 'conversational_core') and self.framework.conversational_core:
                # Use Core Framework for AI response
                response_text = self.framework.conversational_core.respond(message)
                engine = "core-framework"
                model = "stillme-core"
            else:
                # Fallback response
                response_text = "Xin lỗi, Core Framework chưa sẵn sàng. Vui lòng thử lại sau."
                engine = "fallback"
                model = "fallback"
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            result = {
                "model": model,
                "response": response_text,
                "engine": engine,
                "status": "success",
                "latency_ms": latency_ms,
                "timestamp": time.time()
            }
            
            logger.info(f"Response: engine={engine}, latency={latency_ms:.1f}ms")
            
            self._send_json_response(200, result)
            
        except Exception as e:
            logger.error(f"Error processing request: {type(e).__name__}")
            self._send_json_response(500, {
                "error": str(e),
                "status": "error"
            })
    
    def log_message(self, format, *args):
        """Override log message to avoid verbose logging"""
        pass

def main():
    """Main function to start the server"""
    logger.info("🚀 Starting StillMe AI Backend with Core Framework...")
    logger.info(f"📡 Backend will be available at: http://0.0.0.0:{BACKEND_PORT}")
    
    if CORE_FRAMEWORK_AVAILABLE:
        logger.info("✅ Core Framework available - StillMe persona will be enforced")
    else:
        logger.warning("⚠️ Core Framework not available - using fallback mode")
    
    logger.info("🧠 StillMe persona enforcement: ACTIVE")
    logger.info("🌐 Access: LAN IP (for desktop/mobile app testing)")
    logger.info("==================================================")
    
    server_address = ('0.0.0.0', BACKEND_PORT)
    httpd = HTTPServer(server_address, StillMeBackendHandler)
    
    logger.info(f"✅ StillMe Backend started successfully on 0.0.0.0:{BACKEND_PORT}")
    logger.info("📱 Desktop/Mobile apps can connect via LAN IP")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 StillMe Backend stopped by user")
        httpd.server_close()

if __name__ == '__main__':
    main()
