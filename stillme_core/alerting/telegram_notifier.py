"""
📱 StillMe IPC Telegram Notifier
================================

Real Telegram notifications for StillMe IPC learning events.
Sends alerts to founder via Telegram Bot API.

Author: StillMe IPC (Intelligent Personal Companion)
Version: 1.0.0
Date: 2025-09-29
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Real Telegram notifier for StillMe IPC"""

    def __init__(self):
        self.config_file = Path("artifacts/telegram_config.json")
        self.load_config()

    def load_config(self):
        """Load Telegram configuration from .env first, then config file"""
        # Load from .env first
        env_config = {
            "enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
            "parse_mode": "HTML"
        }

        # Load from config file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    file_config = json.load(f)
                # Merge with env config (env takes priority)
                env_config.update(file_config)
            except:
                pass

        self.config = env_config
        self.save_config()

    def save_config(self):
        """Save Telegram configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def setup_telegram(self, bot_token: str, chat_id: str):
        """Setup Telegram configuration"""
        self.config.update({
            "enabled": True,
            "bot_token": bot_token,
            "chat_id": chat_id
        })
        self.save_config()
        logger.info("📱 Telegram configuration saved")

    def send_alert(self, title: str, message: str, level: str = "info"):
        """Send real Telegram alert"""
        if not self.config["enabled"]:
            logger.warning("📱 Telegram notifications disabled")
            return False

        try:
            # Create message
            emoji_map = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅",
                "critical": "🚨"
            }

            emoji = emoji_map.get(level, "ℹ️")

            telegram_message = f"""
{emoji} <b>StillMe IPC Alert</b>
🧠 <i>Intelligent Personal Companion</i>

<b>📋 {title}</b>

{message}

📊 <b>System Info:</b>
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Level: {level.upper()}
• Source: StillMe IPC Learning System

🚀 <a href="http://localhost:8507">Open Dashboard</a>
            """.strip()

            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
            data = {
                "chat_id": self.config["chat_id"],
                "text": telegram_message,
                "parse_mode": self.config["parse_mode"],
                "disable_web_page_preview": True
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            logger.info(f"📱 Telegram message sent successfully: {title}")
            return True

        except Exception as e:
            logger.error(f"📱 Failed to send Telegram message: {e}")
            return False

    def test_telegram(self):
        """Test Telegram configuration"""
        if not self.config["enabled"]:
            return False

        return self.send_alert(
            "Test Telegram",
            "This is a test message from StillMe IPC Learning System.\n\nIf you receive this, Telegram notifications are working correctly!",
            "info"
        )

    def get_bot_info(self):
        """Get bot information"""
        if not self.config["enabled"]:
            return None

        try:
            url = f"https://api.telegram.org/bot{self.config['bot_token']}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"📱 Failed to get bot info: {e}")
            return None
