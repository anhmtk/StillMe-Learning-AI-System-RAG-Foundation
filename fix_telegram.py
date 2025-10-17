#!/usr/bin/env python3
"""
Fix Telegram Notification Issues
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from stillme_core.env_loader import load_env_hierarchy
    load_env_hierarchy()
except ImportError:
    print("Warning: Could not import env_loader")
except Exception as e:
    print(f"Warning: Error loading environment: {e}")


async def test_telegram_directly():
    """Test Telegram API directly"""
    import os
    import requests
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"🔍 Telegram Configuration:")
    print(f"  Bot Token: {bot_token[:10]}...{bot_token[-5:] if bot_token else 'NOT_SET'}")
    print(f"  Chat ID: {chat_id}")
    
    if not bot_token or not chat_id:
        print("❌ Missing Telegram configuration!")
        return
    
    # Test 1: Get bot info
    print("\n📋 Testing bot info...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            print(f"  ✅ Bot info: {bot_info['result']['first_name']} (@{bot_info['result']['username']})")
        else:
            print(f"  ❌ Bot info failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"  ❌ Bot info error: {e}")
        return
    
    # Test 2: Send test message
    print("\n📱 Testing message send...")
    try:
        message = "🧪 Test message from StillMe Learning System"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("  ✅ Message sent successfully!")
            result = response.json()
            print(f"  Message ID: {result['result']['message_id']}")
        else:
            print(f"  ❌ Message send failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
            # Try to get chat info
            if response.status_code == 400:
                print("\n🔍 Trying to get chat info...")
                chat_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat", 
                                           params={'chat_id': chat_id})
                if chat_response.status_code == 200:
                    chat_info = chat_response.json()
                    print(f"  Chat info: {chat_info['result']}")
                else:
                    print(f"  ❌ Chat info failed: {chat_response.status_code} - {chat_response.text}")
                    
    except Exception as e:
        print(f"  ❌ Message send error: {e}")


if __name__ == "__main__":
    asyncio.run(test_telegram_directly())
