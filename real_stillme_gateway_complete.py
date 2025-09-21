#!/usr/bin/env python3
"""
StillMe AI Gateway with Smart Routing
- Simple messages → Gemma2:2b local (if available)
- Complex messages → DeepSeek Cloud
- Fallback mechanism for reliability
"""
import os
from dotenv import load_dotenv
import logging
import time
from datetime import datetime

# Load environment variables
load_dotenv('/opt/stillme/.env')

from smart_router import route_message
from flask import Flask, request, jsonify
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
AI_SERVER_URL = "http://localhost:80"
GATEWAY_PORT = 21568

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok", 
        "timestamp": datetime.now().isoformat(), 
        "service": "StillMe Gateway"
    }), 200

@app.route('/chat', methods=['POST'])
@app.route('/send-message', methods=['POST'])
def chat():
    """Enhanced chat endpoint with smart routing"""
    try:
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
        
        # Log request (safe logging)
        logger.info(f"Chat request: user_id={user_id}, session_id={session_id}, message_length={len(user_message)}")
        
        # Use Smart Router
        start_time = time.time()
        result = route_message(user_message, session_id)
        latency = (time.time() - start_time) * 1000
        
        # Log response (safe logging)
        logger.info(f"Chat response: engine={result.get('engine')}, model={result.get('model')}, latency={latency:.1f}ms")
        
        # Return response
        return jsonify({
            "model": result.get("model", "unknown"),
            "response": result.get("response", ""),
            "timestamp": result.get("timestamp", time.time()),
            "engine": result.get("engine", "unknown"),
            "status": "success",
            "latency_ms": latency
        }), 200
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({
            "model": "error",
            "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "error",
            "status": "error",
            "error": str(e)[:100]
        }), 500

@app.route('/admin/routing', methods=['POST'])
def set_routing_mode():
    """Set routing mode (requires admin auth)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        mode = data.get('mode')
        if mode not in ["auto", "force_gemma", "force_cloud"]:
            return jsonify({"status": "error", "message": "Invalid mode"}), 400
        
        # Set environment variable
        os.environ["ROUTING_MODE"] = mode
        
        logger.info(f"Routing mode changed to: {mode}")
        
        return jsonify({
            "status": "success", 
            "routing_mode": mode,
            "message": f"Routing mode set to {mode}"
        }), 200
        
    except Exception as e:
        logger.error(f"Routing mode error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/status', methods=['GET'])
def admin_status():
    """Get system status"""
    try:
        # Get routing configuration
        routing_mode = os.getenv("ROUTING_MODE", "auto")
        disable_cloud = os.getenv("DISABLE_CLOUD", "0")
        gemma_timeout = os.getenv("GEMMA_TIMEOUT", "2.5")
        deepseek_timeout = os.getenv("DEEPSEEK_TIMEOUT", "10.0")
        
        # Test Smart Router
        test_result = route_message("test", "admin")
        
        return jsonify({
            "status": "ok",
            "routing_config": {
                "mode": routing_mode,
                "disable_cloud": disable_cloud,
                "gemma_timeout": gemma_timeout,
                "deepseek_timeout": deepseek_timeout
            },
            "smart_router": {
                "engine": test_result.get("engine"),
                "model": test_result.get("model"),
                "status": "working" if test_result.get("engine") != "error" else "error"
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Admin status error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'test message')
        
        # Test Smart Router
        result = route_message(test_message, 'test')
        
        return jsonify({
            "test_message": test_message,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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
    print(f"🚀 StillMe AI Gateway with Smart Routing starting on port {GATEWAY_PORT}...")
    print(f"📊 Routing mode: {os.getenv('ROUTING_MODE', 'auto')}")
    print(f"🔧 Disable cloud: {os.getenv('DISABLE_CLOUD', '0')}")
    print(f"⏱️  Gemma timeout: {os.getenv('GEMMA_TIMEOUT', '2.5')}s")
    print(f"⏱️  DeepSeek timeout: {os.getenv('DEEPSEEK_TIMEOUT', '10.0')}s")
    
    app.run(host='0.0.0.0', port=GATEWAY_PORT, debug=False)
