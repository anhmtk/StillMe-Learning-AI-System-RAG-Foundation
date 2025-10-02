#!/usr/bin/env python3
"""
StillMe IPC Background Service
Chạy ngầm, tự động khám phá kiến thức định kỳ
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.alerting.alerting_system import AlertingSystem
from stillme_core.learning.proposals_manager import ProposalsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("artifacts/stillme_service.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class StillMeBackgroundService:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
        self.config_file = project_root / "artifacts" / "background_service_config.json"
        self.load_config()

    def load_config(self):
        """Load background service configuration"""
        default_config = {
            "enabled": True,
            "discovery_interval_hours": 3,  # Quét mỗi 3 giờ
            "max_proposals_per_discovery": 5,  # Tối đa 5 proposals mỗi lần
            "auto_approve_founder_knowledge": True,  # Tự động approve kiến thức founder
            "notification_enabled": True,
            "last_discovery_time": None,
            "discovery_count_today": 0,
            "max_discoveries_per_day": 8,  # Tối đa 8 lần quét/ngày
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.config = json.load(f)
                # Reset daily counter if new day
                if self.config.get("last_discovery_date") != datetime.now().strftime(
                    "%Y-%m-%d"
                ):
                    self.config["discovery_count_today"] = 0
                    self.config["last_discovery_date"] = datetime.now().strftime(
                        "%Y-%m-%d"
                    )
            except:
                self.config = default_config
        else:
            self.config = default_config

        self.save_config()

    def save_config(self):
        """Save background service configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def discover_knowledge(self):
        """Khám phá kiến thức mới"""
        if not self.config["enabled"]:
            logger.info("🔴 Background service is disabled")
            return

        if (
            self.config["discovery_count_today"]
            >= self.config["max_discoveries_per_day"]
        ):
            logger.info(
                f"📊 Daily discovery limit reached: {self.config['discovery_count_today']}/{self.config['max_discoveries_per_day']}"
            )
            return

        logger.info("🔍 Starting knowledge discovery...")

        try:
            # Import discovery function
            from scripts.knowledge_discovery import KnowledgeDiscovery

            discovery = KnowledgeDiscovery()
            discovered_count = discovery.discover_knowledge()

            if discovered_count > 0:
                self.config["discovery_count_today"] += 1
                self.config["last_discovery_time"] = datetime.now().isoformat()
                self.save_config()

                logger.info(f"✅ Discovery completed: {discovered_count} new proposals")

                if self.config["notification_enabled"]:
                    self.alerting_system.send_alert(
                        "Knowledge Discovery Completed",
                        f"StillMe IPC has discovered {discovered_count} new learning opportunities!\n\n"
                        f"🔍 Discovery time: {datetime.now().strftime('%H:%M:%S')}\n"
                        f"📊 Total discoveries today: {self.config['discovery_count_today']}\n\n"
                        f"Please check the dashboard to review new proposals!",
                        "info",
                    )
            else:
                logger.info("ℹ️ No new knowledge discovered this time")

        except Exception as e:
            logger.error(f"❌ Knowledge discovery failed: {e}")

    def _export_dashboard_data(self):
        """Export dashboard data for public viewing"""
        try:
            logger.info("📊 Exporting dashboard data...")

            # Run export script
            export_script = project_root / "scripts" / "export_dashboard_data.py"
            if export_script.exists():
                import subprocess

                result = subprocess.run(
                    [sys.executable, str(export_script)],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                )

                if result.returncode == 0:
                    logger.info("✅ Dashboard data exported successfully")
                else:
                    logger.error(f"❌ Dashboard export failed: {result.stderr}")
            else:
                logger.warning("⚠️ Dashboard export script not found")

        except Exception as e:
            logger.error(f"Error exporting dashboard data: {e}")

    def start_service(self):
        """Khởi động background service"""
        logger.info("🧠 StillMe IPC Background Service")
        logger.info("==========================================")
        logger.info("🚀 Starting background service...")

        # Schedule discovery every X hours
        discovery_interval = self.config["discovery_interval_hours"]
        schedule.every(discovery_interval).hours.do(self.discover_knowledge)

        # Schedule dashboard data export (every 6 hours)
        schedule.every(6).hours.do(self._export_dashboard_data)

        logger.info(
            f"⏰ Scheduled knowledge discovery every {discovery_interval} hours"
        )
        logger.info(
            f"📊 Max discoveries per day: {self.config['max_discoveries_per_day']}"
        )
        logger.info("📊 Dashboard data export every 6 hours")
        logger.info(
            f"🔔 Notifications: {'Enabled' if self.config['notification_enabled'] else 'Disabled'}"
        )

        # Run initial discovery
        logger.info("🔍 Running initial knowledge discovery...")
        self.discover_knowledge()

        logger.info("✅ Background service started successfully!")
        logger.info("💡 The service will run continuously in the background.")
        logger.info("   Press Ctrl+C to stop the service.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Stopping background service...")
            logger.info("👋 StillMe IPC Background Service stopped.")

    def stop_service(self):
        """Dừng background service"""
        self.config["enabled"] = False
        self.save_config()
        logger.info("🛑 Background service stopped")


def main():
    """Main function"""
    service = StillMeBackgroundService()

    try:
        service.start_service()
    except Exception as e:
        logger.error(f"❌ Background service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
