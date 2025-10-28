"""
AI Service for StillMe V2
Handles AI interactions and responses
"""

import logging
import time
from datetime import datetime
from typing import Optional
import sys
import os
import httpx
import json

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Import config with fallback
try:
    from config import DEEPSEEK_API_KEY, OPENAI_API_KEY
except ImportError:
    DEEPSEEK_API_KEY = "sk-your-actual-deepseek-key"
    OPENAI_API_KEY = "sk-your-actual-openai-key"

logger = logging.getLogger(__name__)

class AIService:
    """
    AI Service for generating responses
    """
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY if DEEPSEEK_API_KEY != "sk-your-actual-deepseek-key" else OPENAI_API_KEY
        self.model = "deepseek-chat" if DEEPSEEK_API_KEY != "sk-your-actual-deepseek-key" else "gpt-3.5-turbo"
        self.base_url = "https://api.deepseek.com/v1" if DEEPSEEK_API_KEY != "sk-your-actual-deepseek-key" else "https://api.openai.com/v1"
        logger.info(f"✅ AI Service initialized with model: {self.model}")
    
        async def generate_response(self, message: str, context: Optional[str] = None) -> dict:
            """
            Generate AI response to user message
            Returns dict with response, model, latency_ms, tokens_used
            """
            start_time = time.time()
        
            try:
                logger.info(f"Generating AI response for: {message[:50]}...")
            
                # Check if we have a valid API key
                if self.api_key == "sk-your-actual-deepseek-key" or self.api_key == "sk-your-actual-openai-key" or not self.api_key:
                    logger.warning("No valid API key found, using fallback response")
                    latency_ms = int((time.time() - start_time) * 1000)
                    return {
                        "response": f"I understand you're asking about: {message}. Based on my current knowledge at this evolution stage, I can provide insights on this topic. Would you like me to explore this further with you?",
                        "model": "fallback",
                        "latency_ms": latency_ms,
                        "tokens_used": 0
                    }
            
                # Call actual AI API
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                
                    # Prepare messages
                    messages = [
                        {
                            "role": "system",
                            "content": "You are StillMe V2, a self-evolving AI assistant. You learn daily from various sources and continuously improve your knowledge. Be helpful, informative, and engaging in your responses."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                
                    # Add context if provided
                    if context:
                        messages.append({
                            "role": "system",
                            "content": f"Context: {context}"
                        })
                
                    data = {
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                }
                
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=30.0
                    )
                
                    latency_ms = int((time.time() - start_time) * 1000)
                
                    if response.status_code == 200:
                        result = response.json()
                        ai_response = result["choices"][0]["message"]["content"]
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                    
                        logger.info(f"AI response generated successfully in {latency_ms}ms")
                        
                        return {
                            "response": ai_response,
                            "model": self.model,
                            "latency_ms": latency_ms,
                            "tokens_used": tokens_used
                        }
                    else:
                        logger.error(f"AI API error: {response.status_code} - {response.text}")
                        return {
                            "response": "I apologize, but I'm having trouble connecting to the AI service right now. Please try again later.",
                            "model": "error",
                            "latency_ms": latency_ms,
                            "tokens_used": 0
                        }
            
            except Exception as e:
                logger.error(f"AI response error: {str(e)}")
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "response": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                    "model": "error",
                    "latency_ms": latency_ms,
                    "tokens_used": 0
                }
    
    async def generate_learning_content(self, topic: str) -> str:
        """
        Generate learning content for a specific topic
        """
        try:
            logger.info(f"Generating learning content for topic: {topic}")
            
            # Check if we have a valid API key
            if self.api_key == "sk-your-actual-deepseek-key" or self.api_key == "sk-your-actual-openai-key" or not self.api_key:
                logger.warning("No valid API key found, using fallback response")
                return f"Here's what I know about {topic}: This is a fascinating topic that involves many aspects. Let me share some insights based on my current knowledge."
            
            # Call actual AI API
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are StillMe V2, a self-evolving AI assistant. Generate educational content about the given topic. Be informative, accurate, and engaging."
                    },
                    {
                        "role": "user",
                        "content": f"Please explain: {topic}"
                    }
                ]
                
                data = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 800,
                    "temperature": 0.7
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info("Learning content generated successfully")
                    return content
                else:
                    logger.error(f"AI API error: {response.status_code} - {response.text}")
                    return "I apologize, but I'm having trouble generating learning content right now. Please try again later."
            
        except Exception as e:
            logger.error(f"Learning content error: {str(e)}")
            return "I apologize, but I'm having trouble generating learning content right now. Please try again later."