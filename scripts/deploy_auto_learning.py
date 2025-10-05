#!/usr/bin/env python3
"""
🚀 DEPLOY AUTO LEARNING SYSTEM
Deploy hệ thống học tập tự động hoàn toàn
"""

import subprocess
import time
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AutoLearningDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes = []

    def deploy_auto_learning_system(self):
        """Deploy toàn bộ hệ thống auto learning"""
        logger.info("🚀 Bắt đầu deploy Auto Learning System")

        try:
            # 1. Install dependencies
            self.install_dependencies()

            # 2. Start auto-discovery scheduler
            self.start_auto_discovery()

            # 3. Start auto-approval scheduler
            self.start_auto_approval()

            # 4. Start dashboard
            self.start_dashboard()

            # 5. Verify deployment
            self.verify_deployment()

            logger.info("✅ Auto Learning System deployed successfully!")
            logger.info("🤖 Hệ thống đang chạy tự động hoàn toàn")

        except Exception as e:
            logger.error(f"❌ Lỗi deploy: {e}")
            self.cleanup_processes()
            raise

    def install_dependencies(self):
        """Install required dependencies"""
        logger.info("📦 Installing dependencies...")

        dependencies = [
            "schedule",
            "streamlit",
            "plotly",
            "pandas",
            "requests",
            "beautifulsoup4",
            "feedparser",
        ]

        for dep in dependencies:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    check=True,
                    capture_output=True,
                )
                logger.info(f"✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Failed to install {dep}: {e}")

    def start_auto_discovery(self):
        """Start auto-discovery scheduler"""
        logger.info("🔄 Starting auto-discovery scheduler...")

        try:
            discovery_script = (
                self.project_root / "scripts" / "auto_discovery_scheduler.py"
            )
            process = subprocess.Popen(
                [sys.executable, str(discovery_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
            )
            self.processes.append(("auto_discovery", process))
            logger.info("✅ Auto-discovery scheduler started")

        except Exception as e:
            logger.error(f"❌ Failed to start auto-discovery: {e}")
            raise

    def start_auto_approval(self):
        """Start auto-approval scheduler"""
        logger.info("🤖 Starting auto-approval scheduler...")

        try:
            approval_script = (
                self.project_root / "scripts" / "auto_approval_scheduler.py"
            )
            process = subprocess.Popen(
                [sys.executable, str(approval_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
            )
            self.processes.append(("auto_approval", process))
            logger.info("✅ Auto-approval scheduler started")

        except Exception as e:
            logger.error(f"❌ Failed to start auto-approval: {e}")
            raise

    def start_dashboard(self):
        """Start auto learning dashboard"""
        logger.info("📊 Starting auto learning dashboard...")

        try:
            dashboard_script = (
                self.project_root
                / "dashboards"
                / "streamlit"
                / "auto_learning_dashboard.py"
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(dashboard_script),
                    "--server.port",
                    "8502",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
            )
            self.processes.append(("dashboard", process))
            logger.info("✅ Auto learning dashboard started on port 8502")

        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {e}")
            raise

    def verify_deployment(self):
        """Verify deployment is working"""
        logger.info("🔍 Verifying deployment...")

        # Wait for services to start
        time.sleep(5)

        # Check processes
        for name, process in self.processes:
            if process.poll() is None:
                logger.info(f"✅ {name} is running")
            else:
                logger.error(f"❌ {name} is not running")

        logger.info("🎯 Deployment verification completed")
        logger.info("📊 Dashboard: http://localhost:8502")
        logger.info("🔄 Auto-discovery: Every 6 hours")
        logger.info("🤖 Auto-approval: Every 1 hour")
        logger.info("🔇 Silent learning: Background")

    def cleanup_processes(self):
        """Cleanup all processes"""
        logger.info("🧹 Cleaning up processes...")

        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ Stopped {name}")
            except:
                try:
                    process.kill()
                    logger.info(f"🔪 Killed {name}")
                except:
                    logger.warning(f"⚠️ Could not stop {name}")

    def show_status(self):
        """Show deployment status"""
        logger.info("📊 Auto Learning System Status:")

        for name, process in self.processes:
            if process.poll() is None:
                logger.info(f"✅ {name}: Running (PID: {process.pid})")
            else:
                logger.info(f"❌ {name}: Stopped")

    def stop_all(self):
        """Stop all services"""
        logger.info("🛑 Stopping all services...")
        self.cleanup_processes()
        logger.info("✅ All services stopped")


def main():
    """Main function"""
    deployer = AutoLearningDeployer()

    try:
        deployer.deploy_auto_learning_system()

        # Keep running
        logger.info("🔄 Auto Learning System is running...")
        logger.info("Press Ctrl+C to stop")

        while True:
            time.sleep(60)
            deployer.show_status()

    except KeyboardInterrupt:
        logger.info("🛑 Stopping Auto Learning System...")
        deployer.stop_all()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        deployer.stop_all()


if __name__ == "__main__":
    main()
