#!/usr/bin/env python3
"""
Local StillMe Backend - Chạy trên máy tính cục bộ
Xử lý routing logic và AI models (Gemma, DeepSeek Coder, DeepSeek Cloud)
Bảo mật: HMAC authentication, bind 127.0.0.1 only
"""
import os
import time
import json
import logging
import requests
import hmac
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_PORT = int(os.getenv('BACKEND_PORT', '1216'))
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
GATEWAY_SECRET = os.getenv('GATEWAY_SECRET', '')
DRIFT_MS = 5 * 60 * 1000  # 5 minutes

class SmartRouter:
    def __init__(self):
        self.gemma_timeout = float(os.getenv('GEMMA_TIMEOUT', '3.0'))
        self.deepseek_timeout = float(os.getenv('DEEPSEEK_TIMEOUT', '30.0'))
        self.deepseek_retry = int(os.getenv('DEEPSEEK_RETRY', '2'))
        self.deepseek_backoff = float(os.getenv('DEEPSEEK_BACKOFF', '2.0'))
        
    def is_simple_question(self, text: str) -> bool:
        """Kiểm tra câu hỏi đơn giản"""
        if len(text) > 100:
            return False
            
        simple_keywords = [
            'xin chào', 'hello', 'hi', 'chào', 'cảm ơn', 'thank you',
            '2+2', 'ping', 'pong', 'thời tiết', 'weather', 'giờ', 'time',
            'tên', 'name', 'tuổi', 'age', 'khỏe không', 'how are you'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in simple_keywords)
    
    def is_code_question(self, text: str) -> bool:
        """Kiểm tra câu hỏi về code"""
        code_keywords = [
            'code', 'python', 'dart', 'kotlin', 'java', 'javascript',
            'function', 'class', 'method', 'variable', 'loop', 'array',
            'algorithm', 'bug', 'error', 'debug', 'implement', 'write code',
            'programming', 'development', 'syntax', 'compile', 'runtime',
            'viết code', 'lập trình', 'thuật toán', 'hàm', 'biến',
            'csv', 'json', 'api', 'database', 'sql', 'html', 'css'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in code_keywords)
    
    def is_complex_question(self, text: str) -> bool:
        """Kiểm tra câu hỏi phức tạp"""
        complex_keywords = [
            'phân tích', 'analyze', 'so sánh', 'compare', 'đánh giá', 'evaluate',
            'microservices', 'architecture', 'design pattern', 'scalability',
            'machine learning', 'ai', 'neural', 'model', 'training',
            'deploy', 'production', 'staging', 'testing', 'performance',
            'optimization', 'security', 'authentication', 'authorization'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in complex_keywords)
    
    def call_ollama(self, model: str, message: str, timeout: float = None) -> Dict:
        """Gọi Ollama local model"""
        if timeout is None:
            timeout = self.gemma_timeout
            
        try:
            logger.info(f"Calling Ollama model: {model}")
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": message,
                    "stream": False
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "")
                logger.info(f"Ollama {model} response: {content[:100]}...")
                return {
                    "model": model,
                    "response": content,
                    "engine": "ollama-local",
                    "status": "success"
                }
            else:
                logger.error(f"Ollama {model} error: {response.status_code}")
                return {"error": f"Ollama {model} error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Ollama {model} exception: {str(e)}")
            return {"error": f"Ollama {model} error: {str(e)}"}
    
    def call_deepseek_cloud(self, message: str, timeout: float = None) -> Dict:
        """Gọi DeepSeek Cloud"""
        if timeout is None:
            timeout = self.deepseek_timeout
            
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return {"error": "DEEPSEEK_API_KEY not found"}
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        start_time = time.perf_counter()
        
        for attempt in range(self.deepseek_retry + 1):
            try:
                logger.info(f"Calling DeepSeek Cloud (attempt {attempt + 1})")
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                
                data = response.json()
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    if content.strip():
                        return {
                            "model": "deepseek-chat",
                            "response": content,
                            "engine": "deepseek-cloud",
                            "status": "success",
                            "latency_ms": latency_ms
                        }
                    else:
                        return {"error": "Empty response from DeepSeek"}
                else:
                    return {"error": "No choices in response"}
                    
            except Exception as e:
                logger.error(f"DeepSeek Cloud error (attempt {attempt + 1}): {str(e)}")
                if attempt < self.deepseek_retry:
                    time.sleep(self.deepseek_backoff * (2 ** attempt))
                else:
                    return {"error": str(e)}
    
    def route_message(self, message: str, session_id: str = "default") -> Dict:
        """Route message to appropriate engine"""
        try:
            logger.info(f"Routing message: '{message}' with session: {session_id}")
            
            # 1. Câu đơn giản → Gemma2:2b
            if self.is_simple_question(message):
                logger.info("Simple question detected, using Gemma2:2b")
                result = self.call_ollama("gemma2:2b", message)
                if "error" in result:
                    logger.warning("Gemma2:2b failed, falling back to DeepSeek Cloud")
                    result = self.call_deepseek_cloud(message)
                return result
            
            # 2. Câu về code → DeepSeek Coder 6.7b
            elif self.is_code_question(message):
                logger.info("Code question detected, using DeepSeek Coder 6.7b")
                result = self.call_ollama("deepseek-coder:6.7b", message)
                if "error" in result:
                    logger.warning("DeepSeek Coder failed, falling back to DeepSeek Cloud")
                    result = self.call_deepseek_cloud(message)
                return result
            
            # 3. Câu phức tạp → DeepSeek Cloud
            elif self.is_complex_question(message):
                logger.info("Complex question detected, using DeepSeek Cloud")
                result = self.call_deepseek_cloud(message)
                if "error" in result:
                    logger.warning("DeepSeek Cloud failed, falling back to Gemma2:2b")
                    result = self.call_ollama("gemma2:2b", message)
                return result
            
            # 4. Câu khác → Gemma2:2b (default)
            else:
                logger.info("Default question, using Gemma2:2b")
                result = self.call_ollama("gemma2:2b", message)
                if "error" in result:
                    logger.warning("Gemma2:2b failed, falling back to DeepSeek Cloud")
                    result = self.call_deepseek_cloud(message)
                return result
                
        except Exception as e:
            logger.error(f"Error in route_message: {str(e)}")
            return {
                "status": "error",
                "engine": "fallback",
                "error": str(e)
            }

# Global router instance
smart_router = SmartRouter()

def verify_hmac(timestamp: str, body: bytes, signature: str) -> bool:
    """Verify HMAC signature from Gateway"""
    if not GATEWAY_SECRET:
        logger.warning("GATEWAY_SECRET not set, skipping HMAC verification")
        return True
    
    try:
        ts_int = int(timestamp)
    except (ValueError, TypeError):
        logger.warning("Invalid timestamp format")
        return False
    
    # Check timestamp drift
    now = int(time.time() * 1000)
    if abs(now - ts_int) > DRIFT_MS:
        logger.warning("Timestamp drift too large: %d ms", abs(now - ts_int))
        return False
    
    # Generate expected signature
    expected_sig = hmac.new(
        GATEWAY_SECRET.encode(),
        f"{ts_int}.".encode() + body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_sig, signature)

class StillMeBackendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._handle_health()
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/inference':
            self._handle_inference()
        elif self.path == '/chat':
            self._handle_inference()  # Same handler for /chat
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-User-ID, X-User-Lang')
        self.end_headers()
    
    def _handle_health(self):
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "mode": "local-backend",
            "routing": "smart",
            "models": {
                "simple": "gemma2:2b",
                "code": "deepseek-coder:6.7b",
                "complex": "deepseek-cloud"
            },
            "timestamp": datetime.now().isoformat(),
            "service": "StillMe Local Backend"
        }
        self._send_json_response(200, health_data)
    
    def _handle_inference(self):
        """Handle chat inference requests with HMAC verification"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Verify HMAC signature (except for health endpoint)
            if self.path != '/health':
                timestamp = self.headers.get('X-Timestamp')
                signature = self.headers.get('X-Signature')
                
                if not timestamp or not signature:
                    logger.warning("Missing HMAC headers")
                    self._send_json_response(401, {"error": "Unauthorized"})
                    return
                
                if not verify_hmac(timestamp, post_data, signature):
                    logger.warning("HMAC verification failed")
                    self._send_json_response(401, {"error": "Unauthorized"})
                    return
            
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
            
            # Add latency to result
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
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom log message format"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Main function to start the local backend"""
    logger.info("🚀 Starting StillMe Local Backend...")
    logger.info(f"📡 Backend will be available at: http://127.0.0.1:{BACKEND_PORT}")
    logger.info(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
    logger.info("🧠 Smart Routing: Simple → Gemma, Code → DeepSeek Coder, Complex → DeepSeek Cloud")
    logger.info("🔒 Security: HMAC authentication enabled")
    logger.info("🌐 Access: SSH reverse tunnel only (127.0.0.1)")
    logger.info("=" * 50)
    
    if not GATEWAY_SECRET:
        logger.warning("⚠️  GATEWAY_SECRET not set - HMAC verification disabled")
    
    try:
        # Bind only to localhost for security
        server = HTTPServer(('127.0.0.1', BACKEND_PORT), StillMeBackendHandler)
        logger.info(f"✅ Local Backend started successfully on 127.0.0.1:{BACKEND_PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Local Backend stopped by user")
    except Exception as e:
        logger.error(f"❌ Local Backend failed to start: {e}")

if __name__ == "__main__":
    main()
