#!/usr/bin/env python3
"""
Gateway patch với smart routing logic
File này sẽ thay thế logic routing hiện tại trên VPS
"""
import re
import time
import requests
import os
from typing import Dict, Any, Optional

class SmartRouter:
    def __init__(self):
        self.gemma_timeout = float(os.getenv('GEMMA_TIMEOUT', '2.5'))
        self.deepseek_timeout = float(os.getenv('DEEPSEEK_TIMEOUT', '10.0'))
        self.deepseek_retry = int(os.getenv('DEEPSEEK_RETRY', '1'))
        self.deepseek_backoff = float(os.getenv('DEEPSEEK_BACKOFF', '1.5'))
        
    def is_simple(self, text: str) -> bool:
        """Heuristic để phân loại câu đơn giản"""
        if len(text) <= 80:
            complex_keywords = [
                'code', 'python', 'dart', 'kotlin', 'java', 'javascript',
                'rewrite', 'optimize', 'algorithm', 'bug', 'stack', 'error',
                'complex', 'advanced', 'detailed', 'explain', 'analyze',
                'implement', 'design', 'architecture', 'database', 'api',
                'framework', 'library', 'function', 'class', 'method'
            ]
            
            text_lower = text.lower()
            for keyword in complex_keywords:
                if keyword in text_lower:
                    return False
            return True
        return False
    
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
        """Gọi Gemma local"""
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
            print(f"Gemma local error: {str(e)[:100]}")
        
        # Fallback response
        return {
            "model": "gemma2:2b-fallback",
            "response": f"Xin chào! Tôi là StillMe AI. Bạn hỏi: '{payload['message']}'. Hiện tại hệ thống đang bận, vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "gemma-fallback"
        }
    
    def call_deepseek(self, payload: Dict, timeout: float = None, retry: int = None, backoff: float = None) -> Dict:
        """Gọi DeepSeek với retry"""
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
                    print(f"DeepSeek API error: {response.status_code}")
                    
            except Exception as e:
                if attempt < retry:
                    time.sleep(backoff)
                    continue
                print(f"DeepSeek error: {str(e)[:100]}")
        
        raise TimeoutError("DeepSeek timeout after retries")
    
    def route_chat(self, payload: Dict, flags: Dict[str, Any] = None) -> Dict:
        """Main routing function"""
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
            print(f"Router: {engine}, latency: {latency:.1f}ms, success: true")
            return result
            
        except TimeoutError:
            if engine == "deepseek-cloud":
                try:
                    print("DeepSeek timeout, falling back to Gemma...")
                    result = self.call_gemma_local(payload, timeout=2.0)
                    latency = (time.time() - start_time) * 1000
                    print(f"Router: deepseek->gemma fallback, latency: {latency:.1f}ms, success: true")
                    return result
                except:
                    pass
            
            latency = (time.time() - start_time) * 1000
            print(f"Router: {engine}, latency: {latency:.1f}ms, success: false")
            return {
                "model": "fallback",
                "response": "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau.",
                "timestamp": time.time(),
                "engine": "fallback",
                "error": "timeout"
            }
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            print(f"Router: {engine}, latency: {latency:.1f}ms, success: false, error: {str(e)[:50]}")
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
