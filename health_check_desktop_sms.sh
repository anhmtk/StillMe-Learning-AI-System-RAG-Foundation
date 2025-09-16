#!/bin/bash

# health_check_desktop_sms.sh
# StillMe Health Check với Desktop App và SMS Notifications

# --- Configuration ---
GATEWAY_URL="https://your-domain.com/health" # Replace with your actual domain
AI_SERVER_URL="https://your-domain.com/ai/health" # Replace with your actual domain
ALERT_PHONE="+84901234567" # Replace with your phone number
TELEGRAM_BOT_TOKEN="" # Optional: Telegram bot token
TELEGRAM_CHAT_ID="" # Optional: Telegram chat ID
DISCORD_WEBHOOK_URL="" # Optional: Discord webhook URL

# --- Functions ---
send_desktop_alert() {
    TITLE="$1"
    MESSAGE="$2"
    SEVERITY="$3"
    
    # Gửi đến Desktop App
    python3 -c "
import requests
import json
from datetime import datetime

try:
    payload = {
        'type': 'system_alert',
        'title': '$TITLE',
        'message': '$MESSAGE',
        'severity': '$SEVERITY',
        'timestamp': datetime.now().isoformat(),
        'source': 'stillme_vps'
    }
    
    # Thử gửi đến Desktop App
    response = requests.post('http://localhost:3000/api/notifications', json=payload, timeout=5)
    if response.status_code == 200:
        print('✅ Desktop notification sent: $TITLE')
    else:
        print('❌ Desktop notification failed: ' + str(response.status_code))
        
except Exception as e:
    print('❌ Desktop app not reachable: ' + str(e))
"
}

send_sms_alert() {
    MESSAGE="$1"
    
    # Gửi SMS qua TextBelt (miễn phí)
    python3 -c "
import requests
import os

try:
    url = 'https://textbelt.com/text'
    data = {
        'phone': '$ALERT_PHONE',
        'message': '[StillMe Alert] $MESSAGE',
        'key': 'textbelt'
    }
    
    response = requests.post(url, data=data, timeout=10)
    result = response.json()
    
    if result.get('success'):
        print('✅ SMS sent via TextBelt: $MESSAGE')
    else:
        print('❌ SMS failed via TextBelt: ' + str(result.get('error')))
        
except Exception as e:
    print('❌ TextBelt SMS error: ' + str(e))
"
}

send_telegram_alert() {
    MESSAGE="$1"
    
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        python3 -c "
import requests

try:
    url = 'https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage'
    payload = {
        'chat_id': '$TELEGRAM_CHAT_ID',
        'text': '🚨 [StillMe Alert]\n$MESSAGE',
        'parse_mode': 'HTML'
    }
    
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        print('✅ Telegram notification sent: $MESSAGE')
    else:
        print('❌ Telegram notification failed: ' + str(response.status_code))
        
except Exception as e:
    print('❌ Telegram API error: ' + str(e))
"
    fi
}

send_discord_alert() {
    MESSAGE="$1"
    
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        python3 -c "
import requests

try:
    payload = {
        'content': '🚨 **StillMe Alert**\n$MESSAGE',
        'username': 'StillMe VPS',
        'avatar_url': 'https://example.com/stillme-avatar.png'
    }
    
    response = requests.post('$DISCORD_WEBHOOK_URL', json=payload, timeout=10)
    
    if response.status_code == 204:
        print('✅ Discord notification sent: $MESSAGE')
    else:
        print('❌ Discord notification failed: ' + str(response.status_code))
        
except Exception as e:
    print('❌ Discord webhook error: ' + str(e))
"
    fi
}

send_all_alerts() {
    TITLE="$1"
    MESSAGE="$2"
    SEVERITY="$3"
    
    echo "📢 Sending alerts: $TITLE"
    
    # Desktop App
    send_desktop_alert "$TITLE" "$MESSAGE" "$SEVERITY"
    
    # SMS
    send_sms_alert "$MESSAGE"
    
    # Telegram
    send_telegram_alert "$MESSAGE"
    
    # Discord
    send_discord_alert "$MESSAGE"
    
    echo "📊 Alert sending completed"
}

# --- Main Checks ---

echo "🔍 Starting StillMe Health Check..."

# Check Gateway
if ! curl -f -s "$GATEWAY_URL" > /dev/null; then
    send_all_alerts "StillMe Gateway Down" "The StillMe Gateway API at $GATEWAY_URL is not reachable." "high"
else
    echo "✅ Gateway is healthy"
fi

# Check AI Server
if ! curl -f -s "$AI_SERVER_URL" > /dev/null; then
    send_all_alerts "StillMe AI Server Down" "The StillMe AI Server at $AI_SERVER_URL is not reachable." "high"
else
    echo "✅ AI Server is healthy"
fi

# Check Docker containers status
if ! docker-compose -f /opt/stillme/docker-compose.yml ps | grep -q "Up"; then
    send_all_alerts "StillMe Docker Containers Down" "One or more Docker containers for StillMe are not running. Check logs on VPS." "high"
else
    echo "✅ Docker containers are running"
fi

# Basic system resource check (CPU, Memory, Disk)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//g')

if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    send_all_alerts "High CPU Usage on StillMe VPS" "CPU usage is currently at ${CPU_USAGE}%." "medium"
fi

if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    send_all_alerts "High Memory Usage on StillMe VPS" "Memory usage is currently at ${MEM_USAGE}%." "medium"
fi

if (( $DISK_USAGE > 90 )); then
    send_all_alerts "High Disk Usage on StillMe VPS" "Disk usage is currently at ${DISK_USAGE}%." "medium"
fi

echo "✅ Health check completed"
