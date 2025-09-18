#!/usr/bin/env python3
"""
Create lightweight deployment package (without node_modules)
"""

import os
import zipfile
import shutil
from pathlib import Path

def create_lightweight_package():
    """Create lightweight deployment package"""
    print("📦 Creating lightweight deployment package...")
    
    # Create temporary directory
    temp_dir = Path("temp_deployment")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    # Copy essential files (excluding node_modules)
    essential_files = [
        "stillme_core/",
        "real_stillme_gateway.py",
        "stable_ai_server.py", 
        ".env",
        "requirements.txt"
    ]
    
    print("📋 Copying essential files...")
    for file_path in essential_files:
        if Path(file_path).exists():
            if Path(file_path).is_dir():
                # Copy directory but exclude node_modules
                if file_path == "stillme_core/":
                    shutil.copytree(file_path, temp_dir / file_path)
                else:
                    shutil.copytree(file_path, temp_dir / file_path)
            else:
                shutil.copy2(file_path, temp_dir / file_path)
            print(f"✅ Added: {file_path}")
    
    # Create deploy script
    deploy_script = """#!/bin/bash
echo "🚀 StillMe VPS Deployment Script"
echo "=================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create StillMe directory
echo "📁 Creating StillMe directory..."
mkdir -p /opt/stillme
cp -r stillme_core /opt/stillme/
cp real_stillme_gateway.py /opt/stillme/
cp stable_ai_server.py /opt/stillme/
cp .env /opt/stillme/

# Set permissions
chmod +x /opt/stillme/real_stillme_gateway.py
chmod +x /opt/stillme/stable_ai_server.py

# Create systemd service for Gateway
echo "🔧 Creating Gateway service..."
cat > /etc/systemd/system/stillme-gateway.service << EOF
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

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for AI Server
echo "🔧 Creating AI Server service..."
cat > /etc/systemd/system/stillme-ai.service << EOF
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

# Check status
echo "📊 Checking service status..."
systemctl status stillme-gateway --no-pager
systemctl status stillme-ai --no-pager

echo "✅ StillMe deployment completed!"
echo "🌐 Gateway: http://160.191.89.99:21568"
echo "🤖 AI Server: http://160.191.89.99:1216"
"""
    
    with open(temp_dir / "deploy.sh", "w", encoding="utf-8") as f:
        f.write(deploy_script)
    
    # Create ZIP
    zip_path = "stillme_lightweight_deployment.zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    # Get file size
    size = os.path.getsize(zip_path)
    size_mb = size / (1024 * 1024)
    
    print(f"🎉 Lightweight package created: {zip_path} ({size_mb:.1f} MB)")
    return True

if __name__ == "__main__":
    create_lightweight_package()
