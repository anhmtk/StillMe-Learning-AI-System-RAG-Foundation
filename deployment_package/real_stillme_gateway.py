#!/usr/bin/env python3
"""
🌐 REAL STILLME GATEWAY - SIMPLE VERSION
🌐 REAL STILLME GATEWAY - PHIÊN BẢN ĐƠN GIẢN

PURPOSE / MỤC ĐÍCH:
- Simple gateway to connect Chat UI with StillMe AI Server
- Gateway đơn giản để kết nối Chat UI với StillMe AI Server
- Handles HTTP requests and forwards to AI server
- Xử lý HTTP requests và chuyển tiếp đến AI server
- Provides fallback responses when AI server is unavailable
- Cung cấp phản hồi fallback khi AI server không khả dụng
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StillMe.Gateway")

# Configuration
STILLME_AI_SERVER_URL = "http://localhost:1216"
STILLME_AI_SERVER_ENDPOINT = "/inference"
GATEWAY_PORT = 21568

class StillMeGatewayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._send_json_response(200, {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "gateway_version": "2.0.0-simple",
                "ai_server_url": STILLME_AI_SERVER_URL
            })
        elif self.path == '/':
            self._send_json_response(200, {
                "message": "StillMe Gateway is running!",
                "version": "2.0.0-simple",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "endpoints": {
                    "chat": "/send-message",
                    "health": "/health"
                }
            })
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/send-message':
            self._handle_chat_request()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._add_cors_headers()
        self.end_headers()
    
    def _handle_chat_request(self):
        """Handle chat message requests"""
        try:
            # Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if not post_data:
                self._send_json_response(400, {"error": "No data received"})
                return
            
            # Parse JSON data
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self._send_json_response(400, {"error": f"Invalid JSON: {str(e)}"})
                return
            
            # Extract message and language
            user_message = data.get('message', '').strip()
            language = data.get('language', 'vi')
            
            if not user_message:
                self._send_json_response(400, {"error": "Message is required"})
                return
            
            logger.info(f"💬 Received message: {user_message}")
            
            # Try to forward to StillMe AI Server
            ai_response = self._forward_to_ai_server(user_message, language)
            
            if ai_response:
                # Success - return AI response
                response_data = {
                    "received": data,
                    "response": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "ai_server_status": "connected",
                    "gateway_version": "2.0.0-simple"
                }
                self._send_json_response(200, response_data)
            else:
                # Fallback response
                fallback_response = self._generate_fallback_response(user_message, language)
                response_data = {
                    "received": data,
                    "response": fallback_response,
                    "timestamp": datetime.now().isoformat(),
                    "status": "fallback",
                    "ai_server_status": "unavailable",
                    "gateway_version": "2.0.0-simple"
                }
                self._send_json_response(200, response_data)
                
        except Exception as e:
            logger.error(f"❌ Error handling chat request: {e}")
            self._send_json_response(500, {
                "error": "Internal server error",
                "message": str(e)
            })
    
    def _forward_to_ai_server(self, message: str, language: str) -> str | None:
        """Forward message to StillMe AI Server"""
        try:
            import urllib.request
            import urllib.parse
            
            # Prepare request data
            request_data = {
                "message": message,
                "locale": language
            }
            
            # Encode data
            data = json.dumps(request_data).encode('utf-8')
            
            # Create request
            url = f"{STILLME_AI_SERVER_URL}{STILLME_AI_SERVER_ENDPOINT}"
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            # Send request with timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode('utf-8'))
                    ai_text = response_data.get('text', '')
                    logger.info(f"✅ AI Server response: {ai_text[:100]}...")
                    return ai_text
                else:
                    logger.warning(f"⚠️ AI Server returned status {response.status}")
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to AI Server: {e}")
            return None
    
    def _generate_fallback_response(self, message: str, language: str) -> str:
        """Generate fallback response when AI server is unavailable"""
        message_lower = message.lower()
        
        # Simple fallback responses
        if any(word in message_lower for word in ["hello", "hi", "xin chào", "chào"]):
            return "Xin chào! Tôi là StillMe AI Gateway. AI Server hiện tại không khả dụng, nhưng tôi vẫn có thể giúp bạn với một số câu hỏi cơ bản."
        
        elif "test" in message_lower:
            return "✅ Gateway test thành công! AI Server hiện không khả dụng, nhưng Gateway đang hoạt động bình thường."
        
        elif any(word in message_lower for word in ["status", "trạng thái", "health"]):
            return f"🟡 Gateway Status: ONLINE\n🔴 AI Server: OFFLINE\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n📡 Gateway Version: 2.0.0-simple"
        
        else:
            return f"Tôi hiểu bạn đang hỏi về: '{message}'. Hiện tại AI Server không khả dụng, nhưng tôi đã ghi nhận câu hỏi của bạn. Vui lòng thử lại sau."
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self._add_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _add_cors_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-User-Lang')
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Main function to start the gateway"""
    logger.info("🚀 Starting Real StillMe Gateway...")
    logger.info(f"📡 Gateway will be available at: http://localhost:{GATEWAY_PORT}")
    logger.info(f"🤖 StillMe AI Server: {STILLME_AI_SERVER_URL}")
    logger.info(f"🌐 Chat UI can connect to: http://localhost:{GATEWAY_PORT}")
    logger.info("=" * 50)
    
    try:
        server = HTTPServer(('0.0.0.0', GATEWAY_PORT), StillMeGatewayHandler)
        logger.info(f"✅ Gateway started successfully on port {GATEWAY_PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Gateway stopped by user")
    except Exception as e:
        logger.error(f"❌ Gateway failed to start: {e}")

if __name__ == "__main__":
    main()
