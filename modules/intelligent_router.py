# modules/intelligent_router.py
# Stub for intelligent router with ModelRouter
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class ModelRouter:
    """Model router for AI request routing"""

    def __init__(self):
        self.logger = logger
        self.models = {
            "gpt-4": {"available": True, "load": 0.5},
            "gpt-3.5-turbo": {"available": True, "load": 0.3},
            "claude-3": {"available": True, "load": 0.4},
            "llama3": {"available": True, "load": 0.2},
        }
        self.request_count = 0
        self.route_history = []

    def get_ai_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Get AI response for the given prompt"""
        self.request_count += 1

        if not prompt:
            return "Empty prompt provided"

        # Simple routing logic based on prompt characteristics
        selected_model = self._select_model(prompt)
        self.route_history.append({
            "prompt_length": len(prompt),
            "selected_model": selected_model,
            "timestamp": "2025-09-27T16:00:00Z"
        })

        # Mock response based on prompt
        if "code" in prompt.lower() or "programming" in prompt.lower():
            response = f"[{selected_model}] Here's a code solution for your request: {prompt[:50]}..."
        elif "creative" in prompt.lower() or "story" in prompt.lower():
            response = f"[{selected_model}] Creative response: Once upon a time, {prompt[:30]}..."
        elif "analyze" in prompt.lower() or "explain" in prompt.lower():
            response = f"[{selected_model}] Analysis: This request involves {prompt[:40]}..."
        else:
            response = f"[{selected_model}] Standard response: I understand you're asking about {prompt[:40]}..."

        self.logger.info(f"Generated response using {selected_model} for prompt length {len(prompt)}")
        return response

    def _select_model(self, prompt: str) -> str:
        """Select the best model for the given prompt"""
        prompt_lower = prompt.lower()

        # Route based on prompt characteristics
        if len(prompt) > 2000:
            return "gpt-4"  # Use most capable model for long prompts
        elif any(keyword in prompt_lower for keyword in ["code", "programming", "debug", "function"]):
            return "gpt-4"  # Use best model for coding tasks
        elif any(keyword in prompt_lower for keyword in ["creative", "story", "poem", "art"]):
            return "claude-3"  # Good for creative tasks
        elif any(keyword in prompt_lower for keyword in ["quick", "simple", "basic"]):
            return "gpt-3.5-turbo"  # Fast model for simple tasks
        else:
            return "llama3"  # Default local model

    def explain_last_route(self) -> Optional[str]:
        """Explain the last routing decision"""
        if not self.route_history:
            return "No routing history available"

        last_route = self.route_history[-1]
        return f"Last request routed to {last_route['selected_model']} for prompt of length {last_route['prompt_length']}"

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self.route_history:
            return {"total_requests": 0, "model_usage": {}}

        model_usage = {}
        for route in self.route_history:
            model = route["selected_model"]
            model_usage[model] = model_usage.get(model, 0) + 1

        return {
            "total_requests": len(self.route_history),
            "model_usage": model_usage,
            "most_used_model": max(model_usage, key=model_usage.get) if model_usage else None
        }

    def set_model_availability(self, model_name: str, available: bool):
        """Set model availability"""
        if model_name in self.models:
            self.models[model_name]["available"] = available
            self.logger.info(f"Model {model_name} availability set to {available}")

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [model for model, info in self.models.items() if info["available"]]

    def reset_stats(self):
        """Reset routing statistics"""
        self.request_count = 0
        self.route_history.clear()

# Function aliases for backward compatibility
def explain_last_route():
    """Global function to explain last route (for backward compatibility)"""
    router = ModelRouter()
    return router.explain_last_route()

def route_request(prompt: str, context: Dict[str, Any] = None) -> str:
    """Global function to route request (for backward compatibility)"""
    router = ModelRouter()
    return router.get_ai_response(prompt, context)
