#!/usr/bin/env python3
"""
🤖 AUTO-DISCOVERY SCHEDULER
Tự động thu thập kiến thức mỗi 6 giờ cho StillMe IPC
"""

import schedule
import time
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.knowledge_discovery import KnowledgeDiscoverySystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("auto_discovery.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AutoDiscoveryScheduler:
    def __init__(self):
        self.discovery_system = KnowledgeDiscoverySystem()
        self.discovery_count = 0

    def scheduled_discovery(self):
        """Chạy discovery cycle theo lịch"""
        try:
            logger.info("🔄 Bắt đầu auto-discovery cycle...")

            # Chạy knowledge discovery
            proposals_created = self.discovery_system.run_discovery_cycle()

            self.discovery_count += 1
            logger.info(f"✅ Hoàn thành auto-discovery #{self.discovery_count}")
            logger.info(f"📊 Đã tạo {proposals_created} proposals mới")

            # Log summary
            if proposals_created > 0:
                logger.info(
                    f"🎯 Hệ thống đã tự động phát hiện {proposals_created} chủ đề học tập mới"
                )
            else:
                logger.info("ℹ️ Không có chủ đề mới phù hợp trong lần discovery này")

        except Exception as e:
            logger.error(f"❌ Lỗi trong auto-discovery: {e}")
            logger.error("🔧 Sẽ thử lại trong 6 giờ tới")

    def start_scheduler(self):
        """Khởi động scheduler"""
        logger.info("🚀 Khởi động Auto-Discovery Scheduler")
        logger.info("⏰ Lịch chạy: Mỗi 6 giờ")
        logger.info("📊 Bắt đầu discovery ngay lập tức...")

        # Chạy discovery ngay lập tức
        self.scheduled_discovery()

        # Lập lịch chạy mỗi 6 giờ
        schedule.every(6).hours.do(self.scheduled_discovery)

        logger.info("✅ Scheduler đã được thiết lập")
        logger.info("🔄 Đang chạy background...")

        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check mỗi phút
            except KeyboardInterrupt:
                logger.info("🛑 Dừng Auto-Discovery Scheduler")
                break
            except Exception as e:
                logger.error(f"❌ Lỗi trong scheduler loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Main function"""
    scheduler = AutoDiscoveryScheduler()
    scheduler.start_scheduler()


if __name__ == "__main__":
    main()
