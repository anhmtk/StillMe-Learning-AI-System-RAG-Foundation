#!/bin/bash
# Smoke Test - Linux/macOS
# Chạy smoke test end-to-end

BASE_URL="$1"

# Tạo thư mục reports nếu chưa có
mkdir -p reports

# Lấy BASE_URL
if [ -z "$BASE_URL" ]; then
    if [ -f "config/runtime_base_url.txt" ]; then
        BASE_URL=$(cat config/runtime_base_url.txt)
    else
        echo "❌ Không tìm thấy BaseUrl. Chạy compute_base_url.sh trước." >&2
        exit 1
    fi
fi

echo "🧪 Chạy Smoke Test cho: $BASE_URL"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="reports/tailscale_smoke.txt"

# Khởi tạo báo cáo
cat > "$REPORT_FILE" << EOF
=== STILLME TAILSCALE SMOKE TEST REPORT ===
Timestamp: $TIMESTAMP
Base URL: $BASE_URL
Overall Status: RUNNING

Test Results:
EOF

OVERALL_STATUS="PASS"

# Test /livez
echo "🔍 Testing /livez..."
if curl -sf "$BASE_URL/livez" >/dev/null 2>&1; then
    echo "- /livez: PASS" >> "$REPORT_FILE"
    echo "✅ /livez: 200"
else
    echo "- /livez: FAIL" >> "$REPORT_FILE"
    OVERALL_STATUS="FAIL"
    echo "❌ /livez: FAILED"
fi

# Test /readyz
echo "🔍 Testing /readyz..."
if curl -sf "$BASE_URL/readyz" >/dev/null 2>&1; then
    echo "- /readyz: PASS" >> "$REPORT_FILE"
    echo "✅ /readyz: 200"
else
    echo "- /readyz: FAIL" >> "$REPORT_FILE"
    OVERALL_STATUS="FAIL"
    echo "❌ /readyz: FAILED"
fi

# Test /version
echo "🔍 Testing /version..."
VERSION_RESPONSE=$(curl -sf "$BASE_URL/version" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$VERSION_RESPONSE" ]; then
    echo "- /version: PASS" >> "$REPORT_FILE"
    echo "✅ /version: 200"
    echo "$VERSION_RESPONSE" | jq -r '.name + " " + .version' 2>/dev/null || echo "Version info available"
else
    echo "- /version: FAIL" >> "$REPORT_FILE"
    OVERALL_STATUS="FAIL"
    echo "❌ /version: FAILED"
fi

# Test /health (optional)
echo "🔍 Testing /health..."
if curl -sf "$BASE_URL/health" >/dev/null 2>&1; then
    echo "- /health: PASS" >> "$REPORT_FILE"
    echo "✅ /health: 200"
else
    echo "- /health: FAIL" >> "$REPORT_FILE"
    echo "❌ /health: FAILED"
fi

# Cập nhật overall status
sed -i "s/Overall Status: RUNNING/Overall Status: $OVERALL_STATUS/" "$REPORT_FILE"

# Thêm version info
echo "" >> "$REPORT_FILE"
echo "Version Info:" >> "$REPORT_FILE"
echo "$VERSION_RESPONSE" >> "$REPORT_FILE"

# Thêm server logs
echo "" >> "$REPORT_FILE"
echo "Server Logs (last 20 lines):" >> "$REPORT_FILE"
if [ -f "logs/server.log" ]; then
    tail -20 logs/server.log >> "$REPORT_FILE"
else
    echo "No server log found" >> "$REPORT_FILE"
fi

echo "📊 Kết quả tổng thể: $OVERALL_STATUS"
echo "📝 Báo cáo đã lưu: $REPORT_FILE"

if [ "$OVERALL_STATUS" = "FAIL" ]; then
    echo "📝 Server logs:"
    if [ -f "logs/server.log" ]; then
        tail -20 logs/server.log
    fi
    exit 1
else
    exit 0
fi
