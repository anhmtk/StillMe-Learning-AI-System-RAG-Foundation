#!/bin/bash
echo "🚀 StillMe Direct VPS Deployment Script"
echo "========================================"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python dependencies..."
apt install -y python3 python3-pip git

# Create StillMe directory
echo "📁 Creating StillMe directory..."
mkdir -p /opt/stillme
cd /opt/stillme

# Clone or create basic structure
echo "📋 Setting up StillMe structure..."

# Create basic gateway file
cat > real_stillme_gateway.py << 'EOF'
#!/usr/bin/env python3
"""
StillMe AI Gateway - VPS Version
"""

from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
AI_SERVER_URL = "http://localhost:1216"
GATEWAY_PORT = 21568

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "StillMe Gateway",
        "version": "1.0.0"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Forward to AI Server
        ai_response = requests.post(f"{AI_SERVER_URL}/inference", 
                                  json={"message": message}, 
                                  timeout=30)
        
        if ai_response.status_code == 200:
            return jsonify({
                "response": ai_response.json().get("response", "No response"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "AI Server unavailable"}), 503
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    """Alternative chat endpoint"""
    return chat()

if __name__ == '__main__':
    print(f"🚀 Starting StillMe Gateway on port {GATEWAY_PORT}")
    print(f"📡 Gateway URL: http://0.0.0.0:{GATEWAY_PORT}")
    app.run(host='0.0.0.0', port=GATEWAY_PORT, debug=False)
EOF

# Create basic AI server file
cat > stable_ai_server.py << 'EOF'
#!/usr/bin/env python3
"""
StillMe AI Server - VPS Version
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime

app = FastAPI(title="StillMe AI Server", version="1.0.0")

class MessageRequest(BaseModel):
    message: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "StillMe AI Server",
        "version": "1.0.0"
    }

@app.post("/inference")
async def inference(request: MessageRequest):
    """AI inference endpoint"""
    try:
        message = request.message
        
        # Simple response for testing
        response = f"Xin chào! Tôi là StillMe AI. Bạn đã nói: '{message}'. Tôi đang chạy trên VPS và sẵn sàng phục vụ!"
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "StillMe-VPS"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🤖 Starting StillMe AI Server on port 1216")
    print("📡 AI Server URL: http://0.0.0.0:1216")
    uvicorn.run(app, host="0.0.0.0", port=1216)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
flask>=2.3.0
fastapi>=0.104.0
uvicorn>=0.24.0
requests>=2.31.0
pydantic>=2.4.0
EOF

# Create .env file
cat > .env << 'EOF'
# StillMe AI Configuration
AI_SERVER_URL=http://localhost:1216
GATEWAY_PORT=21568
AI_SERVER_PORT=1216
VPS_MODE=true
EOF

# Install Python dependencies
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

# Set permissions
chmod +x real_stillme_gateway.py
chmod +x stable_ai_server.py

# Create systemd service for Gateway
echo "🔧 Creating Gateway service..."
cat > /etc/systemd/system/stillme-gateway.service << 'EOF'
[Unit]
Description=StillMe AI Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
ExecStart=/usr/bin/python3 /opt/stillme/real_stillme_gateway.py
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for AI Server
echo "🔧 Creating AI Server service..."
cat > /etc/systemd/system/stillme-ai.service << 'EOF'
[Unit]
Description=StillMe AI Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
ExecStart=/usr/bin/python3 /opt/stillme/stable_ai_server.py
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "🚀 Starting StillMe services..."
systemctl daemon-reload
systemctl enable stillme-gateway
systemctl enable stillme-ai
systemctl start stillme-gateway
systemctl start stillme-ai

# Wait a moment for services to start
sleep 5

# Check status
echo "📊 Checking service status..."
systemctl status stillme-gateway --no-pager -l
echo ""
systemctl status stillme-ai --no-pager -l

# Test endpoints
echo "🧪 Testing endpoints..."
curl -s http://localhost:21568/health | head -3
curl -s http://localhost:1216/health | head -3

echo ""
echo "✅ StillMe deployment completed!"
echo "🌐 Gateway: http://160.191.89.99:21568"
echo "🤖 AI Server: http://160.191.89.99:1216"
echo "📋 Test with: curl -X POST http://160.191.89.99:21568/chat -H 'Content-Type: application/json' -d '{\"message\":\"Hello\"}'"
