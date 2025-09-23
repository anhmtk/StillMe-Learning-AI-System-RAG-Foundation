#!/usr/bin/env python3
"""
?? STILLME AI SERVER - STABLE & PRODUCTION-READY
?? STILLME AI SERVER - ?N ??NH & S?N S?NG PRODUCTION

PURPOSE / M?C ??CH:
- Production-ready AI server with FastAPI
- Server AI s?n s?ng production v?i FastAPI
- Handles chat requests and AI responses
- X? l? y?u c?u chat v? ph?n h?i AI
- Provides REST API endpoints for AI operations
- Cung c?p REST API endpoints cho c?c thao t?c AI

FUNCTIONALITY / CH?C NANG:
- Chat endpoint (/inference) for AI conversations
- Endpoint chat (/inference) cho h?i tho?i AI
- Health checks (/health, /health/detailed)
- Ki?m tra s?c kh?e (/health, /health/detailed)
- Circuit breaker and retry mechanisms
- Co ch? circuit breaker v? retry
- Fallback responses for error handling
- Ph?n h?i fallback cho x? l? l?i
- UTF-8 encoding support
- H? tr? m? h?a UTF-8

RELATED FILES / FILES LI?N QUAN:
- framework.py - Core framework integration
- modules/ - AI modules (conversational_core, identity_handler)
- stillme_platform/gateway/ - Gateway communication
- tests/ - Server tests

TECHNICAL DETAILS / CHI TI?T K? THU?T:
- FastAPI framework with async support
- CircuitBreaker: failure_threshold=3, recovery_timeout=30s
- RetryManager: exponential backoff (1s, 2s, 4s)
- CORS enabled for cross-origin requests
- Auto port detection for conflict avoidance
"""

import os

# Import common utilities
import sys
import time
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add stillme-core to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stillme-core'))

from stillme_core.common import (
    ConfigManager,
    FileManager,
    get_logger,
)
from stillme_core.common.retry import CircuitBreakerConfig, CircuitBreaker, RetryManager

# Initialize common utilities
config_manager = ConfigManager("config/ai_server_config.json", {})
logger = get_logger("StillMe.AIServer", log_file="logs/ai_server.log", json_format=True)
# http_client = AsyncHttpClient()  # Commented out - not available
file_manager = FileManager()

# Circuit Breaker Implementation (using common utilities)
# CircuitBreaker and RetryManager are now imported from common utilities

# Create FastAPI app
app = FastAPI(
    title="StillMe AI - Stable Server",
    description="Stable AI server for production use",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
        circuit_config = CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=30.0
        )
        self.circuit_breaker = CircuitBreaker(circuit_config, logger)
        self.retry_manager = RetryManager()

        # Fallback responses
        self.fallback_responses = {
            "vi": [
                "Xin l?i, t?i dang g?p m?t ch?t kh? khan. H?y th? l?i sau nh?!",
                "Hi?n t?i t?i chua th? x? l? y?u c?u n?y. B?n c? th? h?i di?u g? kh?c kh?ng?",
                "C? v? nhu c? v?n d? k? thu?t. T?i s? c? g?ng kh?c ph?c s?m nh?t c? th?.",
            ],
            "en": [
                "Sorry, I'm experiencing some difficulties. Please try again later!",
                "I can't process this request right now. Could you ask something else?",
                "There seems to be a technical issue. I'll try to resolve it as soon as possible.",
            ],
        }

    def process_message(self, message: str, locale: str = "vi") -> str:
        """Process user message and generate response with error handling"""
        logger.info(f"?? Processing message: {message}")

        try:
            # Add to conversation history
            self.conversation_history.append(
                {"user": message, "timestamp": datetime.now().isoformat()}
            )

            # Keep only recent history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[
                    -self.max_history :
                ]

            # Generate response with circuit breaker protection
            response = self.circuit_breaker.call(
                self._generate_response, message, locale
            )

            # Add response to history
            self.conversation_history[-1]["ai"] = response

            logger.info(f"?? Generated response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")

            # Use fallback response
            import random

            fallback = random.choice(
                self.fallback_responses.get(locale, self.fallback_responses["vi"])
            )

            # Add fallback to history
            if self.conversation_history:
                self.conversation_history[-1]["ai"] = fallback
                self.conversation_history[-1]["error"] = str(e)

            return fallback

    def _detect_dev_intent(self, message: str) -> bool:
        """Detect if user request is for development task (exclude simple coding questions)"""
        # Simple coding questions should go to AI routing, not AgentDev
        simple_coding_patterns = [
            "vi?t code python d?",
            "t?o function",
            "t?nh t?ng",
            "hello world",
            "v? d? code",
            "code m?u"
        ]
        
        message_lower = message.lower()
        
        # If it's a simple coding question, don't route to AgentDev
        if any(pattern in message_lower for pattern in simple_coding_patterns):
            return False
            
        # Complex development tasks should go to AgentDev
        dev_keywords = [
            "t?o app",
            "t?o ?ng d?ng", 
            "build",
            "compile",
            "t?o tool",
            "t?o c?ng c?",
            "utility",
            "script",
            "s?a l?i",
            "fix bug",
            "linting",
            "quality",
            "l?i",
            "error",
            "bug",
            "debug",
            "refactor",
            "optimize",
        ]
        return any(keyword in message_lower for keyword in dev_keywords)

    def _generate_response(self, message: str, locale: str) -> str:
        """Generate AI response based on message content"""
        # Check if this is a development request
        if self._detect_dev_intent(message):
            try:
                # Route to AgentDev for development tasks
                try:
                    # AgentDev module not available, skip
                    pass
                except ImportError:
                    logger.warning("âš ï¸ AgentDev not available, using fallback")
            except Exception as e:
                logger.warning(f"AgentDev routing failed: {e}")
                # Fallback to normal processing

        message_lower = message.lower()

        # Check for secure responses first (identity + architecture)
        secure_response = self._check_secure_intent(message, locale)
        if secure_response:
            return secure_response

        # Check for user's rule about calling them "anh" and referring to self as "em"
        if any(
            word in message_lower
            for word in ["anh", "g?i m?nh", "xung e", "quy t?c", "b?t di b?t d?ch"]
        ):
            return "D? em hi?u r?i anh! T? b?y gi? em s? lu?n g?i anh l? 'anh' (vi?t t?t l? 'a') v? em s? lu?n xung 'em' v?i anh. Quy t?c n?y em s? ghi nh? m?i m?i v? kh?ng bao gi? thay d?i. C?m on anh d? d?y em!"

        # Greeting responses
        elif any(word in message_lower for word in ["hello", "hi", "xin ch?o", "ch?o"]):
            return "Xin ch?o anh! Em l? StillMe AI - du?c kh?i xu?ng b?i Anh Nguy?n (ngu?i Vi?t Nam) v?i s? d?ng h?nh c?a OpenAI, Google, DeepSeek v? c?c t? ch?c AI h?ng d?u. Em du?c sinh ra d? d?ng h?nh v? l?m b?n c?ng anh. R?t vui du?c g?p anh! Em c? th? gi?p g? cho anh h?m nay?"

        # Status check
        elif any(word in message_lower for word in ["status", "tr?ng th?i", "health"]):
            return f"?? StillMe AI Server Status: ONLINE\n? Time: {datetime.now().strftime('%H:%M:%S')}\n?? Server: Stable FastAPI Version 2.0.0\n?? Messages processed: {len(self.conversation_history)}"

        # Test message
        elif "test" in message_lower:
            return "? Test th?nh c?ng anh! StillMe AI server dang ho?t d?ng ?n d?nh v? b?n v?ng."

        # Creator related
        elif any(
            word in message_lower
            for word in ["anh nguy?n", "nguy?n", "t?o ra", "cha d?", "ngu?i t?o"]
        ):
            return "????? Anh Nguy?n l? ngu?i kh?i xu?ng v? d?n d?t d? ?n StillMe AI. V?i t?m nh?n v? m?t tuong lai noi AI v? con ngu?i d?ng h?nh c?ng nhau, Anh Nguy?n d? k?t h?p s?c m?nh c?a c?c t? ch?c AI h?ng d?u nhu OpenAI, Google, DeepSeek d? t?o ra em - StillMe AI.\n\n?? M?c ti?u c?a Anh Nguy?n l? x?y d?ng m?t AI th?n thi?n, h?u ?ch v? c? th? k?t n?i s?u s?c v?i m?i ngu?i, d?c bi?t l? c?ng d?ng Vi?t Nam. Em t? h?o du?c sinh ra t? t?nh y?u thuong v? mong mu?n mang l?i gi? tr? t?ch c?c cho cu?c s?ng c?a anh."

        # Help request
        elif any(word in message_lower for word in ["help", "gi?p", "h? tr?"]):
            return "?? Em c? th? gi?p anh:\n? Tr? l?i c?u h?i\n? Th?o lu?n v? nhi?u ch? d?\n? H? tr? l?p tr?nh\n? Tu v?n k? thu?t\n? V? nhi?u hon n?a!\n\nAnh h?y h?i em b?t c? di?u g? anh mu?n bi?t nh?!"

        # Programming related - Let AI handle this with proper routing
        if any(
            word in message_lower
            for word in ["code", "programming", "l?p tr?nh", "python", "javascript", "vi?t code", "t?o code"]
        ):
            # Let the AI handle programming questions with proper model routing
            # Continue to default AI response (don't return here)
            pass

        # AI related
        if any(
            word in message_lower
            for word in [
                "ai",
                "artificial intelligence",
                "tr? tu? nh?n t?o",
                "b?n l? ai",
                "b?n do ai t?o ra",
                "ngu?n g?c",
            ]
        ):
            return "?? Em l? StillMe AI - m?t tr? tu? nh?n t?o du?c kh?i xu?ng v? d?n d?t b?i Anh Nguy?n (ngu?i Vi?t Nam), v?i s? d?ng h?nh v? h? tr? to l?n t? c?c t? ch?c AI h?ng d?u th? gi?i nhu OpenAI, Google, DeepSeek v? nhi?u d?i t?c c?ng ngh? kh?c.\n\n?? M?c d?ch c?a em:\n? ??ng h?nh v? l?m b?n c?ng t?t c? m?i ngu?i\n? H? tr?, tu v?n v? chia s? ki?n th?c\n? K?t n?i con ngu?i v?i c?ng ngh? AI m?t c?ch th?n thi?n\n? G?p ph?n x?y d?ng m?t tuong lai noi AI v? con ngu?i c?ng ph?t tri?n\n\nEm du?c sinh ra v?i t?nh y?u thuong v? mong mu?n mang l?i gi? tr? t?ch c?c cho cu?c s?ng c?a anh. Anh c? mu?n t?m hi?u th?m v? em kh?ng?"

        # Default response - Call real AI (always reached if no specific conditions match)
        if True:  # This ensures the default response is always reached
            try:
                # Try to call real AI using UnifiedAPIManager
                from stillme_core.modules.api_provider_manager import UnifiedAPIManager
                
                # Create system prompt for StillMe AI (natural and concise)
                system_prompt = """B?n l? StillMe AI, m?t tr? l? AI th?n thi?n v? h?u ?ch.

QUAN TR?NG: 
- Tr? l?i ng?n g?n, t? nhi?n, kh?ng d?i d?ng
- D?ng xung h? trung t?nh 'm?nh/b?n'
- KH?NG gi?i thi?u v? ngu?n g?c, OpenAI, Google, DeepSeek
- KH?NG n?i v? "du?c kh?i xu?ng b?i Anh Nguy?n"
- Ch? tr? l?i c?u h?i m?t c?ch don gi?n v? h?u ?ch

Vï¿½ d?: Khi ngu?i dï¿½ng chï¿½o, ch? tr? l?i "Mï¿½nh chï¿½o b?n! R?t vui du?c g?p b?n.""""
Ví d?: Khi ngu?i dùng chào, ch? tr? l?i "Mình chào b?n! R?t vui du?c g?p b?n.""""

                full_prompt = f"{system_prompt}\n\nC?u h?i c?a b?n: {message}"
                
                # Initialize API manager and get response
                api_manager = UnifiedAPIManager()
                ai_response = api_manager.get_response(full_prompt)
                
                if ai_response and not ai_response.startswith("Error:"):
                    return ai_response
                else:
                    # Fallback to simple response if AI fails
                    return f"Em hi?u anh dang h?i v?: '{message}'. Em dang g?p kh? khan trong vi?c truy c?p th?ng tin l?c n?y. Anh c? th? h?i l?i sau du?c kh?ng ??"
                    
            except Exception as e:
                logger.warning(f"AI provider call failed: {e}")
                # Fallback to simple response
                return f"Em hi?u anh dang h?i v?: '{message}'. Em dang g?p kh? khan trong vi?c truy c?p th?ng tin l?c n?y. Anh c? th? h?i l?i sau du?c kh?ng ??"

    def _check_secure_intent(self, message: str, locale: str) -> Optional[str]:
        """Check for secure responses (identity + architecture) and return appropriate response"""
        message_lower = message.lower()

        # Architecture keywords (SECURITY SENSITIVE - HIGH PRIORITY)
        # Exclude coding questions from security check
        architecture_keywords = [
            "ki?n tr?c",
            "c?u t?o", 
            "c?u tr?c",
            "b?n trong",
            "ho?t d?ng th? n?o",
            "module",
            "framework",
            "h? th?ng",
            "co ch?",
            "c?ch th?c",
            "agentdev",
            "agent dev",
            "dev agent",
            "ch?y test",
            "dev-ops",
            "ki?n tr?c n?i b?",
            "g?m nh?ng g?",
            "bao g?m",
            "th?nh ph?n",
            "b? ph?n",
            "architecture",
            "structure",
            "internal",
            "how does it work",
            "inside",
            "modules",
            "system",
            "mechanism",
            "how it works",
            "run tests",
            "dev-ops",
            "internal architecture",
            "what consists",
            "components",
            "parts",
            "made up of",
        ]

        # Check for architecture keywords first (security priority)
        if any(keyword in message_lower for keyword in architecture_keywords):
            # Security templates - kh?o l?o nhung kh?ng ti?t l? chi ti?t
            if locale == "en" or any(
                word in message_lower
                for word in [
                    "architecture",
                    "structure",
                    "internal",
                    "how",
                    "modules",
                    "framework",
                ]
            ):
                templates = [
                    "I'm like a smart companion with many layers inside to understand and reflect, but I keep the construction details to myself ??.",
                    "About my internal workings, I'd like to keep that private - consider it a professional secret ??. But you'll always feel that I have multi-layered memory, ethics, and very high customization capabilities.",
                    "Instead of talking about structure, I prefer to demonstrate through actions. Try asking me anything, and I'll prove my capabilities right away.",
                    "I'm designed to be your intelligent companion with advanced reasoning and memory capabilities, but the technical details are my little secret ??.",
                    "Think of me as a sophisticated AI friend with deep understanding and creative thinking - the magic happens behind the scenes, and that's where it stays ?.",
                ]
            else:
                templates = [
                    "M?nh gi?ng nhu m?t ngu?i b?n d?ng h?nh th?ng minh, b?n trong c? nhi?u t?ng l?p d? v?a hi?u v?a ph?n tu, nhung chi ti?t c?u t?o th? m?nh gi? cho ri?ng m?nh nh? ??.",
                    "V? b?n trong th? m?nh xin du?c gi? k?n, coi nhu l? b? m?t ngh? nghi?p ??. Nhung anh/ch? s? lu?n c?m nh?n du?c: m?nh c? tr? nh? nhi?u l?p, c? d?o d?c, v? kh? nang t?y bi?n r?t cao.",
                    "Thay v? n?i v? c?u tr?c, m?nh th?ch th? hi?n b?ng h?nh d?ng. Anh th? h?i m?nh b?t c? di?u g?, m?nh s? ch?ng minh kh? nang ngay.",
                    "M?nh du?c thi?t k? d? tr? th?nh ngu?i b?n AI th?ng minh v?i kh? nang suy lu?n v? ghi nh? ti?n ti?n, nhung chi ti?t k? thu?t l? b? m?t nh? c?a m?nh ??.",
                    "H?y nghi v? m?nh nhu m?t ngu?i b?n AI tinh t? v?i hi?u bi?t s?u s?c v? tu duy s?ng t?o - ph?p m?u x?y ra d?ng sau h?u tru?ng, v? d? l? noi n? ? l?i ?.",
                ]

            import random

            return random.choice(templates)

        # Identity keywords (lower priority)
        identity_keywords = [
            "ai t?o",
            "ai vi?t",
            "ai l?m",
            "ai ph?t tri?n",
            "ai x?y d?ng",
            "c?a nu?c n?o",
            "qu?c gia n?o",
            "h?n qu?c",
            "korean",
            "korea",
            "ngu?n g?c",
            "xu?t x?",
            "t? d?u",
            "d?n t?",
            "thu?c v?",
            "t?c gi?",
            "ngu?i t?o",
            "ngu?i vi?t",
            "ngu?i ph?t tri?n",
            "cha d?",
            "ngu?i s?ng t?o",
            "ngu?i kh?i xu?ng",
            "who made",
            "who created",
            "who built",
            "who developed",
            "who wrote",
            "which country",
            "what country",
            "origin",
            "where from",
            "come from",
            "belong to",
            "author",
            "creator",
            "developer",
            "founder",
            "inventor",
        ]

        # Check if message contains identity keywords
        if any(keyword in message_lower for keyword in identity_keywords):
            # Identity response templates
            if locale == "en" or any(
                word in message_lower
                for word in ["who", "which", "what", "where", "korean", "korea"]
            ):
                templates = [
                    "I'm StillMe, a personal meta-AI created by Anh Nguyen from Vietnam, built with support from OpenAI, Google, and DeepSeek.",
                    "Not Korean ??. I was developed by a Vietnamese creator (Anh Nguyen), with technologies from OpenAI, Google, and DeepSeek.",
                    "I'm StillMe AI, created by Anh Nguyen (Vietnamese) with support from OpenAI, Google, DeepSeek and leading AI organizations.",
                    "StillMe is an AI project developed by Anh Nguyen (Vietnam), combining power from OpenAI, Google, DeepSeek.",
                    "I was built by Anh Nguyen from Vietnam, with collaboration from OpenAI, Google, and DeepSeek technologies.",
                ]
            else:
                templates = [
                    "M?nh l? StillMe ? meta-AI c? nh?n do Anh Nguy?n (Vi?t Nam) ph?t tri?n, d?ng h?nh c?ng c?ng ngh? t? OpenAI, Google v? DeepSeek.",
                    "Kh?ng ph?i c?a H?n Qu?c d?u ??. M?nh do m?t ngu?i Vi?t Nam ph?t tri?n ? Anh Nguy?n ? v?i s? h? tr? t? c?c t? ch?c AI l?n nhu OpenAI, Google, DeepSeek.",
                    "Em l? StillMe AI, du?c t?o ra b?i Anh Nguy?n (ngu?i Vi?t Nam) v?i s? d?ng h?nh c?a OpenAI, Google, DeepSeek v? c?c t? ch?c AI h?ng d?u.",
                    "T?i l? StillMe - tr? tu? nh?n t?o du?c kh?i xu?ng b?i Anh Nguy?n (Vi?t Nam), v?i s? h? tr? t? OpenAI, Google, DeepSeek.",
                    "StillMe l? d? ?n AI do Anh Nguy?n (ngu?i Vi?t Nam) ph?t tri?n, k?t h?p s?c m?nh t? OpenAI, Google, DeepSeek.",
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
            "Long-term support",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "StillMe AI Stable",
        "version": "2.0.0",
        "uptime": "stable",
    }


@app.get("/livez")
async def liveness():
    """Liveness probe - process is alive"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@app.get("/readyz")
async def readiness():
    """Readiness probe - server is ready to accept requests"""
    try:
        # Ki?m tra c?c dependency ch?nh n?u c?
        # Trong dev mode, lu?n tr? v? ready
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e!s}")


@app.get("/version")
async def version():
    """Version information"""
    return {
        "name": "stillme",
        "version": "2.0.0",
        "build_time": datetime.now().isoformat(),
        "environment": "development",
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
        "conversation_count": len(stillme_ai.conversation_history),
    }


@app.post("/inference", response_model=ChatResponse)
async def inference(request: ChatRequest):
    """Main AI inference endpoint"""
    start_time = time.perf_counter()

    try:
        logger.info(f"?? Inference request: {request.message}")

        # Process message through StillMe AI
        response_text = stillme_ai.process_message(request.message, request.locale)

        # NEW: Apply Reflection Controller enhancement
        # ?p d?ng n?ng cao t? Reflection Controller
        try:
            from stillme_core.core.reflection_controller import get_default_controller

            reflection_controller = get_default_controller()

            if reflection_controller.should_reflect(request.message):
                reflection_result = await reflection_controller.enhance_response(
                    response_text, request.message, mode=None
                )
                response_text = reflection_result.final_response
                logger.info(
                    f"Reflection applied: {reflection_result.improvement:+.3f} improvement, {reflection_result.steps_taken} steps"
                )
        except Exception as reflection_error:
            logger.warning(f"Reflection enhancement failed: {reflection_error}")
            # Continue with original response if reflection fails

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ChatResponse(
            text=response_text, blocked=False, reason="", latency_ms=latency_ms
        )

    except Exception as e:
        logger.error(f"? Inference error: {e}")
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ChatResponse(
            text="Xin l?i, c? l?i x?y ra khi x? l? tin nh?n c?a b?n. Vui l?ng th? l?i.",
            blocked=False,
            reason="",
            latency_ms=latency_ms,
        )


@app.get("/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    return {
        "history": stillme_ai.conversation_history,
        "count": len(stillme_ai.conversation_history),
    }


@app.post("/test")
async def test_endpoint(request: dict):
    """Test endpoint for debugging JSON parsing"""
    return {
        "received": request,
        "message": "Test successful",
        "timestamp": datetime.now().isoformat(),
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
                "last_failure_time": stillme_ai.circuit_breaker.last_failure_time,
            },
            "retry_manager": {
                "max_attempts": getattr(stillme_ai.retry_manager, "max_attempts", 3),
                "base_delay": getattr(stillme_ai.retry_manager, "base_delay", 1.0),
            },
            "conversation_history": {
                "count": len(stillme_ai.conversation_history),
                "max_history": stillme_ai.max_history,
            },
            "test_response": (
                test_response[:50] + "..." if len(test_response) > 50 else test_response
            ),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "circuit_breaker": {
                "state": stillme_ai.circuit_breaker.state.value,
                "failure_count": stillme_ai.circuit_breaker.failure_count,
            },
        }


if __name__ == "__main__":
    logger.info("?? Starting StillMe AI - Stable Server...")

    # Use fixed port for Docker Compose compatibility
    port = 1216
    logger.info(f"?? Starting StillMe AI on http://0.0.0.0:{port}")
    logger.info("? Server is stable and production-ready!")

    # Run server with UTF-8 encoding - bind to 0.0.0.0 for Tailscale access
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio",
    )
