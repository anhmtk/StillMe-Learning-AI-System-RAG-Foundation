#!/usr/bin/env python3
"""
Install StillMe Auto-Restart Script on VPS
Cài đặt script tự động restart trên VPS
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Install Python packages
    packages = [
        "requests",
        "paramiko"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    return True

def make_scripts_executable():
    """Make scripts executable"""
    scripts = [
        "vps_auto_restart_ai_server.sh",
        "vps_restart_ai_server.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            run_command(f"chmod +x {script}", f"Making {script} executable")
        else:
            print(f"⚠️  Script {script} not found")

def test_script():
    """Test the restart script"""
    print("🧪 Testing restart script...")
    
    if os.path.exists("vps_restart_ai_server.py"):
        # Test connectivity
        result = subprocess.run([
            sys.executable, "vps_restart_ai_server.py", "test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Script test passed")
            print("📊 Test results:")
            print(result.stdout)
        else:
            print("❌ Script test failed")
            print("Error:", result.stderr)
    else:
        print("❌ Script not found")

def create_systemd_service():
    """Create systemd service for auto-restart"""
    service_content = """[Unit]
Description=StillMe Auto-Restart Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stillme
ExecStart=/usr/bin/python3 /opt/stillme/vps_restart_ai_server.py monitor
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    with open("stillme-auto-restart.service", "w") as f:
        f.write(service_content)
    
    print("✅ Created systemd service file: stillme-auto-restart.service")
    print("📝 To install the service on VPS, run:")
    print("   sudo cp stillme-auto-restart.service /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable stillme-auto-restart")
    print("   sudo systemctl start stillme-auto-restart")

def main():
    """Main installation function"""
    print("🚀 StillMe Auto-Restart Script Installer")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Make scripts executable
    make_scripts_executable()
    
    # Test script
    test_script()
    
    # Create systemd service
    create_systemd_service()
    
    print("\n🎉 Installation completed!")
    print("\n📋 Usage:")
    print("  python vps_restart_ai_server.py monitor    # Continuous monitoring")
    print("  python vps_restart_ai_server.py restart    # One-time restart")
    print("  python vps_restart_ai_server.py test       # Test connectivity")
    print("  python vps_restart_ai_server.py status     # Show status")
    
    print("\n🔧 Manual commands:")
    print("  ./vps_auto_restart_ai_server.sh monitor    # Bash version")
    print("  ./vps_auto_restart_ai_server.sh restart    # One-time restart")
    print("  ./vps_auto_restart_ai_server.sh test       # Test connectivity")

if __name__ == "__main__":
    main()
