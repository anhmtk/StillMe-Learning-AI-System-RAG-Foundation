"""
Cost Monitor for StillMe - Philosophy-First Cost Tracking

Tracks API costs while prioritizing philosophical queries.
NEVER throttles philosophical queries - only monitors and alerts.
"""

import logging
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class PhilosophicalCostMonitor:
    """
    Cost monitor that prioritizes philosophical queries
    
    Principles:
    1. Philosophical queries are NEVER throttled
    2. Only factual queries can be throttled if budget exceeded
    3. Always log costs for transparency
    4. Alert on unusual spending patterns
    """
    
    def __init__(self):
        """Initialize cost monitor"""
        # Cost tracking
        self.daily_costs: Dict[str, float] = defaultdict(float)  # date -> total cost
        self.philosophical_costs: Dict[str, float] = defaultdict(float)  # date -> philosophical cost
        self.factual_costs: Dict[str, float] = defaultdict(float)  # date -> factual cost
        
        # Query tracking
        self.philosophical_queries: Dict[str, int] = defaultdict(int)  # date -> count
        self.factual_queries: Dict[str, int] = defaultdict(int)  # date -> count
        
        # Budget settings (from env or defaults)
        self.daily_budget = float(os.getenv("DAILY_COST_BUDGET", "5.0"))  # $5/day default
        self.philosophical_budget_ratio = float(os.getenv("PHILOSOPHICAL_BUDGET_RATIO", "0.7"))  # 70% for philosophy
        
        # Alert thresholds
        self.alert_threshold = float(os.getenv("COST_ALERT_THRESHOLD", "0.8"))  # Alert at 80% of budget
        
        logger.info(f"💰 Cost Monitor initialized: daily_budget=${self.daily_budget}, philosophical_ratio={self.philosophical_budget_ratio}")
    
    def _get_today_key(self) -> str:
        """Get today's date key (YYYY-MM-DD)"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _is_philosophical_question(self, question: str) -> bool:
        """Detect if question is philosophical"""
        if not question:
            return False
        
        question_lower = question.lower()
        
        # Philosophical depth indicators
        depth_indicators = [
            "consciousness", "existence", "meaning of life", "meaning of",
            "ethics", "morality", "free will", "reality", "truth",
            "knowledge", "what is", "why do we", "why does",
            "bản chất", "ý thức", "hiện sinh", "đạo đức", "chân lý",
            "tồn tại", "ý nghĩa", "tự do", "thực tại", "nhận thức"
        ]
        
        # Factual indicators that override (named philosophers, theorems, etc.)
        factual_indicators = [
            r"\b(russell|gödel|godel|plato|aristotle|kant|hume|descartes|spinoza|searle|dennett|popper|kuhn)\b",
            r"\b(paradox|theorem|định\s+lý|incompleteness|bất\s+toàn)\b",
            r"\b\d{4}\b",  # Years
            r"\b(conference|hội nghị|treaty|hiệp ước)\b"
        ]
        
        # Check factual first (if factual, not pure philosophical)
        import re
        for pattern in factual_indicators:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return False  # Factual question
        
        # Check philosophical depth
        return any(indicator in question_lower for indicator in depth_indicators)
    
    def calculate_cost(
        self, 
        input_tokens: int, 
        output_tokens: int,
        model: str = "deepseek-chat"
    ) -> float:
        """
        Calculate cost based on token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (for future multi-model pricing)
            
        Returns:
            Cost in USD
        """
        # DeepSeek pricing (as of 2024)
        # Both chat and reasoner have same pricing
        input_cost_per_1m = 0.28  # $0.28 per 1M input tokens
        output_cost_per_1m = 0.42  # $0.42 per 1M output tokens
        
        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
        
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def track_usage(
        self,
        question: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "deepseek-chat",
        response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track API usage and cost
        
        Args:
            question: User question
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            model: Model used
            response: Optional response (for analysis)
            
        Returns:
            Tracking info dict
        """
        # Calculate cost
        cost = self.calculate_cost(input_tokens, output_tokens, model)
        
        # Determine if philosophical
        is_philosophical = self._is_philosophical_question(question)
        
        # Get today's key
        today = self._get_today_key()
        
        # Update tracking
        self.daily_costs[today] += cost
        
        if is_philosophical:
            self.philosophical_costs[today] += cost
            self.philosophical_queries[today] += 1
            logger.info(f"🧠 Philosophical query #{self.philosophical_queries[today]}: ${cost:.4f} (input={input_tokens}, output={output_tokens})")
        else:
            self.factual_costs[today] += cost
            self.factual_queries[today] += 1
            if cost > 0.01:  # Alert on expensive factual queries
                logger.warning(f"💰 Expensive factual query: ${cost:.4f} (input={input_tokens}, output={output_tokens})")
        
        # Check budget and alert
        daily_total = self.daily_costs[today]
        if daily_total >= self.daily_budget * self.alert_threshold:
            logger.warning(f"⚠️ Daily cost alert: ${daily_total:.2f} / ${self.daily_budget:.2f} ({daily_total/self.daily_budget*100:.1f}%)")
        
        if daily_total >= self.daily_budget:
            logger.error(f"🚨 Daily budget exceeded: ${daily_total:.2f} / ${self.daily_budget:.2f}")
        
        return {
            "cost": cost,
            "is_philosophical": is_philosophical,
            "daily_total": daily_total,
            "daily_philosophical": self.philosophical_costs[today],
            "daily_factual": self.factual_costs[today],
            "budget_remaining": max(0, self.daily_budget - daily_total),
            "budget_percentage": (daily_total / self.daily_budget * 100) if self.daily_budget > 0 else 0
        }
    
    def should_throttle(self, question: str) -> bool:
        """
        Determine if query should be throttled
        
        CRITICAL: NEVER throttle philosophical queries
        
        Args:
            question: User question
            
        Returns:
            True if should throttle, False otherwise
        """
        # NEVER throttle philosophical queries
        if self._is_philosophical_question(question):
            return False
        
        # Check if budget exceeded
        today = self._get_today_key()
        daily_total = self.daily_costs[today]
        
        # Only throttle factual queries if budget exceeded
        if daily_total >= self.daily_budget:
            logger.warning(f"⏸️ Throttling factual queries - budget exceeded: ${daily_total:.2f} / ${self.daily_budget:.2f}")
            return True
        
        return False
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily cost statistics
        
        Args:
            date: Date string (YYYY-MM-DD) or None for today
            
        Returns:
            Statistics dict
        """
        if date is None:
            date = self._get_today_key()
        
        total_cost = self.daily_costs.get(date, 0.0)
        philosophical_cost = self.philosophical_costs.get(date, 0.0)
        factual_cost = self.factual_costs.get(date, 0.0)
        
        philosophical_count = self.philosophical_queries.get(date, 0)
        factual_count = self.factual_queries.get(date, 0)
        
        return {
            "date": date,
            "total_cost": round(total_cost, 4),
            "philosophical_cost": round(philosophical_cost, 4),
            "factual_cost": round(factual_cost, 4),
            "philosophical_queries": philosophical_count,
            "factual_queries": factual_count,
            "budget": self.daily_budget,
            "budget_remaining": max(0, self.daily_budget - total_cost),
            "budget_percentage": round((total_cost / self.daily_budget * 100) if self.daily_budget > 0 else 0, 2),
            "philosophical_ratio": round((philosophical_cost / total_cost * 100) if total_cost > 0 else 0, 2)
        }
    
    def get_weekly_stats(self) -> Dict[str, Any]:
        """Get weekly cost statistics"""
        today = datetime.now()
        week_start = today - timedelta(days=7)
        
        weekly_total = 0.0
        weekly_philosophical = 0.0
        weekly_factual = 0.0
        weekly_philosophical_count = 0
        weekly_factual_count = 0
        
        for i in range(7):
            date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.get_daily_stats(date)
            weekly_total += stats["total_cost"]
            weekly_philosophical += stats["philosophical_cost"]
            weekly_factual += stats["factual_cost"]
            weekly_philosophical_count += stats["philosophical_queries"]
            weekly_factual_count += stats["factual_queries"]
        
        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": today.strftime("%Y-%m-%d"),
            "total_cost": round(weekly_total, 4),
            "philosophical_cost": round(weekly_philosophical, 4),
            "factual_cost": round(weekly_factual, 4),
            "philosophical_queries": weekly_philosophical_count,
            "factual_queries": weekly_factual_count,
            "philosophical_ratio": round((weekly_philosophical / weekly_total * 100) if weekly_total > 0 else 0, 2)
        }


# Global cost monitor instance
_cost_monitor: Optional[PhilosophicalCostMonitor] = None


def get_cost_monitor() -> PhilosophicalCostMonitor:
    """Get global cost monitor instance (singleton)"""
    global _cost_monitor
    if _cost_monitor is None:
        _cost_monitor = PhilosophicalCostMonitor()
    return _cost_monitor

