"""
NPR Phase 2.2: Self-Distilled Learning for Validation Chain Optimization

Implements PAPO-inspired algorithm (Parallel-Aware Policy Optimization) to optimize
validation thresholds based on historical performance.

Key concepts from NPR paper:
- Reward function: Measures validation quality (success rate, false positive rate)
- Policy optimization: Adjusts thresholds to maximize reward
- Progressive training: From static thresholds → adaptive thresholds
- Self-distillation: StillMe learns from its own validation history
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    """Configuration for a single threshold parameter"""
    name: str  # e.g., "citation_relevance_min_overlap", "confidence_threshold"
    current_value: float
    min_value: float = 0.0
    max_value: float = 1.0
    step_size: float = 0.01  # How much to adjust per optimization step
    description: str = ""


@dataclass
class ValidationReward:
    """Reward signal for validation quality"""
    success_rate: float  # Pass rate (0.0-1.0)
    false_positive_rate: float  # False positives (0.0-1.0)
    false_negative_rate: float  # False negatives (0.0-1.0)
    hallucination_prevention_rate: float  # Hallucinations prevented (0.0-1.0)
    overall_reward: float  # Combined reward score (0.0-1.0)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ThresholdOptimizationState:
    """State for threshold optimization"""
    threshold_name: str
    current_value: float
    best_value: float
    best_reward: float
    optimization_history: List[Tuple[float, float]] = field(default_factory=list)  # (value, reward)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class RewardFunction:
    """
    Reward function for validation quality.
    
    Based on NPR paper's reward design:
    - High success rate = positive reward
    - Low false positive rate = positive reward
    - Low false negative rate = positive reward
    - High hallucination prevention = positive reward
    """
    
    @staticmethod
    def calculate_reward(
        success_rate: float,
        false_positive_rate: float,
        false_negative_rate: float,
        hallucination_prevention_rate: float,
        weights: Optional[Dict[str, float]] = None
    ) -> ValidationReward:
        """
        Calculate reward for validation quality.
        
        Args:
            success_rate: Pass rate (0.0-1.0)
            false_positive_rate: False positives (0.0-1.0)
            false_negative_rate: False negatives (0.0-1.0)
            hallucination_prevention_rate: Hallucinations prevented (0.0-1.0)
            weights: Optional weights for each component (default: balanced)
            
        Returns:
            ValidationReward with overall reward score
        """
        if weights is None:
            weights = {
                "success_rate": 0.3,
                "false_positive_rate": 0.2,  # Penalty for false positives
                "false_negative_rate": 0.2,  # Penalty for false negatives
                "hallucination_prevention": 0.3  # High weight for hallucination prevention
            }
        
        # Calculate reward components
        # Success rate: direct contribution
        success_component = success_rate * weights["success_rate"]
        
        # False positive rate: penalty (lower is better)
        fp_penalty = (1.0 - false_positive_rate) * weights["false_positive_rate"]
        
        # False negative rate: penalty (lower is better)
        fn_penalty = (1.0 - false_negative_rate) * weights["false_negative_rate"]
        
        # Hallucination prevention: direct contribution
        hallucination_component = hallucination_prevention_rate * weights["hallucination_prevention"]
        
        # Overall reward: sum of components
        overall_reward = success_component + fp_penalty + fn_penalty + hallucination_component
        
        return ValidationReward(
            success_rate=success_rate,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            hallucination_prevention_rate=hallucination_prevention_rate,
            overall_reward=overall_reward
        )


class PAPOOptimizer:
    """
    PAPO-inspired optimizer for threshold parameters.
    
    Based on NPR paper's Parallel-Aware Policy Optimization:
    - Tracks reward for each threshold value
    - Optimizes thresholds to maximize reward
    - Uses gradient-free optimization (since thresholds are discrete)
    - Progressive training: starts conservative, adapts over time
    """
    
    def __init__(self, state_file: Optional[str] = None):
        """
        Initialize PAPO optimizer.
        
        Args:
            state_file: Optional path to save optimization state
        """
        self.state_file = state_file or "data/papo_optimization_state.json"
        self.optimization_states: Dict[str, ThresholdOptimizationState] = {}
        self.reward_history: List[ValidationReward] = []
        self._load_state()
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
    
    def _initialize_default_thresholds(self):
        """Initialize default threshold configurations"""
        default_thresholds = {
            "citation_relevance_min_overlap": ThresholdConfig(
                name="citation_relevance_min_overlap",
                current_value=0.1,
                min_value=0.0,
                max_value=0.5,
                step_size=0.01,
                description="Minimum keyword overlap for citation relevance"
            ),
            "evidence_overlap_threshold": ThresholdConfig(
                name="evidence_overlap_threshold",
                current_value=0.01,
                min_value=0.0,
                max_value=0.2,
                step_size=0.005,
                description="Minimum evidence overlap threshold"
            ),
            "confidence_threshold": ThresholdConfig(
                name="confidence_threshold",
                current_value=0.5,
                min_value=0.3,
                max_value=0.8,
                step_size=0.02,
                description="Minimum confidence threshold for uncertainty expression"
            ),
            "similarity_threshold": ThresholdConfig(
                name="similarity_threshold",
                current_value=0.1,
                min_value=0.0,
                max_value=0.3,
                step_size=0.01,
                description="Minimum similarity threshold for RAG retrieval"
            ),
        }
        
        # Initialize optimization states for each threshold
        for name, config in default_thresholds.items():
            if name not in self.optimization_states:
                self.optimization_states[name] = ThresholdOptimizationState(
                    threshold_name=name,
                    current_value=config.current_value,
                    best_value=config.current_value,
                    best_reward=0.0
                )
    
    def _load_state(self):
        """Load optimization state from file"""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Load optimization states
                    for name, state_data in data.get("optimization_states", {}).items():
                        self.optimization_states[name] = ThresholdOptimizationState(
                            threshold_name=state_data["threshold_name"],
                            current_value=state_data["current_value"],
                            best_value=state_data["best_value"],
                            best_reward=state_data["best_reward"],
                            optimization_history=[
                                (h[0], h[1]) for h in state_data.get("optimization_history", [])
                            ],
                            last_updated=state_data.get("last_updated", datetime.utcnow().isoformat())
                        )
                    
                    logger.info(f"✅ Loaded PAPO optimization state from {self.state_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load PAPO optimization state: {e}")
    
    def _save_state(self):
        """Save optimization state to file"""
        try:
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "optimization_states": {
                    name: {
                        "threshold_name": state.threshold_name,
                        "current_value": state.current_value,
                        "best_value": state.best_value,
                        "best_reward": state.best_reward,
                        "optimization_history": state.optimization_history,
                        "last_updated": state.last_updated
                    }
                    for name, state in self.optimization_states.items()
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Saved PAPO optimization state to {self.state_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save PAPO optimization state: {e}")
    
    def record_reward(
        self,
        threshold_name: str,
        threshold_value: float,
        reward: ValidationReward
    ) -> None:
        """
        Record reward for a threshold value.
        
        Args:
            threshold_name: Name of threshold parameter
            threshold_value: Value of threshold that produced this reward
            reward: ValidationReward object
        """
        if threshold_name not in self.optimization_states:
            self.optimization_states[threshold_name] = ThresholdOptimizationState(
                threshold_name=threshold_name,
                current_value=threshold_value,
                best_value=threshold_value,
                best_reward=reward.overall_reward
            )
        
        state = self.optimization_states[threshold_name]
        
        # Record in history
        state.optimization_history.append((threshold_value, reward.overall_reward))
        
        # Keep only last 100 entries
        if len(state.optimization_history) > 100:
            state.optimization_history = state.optimization_history[-100:]
        
        # Update best if this is better
        if reward.overall_reward > state.best_reward:
            state.best_value = threshold_value
            state.best_reward = reward.overall_reward
            logger.info(f"🎯 [PAPO] New best reward for {threshold_name}: {reward.overall_reward:.3f} (value: {threshold_value:.3f})")
        
        # Update current value
        state.current_value = threshold_value
        state.last_updated = datetime.utcnow().isoformat()
        
        # Save state
        self._save_state()
    
    def optimize_threshold(
        self,
        threshold_name: str,
        config: ThresholdConfig,
        current_reward: float
    ) -> float:
        """
        Optimize a threshold parameter using PAPO-inspired algorithm.
        
        Strategy:
        1. Try increasing threshold (if current reward is good)
        2. Try decreasing threshold (if current reward is poor)
        3. Use best value if it's significantly better
        
        Args:
            threshold_name: Name of threshold parameter
            config: ThresholdConfig with bounds and step size
            current_reward: Current reward value
            
        Returns:
            Optimized threshold value
        """
        if threshold_name not in self.optimization_states:
            self.optimization_states[threshold_name] = ThresholdOptimizationState(
                threshold_name=threshold_name,
                current_value=config.current_value,
                best_value=config.current_value,
                best_reward=current_reward
            )
        
        state = self.optimization_states[threshold_name]
        
        # If we have enough history, use best value
        if len(state.optimization_history) >= 10:
            # Check if best value is significantly better (5% improvement)
            if state.best_reward > current_reward * 1.05:
                logger.info(f"🎯 [PAPO] Using best value for {threshold_name}: {state.best_value:.3f} (reward: {state.best_reward:.3f} vs current: {current_reward:.3f})")
                return state.best_value
        
        # Otherwise, try small adjustments
        # Strategy: If reward is good, try increasing threshold (stricter)
        # If reward is poor, try decreasing threshold (more lenient)
        if current_reward >= 0.7:  # Good reward
            # Try increasing threshold (stricter validation)
            new_value = min(config.max_value, state.current_value + config.step_size)
        elif current_reward < 0.5:  # Poor reward
            # Try decreasing threshold (more lenient validation)
            new_value = max(config.min_value, state.current_value - config.step_size)
        else:  # Medium reward
            # Keep current value
            new_value = state.current_value
        
        # Ensure within bounds
        new_value = max(config.min_value, min(config.max_value, new_value))
        
        return new_value
    
    def get_optimized_threshold(self, threshold_name: str, default_value: float) -> float:
        """
        Get optimized threshold value.
        
        Args:
            threshold_name: Name of threshold parameter
            default_value: Default value if no optimization available
            
        Returns:
            Optimized threshold value
        """
        if threshold_name in self.optimization_states:
            state = self.optimization_states[threshold_name]
            # Use best value if we have enough history
            if len(state.optimization_history) >= 5:
                return state.best_value
            return state.current_value
        return default_value
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization progress.
        
        Returns:
            Dictionary with optimization summary
        """
        summary = {
            "total_thresholds": len(self.optimization_states),
            "thresholds": {}
        }
        
        for name, state in self.optimization_states.items():
            summary["thresholds"][name] = {
                "current_value": state.current_value,
                "best_value": state.best_value,
                "best_reward": state.best_reward,
                "optimization_steps": len(state.optimization_history),
                "last_updated": state.last_updated
            }
        
        return summary


class SelfDistilledLearning:
    """
    Self-Distilled Learning system for StillMe validation chain.
    
    Implements NPR Phase 2.2: Self-Distilled Learning
    - Tracks validation metrics
    - Calculates rewards
    - Optimizes thresholds using PAPO algorithm
    - Progressive training: from static → adaptive
    """
    
    def __init__(self):
        """Initialize Self-Distilled Learning system"""
        from backend.validators.validation_metrics_tracker import get_validation_tracker
        from backend.validators.metrics import get_metrics
        
        self.tracker = get_validation_tracker()
        self.metrics = get_metrics()
        self.reward_function = RewardFunction()
        self.papo_optimizer = PAPOOptimizer()
        
        logger.info("✅ Self-Distilled Learning system initialized")
    
    def calculate_reward_from_metrics(self, days: int = 7) -> ValidationReward:
        """
        Calculate reward from recent validation metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ValidationReward with overall reward score
        """
        # Get metrics summary
        metrics = self.tracker.get_metrics_summary(days=days)
        
        if metrics["total_validations"] == 0:
            # No data yet, return neutral reward
            return ValidationReward(
                success_rate=0.5,
                false_positive_rate=0.5,
                false_negative_rate=0.5,
                hallucination_prevention_rate=0.5,
                overall_reward=0.5
            )
        
        # Calculate metrics
        success_rate = metrics["pass_rate"]
        
        # Estimate false positive rate (validations that passed but shouldn't have)
        # This is hard to measure directly, so we use heuristics:
        # - High pass rate with low confidence = potential false positives
        avg_confidence = metrics.get("avg_confidence", 0.5)
        false_positive_rate = max(0.0, 1.0 - avg_confidence) if success_rate > 0.8 else 0.1
        
        # Estimate false negative rate (validations that failed but shouldn't have)
        # High failure rate with high confidence = potential false negatives
        false_negative_rate = max(0.0, (1.0 - success_rate) * 0.3) if avg_confidence > 0.7 else 0.1
        
        # Hallucination prevention rate (from metrics)
        # This is tracked in ValidationMetrics
        hallucination_prevention_rate = 0.7  # Default estimate, can be improved with better tracking
        
        # Calculate reward
        reward = self.reward_function.calculate_reward(
            success_rate=success_rate,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            hallucination_prevention_rate=hallucination_prevention_rate
        )
        
        logger.info(f"📊 [Self-Distilled] Reward calculated: {reward.overall_reward:.3f} "
                   f"(success: {success_rate:.3f}, fp: {false_positive_rate:.3f}, "
                   f"fn: {false_negative_rate:.3f}, hallucination: {hallucination_prevention_rate:.3f})")
        
        return reward
    
    def optimize_thresholds(self, days: int = 7) -> Dict[str, float]:
        """
        Optimize validation thresholds using PAPO algorithm.
        
        Args:
            days: Number of days to analyze for optimization
            
        Returns:
            Dictionary mapping threshold names to optimized values
        """
        # Calculate current reward
        current_reward = self.calculate_reward_from_metrics(days=days)
        
        # Get threshold configurations
        threshold_configs = {
            "citation_relevance_min_overlap": ThresholdConfig(
                name="citation_relevance_min_overlap",
                current_value=0.1,
                min_value=0.0,
                max_value=0.5,
                step_size=0.01
            ),
            "evidence_overlap_threshold": ThresholdConfig(
                name="evidence_overlap_threshold",
                current_value=0.01,
                min_value=0.0,
                max_value=0.2,
                step_size=0.005
            ),
            "confidence_threshold": ThresholdConfig(
                name="confidence_threshold",
                current_value=0.5,
                min_value=0.3,
                max_value=0.8,
                step_size=0.02
            ),
        }
        
        optimized_values = {}
        
        for name, config in threshold_configs.items():
            # Get current value from optimizer
            current_value = self.papo_optimizer.get_optimized_threshold(name, config.current_value)
            
            # Optimize
            optimized_value = self.papo_optimizer.optimize_threshold(
                name,
                config,
                current_reward.overall_reward
            )
            
            optimized_values[name] = optimized_value
            
            # Record reward for this threshold value
            self.papo_optimizer.record_reward(
                name,
                optimized_value,
                current_reward
            )
        
        logger.info(f"🎯 [Self-Distilled] Optimized thresholds: {optimized_values}")
        
        return optimized_values
    
    def get_adaptive_threshold(
        self, 
        threshold_name: str, 
        default_value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Get adaptive threshold value (optimized by PAPO).
        
        Phase 2.3: Context-aware thresholds - thresholds adapt based on question context.
        
        Args:
            threshold_name: Name of threshold parameter
            default_value: Default value if optimization not available
            context: Optional context dict with:
                - is_philosophical: bool (philosophical questions may need different thresholds)
                - is_technical: bool (technical questions may need stricter thresholds)
                - has_context: bool (questions with context may need different thresholds)
                - question_category: str (e.g., "factual", "philosophical", "technical")
                - context_quality: str (e.g., "high", "medium", "low")
                - avg_similarity: float (RAG similarity score)
            
        Returns:
            Adaptive threshold value (context-aware)
        """
        # Get base optimized threshold
        base_threshold = self.papo_optimizer.get_optimized_threshold(threshold_name, default_value)
        
        # Phase 2.3: Apply context-aware adjustments
        if context:
            adjusted_threshold = self._apply_context_adjustments(
                threshold_name,
                base_threshold,
                context
            )
            return adjusted_threshold
        
        return base_threshold
    
    def _apply_context_adjustments(
        self,
        threshold_name: str,
        base_threshold: float,
        context: Dict[str, Any]
    ) -> float:
        """
        Apply context-aware adjustments to threshold.
        
        Phase 2.3: Progressive training - thresholds adapt based on context.
        
        Strategy:
        - Philosophical questions: More lenient thresholds (allow more uncertainty)
        - Technical questions: Stricter thresholds (require more evidence)
        - High context quality: Can be stricter (good RAG results)
        - Low context quality: More lenient (poor RAG results)
        
        Args:
            threshold_name: Name of threshold parameter
            base_threshold: Base threshold value from PAPO optimization
            context: Context dict with question/context information
            
        Returns:
            Context-adjusted threshold value
        """
        adjusted = base_threshold
        
        is_philosophical = context.get("is_philosophical", False)
        is_technical = context.get("is_technical", False)
        has_context = context.get("has_context", False)
        context_quality = context.get("context_quality", "medium")
        avg_similarity = context.get("avg_similarity", 0.5)
        
        # Adjustment factors (how much to adjust based on context)
        adjustment_factor = 0.1  # 10% adjustment
        
        # Apply adjustments based on threshold type
        if threshold_name == "citation_relevance_min_overlap":
            # Citation relevance: Philosophical questions may have less strict citation requirements
            if is_philosophical:
                adjusted = base_threshold * (1.0 - adjustment_factor * 0.5)  # 5% more lenient
            elif is_technical:
                adjusted = base_threshold * (1.0 + adjustment_factor)  # 10% stricter
            # High context quality: Can require more relevance
            if context_quality == "high" and has_context:
                adjusted = base_threshold * (1.0 + adjustment_factor * 0.5)  # 5% stricter
            # Low context quality: More lenient
            elif context_quality == "low" and has_context:
                adjusted = base_threshold * (1.0 - adjustment_factor)  # 10% more lenient
        
        elif threshold_name == "evidence_overlap_threshold":
            # Evidence overlap: Philosophical questions may have lower overlap requirements
            if is_philosophical:
                adjusted = base_threshold * (1.0 - adjustment_factor)  # 10% more lenient
            elif is_technical:
                adjusted = base_threshold * (1.0 + adjustment_factor * 1.5)  # 15% stricter
            # Adjust based on context quality
            if context_quality == "high" and avg_similarity > 0.6:
                adjusted = base_threshold * (1.0 + adjustment_factor)  # 10% stricter
            elif context_quality == "low" or avg_similarity < 0.3:
                adjusted = base_threshold * (1.0 - adjustment_factor * 0.5)  # 5% more lenient
        
        elif threshold_name == "confidence_threshold":
            # Confidence: Philosophical questions may express more uncertainty
            if is_philosophical:
                adjusted = base_threshold * (1.0 - adjustment_factor * 0.5)  # 5% more lenient
            elif is_technical:
                adjusted = base_threshold * (1.0 + adjustment_factor)  # 10% stricter
            # High context quality: Can require higher confidence
            if context_quality == "high" and has_context:
                adjusted = base_threshold * (1.0 + adjustment_factor * 0.5)  # 5% stricter
        
        # Ensure adjusted threshold stays within reasonable bounds
        # Get threshold config to know bounds
        threshold_configs = {
            "citation_relevance_min_overlap": (0.0, 0.5),
            "evidence_overlap_threshold": (0.0, 0.2),
            "confidence_threshold": (0.3, 0.8),
        }
        
        if threshold_name in threshold_configs:
            min_val, max_val = threshold_configs[threshold_name]
            adjusted = max(min_val, min(max_val, adjusted))
        
        return adjusted
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get summary of self-distilled learning progress.
        
        Returns:
            Dictionary with learning summary
        """
        reward = self.calculate_reward_from_metrics(days=7)
        optimization_summary = self.papo_optimizer.get_optimization_summary()
        
        return {
            "current_reward": reward.overall_reward,
            "reward_components": {
                "success_rate": reward.success_rate,
                "false_positive_rate": reward.false_positive_rate,
                "false_negative_rate": reward.false_negative_rate,
                "hallucination_prevention_rate": reward.hallucination_prevention_rate
            },
            "optimization": optimization_summary,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
_self_distilled_learning: Optional[SelfDistilledLearning] = None


def get_self_distilled_learning() -> SelfDistilledLearning:
    """Get global Self-Distilled Learning instance"""
    global _self_distilled_learning
    if _self_distilled_learning is None:
        _self_distilled_learning = SelfDistilledLearning()
    return _self_distilled_learning

