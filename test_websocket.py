#!/usr/bin/env python3
"""
WebSocket Test for StillMe Gateway
Test WebSocket connection và real-time communication
"""

import asyncio
import json
from datetime import datetime

import websockets


async def test_websocket():
    """Test WebSocket connection to Gateway"""
    uri = "ws://192.168.1.8:8000/ws/desktop-client"

    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")

            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Welcome message: {welcome_data}")

            # Send test message
            test_message = {
                "type": "test",
                "message": "Hello from desktop client!",
                "timestamp": datetime.now().isoformat(),
            }

            print("📤 Sending test message...")
            await websocket.send(json.dumps(test_message))

            # Wait for echo response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Echo response: {response_data}")

            # Test AI message
            ai_message = {
                "type": "chat",
                "message": "Xin chào StillMe!",
                "language": "vi",
                "timestamp": datetime.now().isoformat(),
            }

            print("🤖 Sending AI message...")
            await websocket.send(json.dumps(ai_message))

            # Wait for AI response
            ai_response = await websocket.recv()
            ai_response_data = json.loads(ai_response)
            print(f"🧠 AI response: {ai_response_data}")

            print("✅ WebSocket test completed successfully!")

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


if __name__ == "__main__":
    print("🧪 Testing WebSocket Connection to StillMe Gateway")
    print("=" * 50)
    asyncio.run(test_websocket())
