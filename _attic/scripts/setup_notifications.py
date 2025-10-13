#!/usr/bin/env python3
"""
📧📱 StillMe IPC Notification Setup
===================================

Setup real email and Telegram notifications for StillMe IPC.
Configure Gmail SMTP and Telegram Bot for founder alerts.

Author: StillMe IPC (Intelligent Personal Companion)
Version: 1.0.0
Date: 2025-09-29
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.alerting.email_notifier import EmailNotifier
from stillme_core.alerting.telegram_notifier import TelegramNotifier


def setup_email():
    """Setup email notifications"""
    print("📧 Setting up Email Notifications")
    print("==================================")

    # Check if already configured in .env
    sender_email = os.getenv("SMTP_USERNAME")
    sender_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("ALERT_EMAIL")

    if sender_email and sender_password and recipient_email:
        print("✅ Email configuration found in .env file!")
        print(f"📧 Sender: {sender_email}")
        print(f"📨 Recipient: {recipient_email}")
        print()

        # Test email
        print("🧪 Testing email...")
        email_notifier = EmailNotifier()
        if email_notifier.test_email():
            print("✅ Email setup successful!")
            print(f"📧 Test email sent to: {recipient_email}")
            return True
        else:
            print("❌ Email test failed!")
            print("💡 Check your .env configuration:")
            print("   • SMTP_USERNAME")
            print("   • SMTP_PASSWORD (App Password)")
            print("   • ALERT_EMAIL")
            return False
    else:
        print("❌ Email configuration not found in .env file!")
        print("📋 Please add to your .env file:")
        print("   SMTP_USERNAME=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        print("   ALERT_EMAIL=recipient@example.com")
        print()
        print("🔐 For Gmail App Password:")
        print("1. Go to Google Account settings")
        print("2. Security → 2-Step Verification → App passwords")
        print("3. Generate password for 'Mail'")
        return False


def setup_telegram():
    """Setup Telegram notifications"""
    print("\n📱 Setting up Telegram Notifications")
    print("====================================")

    # Check if already configured in .env
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        print("✅ Telegram configuration found in .env file!")
        print(f"🤖 Bot Token: {bot_token[:10]}...")
        print(f"💬 Chat ID: {chat_id}")
        print()

        # Test Telegram
        print("🧪 Testing Telegram...")
        telegram_notifier = TelegramNotifier()
        if telegram_notifier.test_telegram():
            print("✅ Telegram setup successful!")
            print("📱 Test message sent to your Telegram!")
            return True
        else:
            print("❌ Telegram test failed!")
            print("💡 Check your .env configuration:")
            print("   • TELEGRAM_BOT_TOKEN")
            print("   • TELEGRAM_CHAT_ID")
            return False
    else:
        print("❌ Telegram configuration not found in .env file!")
        print("📋 Please add to your .env file:")
        print("   TELEGRAM_BOT_TOKEN=your-bot-token")
        print("   TELEGRAM_CHAT_ID=your-chat-id")
        print()
        print("🤖 To create a bot:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot")
        print("3. Follow instructions to get Bot Token")
        print()
        print("💬 To get Chat ID:")
        print("1. Message your bot")
        print("2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("3. Find 'chat':{'id': YOUR_CHAT_ID}")
        return False


def main():
    """Main setup function"""
    print("🧠 StillMe IPC Notification Setup")
    print("=================================")
    print("Configure real email and Telegram notifications")
    print()

    # Setup email
    email_success = setup_email()

    # Setup Telegram
    telegram_success = setup_telegram()

    print("\n🎉 Setup Complete!")
    print("==================")
    print(f"📧 Email notifications: {'✅ Enabled' if email_success else '❌ Disabled'}")
    print(
        f"📱 Telegram notifications: {'✅ Enabled' if telegram_success else '❌ Disabled'}"
    )

    if email_success or telegram_success:
        print("\n💡 Next steps:")
        print("1. Run: python scripts/stillme_control.py background")
        print("2. StillMe will send real notifications!")
        print("3. Check your email/Telegram for alerts")
    else:
        print("\n⚠️ No notifications configured.")
        print("StillMe will only show desktop notifications.")


if __name__ == "__main__":
    main()
