#!/usr/bin/env python3
"""
VPS Gateway Proxy - Chỉ làm proxy forward request
Bảo mật: HMAC signing, rate limiting, timeout, secure logging
Không xử lý AI logic, chỉ forward đến Local PC Backend qua SSH tunnel
"""
import os
import time
import json
import logging
import requests
import hmac
import hashlib
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from collections import defaultdict, deque
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
GATEWAY_PORT = int(os.getenv('GATEWAY_PORT', '21568'))
LOCAL_BACKEND_URL = os.getenv('LOCAL_BACKEND_URL', 'http://localhost:1216')
GATEWAY_SECRET = os.getenv('GATEWAY_SECRET', '')
REQUEST_CONNECT_TIMEOUT = float(os.getenv('REQUEST_CONNECT_TIMEOUT', '10'))
REQUEST_READ_TIMEOUT = float(os.getenv('REQUEST_READ_TIMEOUT', '20'))
RATE_LIMIT_RPS = int(os.getenv('RATE_LIMIT_RPS', '10'))
RATE_LIMIT_BURST = int(os.getenv('RATE_LIMIT_BURST', '20'))

# Rate limiting (token bucket per IP)
rate_limit_buckets = defaultdict(lambda: {"tokens": RATE_LIMIT_BURST, "last": time.time()})
rate_limit_lock = threading.Lock()

def check_rate_limit(ip: str) -> bool:
    """Check if IP is within rate limit"""
    now = time.time()
    with rate_limit_lock:
        bucket = rate_limit_buckets[ip]
        # Refill tokens
        elapsed = now - bucket["last"]
        bucket["tokens"] = min(RATE_LIMIT_BURST, bucket["tokens"] + elapsed * RATE_LIMIT_RPS)
        bucket["last"] = now
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False

def create_hmac_signature(body: bytes) -> tuple[str, str]:
    """Create HMAC signature for request"""
    timestamp = str(int(time.time() * 1000))
    signature = hmac.new(
        GATEWAY_SECRET.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "mode": "vps-proxy",
        "local_backend": LOCAL_BACKEND_URL,
        "timestamp": datetime.now().isoformat(),
        "service": "StillMe VPS Gateway Proxy"
    }), 200

@app.route('/chat', methods=['POST'])
@app.route('/send-message', methods=['POST'])
def chat():
    """Proxy chat endpoint - forward to local backend with HMAC signing"""
    try:
        # Get client IP for rate limiting
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
        
        # Check rate limit
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({
                "error": "Rate limit exceeded",
                "status": "error"
            }), 429
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        user_message = data.get('message')
        session_id = data.get('session_id', 'default')
        user_id = request.headers.get('X-User-ID', 'anonymous')
        user_lang = request.headers.get('X-User-Lang', 'vi')
        
        if not user_message:
            return jsonify({
                "error": "No message provided",
                "status": "error"
            }), 400
        
        # Log request (safe logging - no body content)
        logger.info(f"Proxy request: user_id={user_id}, session_id={session_id}, message_length={len(user_message)}")
        
        # Prepare request for local backend
        backend_payload = {
            "message": user_message,
            "session_id": session_id,
            "user_id": user_id,
            "language": user_lang
        }
        
        # Create HMAC signature
        body_bytes = json.dumps(backend_payload).encode('utf-8')
        timestamp, signature = create_hmac_signature(body_bytes)
        
        # Forward to local backend with HMAC
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{LOCAL_BACKEND_URL}/chat",
                data=body_bytes,
                timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT),
                headers={
                    "Content-Type": "application/json",
                    "X-Timestamp": timestamp,
                    "X-Signature": signature,
                    "X-Forwarded-For": request.remote_addr,
                    "X-User-ID": user_id,
                    "X-User-Lang": user_lang
                }
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                backend_data = response.json()
                
                # Log response (safe logging)
                logger.info(f"Proxy response: status=success, latency={latency:.1f}ms")
                
                # Return response in expected format
                return jsonify({
                    "model": backend_data.get("model", "stillme-local"),
                    "response": backend_data.get("text", backend_data.get("response", "")),
                    "timestamp": backend_data.get("timestamp", time.time()),
                    "engine": backend_data.get("engine", "stillme-local"),
                    "status": "success",
                    "latency_ms": latency
                }), 200
            else:
                logger.error(f"Backend error: {response.status_code}")
                return jsonify({
                    "error": f"Backend error: {response.status_code}",
                    "status": "error"
                }), 500
                
        except requests.exceptions.Timeout:
            logger.warning("Backend timeout")
            return jsonify({
                "error": "Backend timeout - local StillMe may be offline",
                "status": "error"
            }), 504
        except requests.exceptions.ConnectionError:
            logger.error("Backend connection error")
            return jsonify({
                "error": "Cannot connect to local StillMe backend",
                "status": "error"
            }), 503
        except Exception as e:
            logger.error(f"Backend error: {type(e).__name__}")
            return jsonify({
                "error": f"Backend error: {str(e)}",
                "status": "error"
            }), 500
        
    except Exception as e:
        logger.error(f"Proxy error: {type(e).__name__}")
        return jsonify({
            "model": "error",
            "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "error",
            "status": "error",
            "error": str(e)[:100]
        }), 500

@app.route('/admin/backend-status', methods=['GET'])
def backend_status():
    """Check local backend status"""
    try:
        response = requests.get(f"{LOCAL_BACKEND_URL}/health", timeout=5.0)
        if response.status_code == 200:
            return jsonify({
                "status": "connected",
                "backend_url": LOCAL_BACKEND_URL,
                "response": response.json()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "backend_url": LOCAL_BACKEND_URL,
                "error": f"HTTP {response.status_code}"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "disconnected",
            "backend_url": LOCAL_BACKEND_URL,
            "error": str(e)
        }), 503

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status": "error"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "status": "error"
    }), 500

if __name__ == '__main__':
    print(f"🚀 StillMe VPS Gateway Proxy starting on port {GATEWAY_PORT}...")
    print(f"📡 Forwarding requests to: {LOCAL_BACKEND_URL}")
    print(f"🔒 Security: HMAC signing enabled")
    print(f"⏱️  Timeouts: connect={REQUEST_CONNECT_TIMEOUT}s, read={REQUEST_READ_TIMEOUT}s")
    print(f"🚦 Rate limit: {RATE_LIMIT_RPS} RPS, burst={RATE_LIMIT_BURST}")
    print("=" * 50)
    
    if not GATEWAY_SECRET:
        print("⚠️  WARNING: GATEWAY_SECRET not set - HMAC signing disabled")
    
    app.run(host='0.0.0.0', port=GATEWAY_PORT, debug=False)
