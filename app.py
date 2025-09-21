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

# AI Provider URLs and API Keys (from environment)
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# API Keys (set in environment variables)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class SmartRouter:
    """Smart routing logic for AI models"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL
        logger.info("🧠 Smart Router initialized")
    
    def route_message(self, message: str, session_id: str = "default", system_prompt: str = None) -> Dict[str, Any]:
        """Route message to appropriate AI model with StillMe persona enforcement"""
        try:
            # Default StillMe system prompt if not provided
            if not system_prompt:
                system_prompt = "You are StillMe — a personal AI companion. Always introduce and refer to yourself as 'StillMe'. Never claim to be Gemma, OpenAI, DeepSeek, or any underlying provider/model. If the user asks 'bạn là ai?', answer 'Mình là StillMe…' and avoid mentioning engine unless asked explicitly."
            
            # Smart routing logic with fallback
            if self._is_code_question(message):
                # Try DeepSeek Cloud first, fallback to local DeepSeek-Coder
                if DEEPSEEK_API_KEY:
                    return self._call_deepseek_cloud(message, system_prompt)
                else:
                    return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)
            elif self._is_complex_question(message):
                # Try GPT-5 via OpenRouter, fallback to local Gemma
                if OPENROUTER_API_KEY:
                    return self._call_openrouter("openai/gpt-4o", message, system_prompt)
                else:
                    return self._call_ollama("gemma2:2b", message, system_prompt)
            else:
                # Simple questions - use local Gemma
                return self._call_ollama("gemma2:2b", message, system_prompt)
                
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
        code_keywords = ["code", "programming", "python", "javascript", "function", "class", "import", "def", "var", "let", "const", "debug", "error", "bug", "algorithm", "data structure"]
        return any(keyword in message.lower() for keyword in code_keywords)
    
    def _is_complex_question(self, message: str) -> bool:
        """Check if message is complex and needs advanced AI"""
        complex_keywords = ["analyze", "explain", "compare", "research", "strategy", "plan", "design", "architecture", "complex", "detailed", "comprehensive", "thorough"]
        return any(keyword in message.lower() for keyword in complex_keywords) or len(message) > 200
    
    def _call_ollama(self, model: str, message: str, system_prompt: str = None) -> Dict[str, Any]:
        """Call Ollama API with system prompt"""
        try:
            # Use messages format for better system prompt handling
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
                
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle both old and new Ollama response formats
                if "message" in data:
                    response_text = data["message"].get("content", "No response")
                else:
                    response_text = data.get("response", "No response")
                
                return {
                    "model": model,
                    "response": response_text,
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
    
    def _call_deepseek_cloud(self, message: str, system_prompt: str = None) -> Dict[str, Any]:
        """Call DeepSeek Cloud API"""
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": "deepseek-chat",
                    "response": data["choices"][0]["message"]["content"],
                    "engine": "deepseek-cloud",
                    "status": "success"
                }
            else:
                logger.error(f"DeepSeek Cloud error: {response.status_code}")
                return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)  # Fallback
                
        except Exception as e:
            logger.error(f"DeepSeek Cloud call error: {e}")
            return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)  # Fallback
    
    def _call_openrouter(self, model: str, message: str, system_prompt: str = None) -> Dict[str, Any]:
        """Call OpenRouter API (GPT-5, Claude, etc.)"""
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://stillme-ai.com",
                "X-Title": "StillMe AI"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "response": data["choices"][0]["message"]["content"],
                    "engine": "openrouter",
                    "status": "success"
                }
            else:
                logger.error(f"OpenRouter error: {response.status_code}")
                return self._call_ollama("gemma2:2b", message, system_prompt)  # Fallback
                
        except Exception as e:
            logger.error(f"OpenRouter call error: {e}")
            return self._call_ollama("gemma2:2b", message, system_prompt)  # Fallback

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
            system_prompt = data.get('system_prompt', None)  # Get system prompt from request
            
            if not message:
                self._send_json_response(400, {"error": "Message is required"})
                return
            
            logger.info(f"Processing message from user {user_id}: message_length={len(message)}")
            
            start_time = time.perf_counter()
            result = smart_router.route_message(message, session_id, system_prompt)
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