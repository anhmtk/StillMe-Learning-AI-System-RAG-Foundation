#!/usr/bin/env python3
"""
StillMe System Startup Script - Khởi động toàn bộ hệ thống
Bền vững, ổn định, và dễ sử dụng
"""

import subprocess
import time
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

class StillMeSystem:
    """StillMe System Manager"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.processes = {}
        
    def start_ai_server(self):
        """Start Stable AI Server"""
        logger.info("🚀 Starting StillMe AI Server...")
        try:
            cmd = [sys.executable, "stable_ai_server.py"]
            process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['ai_server'] = process
            logger.info("✅ StillMe AI Server started")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start AI Server: {e}")
            return False
    
    def start_gateway_server(self):
        """Start Gateway Server"""
        logger.info("🌐 Starting Gateway Server...")
        try:
            gateway_dir = self.root_dir / "stillme_platform" / "gateway"
            cmd = [sys.executable, "simple_main.py"]
            process = subprocess.Popen(
                cmd,
                cwd=gateway_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['gateway'] = process
            logger.info("✅ Gateway Server started")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Gateway: {e}")
            return False
    
    def check_services(self):
        """Check if services are running"""
        logger.info("🔍 Checking services...")
        
        # Check AI Server
        try:
            import requests
            response = requests.get("http://127.0.0.1:7860/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ AI Server is healthy")
            else:
                logger.warning("⚠️ AI Server responded with non-200 status")
        except Exception as e:
            logger.warning(f"⚠️ AI Server not responding: {e}")
        
        # Check Gateway
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Gateway Server is healthy")
            else:
                logger.warning("⚠️ Gateway responded with non-200 status")
        except Exception as e:
            logger.warning(f"⚠️ Gateway not responding: {e}")
    
    def stop_all(self):
        """Stop all services"""
        logger.info("🛑 Stopping all services...")
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {name} stopped")
            except Exception as e:
                logger.error(f"❌ Failed to stop {name}: {e}")
        self.processes.clear()
    
    def run(self):
        """Run the complete system"""
        logger.info("🎯 Starting StillMe System...")
        
        try:
            # Start AI Server
            if not self.start_ai_server():
                logger.error("❌ Failed to start AI Server")
                return False
            
            # Wait a bit for AI Server to start
            time.sleep(3)
            
            # Start Gateway Server
            if not self.start_gateway_server():
                logger.error("❌ Failed to start Gateway")
                return False
            
            # Wait a bit for Gateway to start
            time.sleep(3)
            
            # Check services
            self.check_services()
            
            logger.info("🎉 StillMe System is running!")
            logger.info("📱 Mobile App: Connect to Gateway at http://localhost:8000")
            logger.info("💻 Desktop App: Connect to Gateway at http://localhost:8000")
            logger.info("🤖 AI Server: Running at http://localhost:7860")
            
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.stop_all()
            return True
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            self.stop_all()
            return False

def main():
    """Main function"""
    print("🚀 StillMe AI System Startup")
    print("=" * 50)
    
    system = StillMeSystem()
    
    try:
        success = system.run()
        if success:
            print("\n✅ StillMe System started successfully!")
            print("📱 Mobile App: npx react-native run-android")
            print("💻 Desktop App: npm start")
            print("🌐 Gateway: http://localhost:8000")
            print("🤖 AI Server: http://localhost:7860")
            print("\nPress Ctrl+C to stop all services")
            
            # Keep running until user stops
            while True:
                time.sleep(1)
        else:
            print("\n❌ Failed to start StillMe System")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down StillMe System...")
        system.stop_all()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()
