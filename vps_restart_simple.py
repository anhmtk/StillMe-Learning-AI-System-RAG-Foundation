#!/usr/bin/env python3
"""
StillMe AI Server Simple Restart Script (Windows Compatible)
Script đơn giản để restart AI Server trên VPS
"""

import requests
import time
import json
from datetime import datetime

# Configuration
VPS_IP = "160.191.89.99"
AI_SERVER_PORT = 1216
GATEWAY_PORT = 21568

def test_port(ip, port, service_name):
    """Test if port is accessible"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"[OK] {service_name} is accessible on port {port}")
            return True
        else:
            print(f"[FAIL] {service_name} is NOT accessible on port {port}")
            return False
    except Exception as e:
        print(f"[ERROR] Error testing port {port}: {str(e)}")
        return False

def test_http_endpoint(url, service_name):
    """Test HTTP endpoint"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"[OK] {service_name} HTTP endpoint is responding")
            return True
        else:
            print(f"[FAIL] {service_name} HTTP endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] {service_name} HTTP endpoint error: {str(e)}")
        return False

def test_chat_endpoint():
    """Test chat endpoint"""
    try:
        url = f"http://{VPS_IP}:{GATEWAY_PORT}/chat"
        data = {"message": "Test message"}
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"[OK] Chat endpoint is responding")
            return True
        else:
            print(f"[FAIL] Chat endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Chat endpoint error: {str(e)}")
        return False

def main():
    """Main function"""
    print("StillMe VPS Services Test")
    print("=" * 40)
    print(f"VPS IP: {VPS_IP}")
    print(f"AI Server Port: {AI_SERVER_PORT}")
    print(f"Gateway Port: {GATEWAY_PORT}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test AI Server
    print("Testing AI Server...")
    ai_port_ok = test_port(VPS_IP, AI_SERVER_PORT, "AI Server")
    ai_http_ok = test_http_endpoint(f"http://{VPS_IP}:{AI_SERVER_PORT}/health", "AI Server")
    
    print()
    
    # Test Gateway
    print("Testing Gateway...")
    gateway_port_ok = test_port(VPS_IP, GATEWAY_PORT, "Gateway")
    gateway_http_ok = test_http_endpoint(f"http://{VPS_IP}:{GATEWAY_PORT}/health", "Gateway")
    
    print()
    
    # Test Chat
    print("Testing Chat Endpoint...")
    chat_ok = test_chat_endpoint()
    
    print()
    print("=" * 40)
    print("SUMMARY:")
    print(f"AI Server: {'OK' if ai_port_ok and ai_http_ok else 'FAIL'}")
    print(f"Gateway: {'OK' if gateway_port_ok and gateway_http_ok else 'FAIL'}")
    print(f"Chat: {'OK' if chat_ok else 'FAIL'}")
    
    if not (ai_port_ok and ai_http_ok):
        print()
        print("AI Server is down! You need to restart it manually on VPS:")
        print("ssh root@160.191.89.99")
        print("systemctl restart stillme-ai-server")
        print("systemctl status stillme-ai-server")
    
    if not (gateway_port_ok and gateway_http_ok):
        print()
        print("Gateway is down! You need to restart it manually on VPS:")
        print("ssh root@160.191.89.99")
        print("systemctl restart stillme-gateway")
        print("systemctl status stillme-gateway")

if __name__ == "__main__":
    main()
