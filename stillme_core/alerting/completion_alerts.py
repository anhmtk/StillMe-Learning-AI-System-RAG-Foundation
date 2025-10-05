#!/usr/bin/env python3
"""
🎉 COMPLETION ALERT SERVICE
Chỉ gửi thông báo khi hoàn thành học tập 100%
"""

import logging
from typing import Dict, Any
from datetime import datetime

from stillme_core.alerting.alerting_system import AlertingSystem

logger = logging.getLogger(__name__)

class CompletionAlertService:
    def __init__(self):
        self.alerting_system = AlertingSystem()
        logger.info("🎉 CompletionAlertService initialized")
        logger.info("📢 Chế độ: Chỉ gửi thông báo khi hoàn thành 100%")
    
    def send_learning_completed_alert(self, proposal: Dict[str, Any]):
        """Gửi thông báo hoàn thành học tập"""
        try:
            title = proposal.get('title', 'Unknown Learning Session')
            objectives = proposal.get('learning_objectives', [])
            duration = proposal.get('estimated_duration', 0)
            progress = proposal.get('learning_progress', 100.0)
            
            # Create completion message
            message = self._create_completion_message(title, objectives, duration, progress)
            
            # Send through all channels
            self.alerting_system.send_alert(
                "🎉 STILLME ĐÃ HOÀN THÀNH HỌC TẬP",
                message,
                "success"
            )
            
            logger.info(f"📢 Đã gửi completion alert: {title}")
            
        except Exception as e:
            logger.error(f"❌ Lỗi gửi completion alert: {e}")
    
    def _create_completion_message(self, title: str, objectives: list, duration: int, progress: float) -> str:
        """Tạo message hoàn thành"""
        objectives_text = "\n".join([f"  • {obj}" for obj in objectives[:3]])  # Show first 3 objectives
        if len(objectives) > 3:
            objectives_text += f"\n  • ... và {len(objectives) - 3} objectives khác"
        
        message = f"""
🎉 **STILLME ĐÃ HOÀN THÀNH HỌC TẬP**

📚 **Bài học:** {title}
✅ **Tiến độ:** {progress:.1f}% hoàn thành
⏱️ **Thời gian:** {duration} phút
📊 **Số objectives:** {len(objectives)}

🎯 **Objectives đã học:**
{objectives_text}

🧠 **StillMe IPC tiếp tục học tập và phát triển!**
📈 **Hệ thống tự động sẽ tìm kiếm kiến thức mới...**

---
⏰ Hoàn thành lúc: {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}
        """
        
        return message.strip()
    
    def send_batch_completion_alert(self, completed_sessions: list):
        """Gửi thông báo tổng hợp cho nhiều session hoàn thành"""
        try:
            if not completed_sessions:
                return
            
            total_sessions = len(completed_sessions)
            total_duration = sum(s.get('estimated_duration', 0) for s in completed_sessions)
            
            message = f"""
🎉 **STILLME ĐÃ HOÀN THÀNH {total_sessions} BÀI HỌC**

📊 **Tổng kết:**
  • Số bài học: {total_sessions}
  • Tổng thời gian: {total_duration} phút
  • Trung bình: {total_duration/total_sessions:.1f} phút/bài

📚 **Các bài học đã hoàn thành:**
{self._format_completed_sessions(completed_sessions)}

🧠 **StillMe IPC đang trở nên thông minh hơn!**
            """
            
            self.alerting_system.send_alert(
                f"🎉 Hoàn thành {total_sessions} bài học",
                message,
                "success"
            )
            
            logger.info(f"📢 Đã gửi batch completion alert: {total_sessions} sessions")
            
        except Exception as e:
            logger.error(f"❌ Lỗi gửi batch completion alert: {e}")
    
    def _format_completed_sessions(self, sessions: list) -> str:
        """Format danh sách sessions hoàn thành"""
        formatted = []
        for i, session in enumerate(sessions[:5], 1):  # Show max 5 sessions
            title = session.get('title', 'Unknown')
            duration = session.get('estimated_duration', 0)
            formatted.append(f"  {i}. {title} ({duration} phút)")
        
        if len(sessions) > 5:
            formatted.append(f"  ... và {len(sessions) - 5} bài học khác")
        
        return "\n".join(formatted)
    
    def send_learning_summary_alert(self, daily_stats: Dict[str, Any]):
        """Gửi thông báo tổng kết học tập hàng ngày"""
        try:
            completed_today = daily_stats.get('completed_today', 0)
            total_duration = daily_stats.get('total_duration', 0)
            active_sessions = daily_stats.get('active_sessions', 0)
            
            message = f"""
📊 **TỔNG KẾT HỌC TẬP HÔM NAY**

✅ **Đã hoàn thành:** {completed_today} bài học
⏱️ **Tổng thời gian:** {total_duration} phút
🔄 **Đang học:** {active_sessions} bài học

🧠 **StillMe IPC đang học tập liên tục!**
📈 **Hệ thống tự động sẽ tiếp tục tìm kiếm kiến thức mới...**
            """
            
            self.alerting_system.send_alert(
                "📊 Tổng kết học tập hôm nay",
                message,
                "info"
            )
            
            logger.info(f"📢 Đã gửi daily summary alert")
            
        except Exception as e:
            logger.error(f"❌ Lỗi gửi daily summary alert: {e}")

def main():
    """Test function"""
    service = CompletionAlertService()
    print("🎉 Completion Alert Service initialized")
    print("📢 Sẵn sàng gửi thông báo hoàn thành học tập")

if __name__ == "__main__":
    main()
