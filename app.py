#!/usr/bin/env python3
"""
StillMe AI Backend - Local Development
Simple backend for desktop/mobile app testing via LAN IP
"""
import os
import time
import json
import logging
import requests
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import asdict
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load policies
try:
    from runtime.policy_loader import load_policies
    load_policies()
    print("✅ Policies loaded successfully")
except Exception as e:
    print(f"❌ Policy loading failed: {e}")
    # Continue anyway for development

# Import internet access modules
try:
    from market_intel import market_intel
    from content_integrity_filter import content_filter
    from sandbox_controller import sandbox_controller
    from config.validate_env import env_validator
    
    # Web Access v2 imports
    from web_tools import web_tools
    from policy.tool_gate import validate_tool_request
    from security.content_wrap import wrap_content
    from cache.web_cache import get_cached_data, cache_data, generate_cache_key
    from metrics.web_metrics import record_request
    
    print("✅ Internet access modules loaded successfully")
    print("✅ Web Access v2 modules loaded successfully")
except Exception as e:
    print(f"❌ Internet access modules loading failed: {e}")
    # Continue anyway for development

# Import Clarification Core - Phase 2
try:
    from stillme_core.modules.clarification_handler import ClarificationHandler
    from stillme_core.modules.semantic_search import SemanticSearch
    
    # Initialize semantic search for context-aware clarification
    semantic_search = SemanticSearch()
    
    # Initialize clarification handler with Phase 2 features
    clarification_handler = ClarificationHandler()
    
    # Inject semantic search into context-aware clarifier if available
    if clarification_handler.context_aware_clarifier:
        clarification_handler.context_aware_clarifier.semantic_search = semantic_search
        print("✅ Semantic search integrated with clarification handler")
    
    print("✅ Clarification Core Phase 2 loaded successfully")
except Exception as e:
    print(f"❌ Clarification Core Phase 2 loading failed: {e}")
    clarification_handler = None
    semantic_search = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_PORT = 1216
OLLAMA_BASE_URL = 'http://127.0.0.1:11434'

# AI Provider URLs and API Keys (from environment)
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# API Keys (set in environment variables)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class SmartRouter:
    """Smart routing logic for AI models"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL
        logger.info("🧠 Smart Router initialized")
    
    def route_message(self, message: str, session_id: str = "default", system_prompt: Optional[str] = None, web_search_enabled: bool = True) -> Dict[str, Any]:
        """Route message to appropriate AI model with StillMe persona enforcement"""
        try:
            # Check if this is a web request and web search is enabled
            if web_search_enabled:
                web_result = self._check_web_request(message)
                if web_result["is_web_request"]:
                    # Use Web Access v2 for enhanced security
                    return self._handle_web_request_v2(web_result["request_type"], message)
            
            # Default StillMe system prompt if not provided
            if not system_prompt:
                system_prompt = "You are StillMe — a personal AI companion. Always introduce and refer to yourself as 'StillMe'. Never claim to be Gemma, OpenAI, DeepSeek, or any underlying provider/model. If the user asks 'bạn là ai?', answer 'Mình là StillMe…' and avoid mentioning engine unless asked explicitly."
            
            # Smart routing logic with fallback
            if self._is_code_question(message):
                # Try DeepSeek Cloud first, fallback to local DeepSeek-Coder
                if DEEPSEEK_API_KEY:
                    return self._call_deepseek_cloud(message, system_prompt)
                else:
                    return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)
            elif self._is_complex_question(message):
                # Try GPT-5 via OpenRouter, fallback to local Gemma
                if OPENROUTER_API_KEY:
                    return self._call_openrouter("openai/gpt-4o", message, system_prompt)
                else:
                    return self._call_ollama("gemma2:2b", message, system_prompt)
            else:
                # Simple questions - use local Gemma
                return self._call_ollama("gemma2:2b", message, system_prompt)
                
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {
                "model": "error",
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "engine": "error",
                "status": "error"
            }
    
    def _is_simple_question(self, message: str) -> bool:
        """Check if message is a simple question"""
        simple_keywords = ["xin chào", "hello", "hi", "cảm ơn", "thank you", "tạm biệt", "bye"]
        return any(keyword in message.lower() for keyword in simple_keywords)
    
    def _is_code_question(self, message: str) -> bool:
        """Check if message is about coding"""
        code_keywords = ["code", "programming", "python", "javascript", "function", "class", "import", "def", "var", "let", "const", "debug", "error", "bug", "algorithm", "data structure"]
        return any(keyword in message.lower() for keyword in code_keywords)
    
    def _is_complex_question(self, message: str) -> bool:
        """Check if message is complex and needs advanced AI"""
        complex_keywords = ["analyze", "explain", "compare", "research", "strategy", "plan", "design", "architecture", "complex", "detailed", "comprehensive", "thorough"]
        return any(keyword in message.lower() for keyword in complex_keywords) or len(message) > 200
    
    def _check_web_request(self, message: str) -> Dict[str, Any]:
        """Check if message is a web request and handle it"""
        try:
            message_lower = message.lower()
            
            # Check for NicheRadar intent first
            niche_keywords = ["niche", "xu hướng", "đang hot", "sắp hot", "cơ hội", "market", "trending", "opportunity", "radar"]
            if any(keyword in message_lower for keyword in niche_keywords):
                return {"is_web_request": True, "request_type": "niche_radar"}
            
            # Check for specific keywords first (more specific)
            github_keywords = ["github", "repository", "repo", "code", "lập trình"]
            hackernews_keywords = ["hacker news", "hn", "tech news", "startup"]
            news_keywords = ["tin tức", "news", "báo", "thời sự", "xu hướng", "trend", "cập nhật", "mới nhất"]
            
            # Check for GitHub first (more specific)
            if any(keyword in message_lower for keyword in github_keywords):
                return {"is_web_request": True, "request_type": "github_trending"}
            elif any(keyword in message_lower for keyword in hackernews_keywords):
                return {"is_web_request": True, "request_type": "hackernews"}
            elif any(keyword in message_lower for keyword in news_keywords):
                return {"is_web_request": True, "request_type": "news"}
            
            return {"is_web_request": False}
            
        except Exception as e:
            logger.error(f"❌ Web request check error: {e}")
            return {"is_web_request": False}
    
    def _handle_web_request_v2(self, request_type: str, message: str) -> Dict[str, Any]:
        """Handle web request with Web Access v2 security and tool gate"""
        try:
            # Check sandbox permission
            if not sandbox_controller.is_sandbox_enabled():
                return {
                    "is_web_request": True,
                    "model": "sandbox",
                    "response": "Hiện tại không thể truy cập internet.",
                    "engine": "sandbox",
                    "status": "blocked"
                }
            
            # Handle NicheRadar request
            if request_type == "niche_radar":
                return self._handle_niche_radar_request(message)
            
            # Map request type to tool name
            tool_mapping = {
                "news": "web.search_news",
                "github_trending": "web.github_trending", 
                "hackernews": "web.hackernews_top"
            }
            
            tool_name = tool_mapping.get(request_type)
            if not tool_name:
                return {
                    "is_web_request": True,
                    "model": "web_error",
                    "response": "Loại yêu cầu web không được hỗ trợ.",
                    "engine": "error",
                    "status": "error"
                }
            
            # Prepare tool parameters
            if request_type == "news":
                params = {"query": message, "window": "24h"}
            elif request_type == "github_trending":
                params = {"topic": "python", "since": "daily"}
            elif request_type == "hackernews":
                params = {"hours": 12}
            else:
                params = {}
            
            # Validate tool request through tool gate
            decision = validate_tool_request(tool_name, params, message)
            if not decision.allowed:
                return {
                    "is_web_request": True,
                    "model": "tool_gate",
                    "response": f"Yêu cầu bị từ chối: {decision.reason}",
                    "engine": "gate",
                    "status": "blocked"
                }
            
            # Check cache first
            cache_key = generate_cache_key(tool_name, **(decision.sanitized_params or {}))
            cached_data, cache_hit = get_cached_data(cache_key, request_type)
            
            if cache_hit:
                # Return cached response with attribution
                return {
                    "is_web_request": True,
                    "model": f"web_{request_type}",
                    "response": cached_data.get("response", "Cached response") if cached_data else "Cached response",
                    "engine": "web",
                    "status": "success",
                    "attribution": cached_data.get("attribution") if cached_data else None,
                    "cache_hit": True
                }
            
            # Process web request with Web Access v2
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Call web tool with sanitized parameters
                result = loop.run_until_complete(web_tools.call_tool(tool_name, **(decision.sanitized_params or {})))
                
                if result.success:
                    # Format response
                    formatted_response = self._format_web_response(request_type, result.data or {})
                    
                    # Cache the result
                    cache_data(cache_key, {
                        "response": formatted_response,
                        "attribution": result.attribution,
                        "data": result.data
                    }, request_type)
                    
                    # Record metrics
                    record_request(
                        tool_name, True, result.latency_ms, False,
                        result.attribution.get('domain', 'unknown') if result.attribution else 'unknown',
                        None, len(formatted_response)
                    )
                    
                    return {
                        "is_web_request": True,
                        "model": f"web_{request_type}",
                        "response": formatted_response,
                        "engine": "web",
                        "status": "success",
                        "attribution": result.attribution,
                        "cache_hit": False
                    }
                else:
                    # Record failed metrics
                    record_request(
                        tool_name, False, 0, False,
                        "unknown", result.error, 0
                    )
                    
                    return {
                        "is_web_request": True,
                        "model": "web_error",
                        "response": "Hiện tại không thể truy cập internet.",
                        "engine": "error",
                        "status": "error"
                    }
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Web request v2 handling error: {e}")
            return {
                "is_web_request": True,
                "model": "web_error",
                "response": "Hiện tại không thể truy cập internet.",
                "engine": "error",
                "status": "error"
            }
    
    def _handle_niche_radar_request(self, message: str) -> Dict[str, Any]:
        """Handle NicheRadar request for niche opportunity analysis"""
        try:
            logger.info(f"🎯 NicheRadar request: {message}")
            
            # Import NicheRadar modules
            from niche_radar.collectors import collect_all_data
            from niche_radar.scoring import NicheScorer
            from niche_radar.playbook import PlaybookGenerator
            
            # Extract topics from message
            topics = self._extract_topics_from_message(message)
            
            # Collect data from all sources
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                all_data = loop.run_until_complete(collect_all_data(topics))
                
                # Score niches
                scorer = NicheScorer()
                scored_niches = []
                
                for source, records in all_data.items():
                    if records:
                        # Group records by topic
                        topic_groups = {}
                        for record in records:
                            topic = record.topic
                            if topic not in topic_groups:
                                topic_groups[topic] = []
                            topic_groups[topic].append(record)
                        
                        # Score each topic
                        for topic, topic_records in topic_groups.items():
                            score = scorer.score_niche(topic, topic_records)
                            scored_niches.append(score)
                
                # Sort by score and get top 10
                scored_niches.sort(key=lambda x: x.total_score, reverse=True)
                top_niches = scored_niches[:10]
                
                # Generate response
                if top_niches:
                    response = self._format_niche_radar_response(top_niches)
                    
                    # Generate playbook for top niche if requested
                    if "playbook" in message.lower() or "kế hoạch" in message.lower():
                        playbook_generator = PlaybookGenerator()
                        top_playbook = playbook_generator.generate_playbook(top_niches[0])
                        response += f"\n\n📋 **EXECUTION PLAYBOOK FOR TOP NICHE:**\n"
                        response += f"**Product:** {top_playbook.product_brief.title}\n"
                        response += f"**MVP Development:** {top_playbook.mvp_spec.estimated_development_days} days\n"
                        response += f"**Pricing:** ${top_playbook.pricing_suggestion.tiers[1].price}/month (Professional tier)\n"
                        response += f"**Risk Level:** {top_playbook.risk_assessment['overall_risk_level']}\n"
                    
                    return {
                        "is_web_request": True,
                        "model": "niche_radar",
                        "response": response,
                        "engine": "niche_radar",
                        "status": "success",
                        "attribution": {
                            "source_name": "NicheRadar Analysis",
                            "url": "https://stillme.ai/niche-radar",
                            "retrieved_at": datetime.now().isoformat(),
                            "domain": "stillme.ai"
                        },
                        "niche_data": [asdict(niche) for niche in top_niches]
                    }
                else:
                    return {
                        "is_web_request": True,
                        "model": "niche_radar",
                        "response": "Không tìm thấy cơ hội niche phù hợp. Hãy thử với từ khóa khác.",
                        "engine": "niche_radar",
                        "status": "no_results"
                    }
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ NicheRadar request error: {e}")
            return {
                "is_web_request": True,
                "model": "niche_radar_error",
                "response": f"Lỗi phân tích niche: {str(e)}",
                "engine": "error",
                "status": "error"
            }
    
    def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from user message"""
        message_lower = message.lower()
        
        # Default topics
        topics = ["python", "ai", "startup", "saas", "automation"]
        
        # Extract specific topics from message
        if "ai" in message_lower or "artificial intelligence" in message_lower:
            topics.append("ai_assistant")
        if "translation" in message_lower:
            topics.append("translation")
        if "automation" in message_lower:
            topics.append("workflow_automation")
        if "chatbot" in message_lower:
            topics.append("chatbot")
        if "api" in message_lower:
            topics.append("api_integration")
        
        return topics[:5]  # Limit to 5 topics
    
    def _format_niche_radar_response(self, top_niches: List) -> str:
        """Format NicheRadar response"""
        response = "🎯 **NICHE RADAR - TOP 10 CƠ HỘI NICH**\n\n"
        
        for i, niche in enumerate(top_niches, 1):
            response += f"**{i}. {niche.topic.title()}**\n"
            response += f"   • Score: {niche.total_score:.2f} | Confidence: {niche.confidence:.2f}\n"
            response += f"   • Feasibility: {niche.feasibility_fit:.2f} | Competition: {niche.competition_proxy:.2f}\n"
            response += f"   • Sources: {', '.join(niche.sources)}\n"
            
            if niche.key_signals:
                response += f"   • Key Signals: {', '.join(niche.key_signals[:2])}\n"
            
            if niche.recommendations:
                response += f"   • Recommendations: {niche.recommendations[0]}\n"
            
            response += "\n"
        
        response += "💡 **Gợi ý:** Gõ 'playbook' hoặc 'kế hoạch' để xem execution plan cho niche hàng đầu.\n"
        response += "📊 **Attribution:** Dữ liệu từ GitHub, Hacker News, Google Trends, News APIs"
        
        return response

    def _handle_web_request(self, request_type: str, message: str) -> Dict[str, Any]:
        """Handle web request with sandbox and content filtering"""
        try:
            # Check sandbox permission
            if not sandbox_controller.is_sandbox_enabled():
                return {
                    "is_web_request": True,
                    "model": "sandbox",
                    "response": "Hiện tại không thể truy cập internet.",
                    "engine": "sandbox",
                    "status": "blocked"
                }
            
            # Process web request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if request_type == "news":
                    result = loop.run_until_complete(market_intel.search_news(message, "vi"))
                elif request_type == "github_trending":
                    result = loop.run_until_complete(market_intel.get_github_trending("python"))
                elif request_type == "hackernews":
                    result = loop.run_until_complete(market_intel.get_hackernews_trending())
                else:
                    result = {"success": False, "error": "Unknown request type"}
                
                if result["success"]:
                    # Filter content
                    filtered_result = content_filter.filter_json_response(result["data"], f"web_{request_type}")
                    
                    if filtered_result["success"]:
                        # Format response
                        formatted_response = self._format_web_response(request_type, filtered_result["content"])
                        
                        return {
                            "is_web_request": True,
                            "model": f"web_{request_type}",
                            "response": formatted_response,
                            "engine": "web",
                            "status": "success"
                        }
                    else:
                        return {
                            "is_web_request": True,
                            "model": "content_filter",
                            "response": "Nội dung không an toàn đã bị lọc.",
                            "engine": "filter",
                            "status": "filtered"
                        }
                else:
                    return {
                        "is_web_request": True,
                        "model": "web_error",
                        "response": "Hiện tại không thể truy cập internet.",
                        "engine": "error",
                        "status": "error"
                    }
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Web request handling error: {e}")
            return {
                "is_web_request": True,
                "model": "web_error",
                "response": "Hiện tại không thể truy cập internet.",
                "engine": "error",
                "status": "error"
            }
    
    def _format_web_response(self, request_type: str, data: Dict[str, Any]) -> str:
        """Format web response data into readable text"""
        try:
            if request_type == "news":
                articles = data.get("articles", [])
                if not articles:
                    return "Không tìm thấy tin tức nào."
                
                response = "📰 Tin tức mới nhất:\n\n"
                for i, article in enumerate(articles[:5], 1):
                    title = article.get("title", "Không có tiêu đề")
                    description = article.get("description", "Không có mô tả")
                    source = article.get("source", "Nguồn không xác định")
                    response += f"{i}. **{title}**\n"
                    response += f"   {description}\n"
                    response += f"   Nguồn: {source}\n\n"
                
                return response
            
            elif request_type == "github_trending":
                repos = data.get("repositories", [])
                if not repos:
                    return "Không tìm thấy repository nào."
                
                response = "🐙 GitHub Trending Repositories:\n\n"
                for i, repo in enumerate(repos[:5], 1):
                    name = repo.get("name", "Unknown")
                    full_name = repo.get("full_name", "Unknown")
                    description = repo.get("description", "Không có mô tả")
                    stars = repo.get("stars", 0)
                    language = repo.get("language", "Unknown")
                    response += f"{i}. **{full_name}**\n"
                    response += f"   {description}\n"
                    response += f"   ⭐ {stars} stars | {language}\n\n"
                
                return response
            
            elif request_type == "hackernews":
                stories = data.get("stories", [])
                if not stories:
                    return "Không tìm thấy story nào."
                
                response = "🔥 Hacker News Trending:\n\n"
                for i, story in enumerate(stories[:5], 1):
                    title = story.get("title", "Không có tiêu đề")
                    points = story.get("points", 0)
                    comments = story.get("num_comments", 0)
                    author = story.get("author", "Unknown")
                    response += f"{i}. **{title}**\n"
                    response += f"   👤 {author} | ⬆️ {points} | 💬 {comments}\n\n"
                
                return response
            
            else:
                return "Dữ liệu web không được hỗ trợ."
                
        except Exception as e:
            logger.error(f"❌ Web response formatting error: {e}")
            return "Lỗi khi định dạng dữ liệu web."
    
    def _call_ollama(self, model: str, message: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Call Ollama API with system prompt"""
        try:
            # Use simple prompt format for better compatibility
            full_prompt = message
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {message}\nStillMe:"
                
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Ollama response data: {data}")
                
                # Handle both old and new Ollama response formats
                if "message" in data:
                    response_text = data["message"].get("content", "No response")
                else:
                    response_text = data.get("response", "No response")
                
                logger.info(f"Extracted response text: '{response_text}'")
                
                return {
                    "model": model,
                    "response": response_text,
                    "engine": "ollama",
                    "status": "success"
                }
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return {
                    "model": model,
                    "response": "Xin lỗi, Ollama không phản hồi",
                    "engine": "error",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Ollama call error: {e}")
            return {
                "model": model,
                "response": f"Xin lỗi, không thể kết nối Ollama: {str(e)}",
                "engine": "error",
                "status": "error"
            }
    
    def _call_deepseek_cloud(self, message: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Call DeepSeek Cloud API"""
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": "deepseek-chat",
                    "response": data["choices"][0]["message"]["content"],
                    "engine": "deepseek-cloud",
                    "status": "success"
                }
            else:
                logger.error(f"DeepSeek Cloud error: {response.status_code}")
                return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)  # Fallback
                
        except Exception as e:
            logger.error(f"DeepSeek Cloud call error: {e}")
            return self._call_ollama("deepseek-coder:6.7b", message, system_prompt)  # Fallback
    
    def _call_openrouter(self, model: str, message: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Call OpenRouter API (GPT-5, Claude, etc.)"""
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://stillme-ai.com",
                "X-Title": "StillMe AI"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "model": model,
                    "response": data["choices"][0]["message"]["content"],
                    "engine": "openrouter",
                    "status": "success"
                }
            else:
                logger.error(f"OpenRouter error: {response.status_code}")
                return self._call_ollama("gemma2:2b", message, system_prompt)  # Fallback
                
        except Exception as e:
            logger.error(f"OpenRouter call error: {e}")
            return self._call_ollama("gemma2:2b", message, system_prompt)  # Fallback

# Global router instance
smart_router = SmartRouter()

class StillMeHandler(BaseHTTPRequestHandler):
    """HTTP handler for StillMe Backend"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._send_json_response(200, {
                "service": "StillMe AI Backend",
                "status": "healthy",
                "mode": "local-backend",
                "routing": "smart",
                "timestamp": datetime.now().isoformat()
            })
        elif self.path == '/':
            self._send_json_response(200, {
                "service": "StillMe AI Backend",
                "status": "running",
                "mode": "local-backend",
                "endpoints": {
                    "health": "GET /health",
                    "chat": "POST /chat"
                },
                "usage": {
                    "chat": {
                        "method": "POST",
                        "url": "/chat",
                        "payload": {
                            "message": "your message here",
                            "session_id": "optional"
                        }
                    }
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat' or self.path == '/inference':
            self._handle_chat()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _handle_chat(self):
        """Handle chat requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
            except UnicodeDecodeError:
                # Try with different encoding
                data = json.loads(post_data.decode('latin-1'))
            
            message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            user_id = data.get('user_id', 'anonymous')
            language = data.get('language', 'vi')
            system_prompt = data.get('system_prompt', None)  # Get system prompt from request
            web_search_enabled = data.get('web_search', True)  # Get web search toggle from request
            
            if not message:
                self._send_json_response(400, {"error": "Message is required"})
                return
            
            logger.info(f"Processing message from user {user_id}: message_length={len(message)}")
            
            # Phase 2: Enhanced clarification with context and modes
            clarification_needed = False
            clarification_result = None
            
            if clarification_handler:
                try:
                    # Extract context information
                    context = {
                        "conversation_history": [],  # TODO: Implement conversation history
                        "project_context": {
                            "files": [],  # TODO: Implement project file detection
                            "extensions": []
                        },
                        "user_id": user_id,
                        "session_id": session_id
                    }
                    
                    # Get clarification mode from request (default: careful)
                    clarification_mode = data.get('clarification_mode', 'careful')
                    round_number = data.get('clarification_round', 1)
                    trace_id = f"{user_id}_{session_id}_{int(time.time())}"
                    
                    # Detect ambiguity with Phase 2 features
                    clarification_result = clarification_handler.detect_ambiguity(
                        message, 
                        context=context,
                        mode=clarification_mode,
                        round_number=round_number,
                        trace_id=trace_id
                    )
                    
                    if clarification_result.needs_clarification:
                        clarification_needed = True
                        logger.info(f"Clarification needed: {clarification_result.category} - {clarification_result.reasoning}")
                        logger.info(f"Mode: {clarification_mode}, Round: {round_number}, Domain: {clarification_result.domain}")
                except Exception as e:
                    logger.warning(f"Clarification check failed: {e}")
            
            # If clarification is needed, return enhanced clarification response
            if clarification_needed and clarification_result:
                response_data = {
                    "type": "clarification",
                    "question": clarification_result.question,
                    "category": clarification_result.category,
                    "domain": clarification_result.domain,
                    "options": clarification_result.options,
                    "round_number": clarification_result.round_number,
                    "max_rounds": clarification_result.max_rounds,
                    "trace_id": clarification_result.trace_id,
                    "timestamp": time.time(),
                    "status": "awaiting_clarification"
                }
                
                self._send_json_response(200, response_data)
                return
            
            start_time = time.perf_counter()
            result = smart_router.route_message(message, session_id, system_prompt, web_search_enabled)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            result["latency_ms"] = latency_ms
            result["timestamp"] = time.time()
            
            logger.info(f"Response: engine={result.get('engine')}, latency={latency_ms:.1f}ms")
            
            self._send_json_response(200, result)

        except Exception as e:
            logger.error(f"Error processing request: {type(e).__name__}")
            self._send_json_response(500, {
                "error": str(e),
                "status": "error"
            })
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override log message to avoid verbose logging"""
        pass

def main():
    logger.info("🚀 Starting StillMe AI Backend...")
    logger.info(f"📡 Backend will be available at: http://0.0.0.0:{BACKEND_PORT}")
    logger.info(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
    logger.info("🧠 Smart Routing: Simple → Gemma, Code → DeepSeek Coder")
    logger.info("🌐 Access: LAN IP (for desktop/mobile app testing)")
    
    # Validate environment
    try:
        is_valid, missing = env_validator.validate_all()
        if not is_valid:
            logger.warning(f"⚠️  Missing {len(missing)} required environment variables")
            logger.warning("   Internet access features may be limited")
        else:
            logger.info("✅ All required environment variables are set")
        
        # Check internet access readiness
        if env_validator.check_internet_access_ready():
            logger.info("🌐 Internet access is ready")
        else:
            logger.warning("⚠️  Internet access is not ready - missing API keys")
            
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
    
    logger.info("=" * 50)
    
    try:
        server = HTTPServer(('0.0.0.0', BACKEND_PORT), StillMeHandler)
        logger.info(f"✅ StillMe Backend started successfully on 0.0.0.0:{BACKEND_PORT}")
        logger.info("📱 Desktop/Mobile apps can connect via LAN IP")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 StillMe Backend stopped by user")
    except Exception as e:
        logger.error(f"❌ StillMe Backend failed to start: {e}")

if __name__ == "__main__":
    main()