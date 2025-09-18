#!/bin/bash
echo "Setting up StillMe on VPS..."

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git

# Create stillme directory
mkdir -p /opt/stillme
cd /opt/stillme

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create systemd services
cat > /etc/systemd/system/stillme-gateway.service << 'EOF'
[Unit]
Description=StillMe Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
Environment=PATH=/opt/stillme/venv/bin
ExecStart=/opt/stillme/venv/bin/python real_stillme_gateway.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/stillme-ai.service << 'EOF'
[Unit]
Description=StillMe AI Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
Environment=PATH=/opt/stillme/venv/bin
ExecStart=/opt/stillme/venv/bin/python stable_ai_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable stillme-gateway
systemctl enable stillme-ai
systemctl start stillme-gateway
systemctl start stillme-ai

echo "StillMe deployment completed!"
echo "Gateway: http://160.191.89.99:21568"
echo "AI Server: http://160.191.89.99:1216"
