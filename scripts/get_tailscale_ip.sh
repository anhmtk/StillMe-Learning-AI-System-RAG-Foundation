#!/bin/bash
# Get Tailscale IP - Linux/macOS
# Trả về IPv4 của Tailscale interface hoặc chuỗi rỗng

# Thử dùng tailscale CLI trước
if command -v tailscale >/dev/null 2>&1; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -n1)
    if [[ $TAILSCALE_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "$TAILSCALE_IP"
        exit 0
    fi
fi

# Dò interface tailscale0 từ ip addr
if command -v ip >/dev/null 2>&1; then
    TAILSCALE_IP=$(ip addr show tailscale0 2>/dev/null | grep -oP 'inet \K[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n1)
    if [[ $TAILSCALE_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "$TAILSCALE_IP"
        exit 0
    fi
fi

# Không tìm thấy Tailscale IP
echo ""
exit 0
