#!/usr/bin/env python3
"""
StillMe AI Backend - Local Development
Simple backend for desktop/mobile app testing via LAN IP
"""
import os
import time
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_PORT = 1216
OLLAMA_BASE_URL = 'http://127.0.0.1:11434'

class SmartRouter:
    """Smart routing logic for AI models"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL
        logger.info("🧠 Smart Router initialized")
    
    def route_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Route message to appropriate AI model"""
        try:
            # Simple routing logic
            if self._is_simple_question(message):
                return self._call_ollama("gemma2:2b", message)
            elif self._is_code_question(message):
                return self._call_ollama("deepseek-coder:6.7b", message)
            else:
                return self._call_ollama("gemma2:2b", message)  # Default to Gemma
                
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {
                "model": "error",
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "engine": "error",
                "status": "error"
            }
    
    def _is_simple_question(self, message: str) -> bool:
        """Check if message is a simple question"""
        simple_keywords = ["xin chào", "hello", "hi", "cảm ơn", "thank you", "tạm biệt", "bye"]
        return any(keyword in message.lower() for keyword in simple_keywords)
    
    def _is_code_question(self, message: str) -> bool:
        """Check if message is about coding"""
        code_keywords = ["code", "programming", "python", "javascript", "function", "class", "import", "def", "var", "let", "const"]
        return any(keyword in message.lower() for keyword in code_keywords)
    
    def _call_ollama(self, model: str, message: str) -> Dict[str, Any]:
        """Call Ollama API"""
        try:
            payload = {
                "model": model,
                "prompt": message,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "response": data.get("response", "No response"),
                    "engine": "ollama",
                    "status": "success"
                }
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return {
                    "model": model,
                    "response": "Xin lỗi, Ollama không phản hồi",
                    "engine": "error",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Ollama call error: {e}")
            return {
                "model": model,
                "response": f"Xin lỗi, không thể kết nối Ollama: {str(e)}",
                "engine": "error",
                "status": "error"
            }

# Global router instance
smart_router = SmartRouter()

class StillMeHandler(BaseHTTPRequestHandler):
    """HTTP handler for StillMe Backend"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._send_json_response(200, {
                "service": "StillMe AI Backend",
                "status": "healthy",
                "mode": "local-backend",
                "routing": "smart",
                "timestamp": datetime.now().isoformat()
            })
        elif self.path == '/':
            self._send_json_response(200, {
                "service": "StillMe AI Backend",
                "status": "running",
                "mode": "local-backend",
                "endpoints": {
                    "health": "GET /health",
                    "chat": "POST /chat"
                },
                "usage": {
                    "chat": {
                        "method": "POST",
                        "url": "/chat",
                        "payload": {
                            "message": "your message here",
                            "session_id": "optional"
                        }
                    }
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat' or self.path == '/inference':
            self._handle_chat()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _handle_chat(self):
        """Handle chat requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            user_id = data.get('user_id', 'anonymous')
            language = data.get('language', 'vi')
            
            if not message:
                self._send_json_response(400, {"error": "Message is required"})
                return
            
            logger.info(f"Processing message from user {user_id}: message_length={len(message)}")
            
            start_time = time.perf_counter()
            result = smart_router.route_message(message, session_id)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            result["latency_ms"] = latency_ms
            result["timestamp"] = time.time()
            
            logger.info(f"Response: engine={result.get('engine')}, latency={latency_ms:.1f}ms")
            
            self._send_json_response(200, result)
            
        except Exception as e:
            logger.error(f"Error processing request: {type(e).__name__}")
            self._send_json_response(500, {
                "error": str(e),
                "status": "error"
            })
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override log message to avoid verbose logging"""
        pass

def main():
    logger.info("🚀 Starting StillMe AI Backend...")
    logger.info(f"📡 Backend will be available at: http://0.0.0.0:{BACKEND_PORT}")
    logger.info(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
    logger.info("🧠 Smart Routing: Simple → Gemma, Code → DeepSeek Coder")
    logger.info("🌐 Access: LAN IP (for desktop/mobile app testing)")
    logger.info("=" * 50)
    
    try:
        server = HTTPServer(('0.0.0.0', BACKEND_PORT), StillMeHandler)
        logger.info(f"✅ StillMe Backend started successfully on 0.0.0.0:{BACKEND_PORT}")
        logger.info("📱 Desktop/Mobile apps can connect via LAN IP")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 StillMe Backend stopped by user")
    except Exception as e:
        logger.error(f"❌ StillMe Backend failed to start: {e}")

if __name__ == "__main__":
    main()