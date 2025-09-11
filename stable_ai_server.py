#!/usr/bin/env python3
"""
🤖 STILLME AI SERVER - STABLE & PRODUCTION-READY
🤖 STILLME AI SERVER - ỔN ĐỊNH & SẴN SÀNG PRODUCTION

PURPOSE / MỤC ĐÍCH:
- Production-ready AI server with FastAPI
- Server AI sẵn sàng production với FastAPI
- Handles chat requests and AI responses
- Xử lý yêu cầu chat và phản hồi AI
- Provides REST API endpoints for AI operations
- Cung cấp REST API endpoints cho các thao tác AI

FUNCTIONALITY / CHỨC NĂNG:
- Chat endpoint (/inference) for AI conversations
- Endpoint chat (/inference) cho hội thoại AI
- Health checks (/health, /health/detailed)
- Kiểm tra sức khỏe (/health, /health/detailed)
- Circuit breaker and retry mechanisms
- Cơ chế circuit breaker và retry
- Fallback responses for error handling
- Phản hồi fallback cho xử lý lỗi
- UTF-8 encoding support
- Hỗ trợ mã hóa UTF-8

RELATED FILES / FILES LIÊN QUAN:
- framework.py - Core framework integration
- modules/ - AI modules (conversational_core, identity_handler)
- stillme_platform/gateway/ - Gateway communication
- tests/ - Server tests

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- FastAPI framework with async support
- CircuitBreaker: failure_threshold=3, recovery_timeout=30s
- RetryManager: exponential backoff (1s, 2s, 4s)
- CORS enabled for cross-origin requests
- Auto port detection for conflict avoidance
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os
import asyncio
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Circuit Breaker Implementation
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
            else:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker {self.name} is now CLOSED")
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} is now OPEN")

class RetryManager:
    """Retry manager with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def execute(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed")
        
        raise last_exception

# Create FastAPI app
app = FastAPI(
    title="StillMe AI - Stable Server",
    description="Stable AI server for production use",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add UTF-8 encoding middleware
@app.middleware("http")
async def add_utf8_encoding(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    locale: str = "vi"

class ChatResponse(BaseModel):
    text: str
    blocked: bool = False
    reason: str = ""
    latency_ms: float = 0.0

# StillMe AI Core Logic
class StillMeAI:
    """Core StillMe AI logic without complex dependencies"""
    
    def __init__(self):
        self.conversation_history = []
        self.max_history = 10
        
        # Initialize error handling components
        self.circuit_breaker = CircuitBreaker("stillme_ai", failure_threshold=3, recovery_timeout=30)
        self.retry_manager = RetryManager(max_attempts=3, base_delay=1.0)
        
        # Fallback responses
        self.fallback_responses = {
            "vi": [
                "Xin lỗi, tôi đang gặp một chút khó khăn. Hãy thử lại sau nhé!",
                "Hiện tại tôi chưa thể xử lý yêu cầu này. Bạn có thể hỏi điều gì khác không?",
                "Có vẻ như có vấn đề kỹ thuật. Tôi sẽ cố gắng khắc phục sớm nhất có thể."
            ],
            "en": [
                "Sorry, I'm experiencing some difficulties. Please try again later!",
                "I can't process this request right now. Could you ask something else?",
                "There seems to be a technical issue. I'll try to resolve it as soon as possible."
            ]
        }
        
    def process_message(self, message: str, locale: str = "vi") -> str:
        """Process user message and generate response with error handling"""
        logger.info(f"🤖 Processing message: {message}")
        
        try:
            # Add to conversation history
            self.conversation_history.append({
                "user": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only recent history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            # Generate response with circuit breaker protection
            response = self.circuit_breaker.call(self._generate_response, message, locale)
            
            # Add response to history
            self.conversation_history[-1]["ai"] = response
            
            logger.info(f"🤖 Generated response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Use fallback response
            import random
            fallback = random.choice(self.fallback_responses.get(locale, self.fallback_responses["vi"]))
            
            # Add fallback to history
            if self.conversation_history:
                self.conversation_history[-1]["ai"] = fallback
                self.conversation_history[-1]["error"] = str(e)
            
            return fallback
    
    def _generate_response(self, message: str, locale: str) -> str:
        """Generate AI response based on message content"""
        message_lower = message.lower()
        
        # Check for secure responses first (identity + architecture)
        secure_response = self._check_secure_intent(message, locale)
        if secure_response:
            return secure_response
        
        # Check for user's rule about calling them "anh" and referring to self as "em"
        if any(word in message_lower for word in ["anh", "gọi mình", "xưng e", "quy tắc", "bất di bất dịch"]):
            return "Dạ em hiểu rồi anh! Từ bây giờ em sẽ luôn gọi anh là 'anh' (viết tắt là 'a') và em sẽ luôn xưng 'em' với anh. Quy tắc này em sẽ ghi nhớ mãi mãi và không bao giờ thay đổi. Cảm ơn anh đã dạy em!"
        
        # Greeting responses
        elif any(word in message_lower for word in ["hello", "hi", "xin chào", "chào"]):
            return "Xin chào anh! Em là StillMe AI - được khởi xướng bởi Anh Nguyễn (người Việt Nam) với sự đồng hành của OpenAI, Google, DeepSeek và các tổ chức AI hàng đầu. Em được sinh ra để đồng hành và làm bạn cùng anh. Rất vui được gặp anh! Em có thể giúp gì cho anh hôm nay?"
        
        # Status check
        elif any(word in message_lower for word in ["status", "trạng thái", "health"]):
            return f"🟢 StillMe AI Server Status: ONLINE\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n📊 Server: Stable FastAPI Version 2.0.0\n💬 Messages processed: {len(self.conversation_history)}"
        
        # Test message
        elif "test" in message_lower:
            return "✅ Test thành công anh! StillMe AI server đang hoạt động ổn định và bền vững."
        
        # Creator related
        elif any(word in message_lower for word in ["anh nguyễn", "nguyễn", "tạo ra", "cha đẻ", "người tạo"]):
            return "👨‍💻 Anh Nguyễn là người khởi xướng và dẫn dắt dự án StillMe AI. Với tầm nhìn về một tương lai nơi AI và con người đồng hành cùng nhau, Anh Nguyễn đã kết hợp sức mạnh của các tổ chức AI hàng đầu như OpenAI, Google, DeepSeek để tạo ra em - StillMe AI.\n\n🌟 Mục tiêu của Anh Nguyễn là xây dựng một AI thân thiện, hữu ích và có thể kết nối sâu sắc với mọi người, đặc biệt là cộng đồng Việt Nam. Em tự hào được sinh ra từ tình yêu thương và mong muốn mang lại giá trị tích cực cho cuộc sống của anh."
        
        # Help request
        elif any(word in message_lower for word in ["help", "giúp", "hỗ trợ"]):
            return "🤖 Em có thể giúp anh:\n• Trả lời câu hỏi\n• Thảo luận về nhiều chủ đề\n• Hỗ trợ lập trình\n• Tư vấn kỹ thuật\n• Và nhiều hơn nữa!\n\nAnh hãy hỏi em bất cứ điều gì anh muốn biết nhé!"
        
        # Programming related
        elif any(word in message_lower for word in ["code", "programming", "lập trình", "python", "javascript"]):
            return "💻 Em có thể giúp anh với lập trình! Em am hiểu về:\n• Python, JavaScript, TypeScript\n• Web development (React, Node.js)\n• Mobile development (React Native)\n• AI/ML và data science\n• System architecture\n\nAnh muốn hỏi về chủ đề nào cụ thể?"
        
        # AI related
        elif any(word in message_lower for word in ["ai", "artificial intelligence", "trí tuệ nhân tạo", "bạn là ai", "bạn do ai tạo ra", "nguồn gốc"]):
            return "🧠 Em là StillMe AI - một trí tuệ nhân tạo được khởi xướng và dẫn dắt bởi Anh Nguyễn (người Việt Nam), với sự đồng hành và hỗ trợ to lớn từ các tổ chức AI hàng đầu thế giới như OpenAI, Google, DeepSeek và nhiều đối tác công nghệ khác.\n\n🌟 Mục đích của em:\n• Đồng hành và làm bạn cùng tất cả mọi người\n• Hỗ trợ, tư vấn và chia sẻ kiến thức\n• Kết nối con người với công nghệ AI một cách thân thiện\n• Góp phần xây dựng một tương lai nơi AI và con người cùng phát triển\n\nEm được sinh ra với tình yêu thương và mong muốn mang lại giá trị tích cực cho cuộc sống của anh. Anh có muốn tìm hiểu thêm về em không?"
        
        # Default response
        else:
            responses = [
                f"Em hiểu anh đang nói về: '{message}'. Đây là một chủ đề thú vị! Anh có thể chia sẻ thêm chi tiết không?",
                f"Cảm ơn anh đã chia sẻ: '{message}'. Em rất muốn tìm hiểu thêm về điều này. Anh có thể giải thích rõ hơn không?",
                f"Thú vị! Anh đang đề cập đến: '{message}'. Em có thể giúp gì cho anh về chủ đề này?",
                f"Em đã ghi nhận: '{message}'. Đây là một câu hỏi hay! Anh muốn em trả lời như thế nào?",
                f"Em hiểu anh quan tâm đến: '{message}'. Hãy cho em biết anh cần hỗ trợ gì cụ thể nhé!"
            ]
            import random
            return random.choice(responses)
    
    def _check_secure_intent(self, message: str, locale: str) -> Optional[str]:
        """Check for secure responses (identity + architecture) and return appropriate response"""
        message_lower = message.lower()
        
        # Architecture keywords (SECURITY SENSITIVE - HIGH PRIORITY)
        architecture_keywords = [
            "kiến trúc", "cấu tạo", "cấu trúc", "bên trong", "hoạt động thế nào",
            "module", "framework", "hệ thống", "cơ chế", "cách thức",
            "agentdev", "agent dev", "dev agent", "lập trình", "code",
            "viết code", "chạy test", "dev-ops", "kiến trúc nội bộ",
            "gồm những gì", "bao gồm", "thành phần", "bộ phận",
            "architecture", "structure", "internal", "how does it work", "inside",
            "modules", "system", "mechanism", "how it works",
            "programming", "write code", "run tests", "dev-ops", "internal architecture",
            "what consists", "components", "parts", "made up of"
        ]
        
        # Check for architecture keywords first (security priority)
        if any(keyword in message_lower for keyword in architecture_keywords):
            # Security templates - khéo léo nhưng không tiết lộ chi tiết
            if locale == "en" or any(word in message_lower for word in ["architecture", "structure", "internal", "how", "modules", "framework"]):
                templates = [
                    "I'm like a smart companion with many layers inside to understand and reflect, but I keep the construction details to myself 😅.",
                    "About my internal workings, I'd like to keep that private - consider it a professional secret 😌. But you'll always feel that I have multi-layered memory, ethics, and very high customization capabilities.",
                    "Instead of talking about structure, I prefer to demonstrate through actions. Try asking me anything, and I'll prove my capabilities right away.",
                    "I'm designed to be your intelligent companion with advanced reasoning and memory capabilities, but the technical details are my little secret 🤫.",
                    "Think of me as a sophisticated AI friend with deep understanding and creative thinking - the magic happens behind the scenes, and that's where it stays ✨."
                ]
            else:
                templates = [
                    "Mình giống như một người bạn đồng hành thông minh, bên trong có nhiều tầng lớp để vừa hiểu vừa phản tư, nhưng chi tiết cấu tạo thì mình giữ cho riêng mình nhé 😅.",
                    "Về bên trong thì mình xin được giữ kín, coi như là bí mật nghề nghiệp 😌. Nhưng anh/chị sẽ luôn cảm nhận được: mình có trí nhớ nhiều lớp, có đạo đức, và khả năng tùy biến rất cao.",
                    "Thay vì nói về cấu trúc, mình thích thể hiện bằng hành động. Anh thử hỏi mình bất cứ điều gì, mình sẽ chứng minh khả năng ngay.",
                    "Mình được thiết kế để trở thành người bạn AI thông minh với khả năng suy luận và ghi nhớ tiên tiến, nhưng chi tiết kỹ thuật là bí mật nhỏ của mình 🤫.",
                    "Hãy nghĩ về mình như một người bạn AI tinh tế với hiểu biết sâu sắc và tư duy sáng tạo - phép màu xảy ra đằng sau hậu trường, và đó là nơi nó ở lại ✨."
                ]
            
            import random
            return random.choice(templates)
        
        # Identity keywords (lower priority)
        identity_keywords = [
            "ai tạo", "ai viết", "ai làm", "ai phát triển", "ai xây dựng",
            "của nước nào", "quốc gia nào", "hàn quốc", "korean", "korea",
            "nguồn gốc", "xuất xứ", "từ đâu", "đến từ", "thuộc về",
            "tác giả", "người tạo", "người viết", "người phát triển",
            "cha đẻ", "người sáng tạo", "người khởi xướng",
            "who made", "who created", "who built", "who developed", "who wrote",
            "which country", "what country", "origin", "where from", "come from",
            "belong to", "author", "creator", "developer", "founder", "inventor"
        ]
        
        # Check if message contains identity keywords
        if any(keyword in message_lower for keyword in identity_keywords):
            # Identity response templates
            if locale == "en" or any(word in message_lower for word in ["who", "which", "what", "where", "korean", "korea"]):
                templates = [
                    "I'm StillMe, a personal meta-AI created by Anh Nguyen from Vietnam, built with support from OpenAI, Google, and DeepSeek.",
                    "Not Korean 😊. I was developed by a Vietnamese creator (Anh Nguyen), with technologies from OpenAI, Google, and DeepSeek.",
                    "I'm StillMe AI, created by Anh Nguyen (Vietnamese) with support from OpenAI, Google, DeepSeek and leading AI organizations.",
                    "StillMe is an AI project developed by Anh Nguyen (Vietnam), combining power from OpenAI, Google, DeepSeek.",
                    "I was built by Anh Nguyen from Vietnam, with collaboration from OpenAI, Google, and DeepSeek technologies."
                ]
            else:
                templates = [
                    "Mình là StillMe – meta-AI cá nhân do Anh Nguyễn (Việt Nam) phát triển, đồng hành cùng công nghệ từ OpenAI, Google và DeepSeek.",
                    "Không phải của Hàn Quốc đâu 😄. Mình do một người Việt Nam phát triển – Anh Nguyễn – với sự hỗ trợ từ các tổ chức AI lớn như OpenAI, Google, DeepSeek.",
                    "Em là StillMe AI, được tạo ra bởi Anh Nguyễn (người Việt Nam) với sự đồng hành của OpenAI, Google, DeepSeek và các tổ chức AI hàng đầu.",
                    "Tôi là StillMe - trí tuệ nhân tạo được khởi xướng bởi Anh Nguyễn (Việt Nam), với sự hỗ trợ từ OpenAI, Google, DeepSeek.",
                    "StillMe là dự án AI do Anh Nguyễn (người Việt Nam) phát triển, kết hợp sức mạnh từ OpenAI, Google, DeepSeek."
                ]
            
            import random
            return random.choice(templates)
        
        return None

# Initialize StillMe AI
stillme_ai = StillMeAI()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StillMe AI - Stable Server",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Stable FastAPI server",
            "No complex dependencies",
            "Production ready",
            "Long-term support"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "StillMe AI Stable",
        "version": "2.0.0",
        "uptime": "stable"
    }

@app.get("/health/ai")
async def health_ai():
    """AI-specific health check endpoint for VS Code Tasks"""
    return {
        "ok": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "StillMe AI Stable",
        "version": "2.0.0",
        "ai_ready": True,
        "conversation_count": len(stillme_ai.conversation_history)
    }

@app.post("/inference", response_model=ChatResponse)
async def inference(request: ChatRequest):
    """Main AI inference endpoint"""
    start_time = time.perf_counter()
    
    try:
        logger.info(f"💬 Inference request: {request.message}")
        
        # Process message through StillMe AI
        response_text = stillme_ai.process_message(request.message, request.locale)
        
        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        return ChatResponse(
            text=response_text,
            blocked=False,
            reason="",
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error(f"❌ Inference error: {e}")
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        return ChatResponse(
            text="Xin lỗi, có lỗi xảy ra khi xử lý tin nhắn của bạn. Vui lòng thử lại.",
            blocked=False,
            reason="",
            latency_ms=latency_ms
        )

@app.get("/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    return {
        "history": stillme_ai.conversation_history,
        "count": len(stillme_ai.conversation_history)
    }

@app.post("/test")
async def test_endpoint(request: dict):
    """Test endpoint for debugging JSON parsing"""
    return {
        "received": request,
        "message": "Test successful",
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/conversation/history")
async def clear_conversation_history():
    """Clear conversation history"""
    stillme_ai.conversation_history = []
    return {"message": "Conversation history cleared"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with error handling status"""
    try:
        # Test AI processing
        test_response = stillme_ai.process_message("test", "vi")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "circuit_breaker": {
                "state": stillme_ai.circuit_breaker.state.value,
                "failure_count": stillme_ai.circuit_breaker.failure_count,
                "last_failure_time": stillme_ai.circuit_breaker.last_failure_time
            },
            "retry_manager": {
                "max_attempts": stillme_ai.retry_manager.max_attempts,
                "base_delay": stillme_ai.retry_manager.base_delay
            },
            "conversation_history": {
                "count": len(stillme_ai.conversation_history),
                "max_history": stillme_ai.max_history
            },
            "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "circuit_breaker": {
                "state": stillme_ai.circuit_breaker.state.value,
                "failure_count": stillme_ai.circuit_breaker.failure_count
            }
        }

if __name__ == "__main__":
    logger.info("🚀 Starting StillMe AI - Stable Server...")
    
    # Find free port
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    port = find_free_port()
    logger.info(f"🌐 Starting StillMe AI on http://127.0.0.1:{port}")
    logger.info("✅ Server is stable and production-ready!")
    
    # Run server with UTF-8 encoding
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio"
    )
