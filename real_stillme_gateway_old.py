#!/usr/bin/env python3
"""
🌐 REAL STILLME GATEWAY - GATEWAY THẬT KẾT NỐI VỚI STILLME AI SERVER

PURPOSE / MỤC ĐÍCH:
- Gateway thật kết nối với StillMe AI Server thay vì câu trả lời có sẵn
- Xử lý yêu cầu chat và chuyển tiếp đến AI Server
- Hỗ trợ dịch thuật tự động (Gemma + NLLB)
- Quản lý phong cách giao tiếp động

FUNCTIONALITY / CHỨC NĂNG:
- Endpoint /send-message: Xử lý tin nhắn chat
- Endpoint /health: Kiểm tra sức khỏe gateway
- Dịch thuật tự động: vi ↔ en, ja ↔ en, etc.
- Phong cách giao tiếp: anh/em, mình/bạn, etc.
- Fallback response khi AI Server không khả dụng
- CORS support cho cross-origin requests

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Flask framework với CORS middleware
- Kết nối HTTP đến StillMe AI Server (port 1216)
- UnifiedAPIManager cho dịch thuật
- CommunicationStyleManager cho phong cách giao tiếp
- Error handling và fallback responses
- UTF-8 encoding support
"""

import logging
import json
import time
import requests
from datetime import datetime
import sys
import os

# Try to import Flask
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    print("Warning: Flask not available. Install with: pip install flask flask-cors")
    FLASK_AVAILABLE = False
    # Create dummy classes
    class Flask:
        def __init__(self, *args, **kwargs):
            pass
        def route(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def run(self, *args, **kwargs):
            pass
    class CORS:
        def __init__(self, *args, **kwargs):
            pass
    def jsonify(*args, **kwargs):
        return json.dumps(*args, **kwargs)

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stillme_core'))

# Try to import StillMe modules
try:
    from stillme_core.modules.communication_style_manager import CommunicationStyleManager
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
    STILLME_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import StillMe modules: {e}")
    CommunicationStyleManager = None
    UnifiedAPIManager = None
    STILLME_MODULES_AVAILABLE = False

# Cấu hình logging chi tiết
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cấu hình StillMe AI Server
STILLME_AI_SERVER_URL = "http://localhost:1216"
STILLME_AI_SERVER_ENDPOINT = "/inference"

# Khởi tạo Flask app
if FLASK_AVAILABLE:
    app = Flask(__name__)
    CORS(app)
else:
    app = Flask(__name__)

def check_ai_server_health():
    """Kiểm tra sức khỏe của StillMe AI Server"""
    try:
        response = requests.get(f"{STILLME_AI_SERVER_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"AI Server health check failed: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    ai_server_healthy = check_ai_server_health()
    
    return jsonify({
        "status": "healthy" if ai_server_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "ai_server_status": "connected" if ai_server_healthy else "disconnected",
        "ai_server_url": STILLME_AI_SERVER_URL,
        "gateway_version": "1.0.0"
    })

@app.route('/send-message', methods=['POST'])
def send_message():
    """Main endpoint for sending messages to StillMe AI"""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        user_message = data.get('message', '')
        language = data.get('language', 'vi')
        
        if not user_message:
            return jsonify({
                "error": "No message provided",
                "status": "error"
            }), 400
        
        logger.info(f"📨 Received message: {user_message[:50]}...")
        
        # Detect source language from headers or content
        user_lang_header = request.headers.get('X-User-Lang', language)
        src_lang = user_lang_header if user_lang_header else 'vi'
        
        # Initialize API manager for translation
        if not STILLME_MODULES_AVAILABLE or UnifiedAPIManager is None:
            logger.warning("⚠️ UnifiedAPIManager not available, skipping translation")
            api_manager = None
            core_lang = 'en'
        else:
            try:
                api_manager = UnifiedAPIManager()
                core_lang = getattr(api_manager, 'translation_core_lang', 'en')
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize UnifiedAPIManager: {e}")
                api_manager = None
                core_lang = 'en'
        
        # Translation metadata
        translation_meta = {
            "orig_lang": src_lang,
            "target_lang": src_lang,
            "input_translated": False,
            "engines": {"in": "none", "out": "none"},
            "confidence": {"in": 1.0, "out": 1.0}
        }
        
        # Pre-translate input if needed
        processed_message = user_message
        if src_lang != core_lang and api_manager is not None:
            try:
                logger.info(f"🌐 Pre-translating from {src_lang} to {core_lang}")
                input_translation = api_manager.translate(user_message, src_lang, core_lang)
                if input_translation["engine"] != "none":
                    processed_message = input_translation["text"]
                    translation_meta["input_translated"] = True
                    translation_meta["engines"]["in"] = input_translation["engine"]
                    translation_meta["confidence"]["in"] = input_translation["confidence"]
                    logger.info(f"✅ Input translated using {input_translation['engine']} (confidence: {input_translation['confidence']:.2f})")
            except Exception as e:
                logger.warning(f"⚠️ Pre-translation failed: {e}")
        
        # Initialize communication style manager
        if STILLME_MODULES_AVAILABLE and CommunicationStyleManager is not None:
            try:
                comms_manager = CommunicationStyleManager()
                logger.info("🎭 Communication Style Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize CommunicationStyleManager: {e}")
                comms_manager = None
        else:
            comms_manager = None
            logger.warning("⚠️ CommunicationStyleManager not available")
        
        # Check AI Server health
        if not check_ai_server_health():
            logger.error("❌ StillMe AI Server is not available")
            return jsonify({
                "received": data,
                "response": "Xin lỗi, StillMe AI Server hiện tại không khả dụng. Vui lòng thử lại sau.",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "ai_server_status": "disconnected",
                "error": "AI Server unavailable"
            }), 503
        
        # Forward request to StillMe AI Server
        try:
            ai_request = {
                "message": processed_message,
                "locale": core_lang
            }
            
            logger.info(f"🤖 Forwarding to AI Server: {processed_message[:50]}...")
            
            ai_response = requests.post(
                f"{STILLME_AI_SERVER_URL}{STILLME_AI_SERVER_ENDPOINT}",
                json=ai_request,
                timeout=30
            )
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                ai_text = ai_data.get('text', 'Không có phản hồi từ AI.')
                
                logger.info(f"✅ AI Server response: {ai_text[:50]}...")
                
                # Post-translate output if needed
                final_response = ai_text
                if src_lang != core_lang and api_manager is not None and not any(phrase in ai_text.lower() for phrase in ["reply in", "respond in", "answer in"]):
                    try:
                        logger.info(f"🌐 Post-translating from {core_lang} to {src_lang}")
                        output_translation = api_manager.translate(ai_text, core_lang, src_lang)
                        if output_translation["engine"] != "none":
                            final_response = output_translation["text"]
                            translation_meta["engines"]["out"] = output_translation["engine"]
                            translation_meta["confidence"]["out"] = output_translation["confidence"]
                            logger.info(f"✅ Output translated using {output_translation['engine']} (confidence: {output_translation['confidence']:.2f})")
                    except Exception as e:
                        logger.warning(f"⚠️ Post-translation failed: {e}")
                
                response = {
                    "received": data,
                    "response": final_response,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "ai_server_status": "connected",
                    "ai_server_response": ai_data,
                    "meta": translation_meta
                }
                
                return jsonify(response)
                
            else:
                logger.error(f"❌ AI Server returned status {ai_response.status_code}")
                return jsonify({
                    "received": data,
                    "response": f"Lỗi từ AI Server: {ai_response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "ai_server_status": "error",
                    "error": f"AI Server returned {ai_response.status_code}"
                }), 500
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request to AI Server failed: {e}")
            return jsonify({
                "received": data,
                "response": "Không thể kết nối đến StillMe AI Server. Vui lòng thử lại sau.",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "ai_server_status": "connection_failed",
                "error": str(e)
            }), 503
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in send_message: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Real StillMe Gateway is running!",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "/health": "Health check",
            "/send-message": "Send message to StillMe AI"
        }
    })

if __name__ == '__main__':
    if FLASK_AVAILABLE:
        logger.info("🚀 Starting Real StillMe Gateway...")
        logger.info("📡 Gateway will be available at: http://localhost:21568")
        logger.info("🤖 StillMe AI Server: http://localhost:1216")
        logger.info("🌐 Chat UI can connect to: http://localhost:21568")
        logger.info("==================================================")
        
        app.run(
            host='0.0.0.0',
            port=21568,
            debug=True,
            threaded=True
        )
    else:
        print("Flask not available. Please install with: pip install flask flask-cors")
        print("Gateway cannot start without Flask.")
