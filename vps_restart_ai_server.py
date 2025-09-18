#!/usr/bin/env python3
"""
StillMe AI Server Auto-Restart Script (Python Version)
Tự động restart AI Server khi gặp lỗi trên VPS
"""

import subprocess
import time
import logging
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
import paramiko
from pathlib import Path

# Configuration
VPS_IP = "160.191.89.99"
VPS_USER = "root"
VPS_PASSWORD = "StillMe@2025!"
AI_SERVER_PORT = 1216
GATEWAY_PORT = 21568
MAX_RETRIES = 3
RETRY_DELAY = 30
LOG_FILE = "stillme_restart.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StillMeRestartManager:
    """Manager for StillMe services auto-restart functionality"""
    
    def __init__(self):
        self.vps_ip = VPS_IP
        self.vps_user = VPS_USER
        self.vps_password = VPS_PASSWORD
        self.ai_server_port = AI_SERVER_PORT
        self.gateway_port = GATEWAY_PORT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        
    def run_ssh_command(self, command: str) -> tuple[bool, str]:
        """Run SSH command on VPS"""
        try:
            # Use sshpass for password authentication
            cmd = [
                "sshpass", "-p", self.vps_password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.vps_user}@{self.vps_ip}",
                command
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "SSH command timed out"
        except Exception as e:
            return False, f"SSH error: {str(e)}"
    
    def test_port_connectivity(self, port: int, service_name: str) -> bool:
        """Test if a port is accessible"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.vps_ip, port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ {service_name} is accessible on port {port}")
                return True
            else:
                logger.warning(f"❌ {service_name} is NOT accessible on port {port}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing port {port}: {str(e)}")
            return False
    
    def test_http_endpoint(self, url: str, service_name: str) -> bool:
        """Test HTTP endpoint"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ {service_name} HTTP endpoint is responding")
                return True
            else:
                logger.warning(f"❌ {service_name} HTTP endpoint returned {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"❌ {service_name} HTTP endpoint error: {str(e)}")
            return False
    
    def get_service_status(self, service_name: str) -> Dict:
        """Get systemd service status"""
        success, output = self.run_ssh_command(f"systemctl status {service_name} --no-pager -l")
        
        if success:
            # Parse systemd status
            is_active = "active (running)" in output.lower()
            is_enabled = "enabled" in output.lower()
            
            return {
                "service": service_name,
                "is_active": is_active,
                "is_enabled": is_enabled,
                "status_output": output,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "service": service_name,
                "is_active": False,
                "is_enabled": False,
                "status_output": output,
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a systemd service"""
        logger.info(f"🔄 Restarting {service_name}...")
        
        # Stop service
        success, output = self.run_ssh_command(f"systemctl stop {service_name}")
        if not success:
            logger.warning(f"Failed to stop {service_name}: {output}")
        
        # Wait a moment
        time.sleep(5)
        
        # Start service
        success, output = self.run_ssh_command(f"systemctl start {service_name}")
        if not success:
            logger.error(f"Failed to start {service_name}: {output}")
            return False
        
        # Wait for service to start
        time.sleep(10)
        
        # Check if it's running
        status = self.get_service_status(service_name)
        if status.get("is_active", False):
            logger.info(f"✅ {service_name} restarted successfully")
            return True
        else:
            logger.error(f"❌ {service_name} failed to restart")
            return False
    
    def restart_ai_server(self) -> bool:
        """Restart AI Server specifically"""
        return self.restart_service("stillme-ai-server")
    
    def restart_gateway(self) -> bool:
        """Restart Gateway specifically"""
        return self.restart_service("stillme-gateway")
    
    def test_all_services(self) -> Dict:
        """Test all StillMe services"""
        logger.info("🧪 Testing StillMe services connectivity...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "vps_ip": self.vps_ip,
            "services": {}
        }
        
        # Test AI Server
        ai_server_port_ok = self.test_port_connectivity(self.ai_server_port, "AI Server")
        ai_server_http_ok = self.test_http_endpoint(f"http://{self.vps_ip}:{self.ai_server_port}/health", "AI Server")
        
        results["services"]["ai_server"] = {
            "port": self.ai_server_port,
            "port_accessible": ai_server_port_ok,
            "http_accessible": ai_server_http_ok,
            "overall_status": ai_server_port_ok and ai_server_http_ok
        }
        
        # Test Gateway
        gateway_port_ok = self.test_port_connectivity(self.gateway_port, "Gateway")
        gateway_http_ok = self.test_http_endpoint(f"http://{self.vps_ip}:{self.gateway_port}/health", "Gateway")
        
        results["services"]["gateway"] = {
            "port": self.gateway_port,
            "port_accessible": gateway_port_ok,
            "http_accessible": gateway_http_ok,
            "overall_status": gateway_port_ok and gateway_http_ok
        }
        
        # Test chat endpoint
        chat_ok = self.test_http_endpoint(f"http://{self.vps_ip}:{self.gateway_port}/chat", "Chat Endpoint")
        results["services"]["chat_endpoint"] = {
            "accessible": chat_ok
        }
        
        return results
    
    def one_time_restart(self) -> Dict:
        """Perform one-time restart of all services"""
        logger.info("🚀 Performing one-time restart of StillMe services...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "restarts": {}
        }
        
        # Check current status
        logger.info("📊 Current service status:")
        ai_status = self.get_service_status("stillme-ai-server")
        gateway_status = self.get_service_status("stillme-gateway")
        
        logger.info(f"AI Server: {'✅ Active' if ai_status.get('is_active') else '❌ Inactive'}")
        logger.info(f"Gateway: {'✅ Active' if gateway_status.get('is_active') else '❌ Inactive'}")
        
        # Restart AI Server if needed
        if not self.test_port_connectivity(self.ai_server_port, "AI Server"):
            logger.info("🔄 AI Server is down, restarting...")
            results["restarts"]["ai_server"] = self.restart_ai_server()
        else:
            logger.info("✅ AI Server is running, no restart needed")
            results["restarts"]["ai_server"] = True
        
        # Restart Gateway if needed
        if not self.test_port_connectivity(self.gateway_port, "Gateway"):
            logger.info("🔄 Gateway is down, restarting...")
            results["restarts"]["gateway"] = self.restart_gateway()
        else:
            logger.info("✅ Gateway is running, no restart needed")
            results["restarts"]["gateway"] = True
        
        # Final status check
        logger.info("📊 Final service status:")
        final_ai_status = self.get_service_status("stillme-ai-server")
        final_gateway_status = self.get_service_status("stillme-gateway")
        
        logger.info(f"AI Server: {'✅ Active' if final_ai_status.get('is_active') else '❌ Inactive'}")
        logger.info(f"Gateway: {'✅ Active' if final_gateway_status.get('is_active') else '❌ Inactive'}")
        
        results["final_status"] = {
            "ai_server": final_ai_status,
            "gateway": final_gateway_status
        }
        
        logger.info("✅ One-time restart completed")
        return results
    
    def monitor_services(self):
        """Continuous monitoring and auto-restart"""
        logger.info("🔄 Starting StillMe services monitoring...")
        
        retry_count = 0
        
        while True:
            logger.info(f"=== Monitoring cycle {datetime.now()} ===")
            
            # Test all services
            test_results = self.test_all_services()
            
            # Check if any service failed
            ai_server_failed = not test_results["services"]["ai_server"]["overall_status"]
            gateway_failed = not test_results["services"]["gateway"]["overall_status"]
            
            # Restart failed services
            if ai_server_failed:
                logger.warning("🔄 AI Server failed, attempting restart...")
                if self.restart_ai_server():
                    retry_count = 0
                else:
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        logger.error(f"❌ AI Server failed to restart after {self.max_retries} attempts")
                        retry_count = 0
            
            if gateway_failed:
                logger.warning("🔄 Gateway failed, attempting restart...")
                if self.restart_gateway():
                    retry_count = 0
                else:
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        logger.error(f"❌ Gateway failed to restart after {self.max_retries} attempts")
                        retry_count = 0
            
            # Wait before next check
            logger.info(f"⏳ Waiting {self.retry_delay} seconds before next check...")
            time.sleep(self.retry_delay)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StillMe Auto-Restart Manager")
    parser.add_argument("action", choices=["monitor", "restart", "test", "status"], 
                       default="monitor", nargs="?",
                       help="Action to perform (default: monitor)")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    manager = StillMeRestartManager()
    
    try:
        if args.action == "monitor":
            manager.monitor_services()
        elif args.action == "restart":
            results = manager.one_time_restart()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        elif args.action == "test":
            results = manager.test_all_services()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        elif args.action == "status":
            ai_status = manager.get_service_status("stillme-ai-server")
            gateway_status = manager.get_service_status("stillme-gateway")
            results = {
                "timestamp": datetime.now().isoformat(),
                "ai_server": ai_status,
                "gateway": gateway_status
            }
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
            else:
                print(json.dumps(results, indent=2))
                
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
