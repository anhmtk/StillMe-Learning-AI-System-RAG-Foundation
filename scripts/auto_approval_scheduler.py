#!/usr/bin/env python3
"""
🤖 AUTO-APPROVAL SCHEDULER
Tự động approve và bắt đầu học tập mỗi giờ
"""

import schedule
import time
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from stillme_core.learning.auto_approval_engine import AutoApprovalEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("auto_approval.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AutoApprovalScheduler:
    def __init__(self):
        self.approval_engine = AutoApprovalEngine()
        self.approval_count = 0
        self.total_approved = 0

    def scheduled_approval(self):
        """Chạy approval cycle theo lịch"""
        try:
            logger.info("🤖 Bắt đầu auto-approval cycle...")

            # Chạy auto-approval
            approved_count = self.approval_engine.run_approval_cycle()

            self.approval_count += 1
            self.total_approved += approved_count

            logger.info(f"✅ Hoàn thành auto-approval #{self.approval_count}")
            logger.info(f"📊 Đã approve {approved_count} proposals trong cycle này")
            logger.info(f"🎯 Tổng cộng đã approve: {self.total_approved} proposals")

            if approved_count > 0:
                logger.info(
                    f"🎉 Hệ thống đã tự động bắt đầu {approved_count} bài học mới"
                )
            else:
                logger.info("ℹ️ Không có proposal nào đạt tiêu chuẩn auto-approval")

        except Exception as e:
            logger.error(f"❌ Lỗi trong auto-approval: {e}")
            logger.error("🔧 Sẽ thử lại trong 1 giờ tới")

    def start_scheduler(self):
        """Khởi động scheduler"""
        logger.info("🤖 Khởi động Auto-Approval Scheduler")
        logger.info("⏰ Lịch chạy: Mỗi 1 giờ")
        logger.info("📊 Bắt đầu approval ngay lập tức...")

        # Chạy approval ngay lập tức
        self.scheduled_approval()

        # Lập lịch chạy mỗi 1 giờ
        schedule.every(1).hours.do(self.scheduled_approval)

        logger.info("✅ Scheduler đã được thiết lập")
        logger.info("🔄 Đang chạy background...")

        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check mỗi phút
            except KeyboardInterrupt:
                logger.info("🛑 Dừng Auto-Approval Scheduler")
                break
            except Exception as e:
                logger.error(f"❌ Lỗi trong scheduler loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Main function"""
    scheduler = AutoApprovalScheduler()
    scheduler.start_scheduler()


if __name__ == "__main__":
    main()
