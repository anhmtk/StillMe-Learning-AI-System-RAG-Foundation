#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-"http://160.191.89.99:21568"}
m="Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột."
echo "==> SEND complex: $m"
curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
  -d "{\"message\":\"$m\",\"session_id\":\"router-test\"}" | jq '{model:.model, text:(.response//.text//.output), ts:.timestamp}'
