#!/usr/bin/env python3
"""
Test script for StillMe Communication Channel
Tests the communication flow between Gateway and clients
"""

import asyncio
import json
import websockets
import aiohttp
import time
from typing import Dict, Any


class CommunicationTester:
    """Test communication flow between Gateway and clients"""
    
    def __init__(self, gateway_url: str = "ws://localhost:8001"):
        self.gateway_url = gateway_url
        self.http_url = gateway_url.replace("ws://", "http://").replace("wss://", "https://")
        
    async def test_gateway_health(self) -> bool:
        """Test Gateway health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.http_url}/api/health/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Gateway Health: {data['status']}")
                        return True
                    else:
                        print(f"❌ Gateway Health: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Gateway Health Error: {e}")
            return False
    
    async def test_websocket_connection(self, client_id: str = "test-client") -> bool:
        """Test WebSocket connection to Gateway"""
        try:
            uri = f"{self.gateway_url}/ws/{client_id}"
            async with websockets.connect(uri) as websocket:
                print(f"✅ WebSocket Connected: {client_id}")
                
                # Send heartbeat
                heartbeat = {
                    "id": f"hb_{int(time.time() * 1000)}",
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "source": client_id,
                    "content": {"heartbeat": True}
                }
                
                await websocket.send(json.dumps(heartbeat))
                print("✅ Heartbeat sent")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✅ Heartbeat response: {data['type']}")
                
                return True
                
        except Exception as e:
            print(f"❌ WebSocket Connection Error: {e}")
            return False
    
    async def test_command_execution(self, client_id: str = "test-client") -> bool:
        """Test command execution through Gateway"""
        try:
            uri = f"{self.gateway_url}/ws/{client_id}"
            async with websockets.connect(uri) as websocket:
                print(f"✅ WebSocket Connected for command test: {client_id}")
                
                # Send test command
                command = {
                    "id": f"cmd_{int(time.time() * 1000)}",
                    "type": "command",
                    "timestamp": time.time(),
                    "source": client_id,
                    "content": {
                        "command": "test",
                        "parameters": {"message": "Hello StillMe!"},
                        "context": {"test": True}
                    }
                }
                
                await websocket.send(json.dumps(command))
                print("✅ Command sent")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"✅ Command response: {data}")
                
                return True
                
        except Exception as e:
            print(f"❌ Command Execution Error: {e}")
            return False
    
    async def test_authentication(self) -> bool:
        """Test authentication endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test login
                login_data = {
                    "username": "testuser",
                    "password": "testpass"
                }
                
                async with session.post(f"{self.http_url}/api/auth/login", json=login_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Authentication successful")
                        print(f"   Access token: {data['access_token'][:20]}...")
                        return True
                    else:
                        print(f"❌ Authentication failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Authentication Error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all communication tests"""
        print("🚀 Starting StillMe Communication Channel Tests")
        print("=" * 50)
        
        results = {}
        
        # Test Gateway Health
        print("\n1. Testing Gateway Health...")
        results['health'] = await self.test_gateway_health()
        
        # Test Authentication
        print("\n2. Testing Authentication...")
        results['auth'] = await self.test_authentication()
        
        # Test WebSocket Connection
        print("\n3. Testing WebSocket Connection...")
        results['websocket'] = await self.test_websocket_connection()
        
        # Test Command Execution
        print("\n4. Testing Command Execution...")
        results['command'] = await self.test_command_execution()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.upper()}: {status}")
        
        total_passed = sum(results.values())
        total_tests = len(results)
        print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 All tests passed! Communication channel is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        return results


async def main():
    """Main test function"""
    tester = CommunicationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("StillMe Communication Channel Test Suite")
    print("Make sure Gateway is running on localhost:8001")
    print("Press Ctrl+C to cancel")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests cancelled by user")
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
