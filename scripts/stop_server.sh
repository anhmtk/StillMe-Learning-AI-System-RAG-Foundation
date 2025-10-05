#!/bin/bash
# Stop StillMe Server - Linux/macOS
# Dừng server process

echo "🛑 Đang dừng StillMe server..."

# Đọc PID từ file nếu có
PID_FILE="logs/server.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && [ "$PID" -gt 0 ] 2>/dev/null; then
        if kill -0 "$PID" 2>/dev/null; then
            kill -TERM "$PID" 2>/dev/null
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                kill -KILL "$PID" 2>/dev/null
            fi
            echo "✅ Đã dừng server với PID: $PID"
        fi
    fi
    rm -f "$PID_FILE"
fi

# Tìm và dừng process python chạy server script
PIDS=$(pgrep -f "python.*stable_ai_server.py\|python.*framework.py" 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "$PIDS" | xargs kill -TERM 2>/dev/null
    sleep 2
    echo "$PIDS" | xargs kill -KILL 2>/dev/null
    echo "✅ Đã dừng server processes"
fi

# Tìm process sử dụng port 8000
PORT_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    kill -TERM "$PORT_PID" 2>/dev/null
    sleep 2
    if kill -0 "$PORT_PID" 2>/dev/null; then
        kill -KILL "$PORT_PID" 2>/dev/null
    fi
    echo "✅ Đã dừng process sử dụng port 8000, PID: $PORT_PID"
fi

echo "🏁 Hoàn thành dừng server"
