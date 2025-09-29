"""
🪟 StillMe IPC Windows Service Installer
========================================

Installs StillMe IPC Background Service as a Windows Service
so it can run automatically without keeping the computer open.

Features:
- Automatic startup with Windows
- Runs in background without user login
- Service management (start/stop/restart)
- Logging to Windows Event Log
- Recovery options (auto-restart on failure)

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-29
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_windows_service():
    """Install StillMe IPC as Windows Service"""
    try:
        project_root = Path(__file__).resolve().parents[1]
        service_script = project_root / "scripts" / "stillme_background_service.py"
        
        if not service_script.exists():
            logger.error(f"Service script not found: {service_script}")
            return False
        
        # Create service using nssm (Non-Sucking Service Manager)
        service_name = "StillMeIPC"
        display_name = "StillMe IPC Background Service"
        description = "StillMe IPC Intelligent Personal Companion - Background Learning Service"
        
        # Check if nssm is available
        try:
            subprocess.run(["nssm", "version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("NSSM (Non-Sucking Service Manager) not found!")
            logger.info("Please install NSSM from: https://nssm.cc/download")
            logger.info("Or run as administrator and install via chocolatey: choco install nssm")
            return False
        
        # Install service
        logger.info(f"Installing Windows Service: {service_name}")
        
        # Set service path
        subprocess.run([
            "nssm", "install", service_name,
            sys.executable, str(service_script)
        ], check=True)
        
        # Configure service
        subprocess.run(["nssm", "set", service_name, "DisplayName", display_name], check=True)
        subprocess.run(["nssm", "set", service_name, "Description", description], check=True)
        subprocess.run(["nssm", "set", service_name, "Start", "SERVICE_AUTO_START"], check=True)
        
        # Set working directory
        subprocess.run(["nssm", "set", service_name, "AppDirectory", str(project_root)], check=True)
        
        # Configure logging
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        subprocess.run(["nssm", "set", service_name, "AppStdout", str(log_dir / "service_stdout.log")], check=True)
        subprocess.run(["nssm", "set", service_name, "AppStderr", str(log_dir / "service_stderr.log")], check=True)
        
        # Set recovery options
        subprocess.run(["nssm", "set", service_name, "AppExit", "Default", "Restart"], check=True)
        subprocess.run(["nssm", "set", service_name, "AppRestartDelay", "5000"], check=True)
        
        # Set service account (run as SYSTEM)
        subprocess.run(["nssm", "set", service_name, "ObjectName", "LocalSystem"], check=True)
        
        logger.info(f"✅ Windows Service '{service_name}' installed successfully!")
        logger.info(f"📋 Service Name: {service_name}")
        logger.info(f"📋 Display Name: {display_name}")
        logger.info(f"📋 Working Directory: {project_root}")
        logger.info(f"📋 Logs Directory: {log_dir}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install service: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def uninstall_windows_service():
    """Uninstall StillMe IPC Windows Service"""
    try:
        service_name = "StillMeIPC"
        
        logger.info(f"Uninstalling Windows Service: {service_name}")
        
        # Stop service first
        try:
            subprocess.run(["nssm", "stop", service_name], check=True)
            logger.info("Service stopped")
        except subprocess.CalledProcessError:
            logger.info("Service was not running")
        
        # Remove service
        subprocess.run(["nssm", "remove", service_name, "confirm"], check=True)
        
        logger.info(f"✅ Windows Service '{service_name}' uninstalled successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to uninstall service: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def manage_service(action):
    """Manage Windows Service"""
    try:
        service_name = "StillMeIPC"
        
        if action == "start":
            subprocess.run(["nssm", "start", service_name], check=True)
            logger.info(f"✅ Service '{service_name}' started")
        elif action == "stop":
            subprocess.run(["nssm", "stop", service_name], check=True)
            logger.info(f"✅ Service '{service_name}' stopped")
        elif action == "restart":
            subprocess.run(["nssm", "restart", service_name], check=True)
            logger.info(f"✅ Service '{service_name}' restarted")
        elif action == "status":
            result = subprocess.run(["nssm", "status", service_name], capture_output=True, text=True)
            logger.info(f"Service Status: {result.stdout.strip()}")
        else:
            logger.error(f"Unknown action: {action}")
            return False
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to {action} service: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StillMe IPC Windows Service Manager")
    parser.add_argument("action", choices=["install", "uninstall", "start", "stop", "restart", "status"],
                       help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "install":
        success = install_windows_service()
        if success:
            print("\n🎉 StillMe IPC Windows Service installed successfully!")
            print("💡 The service will start automatically with Windows")
            print("💡 You can now close your computer and StillMe will continue learning!")
            print("\n📋 Service Management Commands:")
            print("  python scripts/install_windows_service.py start    # Start service")
            print("  python scripts/install_windows_service.py stop     # Stop service")
            print("  python scripts/install_windows_service.py restart  # Restart service")
            print("  python scripts/install_windows_service.py status   # Check status")
            print("  python scripts/install_windows_service.py uninstall # Remove service")
        else:
            print("\n❌ Failed to install Windows Service")
            sys.exit(1)
    
    elif args.action == "uninstall":
        success = uninstall_windows_service()
        if success:
            print("\n✅ StillMe IPC Windows Service uninstalled successfully!")
        else:
            print("\n❌ Failed to uninstall Windows Service")
            sys.exit(1)
    
    else:
        success = manage_service(args.action)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
