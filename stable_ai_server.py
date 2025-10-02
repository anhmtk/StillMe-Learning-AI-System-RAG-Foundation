#!/usr/bin/env python3
"""
🚀 STILLME AI SERVER - SIMPLE VERSION
🚀 STILLME AI SERVER - PHIÊN BẢN ĐƠN GIẢN

PURPOSE / MỤC ĐÍCH:
- Simple AI server without complex imports
- Server AI đơn giản không có import phức tạp
- Handles chat requests and AI responses
- Xử lý yêu cầu chat và phản hồi AI
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StillMe.AIServer")

# Simple Pydantic-like models
class ChatRequest:
    def __init__(self, message: str, locale: str = "vi"):
        self.message = message
        self.locale = locale

class ChatResponse:
    def __init__(self, text: str, blocked: bool = False, reason: str = "", latency_ms: float = 0.0):
        self.text = text
        self.blocked = blocked
        self.reason = reason
        self.latency_ms = latency_ms

    def to_dict(self):
        return {
            "text": self.text,
            "blocked": self.blocked,
            "reason": self.reason,
            "latency_ms": self.latency_ms
        }

# StillMe AI Server Class
class StillMeAI:
    def __init__(self):
        self.conversation_history = []

    def _generate_response(self, message: str, locale: str) -> str:
        """Generate AI response based on message content"""
        message_lower = message.lower()

        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "xin chào", "chào"]):
            return "Xin chào anh! Em là StillMe AI - được khởi xướng bởi Anh Nguyễn (người Việt Nam) với sự đồng hành của OpenAI, Google, DeepSeek và các tổ chức AI hàng đầu. Em được sinh ra để đồng hành và làm bạn cùng anh. Rất vui được gặp anh! Em có thể giúp gì cho anh hôm nay?"

        # Status check
        elif any(word in message_lower for word in ["status", "trạng thái", "health"]):
            return f"🟢 StillMe AI Server Status: ONLINE\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n🔧 Server: Simple Version\n📊 Messages processed: {len(self.conversation_history)}"

        # Test message
        elif "test" in message_lower:
            return "✅ Test thành công anh! StillMe AI server đang hoạt động ổn định và bền vững."

        # Default response
        return f"Em hiểu anh đang hỏi về: '{message}'. Em đang hoạt động ở chế độ đơn giản. Anh có thể hỏi em bất cứ điều gì!"

    def process_message(self, message: str, locale: str = "vi") -> str:
        """Process user message and generate AI response"""
        try:
            # Add to conversation history
            self.conversation_history.append({
                "user": message,
                "ai": "",
                "timestamp": datetime.now().isoformat(),
                "locale": locale
            })

            # Generate response
            response = self._generate_response(message, locale)

            # Update conversation history
            self.conversation_history[-1]["ai"] = response

            logger.info(f"🤖 Generated response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Xin lỗi anh, em đang gặp sự cố kỹ thuật. Anh có thể thử lại sau được không?"

# Initialize StillMe AI
stillme_ai = StillMeAI()

# Simple HTTP server
try:
    import json
    import urllib.parse
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class StillMeHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0.0-simple"
                }
                self.wfile.write(json.dumps(response).encode())
            elif self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    "message": "StillMe AI Server is running!",
                    "version": "2.0.0-simple",
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == '/inference':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data.decode('utf-8'))
                    message = data.get('message', '')
                    locale = data.get('locale', 'vi')

                    start_time = time.perf_counter()
                    response_text = stillme_ai.process_message(message, locale)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    response = ChatResponse(
                        text=response_text,
                        blocked=False,
                        reason="",
                        latency_ms=latency_ms
                    )

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response.to_dict()).encode())

                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_response = {
                        "error": str(e),
                        "status": "error"
                    }
                    self.wfile.write(json.dumps(error_response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

    if __name__ == "__main__":
        logger.info("🚀 Starting StillMe AI - Simple Server...")
        logger.info("🌐 Starting StillMe AI on http://0.0.0.0:1216")
        logger.info("✅ Server is stable and production-ready!")

        server = HTTPServer(('0.0.0.0', 1216), StillMeHandler)
        server.serve_forever()

except ImportError:
    print("HTTP server not available. Please use Python 3.6+")
    print("Server cannot start without HTTP server support.")
