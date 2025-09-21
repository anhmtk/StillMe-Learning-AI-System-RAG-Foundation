#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-"http://160.191.89.99:21568"}
msg_list=("xin chào" "2+2=?" "hello" "ping" "chào buổi sáng")
for m in "${msg_list[@]}"; do
  echo "==> SEND: $m"
  curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
    -d "{\"message\":\"$m\",\"session_id\":\"router-test\"}" | jq '{model:.model, text:(.response//.text//.output), ts:.timestamp}'
done
