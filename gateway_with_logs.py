#!/usr/bin/env python3
"""
StillMe Gateway with Detailed Logging
Gateway với logging chi tiết để theo dõi tiến trình
"""

import logging
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# Cấu hình logging chi tiết
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/stillme_gateway/gateway.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Log khi khởi động
logger.info("🚀 Starting StillMe Gateway...")
logger.info("📅 Current time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/')
def root():
    logger.info("📥 GET / - Root endpoint accessed")
    response = {
        "status": "ok", 
        "message": "StillMe Gateway is running",
        "timestamp": datetime.now().isoformat(),
        "server": "Flask with detailed logging"
    }
    logger.info("📤 GET / - Response: " + json.dumps(response))
    return jsonify(response)

@app.route('/health')
def health():
    logger.info("📥 GET /health - Health check accessed")
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "Gateway running smoothly"
    }
    logger.info("📤 GET /health - Response: " + json.dumps(response))
    return jsonify(response)

@app.route('/send-message', methods=['POST'])
def send_message():
    logger.info("📥 POST /send-message - Message endpoint accessed")
    
    try:
        data = request.get_json()
        logger.info("📨 Received data: " + json.dumps(data))
        
        user_message = data.get('message', '').lower()
        
        # Simple AI responses based on keywords
        if 'xin chào' in user_message or 'hello' in user_message:
            ai_response = "Xin chào! Tôi là StillMe AI. Rất vui được gặp bạn! 😊"
        elif 'thủ đô' in user_message and 'việt nam' in user_message:
            ai_response = "Thủ đô của Việt Nam là Hà Nội. Đây là thành phố lớn thứ hai của Việt Nam sau TP. Hồ Chí Minh."
        elif 'việt nam' in user_message:
            ai_response = "Việt Nam là một quốc gia ở Đông Nam Á với dân số khoảng 98 triệu người. Thủ đô là Hà Nội."
        elif 'hà nội' in user_message:
            ai_response = "Hà Nội là thủ đô của Việt Nam, nằm ở phía Bắc. Đây là trung tâm chính trị, văn hóa của đất nước."
        elif 'tp hồ chí minh' in user_message or 'sài gòn' in user_message:
            ai_response = "TP. Hồ Chí Minh (Sài Gòn) là thành phố lớn nhất Việt Nam, trung tâm kinh tế của cả nước."
        elif 'cảm ơn' in user_message or 'thank' in user_message:
            ai_response = "Không có gì! Tôi rất vui được giúp đỡ bạn. 😊"
        elif 'tạm biệt' in user_message or 'bye' in user_message:
            ai_response = "Tạm biệt! Hẹn gặp lại bạn lần sau. 👋"
        elif 'bạn là ai' in user_message or 'who are you' in user_message:
            ai_response = "Tôi là StillMe AI, một trợ lý AI được tạo ra bởi Anh Nguyễn. Tôi có thể giúp bạn trả lời các câu hỏi!"
        elif 'giúp' in user_message or 'help' in user_message:
            ai_response = "Tôi có thể giúp bạn trả lời các câu hỏi về Việt Nam, thời tiết, hoặc trò chuyện thông thường. Hãy hỏi tôi bất cứ điều gì!"
        else:
            ai_response = f"Tôi hiểu bạn đang nói về '{data.get('message', '')}'. Đây là một chủ đề thú vị! Bạn có thể hỏi tôi về Việt Nam, thời tiết, hoặc bất cứ điều gì khác."
        
        response = {
            "received": data,
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        logger.info("📤 POST /send-message - Response: " + json.dumps(response))
        return jsonify(response)
        
    except Exception as e:
        logger.error("❌ POST /send-message - Error: " + str(e))
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/status')
def status():
    logger.info("📥 GET /status - Status endpoint accessed")
    response = {
        "gateway_status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/", "/health", "/send-message", "/status"],
        "log_file": "/opt/stillme_gateway/gateway.log"
    }
    logger.info("📤 GET /status - Response: " + json.dumps(response))
    return jsonify(response)

if __name__ == '__main__':
    logger.info("🔧 Configuring Flask app...")
    logger.info("🌐 Starting server on 0.0.0.0:9000...")
    logger.info("📝 Logs will be saved to: /opt/stillme_gateway/gateway.log")
    logger.info("✅ Gateway ready to accept connections!")
    
    try:
        app.run(host='0.0.0.0', port=9000, debug=False)
    except Exception as e:
        logger.error("❌ Failed to start server: " + str(e))
        raise
