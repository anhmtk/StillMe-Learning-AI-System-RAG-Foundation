#!/bin/bash
set -euo pipefail

echo "🚀 DEPLOYING VPS GATEWAY PROXY (SECURE VERSION)"
echo "=============================================="

# Backup current gateway
echo "📦 Backing up current gateway..."
BACKUP_DIR="/opt/stillme.backup.$(date +%Y%m%d_%H%M%S)"
cp -r /opt/stillme "$BACKUP_DIR"
echo "✅ Backup saved to: $BACKUP_DIR"

# Create directories
echo "📁 Creating directories..."
mkdir -p /opt/stillme/tools
mkdir -p /var/log/stillme

# Deploy VPS Gateway Proxy (copy from local file)
echo "🔧 Deploying VPS Gateway Proxy..."
if [ -f "vps_gateway_proxy.py" ]; then
    cp vps_gateway_proxy.py /opt/stillme/
    chmod +x /opt/stillme/vps_gateway_proxy.py
    echo "✅ Copied vps_gateway_proxy.py from local"
else
    echo "❌ vps_gateway_proxy.py not found in current directory"
    exit 1
fi

# Deploy Local Backend (for reference)
echo "🔧 Deploying Local Backend reference..."
if [ -f "local_stillme_backend.py" ]; then
    cp local_stillme_backend.py /opt/stillme/
    chmod +x /opt/stillme/local_stillme_backend.py
    echo "✅ Copied local_stillme_backend.py for reference"
fi

# Create environment configuration
echo "🔧 Creating environment configuration..."
cat > /opt/stillme/.env << 'ENV_EOF'
# VPS Gateway Configuration
GATEWAY_PORT=21568
LOCAL_BACKEND_URL=http://localhost:1216
REQUEST_CONNECT_TIMEOUT=10
REQUEST_READ_TIMEOUT=20
RATE_LIMIT_RPS=10
RATE_LIMIT_BURST=20

# Authentication (MUST BE SET MANUALLY)
GATEWAY_SECRET=change_me_super_secret

# Logging
LOG_LEVEL=INFO
ENV_EOF

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/stillme-gateway.service << 'SERVICE_EOF'
[Unit]
Description=StillMe VPS Gateway Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
EnvironmentFile=/opt/stillme/.env
ExecStart=/usr/bin/python3 /opt/stillme/vps_gateway_proxy.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/stillme/gateway.log
StandardError=append:/var/log/stillme/gateway_error.log

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Create test script
echo "📝 Creating test script..."
cat > /opt/stillme/tools/test_vps_proxy.sh << 'TEST_EOF'
#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-http://127.0.0.1:21568}

echo "== VPS Proxy Health =="
curl -s ${HOST}/health | jq .
echo

echo "== Backend Status =="
curl -s ${HOST}/admin/backend-status | jq .
echo

echo "== Chat Test =="
curl -s -X POST ${HOST}/chat -H 'Content-Type: application/json' \
  -d '{"message":"xin chào","session_id":"test"}' | jq '{engine,model,text,latency_ms,status}'
echo
TEST_EOF

chmod +x /opt/stillme/tools/test_vps_proxy.sh

# Reload systemd and restart service
echo "🔄 Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl restart stillme-gateway
systemctl enable stillme-gateway

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Test the deployment
echo "🧪 Testing deployment..."
HOST=http://127.0.0.1:21568 bash /opt/stillme/tools/test_vps_proxy.sh

echo ""
echo "✅ VPS Gateway Proxy deployed successfully!"
echo "📡 Gateway: http://160.191.89.99:21568"
echo "🔗 Backend: http://localhost:1216 (SSH reverse tunnel)"
echo "📋 Test: bash /opt/stillme/tools/test_vps_proxy.sh"
echo ""
echo "⚠️  IMPORTANT SECURITY STEPS:"
echo "1. Set GATEWAY_SECRET in /opt/stillme/.env"
echo "2. Start Local Backend on your PC: python local_stillme_backend.py"
echo "3. Create SSH reverse tunnel: ssh -N -R 1216:127.0.0.1:1216 root@<VPS_IP>"
echo ""
echo "🔒 Security Features:"
echo "- HMAC authentication between Gateway ↔ Backend"
echo "- Rate limiting (10 RPS, burst 20)"
echo "- Timeout protection (10s connect, 20s read)"
echo "- Secure logging (no body content)"
echo "- Local backend binds to 127.0.0.1 only"
