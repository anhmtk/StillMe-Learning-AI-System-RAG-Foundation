#!/bin/bash
# Wait for Server Ready - Linux/macOS
# Chờ server sẵn sàng với health check

BASE_URL="$1"
MAX_ATTEMPTS=60
DELAY_MS=500

if [ -z "$BASE_URL" ]; then
    if [ -f "config/runtime_base_url.txt" ]; then
        BASE_URL=$(cat config/runtime_base_url.txt)
    else
        echo "❌ Không tìm thấy BaseUrl. Chạy compute_base_url.sh trước." >&2
        exit 1
    fi
fi

echo "⏳ Chờ server sẵn sàng tại: $BASE_URL"
echo "🔄 Tối đa $MAX_ATTEMPTS lần thử, mỗi lần cách nhau $DELAY_MS ms"

for ((i=1; i<=MAX_ATTEMPTS; i++)); do
    if curl -sf "$BASE_URL/readyz" >/dev/null 2>&1; then
        echo "✅ Server đã sẵn sàng! (lần thử $i/$MAX_ATTEMPTS)"
        exit 0
    fi
    
    if [ $i -lt $MAX_ATTEMPTS ]; then
        sleep 0.5
        echo "⏳ Lần thử $i/$MAX_ATTEMPTS - Server chưa sẵn sàng..."
    fi
done

echo "❌ Server không sẵn sàng sau $MAX_ATTEMPTS lần thử" >&2
echo "📝 Kiểm tra logs: tail -20 logs/server.log"
exit 1
