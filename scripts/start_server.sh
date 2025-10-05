#!/bin/bash
# Start StillMe Server - Linux/macOS
# Khởi động server detached với logging

# Tạo thư mục logs nếu chưa có
mkdir -p logs

# Xác định server script
SERVER_SCRIPT="stable_ai_server.py"
if [ ! -f "$SERVER_SCRIPT" ]; then
    SERVER_SCRIPT="framework.py"
fi

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "❌ Không tìm thấy server script: $SERVER_SCRIPT" >&2
    exit 1
fi

# Dừng server cũ nếu có
bash "$(dirname "$0")/stop_server.sh" 2>/dev/null

# Khởi động server detached
echo "🚀 Khởi động StillMe server detached..."
nohup python3 -u "$SERVER_SCRIPT" > logs/server.log 2>&1 &
SERVER_PID=$!

if [ $? -eq 0 ]; then
    echo "✅ Server đã khởi động với PID: $SERVER_PID"
    echo "📝 Logs được ghi vào: logs/server.log"
    
    # Lưu PID để dễ dừng sau này
    echo -n "$SERVER_PID" > logs/server.pid
    
    # Disown process để tránh hang terminal
    disown $SERVER_PID
else
    echo "❌ Không thể khởi động server" >&2
    exit 1
fi
