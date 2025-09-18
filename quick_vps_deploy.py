#!/usr/bin/env python3
"""
Quick VPS Deployment for StillMe
"""

import os
import subprocess
from pathlib import Path

def create_deployment():
    """Create deployment package"""
    print("StillMe VPS Deployment Package")
    print("=" * 50)
    
    # VPS credentials
    vps_ip = "160.191.89.99"
    vps_user = "root"
    
    print(f"VPS IP: {vps_ip}")
    print(f"User: {vps_user}")
    
    # Create deployment directory
    deploy_dir = Path("deployment_package")
    deploy_dir.mkdir(exist_ok=True)
    
    print(f"\nCreating deployment package in: {deploy_dir}")
    
    # Copy essential files only
    files_to_copy = [
        "stillme-core",
        "requirements.txt",
        "real_stillme_gateway.py",
        "stable_ai_server.py"
    ]
    
    for item in files_to_copy:
        if Path(item).exists():
            print(f"  Copying {item}...")
            if Path(item).is_dir():
                subprocess.run(f"xcopy /E /I /Y {item} {deploy_dir}\\{item}", shell=True)
            else:
                subprocess.run(f"copy {item} {deploy_dir}\\{item}", shell=True)
    
    # Create .env for VPS
    vps_env = f"""# StillMe VPS Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=anhnguyen.nk86@gmail.com
SMTP_PASSWORD=ctnq umbc isns iijr
ALERT_EMAIL=anhnguyen.nk86@gmail.com
VPS_IP={vps_ip}
VPS_USERNAME={vps_user}
VPS_PASSWORD=StillMe@2025!
"""
    
    with open(deploy_dir / ".env", "w", encoding="utf-8") as f:
        f.write(vps_env)
    
    # Create VPS setup script
    setup_script = f"""#!/bin/bash
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
echo "Gateway: http://{vps_ip}:21568"
echo "AI Server: http://{vps_ip}:1216"
"""
    
    with open(deploy_dir / "setup_vps.sh", "w", encoding="utf-8") as f:
        f.write(setup_script)
    
    print("Deployment package created!")
    
    # Create deployment commands
    print(f"\nDEPLOYMENT COMMANDS:")
    print("=" * 50)
    print(f"# 1. Copy files to VPS:")
    print(f"scp -r {deploy_dir}/* {vps_user}@{vps_ip}:/opt/stillme/")
    print(f"")
    print(f"# 2. Setup VPS (run on VPS):")
    print(f"ssh {vps_user}@{vps_ip}")
    print(f"chmod +x /opt/stillme/setup_vps.sh")
    print(f"/opt/stillme/setup_vps.sh")
    print(f"")
    print(f"# 3. Test services:")
    print(f"curl http://{vps_ip}:21568/health")
    print(f"curl http://{vps_ip}:1216/health")
    
    return True

if __name__ == "__main__":
    create_deployment()
