#!/usr/bin/env python3
"""
🚀 STILLME AI - Phi-4-mini Setup Script
Mục tiêu: Kéo model Phi-4-mini chính thức từ Ollama và warmup
"""

import subprocess
import sys
import time
import requests
import json
from typing import Dict, Any, Optional

def check_ollama_version() -> tuple[bool, str]:
    """Kiểm tra phiên bản Ollama"""
    try:
        result = subprocess.run(['ollama', '-v'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_str = result.stdout.strip()
            print(f"   Raw version output: {version_str}")
            
            # Extract version number - handle "ollama version is 0.11.8"
            import re
            version_match = re.search(r'(\d+\.\d+\.\d+)', version_str)
            if version_match:
                version = version_match.group(1)
                major, minor, patch = map(int, version.split('.'))
                required_major, required_minor, required_patch = 0, 5, 13
                
                if (major > required_major or 
                    (major == required_major and minor > required_minor) or
                    (major == required_major and minor == required_minor and patch >= required_patch)):
                    return True, version
                else:
                    return False, version
            else:
                return False, "Version format not recognized"
        return False, "Unknown"
    except Exception as e:
        print(f"❌ Lỗi kiểm tra phiên bản Ollama: {e}")
        return False, "Error"

def pull_phi4_mini() -> bool:
    """Pull model phi4-mini từ Ollama"""
    print("🔄 Đang pull model phi4-mini...")
    try:
        # Sử dụng encoding utf-8 và tăng timeout
        result = subprocess.run(['ollama', 'pull', 'phi4-mini'], 
                              capture_output=True, text=True, 
                              encoding='utf-8', errors='ignore',
                              timeout=600)  # 10 phút timeout
        
        if result.returncode == 0:
            print("✅ Pull phi4-mini thành công!")
            return True
        else:
            print(f"❌ Lỗi pull phi4-mini: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Timeout khi pull phi4-mini (model có thể rất lớn)")
        print("   Vui lòng chạy thủ công: ollama pull phi4-mini")
        return False
    except Exception as e:
        print(f"❌ Lỗi pull phi4-mini: {e}")
        return False

def warmup_phi4_mini() -> bool:
    """Warmup model phi4-mini với 8 tokens"""
    print("🔥 Đang warmup phi4-mini...")
    
    warmup_payload = {
        "model": "phi4-mini",
        "prompt": "Hello, how are you?",
        "stream": False,
        "options": {
            "num_predict": 8,
            "temperature": 0.1,
            "keep_alive": "1h"
        }
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", 
                               json=warmup_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Warmup thành công! Response: {result.get('response', '')[:50]}...")
            return True
        else:
            print(f"❌ Lỗi warmup: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lỗi warmup phi4-mini: {e}")
        return False

def check_model_ready() -> Dict[str, Any]:
    """Kiểm tra model có sẵn sàng trong /api/ps"""
    try:
        response = requests.get("http://localhost:11434/api/ps", timeout=10)
        if response.status_code == 200:
            models = response.json()
            for model in models.get('models', []):
                if model.get('name', '').startswith('phi4-mini'):
                    return {
                        'ready': True,
                        'name': model.get('name'),
                        'size': model.get('size'),
                        'expires_at': model.get('expires_at')
                    }
            return {'ready': False, 'reason': 'Model not found in /api/ps'}
        else:
            return {'ready': False, 'reason': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'ready': False, 'reason': str(e)}

def get_model_info() -> Optional[Dict[str, Any]]:
    """Lấy thông tin chi tiết về model"""
    try:
        response = requests.post("http://localhost:11434/api/show", 
                               json={"name": "phi4-mini"}, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"⚠️ Không thể lấy model info: {e}")
        return None

def main():
    print("🚀 STILLME AI - Phi-4-mini Setup")
    print("=" * 50)
    
    # 1. Kiểm tra phiên bản Ollama
    print("1️⃣ Kiểm tra phiên bản Ollama...")
    version_ok, version = check_ollama_version()
    print(f"   Phiên bản Ollama: {version}")
    
    if not version_ok:
        print("⚠️ WARNING: Phi-4-mini requires Ollama ≥ 0.5.13")
        print("   Vui lòng nâng cấp Ollama trước khi tiếp tục!")
        return False
    else:
        print("✅ Phiên bản Ollama phù hợp!")
    
    # 2. Pull model
    print("\n2️⃣ Pull model phi4-mini...")
    if not pull_phi4_mini():
        return False
    
    # 3. Warmup model
    print("\n3️⃣ Warmup model phi4-mini...")
    if not warmup_phi4_mini():
        print("⚠️ Warmup thất bại, nhưng model đã được pull")
    
    # 4. Kiểm tra model ready
    print("\n4️⃣ Kiểm tra model ready...")
    model_status = check_model_ready()
    if model_status['ready']:
        print(f"✅ Model ready: {model_status['name']}")
        if model_status.get('size'):
            size_mb = model_status['size'] / (1024 * 1024)
            print(f"   Kích thước: {size_mb:.1f} MB")
    else:
        print(f"❌ Model chưa ready: {model_status['reason']}")
    
    # 5. Lấy thông tin model
    print("\n5️⃣ Thông tin model...")
    model_info = get_model_info()
    if model_info:
        print(f"   Model: {model_info.get('modelfile', 'N/A')[:100]}...")
        if model_info.get('size'):
            size_gb = model_info['size'] / (1024 * 1024 * 1024)
            print(f"   Dung lượng ước tính: {size_gb:.2f} GB")
            
            # Cảnh báo RAM/VRAM
            if size_gb > 8:
                print("⚠️ CẢNH BÁO: Model lớn (>8GB), cần RAM/VRAM đủ")
            elif size_gb > 4:
                print("⚠️ Lưu ý: Model trung bình (4-8GB), kiểm tra RAM/VRAM")
    
    print("\n" + "=" * 50)
    print("🎉 DONE P1 - Phi-4-mini Setup Complete!")
    print(f"   ✅ Ollama version: {version}")
    print(f"   ✅ Model ready: {model_status['ready']}")
    print(f"   ✅ Keep-alive: 1h")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
