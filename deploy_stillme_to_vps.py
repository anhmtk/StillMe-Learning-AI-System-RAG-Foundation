#!/usr/bin/env python3
"""
StillMe VPS Deployment Script
Deploy StillMe AI system to secured VPS
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def create_deployment_package():
    """Create deployment package"""
    print("📦 Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment_package")
    deploy_dir.mkdir(exist_ok=True)
    
    # Copy essential files
    essential_files = [
        "stillme_core/",
        "real_stillme_gateway.py",
        "stable_ai_server.py", 
        ".env",
        "requirements.txt"
    ]
    
    for file_path in essential_files:
        if Path(file_path).exists():
            if Path(file_path).is_dir():
                run_command(f'xcopy "{file_path}" "{deploy_dir / file_path}" /E /I /Y', f"Copying {file_path}")
            else:
                run_command(f'copy "{file_path}" "{deploy_dir / file_path}"', f"Copying {file_path}")
    
    # Create deployment script
    deploy_script = f"""#!/bin/bash
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
"""
    
    with open(deploy_dir / "deploy.sh", "w", encoding="utf-8") as f:
        f.write(deploy_script)
    
    print("✅ Deployment package created successfully!")
    return True

def main():
    """Main deployment function"""
    print("🚀 StillMe VPS Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("stillme_core").exists():
        print("❌ Error: stillme_core directory not found!")
        print("Please run this script from the StillMe project root directory.")
        return False
    
    # Create deployment package
    if not create_deployment_package():
        print("❌ Failed to create deployment package!")
        return False
    
    # Generate deployment commands
    print("\n📋 DEPLOYMENT COMMANDS:")
    print("=" * 50)
    print("1. Copy deployment package to VPS:")
    print(f"   scp -r deployment_package root@160.191.89.99:/tmp/")
    print()
    print("2. SSH into VPS and deploy:")
    print("   ssh root@160.191.89.99")
    print("   cd /tmp/deployment_package")
    print("   chmod +x deploy.sh")
    print("   ./deploy.sh")
    print()
    print("3. Check services:")
    print("   systemctl status stillme-gateway")
    print("   systemctl status stillme-ai")
    print()
    print("4. View logs:")
    print("   journalctl -u stillme-gateway -f")
    print("   journalctl -u stillme-ai -f")
    print()
    print("🌐 After deployment, StillMe will be available at:")
    print("   Gateway: http://160.191.89.99:21568")
    print("   AI Server: http://160.191.89.99:1216")
    
    return True

if __name__ == "__main__":
    main()
