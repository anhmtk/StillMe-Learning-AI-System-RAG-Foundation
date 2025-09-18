#!/bin/bash
# StillMe VPS Deployment Script

echo "🚀 Starting StillMe deployment on VPS..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git

# Create stillme user
echo "👤 Creating stillme user..."
useradd -m -s /bin/bash stillme || true
usermod -aG sudo stillme || true

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/stillme
chown -R stillme:stillme /opt/stillme

# Copy files
echo "📋 Copying application files..."
cp -r stillme_core /opt/stillme/
cp real_stillme_gateway.py /opt/stillme/
cp stable_ai_server.py /opt/stillme/
cp .env /opt/stillme/
cp requirements.txt /opt/stillme/

# Set permissions
chown -R stillme:stillme /opt/stillme
chmod +x /opt/stillme/*.py

# Create virtual environment
echo "🔧 Setting up Python environment..."
cd /opt/stillme
sudo -u stillme python3 -m venv venv
sudo -u stillme ./venv/bin/pip install --upgrade pip
sudo -u stillme ./venv/bin/pip install -r requirements.txt

# Create systemd services
echo "⚙️ Creating systemd services..."

# Gateway service
cat > /etc/systemd/system/stillme-gateway.service << 'EOF'
[Unit]
Description=StillMe AI Gateway
After=network.target

[Service]
Type=simple
User=stillme
WorkingDirectory=/opt/stillme
Environment=PATH=/opt/stillme/venv/bin
ExecStart=/opt/stillme/venv/bin/python real_stillme_gateway.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# AI Server service
cat > /etc/systemd/system/stillme-ai.service << 'EOF'
[Unit]
Description=StillMe AI Server
After=network.target

[Service]
Type=simple
User=stillme
WorkingDirectory=/opt/stillme
Environment=PATH=/opt/stillme/venv/bin
ExecStart=/opt/stillme/venv/bin/python stable_ai_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start services
echo "🚀 Starting StillMe services..."
systemctl daemon-reload
systemctl enable stillme-gateway
systemctl enable stillme-ai
systemctl start stillme-gateway
systemctl start stillme-ai

# Check status
echo "📊 Checking service status..."
systemctl status stillme-gateway --no-pager
systemctl status stillme-ai --no-pager

echo "✅ StillMe deployment completed!"
echo "🌐 Gateway: http://160.191.89.99:21568"
echo "🤖 AI Server: http://160.191.89.99:1216"
