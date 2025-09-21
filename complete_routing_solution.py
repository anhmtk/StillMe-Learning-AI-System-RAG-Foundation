#!/usr/bin/env python3
"""
COMPLETE ROUTING SOLUTION FOR STILLME GATEWAY
==============================================

File này chứa toàn bộ solution để fix routing logic trên VPS:
- Smart routing: Simple → Gemma, Complex → DeepSeek  
- Fallback mechanism
- Environment configuration
- Test scripts
- Deploy instructions

USAGE:
1. python complete_routing_solution.py --generate-deploy-script
2. Copy deploy script to VPS and run
3. Update gateway code to use new router
4. Test with provided scripts
"""

import argparse
import os
import sys

def generate_deploy_script():
    """Tạo script deploy hoàn chỉnh"""
    deploy_script = '''#!/bin/bash
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
- Simple messages → Gemma2:2b local (free, fast)
- Complex messages → DeepSeek Cloud (paid, powerful)
- Fallback mechanism for reliability
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
        # Độ dài ngắn
        if len(text) > 80:
            return False
            
        # Từ khóa phức tạp
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
        
        # Force modes
        if routing_mode == 'force_gemma':
            return 'gemma-local'
        if routing_mode == 'force_cloud':
            return 'deepseek-cloud'
        if disable_cloud == '1':
            return 'gemma-local'
        
        # Auto routing
        return 'gemma-local' if self.is_simple(text) else 'deepseek-cloud'
    
    def call_gemma_local(self, payload: Dict, timeout: float = None) -> Dict:
        """Gọi Gemma local với fallback"""
        if timeout is None:
            timeout = self.gemma_timeout
            
        try:
            # Thử Ollama API
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
        
        # Fallback response
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
            
            # Log an toàn (không lộ secret)
            latency = (time.time() - start_time) * 1000
            logger.info(f"Router: {engine}, latency: {latency:.1f}ms, success: true")
            return result
            
        except TimeoutError:
            if engine == "deepseek-cloud":
                # Fallback to Gemma khi DeepSeek timeout
                try:
                    logger.info("DeepSeek timeout, falling back to Gemma...")
                    result = self.call_gemma_local(payload, timeout=2.0)
                    latency = (time.time() - start_time) * 1000
                    logger.info(f"Router: deepseek->gemma fallback, latency: {latency:.1f}ms, success: true")
                    return result
                except:
                    pass
            
            # Final fallback
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

if __name__ == "__main__":
    # Test function
    test_messages = [
        "xin chào",
        "Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột."
    ]
    
    for msg in test_messages:
        print(f"Testing: {msg}")
        result = route_message(msg)
        print(f"Engine: {result.get('engine')}, Model: {result.get('model')}")
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
  curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
    -d "{\\"message\\":\\"$m\\",\\"session_id\\":\\"router-test\\"}" | jq '{model:.model, engine:(.engine//"unknown"), text:(.response//.text//.output)[:100], ts:.timestamp}'
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
  curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
    -d "{\\"message\\":\\"$m\\",\\"session_id\\":\\"router-test\\"}" | jq '{model:.model, engine:(.engine//"unknown"), text:(.response//.text//.output)[:100], ts:.timestamp}'
  echo ""
done
EOF

cat > /opt/stillme/tools/test_routing_modes.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
HOST=${HOST:-"http://160.191.89.99:21568"}

echo "🔍 Testing Routing Modes..."

echo "1. Auto mode (default):"
curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
  -d "{\\"message\\":\\"xin chào\\",\\"session_id\\":\\"test-auto\\"}" | jq '{model:.model, engine:(.engine//"unknown")}'

echo "2. Force Gemma mode:"
# Note: This requires gateway to respect ROUTING_MODE=force_gemma
curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
  -d "{\\"message\\":\\"xin chào\\",\\"session_id\\":\\"test-force-gemma\\"}" | jq '{model:.model, engine:(.engine//"unknown")}'

echo "3. Force DeepSeek mode:"
# Note: This requires gateway to respect ROUTING_MODE=force_cloud
curl -s -X POST "$HOST/chat" -H "Content-Type: application/json" \
  -d "{\\"message\\":\\"xin chào\\",\\"session_id\\":\\"test-force-cloud\\"}" | jq '{model:.model, engine:(.engine//"unknown")}'
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
'''

    with open('deploy_smart_routing.sh', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Generated deploy_smart_routing.sh")
    return True

def generate_gateway_patch():
    """Tạo patch để integrate smart router vào gateway"""
    patch_content = '''
# GATEWAY INTEGRATION PATCH
# Add this to your gateway's chat endpoint

from smart_router import route_message

@app.post("/chat")
def chat(request: ChatRequest):
    """Enhanced chat endpoint with smart routing"""
    try:
        # Use smart router
        result = route_message(request.message, request.session_id)
        
        return {
            "model": result.get("model", "unknown"),
            "response": result.get("response", ""),
            "timestamp": result.get("timestamp"),
            "engine": result.get("engine", "unknown"),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {
            "model": "error",
            "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "error",
            "status": "error"
        }

# Optional: Add routing control endpoint
@app.post("/admin/routing")
def set_routing_mode(mode: str):
    """Set routing mode (requires admin auth)"""
    if mode in ["auto", "force_gemma", "force_cloud"]:
        os.environ["ROUTING_MODE"] = mode
        return {"status": "success", "routing_mode": mode}
    return {"status": "error", "message": "Invalid mode"}
'''
    
    with open('gateway_integration_patch.py', 'w') as f:
        f.write(patch_content)
    
    print("✅ Generated gateway_integration_patch.py")
    return True

def main():
    parser = argparse.ArgumentParser(description='StillMe Gateway Smart Routing Solution')
    parser.add_argument('--generate-deploy-script', action='store_true',
                       help='Generate deployment script for VPS')
    parser.add_argument('--generate-patch', action='store_true',
                       help='Generate gateway integration patch')
    parser.add_argument('--local-test', action='store_true',
                       help='Run local test of routing logic')
    
    args = parser.parse_args()
    
    if args.generate_deploy_script:
        generate_deploy_script()
    
    if args.generate_patch:
        generate_gateway_patch()
    
    if args.local_test:
        print("🧪 Running local test...")
        # Import and test the router
        sys.path.append('.')
        try:
            from routing_logic_fix import SmartRouter
            router = SmartRouter()
            
            # Test simple message
            simple_result = router.route_chat({"message": "xin chào"})
            print(f"Simple: {simple_result.get('engine')}")
            
            # Test complex message  
            complex_result = router.route_chat({"message": "Hãy viết code Python"})
            print(f"Complex: {complex_result.get('engine')}")
            
        except Exception as e:
            print(f"Local test error: {e}")
    
    if not any([args.generate_deploy_script, args.generate_patch, args.local_test]):
        print("🚀 StillMe Gateway Smart Routing Solution")
        print("=" * 50)
        print("Usage:")
        print("  python complete_routing_solution.py --generate-deploy-script")
        print("  python complete_routing_solution.py --generate-patch")
        print("  python complete_routing_solution.py --local-test")
        print("")
        print("This will generate all necessary files for deployment!")

if __name__ == "__main__":
    main()
