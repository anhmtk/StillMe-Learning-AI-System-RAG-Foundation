#!/bin/bash
# Compute Base URL - Linux/macOS
# Trả về BASE_URL cho StillMe server

# Đọc port từ .env nếu có
PORT="8000"
if [ -f ".env" ]; then
    SERVER_PORT=$(grep "SERVER_PORT=" .env | cut -d'=' -f2 | tr -d '\r\n')
    if [ -n "$SERVER_PORT" ]; then
        PORT="$SERVER_PORT"
    fi
fi

# Lấy Tailscale IP
TAILSCALE_IP=$(bash "$(dirname "$0")/get_tailscale_ip.sh")

if [ -n "$TAILSCALE_IP" ]; then
    BASE_URL="http://$TAILSCALE_IP:$PORT"
else
    # Fallback: lấy LAN IP
    if command -v hostname >/dev/null 2>&1; then
        LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    elif command -v ip >/dev/null 2>&1; then
        LAN_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -n1)
    else
        LAN_IP=""
    fi
    
    if [ -n "$LAN_IP" ] && [[ $LAN_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        BASE_URL="http://$LAN_IP:$PORT"
    else
        # Fallback cuối cùng
        BASE_URL="http://localhost:$PORT"
    fi
fi

echo "$BASE_URL"

# Ghi vào config file
mkdir -p config
echo -n "$BASE_URL" > config/runtime_base_url.txt
