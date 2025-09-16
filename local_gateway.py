#!/usr/bin/env python3
"""
Local Gateway for Testing Chat UI
Gateway chạy local để test Chat UI mà không cần VPS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "http://192.168.1.12:3000", "http://192.168.1.12:3001"])

@app.route('/')
def root():
    logger.info("📥 GET / - Root endpoint accessed")
    response = {
        "status": "ok",
        "message": "StillMe Local Gateway is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    logger.info("📤 GET / - Response: " + str(response))
    return jsonify(response)

@app.route('/health')
def health():
    logger.info("📥 GET /health - Health endpoint accessed")
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "Local Gateway running smoothly"
    }
    logger.info("📤 GET /health - Response: " + str(response))
    return jsonify(response)

@app.route('/send-message', methods=['POST'])
def send_message():
    logger.info("📥 POST /send-message - Message endpoint accessed")
    
    try:
        data = request.get_json()
        logger.info("📨 Received data: " + str(data))
        
        user_message = data.get('message', '').lower()
        
        # Intelligent AI responses based on keywords
        if 'xin chào' in user_message or 'hello' in user_message or 'chào' in user_message:
            ai_response = "Xin chào! Tôi là StillMe AI, trợ lý thông minh được tạo ra bởi Anh Nguyễn. Rất vui được gặp bạn! 😊 Tôi có thể giúp bạn trả lời câu hỏi, trò chuyện, hoặc hỗ trợ công việc hàng ngày."
        elif 'stillme' in user_message or 'tên' in user_message:
            ai_response = "Đúng rồi! Tôi là StillMe AI. Tên tôi có nghĩa là 'Vẫn là tôi' - tôi luôn đồng hành và hỗ trợ bạn trong mọi tình huống. Tôi được tạo ra với mục đích làm bạn đồng hành thông minh và đáng tin cậy! 🤖"
        elif 'bạn là ai' in user_message or 'who are you' in user_message:
            ai_response = "Tôi là StillMe AI, một trợ lý AI thông minh được tạo ra bởi Anh Nguyễn (người Việt Nam). Tôi có sự hỗ trợ từ các tổ chức AI hàng đầu như OpenAI, Google, DeepSeek. Mục đích của tôi là đồng hành và kết bạn với mọi người! 🌟"
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
        elif 'giúp' in user_message or 'help' in user_message:
            ai_response = "Tôi có thể giúp bạn rất nhiều thứ! Tôi có thể trả lời câu hỏi, trò chuyện, giải thích kiến thức, hỗ trợ học tập, hoặc đơn giản là lắng nghe bạn. Hãy hỏi tôi bất cứ điều gì bạn muốn biết!"
        elif 'thời tiết' in user_message:
            ai_response = "Tôi chưa có thông tin thời tiết thời gian thực. Bạn có thể kiểm tra thời tiết trên các ứng dụng dự báo thời tiết hoặc website chính thức."
        elif 'hôm nay' in user_message:
            ai_response = f"Hôm nay là {datetime.now().strftime('%d/%m/%Y')}. Bạn có muốn hỏi gì về ngày hôm nay không?"
        else:
            # More intelligent default response
            ai_response = f"Tôi hiểu bạn đang nói về '{data.get('message', '')}'. Đây là một chủ đề thú vị! Tôi là StillMe AI và tôi có thể giúp bạn tìm hiểu sâu hơn về chủ đề này, hoặc trò chuyện về bất cứ điều gì khác. Bạn muốn biết thêm gì?"
        
        response = {
            "received": data,
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        logger.info("📤 POST /send-message - Response: " + str(response))
        return jsonify(response)
        
    except Exception as e:
        logger.error("❌ POST /send-message - Error: " + str(e))
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == '__main__':
    print("🚀 Starting StillMe Local Gateway...")
    print("📡 Gateway will be available at: http://localhost:21568")
    print("🌐 Chat UI can connect to: http://localhost:21568")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=21568, debug=True)
