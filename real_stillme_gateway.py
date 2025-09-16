#!/usr/bin/env python3
"""
Real StillMe Gateway - Kết nối với StillMe AI Server thật
Gateway thật kết nối với StillMe AI Server thay vì câu trả lời có sẵn
"""

import logging
import json
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stillme_core'))

try:
    from modules.communication_style_manager import CommunicationStyleManager
    from modules.api_provider_manager import UnifiedAPIManager
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    CommunicationStyleManager = None
    UnifiedAPIManager = None

# Cấu hình logging chi tiết
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "http://192.168.1.12:3000", "http://192.168.1.12:3001"])

# Cấu hình StillMe AI Server
STILLME_AI_SERVER_URL = "http://localhost:1216"
STILLME_AI_SERVER_ENDPOINT = "/inference"

# Log khi khởi động
logger.info("🚀 Starting Real StillMe Gateway...")
logger.info("📡 Gateway will be available at: http://localhost:21568")
logger.info("🤖 StillMe AI Server: " + STILLME_AI_SERVER_URL)
logger.info("🌐 Chat UI can connect to: http://localhost:21568")
logger.info("=" * 50)

def check_stillme_ai_server():
    """Kiểm tra StillMe AI Server có hoạt động không"""
    try:
        response = requests.get(f"{STILLME_AI_SERVER_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"⚠️ StillMe AI Server không khả dụng: {e}")
        return False

@app.route('/')
def root():
    logger.info("📥 GET / - Root endpoint accessed")
    ai_server_status = "connected" if check_stillme_ai_server() else "disconnected"
    response = {
        "status": "ok",
        "message": "Real StillMe Gateway is running",
        "timestamp": datetime.now().isoformat(),
        "stillme_ai_server": ai_server_status,
        "version": "2.0.0"
    }
    logger.info("📤 GET / - Response: " + json.dumps(response))
    return jsonify(response)

@app.route('/health')
def health():
    logger.info("📥 GET /health - Health endpoint accessed")
    ai_server_status = "connected" if check_stillme_ai_server() else "disconnected"
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stillme_ai_server": ai_server_status,
        "uptime": "Real Gateway running smoothly"
    }
    logger.info("📤 GET /health - Response: " + json.dumps(response))
    return jsonify(response)

@app.route('/send-message', methods=['POST'])
def send_message():
    logger.info("📥 POST /send-message - Message endpoint accessed")
    
    try:
        data = request.get_json()
        logger.info("📨 Received data: " + json.dumps(data))
        
        user_message = data.get('message', '')
        language = data.get('language', 'vi')
        
        # Detect source language from headers or content
        user_lang_header = request.headers.get('X-User-Lang', language)
        src_lang = user_lang_header if user_lang_header else 'vi'
        
        # Initialize API manager for translation
        if UnifiedAPIManager is None:
            logger.warning("⚠️ UnifiedAPIManager not available, skipping translation")
            api_manager = None
            core_lang = 'en'
        else:
            api_manager = UnifiedAPIManager()
            core_lang = api_manager.translation_core_lang
        
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
            logger.info(f"🌐 Pre-translating from {src_lang} to {core_lang}")
            input_translation = api_manager.translate(user_message, src_lang, core_lang)
            if input_translation["engine"] != "none":
                processed_message = input_translation["text"]
                translation_meta["input_translated"] = True
                translation_meta["engines"]["in"] = input_translation["engine"]
                translation_meta["confidence"]["in"] = input_translation["confidence"]
                logger.info(f"✅ Input translated using {input_translation['engine']} (confidence: {input_translation['confidence']:.2f})")
        
        # Initialize communication style manager
        if CommunicationStyleManager is not None:
            comms_manager = CommunicationStyleManager()
            logger.info("🎭 Communication Style Manager initialized")
        else:
            comms_manager = None
            logger.warning("⚠️ CommunicationStyleManager not available")
        
        # Kiểm tra StillMe AI Server
        if not check_stillme_ai_server():
            logger.warning("⚠️ StillMe AI Server không khả dụng, sử dụng fallback response")
            fallback_response = {
                "received": data,
                "response": "Xin lỗi, StillMe AI Server hiện tại không khả dụng. Vui lòng thử lại sau hoặc khởi động AI Server.",
                "timestamp": datetime.now().isoformat(),
                "status": "ai_server_unavailable",
                "ai_server_status": "disconnected"
            }
            logger.info("📤 POST /send-message - Fallback Response: " + json.dumps(fallback_response))
            return jsonify(fallback_response)
        
        # Gửi request tới StillMe AI Server thật
        logger.info("🤖 Forwarding request to StillMe AI Server...")
        
        ai_request = {
            "message": processed_message,
            "locale": core_lang
        }
        
        try:
            ai_response = requests.post(
                f"{STILLME_AI_SERVER_URL}{STILLME_AI_SERVER_ENDPOINT}",
                json=ai_request,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                logger.info("✅ StillMe AI Server response: " + json.dumps(ai_data))
                
                # Lấy response từ field 'text' thay vì 'response'
                ai_text = ai_data.get('text', 'Không có phản hồi từ AI.')
                
                # Post-translate output if needed
                final_response = ai_text
                if src_lang != core_lang and api_manager is not None and not any(phrase in ai_text.lower() for phrase in ["reply in", "respond in", "answer in"]):
                    logger.info(f"🌐 Post-translating from {core_lang} to {src_lang}")
                    output_translation = api_manager.translate(ai_text, core_lang, src_lang)
                    if output_translation["engine"] != "none":
                        final_response = output_translation["text"]
                        translation_meta["engines"]["out"] = output_translation["engine"]
                        translation_meta["confidence"]["out"] = output_translation["confidence"]
                        logger.info(f"✅ Output translated using {output_translation['engine']} (confidence: {output_translation['confidence']:.2f})")
                
                response = {
                    "received": data,
                    "response": final_response,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "ai_server_status": "connected",
                    "ai_server_response": ai_data,
                    "meta": translation_meta
                }
            else:
                logger.error(f"❌ StillMe AI Server error: {ai_response.status_code}")
                response = {
                    "received": data,
                    "response": f"Lỗi từ StillMe AI Server: {ai_response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                    "status": "ai_server_error",
                    "ai_server_status": "error"
                }
                
        except requests.exceptions.Timeout:
            logger.error("⏰ StillMe AI Server timeout")
            response = {
                "received": data,
                "response": "StillMe AI Server phản hồi quá chậm. Vui lòng thử lại.",
                "timestamp": datetime.now().isoformat(),
                "status": "ai_server_timeout",
                "ai_server_status": "timeout"
            }
        except Exception as e:
            logger.error(f"❌ Error calling StillMe AI Server: {e}")
            response = {
                "received": data,
                "response": f"Lỗi kết nối tới StillMe AI Server: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "ai_server_connection_error",
                "ai_server_status": "connection_error"
            }
        
        logger.info("📤 POST /send-message - Response: " + json.dumps(response))
        return jsonify(response)
        
    except Exception as e:
        logger.error("❌ POST /send-message - Error: " + str(e))
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == '__main__':
    print("🚀 Starting Real StillMe Gateway...")
    print("📡 Gateway will be available at: http://localhost:21568")
    print("🤖 StillMe AI Server: " + STILLME_AI_SERVER_URL)
    print("🌐 Chat UI can connect to: http://localhost:21568")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=21568, debug=True)
