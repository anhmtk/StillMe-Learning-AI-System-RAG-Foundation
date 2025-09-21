#!/bin/bash
set -euo pipefail

echo "🚀 STILLME GATEWAY SMART ROUTING DEPLOYMENT"
echo "=========================================="

# Backup current system
echo "📦 Backing up current gateway..."
BACKUP_DIR="/opt/stillme.backup.$(date +%Y%m%d_%H%M%S)"
cp -r /opt/stillme "$BACKUP_DIR"
echo "✅ Backup saved to: $BACKUP_DIR"

# Create directories
echo "📁 Creating directories..."
mkdir -p /opt/stillme/tools
mkdir -p /opt/stillme/smart_router

# Deploy Smart Router
echo "🔧 Deploying Smart Router..."
cat > /opt/stillme/smart_router.py << 'EOF'
#!/usr/bin/env python3
"""
Smart Routing Logic for StillMe Gateway
"""
import re
import time
import requests
import os
import logging
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartRouter:
    def __init__(self):
        self.gemma_timeout = float(os.getenv('GEMMA_TIMEOUT', '2.5'))
        self.deepseek_timeout = float(os.getenv('DEEPSEEK_TIMEOUT', '10.0'))
        self.deepseek_retry = int(os.getenv('DEEPSEEK_RETRY', '1'))
        self.deepseek_backoff = float(os.getenv('DEEPSEEK_BACKOFF', '1.5'))
        
    def is_simple(self, text: str) -> bool:
        """Heuristic để phân loại câu đơn giản"""
        if len(text) > 80:
            return False
            
        complex_keywords = [
            'code', 'python', 'dart', 'kotlin', 'java', 'javascript',
            'rewrite', 'optimize', 'algorithm', 'bug', 'stack', 'error',
            'complex', 'advanced', 'detailed', 'explain', 'analyze',
            'implement', 'design', 'architecture', 'database', 'api',
            'framework', 'library', 'function', 'class', 'method',
            'debug', 'refactor', 'performance', 'security', 'testing'
        ]
        
        text_lower = text.lower()
        for keyword in complex_keywords:
            if keyword in text_lower:
                return False
        return True
    
    def select_engine(self, text: str, flags: Dict[str, Any]) -> str:
        """Chọn engine dựa trên text và flags"""
        routing_mode = flags.get('ROUTING_MODE', 'auto')
        disable_cloud = flags.get('DISABLE_CLOUD', '0')
        
        if routing_mode == 'force_gemma':
            return 'gemma-local'
        if routing_mode == 'force_cloud':
            return 'deepseek-cloud'
        if disable_cloud == '1':
            return 'gemma-local'
        
        return 'gemma-local' if self.is_simple(text) else 'deepseek-cloud'
    
    def call_gemma_local(self, payload: Dict, timeout: float = None) -> Dict:
        """Gọi Gemma local với fallback"""
        if timeout is None:
            timeout = self.gemma_timeout
            
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma2:2b",
                    "prompt": payload["message"],
                    "stream": False
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": "gemma2:2b",
                    "response": data.get("response", ""),
                    "timestamp": time.time(),
                    "engine": "gemma-local"
                }
        except Exception as e:
            logger.error(f"Gemma local error: {str(e)[:100]}")
        
        return {
            "model": "gemma2:2b-fallback",
            "response": f"Xin chào! Tôi là StillMe AI. Bạn hỏi: '{payload['message']}'. Hiện tại hệ thống đang bận, vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "gemma-fallback"
        }
    
    def call_deepseek(self, payload: Dict, timeout: float = None, retry: int = None, backoff: float = None) -> Dict:
        """Gọi DeepSeek với retry và backoff"""
        if timeout is None:
            timeout = self.deepseek_timeout
        if retry is None:
            retry = self.deepseek_retry
        if backoff is None:
            backoff = self.deepseek_backoff
            
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found")
        
        for attempt in range(retry + 1):
            try:
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": payload["message"]}],
                        "max_tokens": 1000,
                        "temperature": 0.7
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "model": "deepseek-chat",
                        "response": data["choices"][0]["message"]["content"],
                        "timestamp": time.time(),
                        "engine": "deepseek-cloud"
                    }
                else:
                    logger.error(f"DeepSeek API error: {response.status_code}")
                    
            except Exception as e:
                if attempt < retry:
                    time.sleep(backoff)
                    continue
                logger.error(f"DeepSeek error: {str(e)[:100]}")
        
        raise TimeoutError("DeepSeek timeout after retries")
    
    def route_chat(self, payload: Dict, flags: Dict[str, Any] = None) -> Dict:
        """Main routing function với fallback"""
        if flags is None:
            flags = {}
            
        text = payload.get("message", "")
        engine = self.select_engine(text, flags)
        start_time = time.time()
        
        try:
            if engine == "gemma-local":
                result = self.call_gemma_local(payload)
            else:
                result = self.call_deepseek(payload)
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"Router: {engine}, latency: {latency:.1f}ms, success: true")
            return result
            
        except TimeoutError:
            if engine == "deepseek-cloud":
                try:
                    logger.info("DeepSeek timeout, falling back to Gemma...")
                    result = self.call_gemma_local(payload, timeout=2.0)
                    latency = (time.time() - start_time) * 1000
                    logger.info(f"Router: deepseek->gemma fallback, latency: {latency:.1f}ms, success: true")
                    return result
                except:
                    pass
            
            latency = (time.time() - start_time) * 1000
            logger.error(f"Router: {engine}, latency: {latency:.1f}ms, success: false")
            return {
                "model": "fallback",
                "response": "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau.",
                "timestamp": time.time(),
                "engine": "fallback",
                "error": "timeout"
            }
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"Router: {engine}, latency: {latency:.1f}ms, success: false, error: {str(e)[:50]}")
            return {
                "model": "error",
                "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
                "timestamp": time.time(),
                "engine": "error",
                "error": str(e)[:100]
            }

# Global router instance
smart_router = SmartRouter()

def route_message(message: str, session_id: str = None) -> Dict:
    """Main function để route message"""
    payload = {"message": message, "session_id": session_id}
    flags = {
        "ROUTING_MODE": os.getenv("ROUTING_MODE", "auto"),
        "DISABLE_CLOUD": os.getenv("DISABLE_CLOUD", "0")
    }
    return smart_router.route_chat(payload, flags)
EOF

# Update environment variables
echo "🔧 Updating environment variables..."
if ! grep -q "ROUTING_MODE" /opt/stillme/.env; then
    echo "ROUTING_MODE=auto" >> /opt/stillme/.env
    echo "✅ Added ROUTING_MODE=auto"
fi
if ! grep -q "DISABLE_CLOUD" /opt/stillme/.env; then
    echo "DISABLE_CLOUD=0" >> /opt/stillme/.env
    echo "✅ Added DISABLE_CLOUD=0"
fi
if ! grep -q "GEMMA_TIMEOUT" /opt/stillme/.env; then
    echo "GEMMA_TIMEOUT=2.5" >> /opt/stillme/.env
    echo "✅ Added GEMMA_TIMEOUT=2.5"
fi
if ! grep -q "DEEPSEEK_TIMEOUT" /opt/stillme/.env; then
    echo "DEEPSEEK_TIMEOUT=10.0" >> /opt/stillme/.env
    echo "✅ Added DEEPSEEK_TIMEOUT=10.0"
fi
if ! grep -q "DEEPSEEK_RETRY" /opt/stillme/.env; then
    echo "DEEPSEEK_RETRY=1" >> /opt/stillme/.env
    echo "✅ Added DEEPSEEK_RETRY=1"
fi
if ! grep -q "DEEPSEEK_BACKOFF" /opt/stillme/.env; then
    echo "DEEPSEEK_BACKOFF=1.5" >> /opt/stillme/.env
    echo "✅ Added DEEPSEEK_BACKOFF=1.5"
fi

# Deploy test scripts
echo "📝 Deploying test scripts..."
cat > /opt/stillme/tools/test_vps_gateway_simple.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-"http://160.191.89.99:21568"}
echo "🔍 Testing Simple Messages (should use Gemma)..."
msg_list=("xin chào" "2+2=?" "hello" "ping" "chào buổi sáng")
for m in "${msg_list[@]}"; do
  echo "==> SEND: $m"
  curl -s -X POST "$HOST/chat" -H "Content-Type: application/json"     -d "{\"message\":\"$m\",\"session_id\":\"router-test\"}" | jq '{model:.model, engine:(.engine//"unknown"), text:(.response//.text//.output)[:100], ts:.timestamp}'
  echo ""
done
EOF

cat > /opt/stillme/tools/test_vps_gateway_complex.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-"http://160.191.89.99:21568"}
echo "🔍 Testing Complex Messages (should use DeepSeek)..."
msg_list=(
  "Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột."
  "Giải thích thuật toán quicksort và implement bằng Python"
  "Phân tích ưu nhược điểm của microservices architecture"
)
for m in "${msg_list[@]}"; do
  echo "==> SEND: $m"
  curl -s -X POST "$HOST/chat" -H "Content-Type: application/json"     -d "{\"message\":\"$m\",\"session_id\":\"router-test\"}" | jq '{model:.model, engine:(.engine//"unknown"), text:(.response//.text//.output)[:100], ts:.timestamp}'
  echo ""
done
EOF

chmod +x /opt/stillme/tools/test_vps_gateway_*.sh

echo ""
echo "✅ SMART ROUTING DEPLOYMENT COMPLETED!"
echo "====================================="
echo ""
echo "📋 NEXT STEPS:"
echo "1. Update your gateway code to use /opt/stillme/smart_router.py"
echo "2. Restart gateway service: sudo systemctl restart stillme-gateway"
echo "3. Test with scripts:"
echo "   - HOST=http://160.191.89.99:21568 bash /opt/stillme/tools/test_vps_gateway_simple.sh"
echo "   - HOST=http://160.191.89.99:21568 bash /opt/stillme/tools/test_vps_gateway_complex.sh"
echo ""
echo "🔧 ROUTING CONTROLS:"
echo "- ROUTING_MODE=auto|force_gemma|force_cloud"
echo "- DISABLE_CLOUD=0|1"
echo "- GEMMA_TIMEOUT=2.5 (seconds)"
echo "- DEEPSEEK_TIMEOUT=10.0 (seconds)"
echo ""
echo "📊 EXPECTED RESULTS:"
echo "- Simple messages → gemma2:2b (local, fast)"
echo "- Complex messages → deepseek-chat (cloud, powerful)"
echo "- Timeout fallback → gemma2:2b-fallback"
echo ""
echo "🎯 SUCCESS CRITERIA:"
echo "- Simple: 90%+ success rate, <3s latency"
echo "- Complex: 80%+ success rate, <15s latency"
echo "- Fallback: Working gracefully on timeout"
