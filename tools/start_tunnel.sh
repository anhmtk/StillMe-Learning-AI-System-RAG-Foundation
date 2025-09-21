#!/bin/bash
# StillMe SSH Reverse Tunnel Script for Linux/macOS
# Tạo SSH reverse tunnel từ Local PC đến VPS

set -euo pipefail

# Default values
VPS_IP=""
VPS_USER="root"
LOCAL_PORT=1216
REMOTE_PORT=1216

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            VPS_IP="$2"
            shift 2
            ;;
        -u|--user)
            VPS_USER="$2"
            shift 2
            ;;
        -l|--local-port)
            LOCAL_PORT="$2"
            shift 2
            ;;
        -r|--remote-port)
            REMOTE_PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 -i VPS_IP [-u USER] [-l LOCAL_PORT] [-r REMOTE_PORT]"
            echo ""
            echo "Options:"
            echo "  -i, --ip IP        VPS IP address (required)"
            echo "  -u, --user USER    VPS username (default: root)"
            echo "  -l, --local-port   Local port (default: 1216)"
            echo "  -r, --remote-port  Remote port (default: 1216)"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$VPS_IP" ]]; then
    echo "❌ Error: VPS IP is required"
    echo "Usage: $0 -i VPS_IP"
    exit 1
fi

echo "🚀 Starting StillMe SSH Reverse Tunnel..."
echo "📡 Local: 127.0.0.1:$LOCAL_PORT -> VPS: $VPS_IP:$REMOTE_PORT"
echo "🔒 Security: HMAC authentication enabled"
echo "=" | tr -d '\n' && printf '%.0s=' {1..49} && echo

# Check if SSH is available
if ! command -v ssh &> /dev/null; then
    echo "❌ SSH not found. Please install OpenSSH."
    exit 1
fi

echo "✅ SSH found: $(ssh -V 2>&1)"

# Create tunnel command
TUNNEL_CMD="ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -N -R $REMOTE_PORT:127.0.0.1:$LOCAL_PORT $VPS_USER@$VPS_IP"

echo "🔧 Tunnel command: $TUNNEL_CMD"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Make sure Local Backend is running: python local_stillme_backend.py"
echo "2. Set GATEWAY_SECRET in both .env files"
echo "3. Press Ctrl+C to stop tunnel"
echo ""

# Start tunnel
echo "🌐 Starting tunnel..."
exec $TUNNEL_CMD
