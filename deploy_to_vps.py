#!/usr/bin/env python3
"""
StillMe VPS Deployment Script
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def deploy_to_vps():
    """Deploy StillMe to VPS"""
    print("🚀 StillMe VPS Deployment")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    vps_ip = os.getenv("VPS_IP", "160.191.89.99")
    vps_user = os.getenv("VPS_USERNAME", "root")
    vps_password = os.getenv("VPS_PASSWORD", "StillMe@2025!")
    
    print(f"📡 VPS IP: {vps_ip}")
    print(f"👤 User: {vps_user}")
    print(f"🔑 Password: {'*' * len(vps_password)}")
    
    # Create deployment package
    print("\n📦 Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment_package")
    deploy_dir.mkdir(exist_ok=True)
    
    # Copy essential files
    essential_files = [
        "stillme_platform/",
        "stillme-core/",
        "requirements.txt",
        ".env",
        "real_stillme_gateway.py",
        "stable_ai_server.py"
    ]
    
    for file_path in essential_files:
        if Path(file_path).exists():
            print(f"  📄 Copying {file_path}...")
            if Path(file_path).is_dir():
                run_command(f"xcopy /E /I /Y {file_path} {deploy_dir}\\{file_path}")
            else:
                run_command(f"copy {file_path} {deploy_dir}\\{file_path}")
    
    # Create deployment script for VPS
    vps_script = f"""#!/bin/bash
# StillMe VPS Setup Script

echo "🚀 Setting up StillMe on VPS..."

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git

# Create stillme directory
mkdir -p /opt/stillme
cd /opt/stillme

# Copy files (will be done via scp)
echo "📁 Files will be copied here..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/stillme-gateway.service << EOF
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

# Create AI Server service
cat > /etc/systemd/system/stillme-ai.service << EOF
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

echo "✅ StillMe deployment completed!"
echo "🌐 Gateway: http://{vps_ip}:21568"
echo "🤖 AI Server: http://{vps_ip}:1216"
"""
    
    with open(deploy_dir / "setup_vps.sh", "w") as f:
        f.write(vps_script)
    
    print("✅ Deployment package created!")
    
    # Create SCP command
    print(f"\n📤 To deploy to VPS, run these commands:")
    print(f"scp -r {deploy_dir}/* {vps_user}@{vps_ip}:/opt/stillme/")
    print(f"ssh {vps_user}@{vps_ip} 'chmod +x /opt/stillme/setup_vps.sh && /opt/stillme/setup_vps.sh'")
    
    return True

if __name__ == "__main__":
    success = deploy_to_vps()
    if success:
        print("\n🎉 VPS deployment package ready!")
        print("📋 Next steps:")
        print("1. Run the SCP command to copy files")
        print("2. Run the SSH command to setup VPS")
        print("3. Test the deployed services")
    else:
        print("\n❌ VPS deployment failed!")
        sys.exit(1)
