"""
Tiered Validation for StillMe

This module implements priority-based validation tiers,
ensuring critical validators run first, with graceful degradation
for time-constrained scenarios.

Based on StillMe Manifesto Principle 4: "ACCEPT SLOWNESS AS PRICE OF RIGOR"
- We value RIGOR over SPEED
- But we can optimize by prioritizing critical validators
- Non-critical validators can be skipped if time is limited

Tiers:
1. CRITICAL - Must run (anti-hallucination, citation, ethics)
2. IMPORTANT - Should run (evidence overlap, confidence, language)
3. OPTIONAL - Can skip if time limited (philosophical depth, identity check)
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ValidatorTier(Enum):
    """Validation tier priority"""
    CRITICAL = "critical"  # Must run - anti-hallucination, citation, ethics
    IMPORTANT = "important"  # Should run - evidence, confidence, language
    OPTIONAL = "optional"  # Can skip - philosophical depth, identity nuances


class TieredValidation:
    """
    Manages tiered validation based on priority and available time.
    
    This enables StillMe to ensure critical validators always run,
    while gracefully degrading for optional validators when time is limited.
    """
    
    # Validator tier mapping
    VALIDATOR_TIERS = {
        # CRITICAL: Anti-hallucination, citation, ethics
        "CitationRequired": ValidatorTier.CRITICAL,
        "FactualHallucinationValidator": ValidatorTier.CRITICAL,
        "EthicsAdapter": ValidatorTier.CRITICAL,
        
        # IMPORTANT: Evidence, confidence, language
        "EvidenceOverlap": ValidatorTier.IMPORTANT,
        "CitationRelevance": ValidatorTier.IMPORTANT,
        "ConfidenceValidator": ValidatorTier.IMPORTANT,
        "LanguageValidator": ValidatorTier.IMPORTANT,
        "NumericUnitsBasic": ValidatorTier.IMPORTANT,
        
        # OPTIONAL: Philosophical depth, identity nuances
        "PhilosophicalDepthValidator": ValidatorTier.OPTIONAL,
        "IdentityCheckValidator": ValidatorTier.OPTIONAL,
        "EgoNeutralityValidator": ValidatorTier.OPTIONAL,
        "ReligiousChoiceValidator": ValidatorTier.OPTIONAL,
        "SourceConsensusValidator": ValidatorTier.OPTIONAL,
    }
    
    def __init__(self):
        """Initialize tiered validation"""
        pass
    
    def get_validator_tier(self, validator_name: str) -> ValidatorTier:
        """
        Get tier for a validator.
        
        Args:
            validator_name: Name of validator class
            
        Returns:
            ValidatorTier enum
        """
        return self.VALIDATOR_TIERS.get(validator_name, ValidatorTier.OPTIONAL)
    
    def should_run_validator(
        self,
        validator_name: str,
        time_remaining: Optional[float] = None,
        min_time_for_optional: float = 1.0
    ) -> bool:
        """
        Determine if validator should run based on tier and time.
        
        Args:
            validator_name: Name of validator class
            time_remaining: Time remaining for validation (seconds)
            min_time_for_optional: Minimum time required to run optional validators
            
        Returns:
            True if validator should run
        """
        tier = self.get_validator_tier(validator_name)
        
        # CRITICAL: Always run
        if tier == ValidatorTier.CRITICAL:
            return True
        
        # IMPORTANT: Run if time allows (or if time_remaining is None, assume we have time)
        if tier == ValidatorTier.IMPORTANT:
            if time_remaining is None:
                return True
            return time_remaining >= 0.5  # Need at least 0.5s for important validators
        
        # OPTIONAL: Only run if we have plenty of time
        if tier == ValidatorTier.OPTIONAL:
            if time_remaining is None:
                return True
            return time_remaining >= min_time_for_optional
        
        return False
    
    def get_validators_by_tier(
        self,
        validators: List[Any],
        include_tiers: Optional[List[ValidatorTier]] = None
    ) -> List[Any]:
        """
        Filter validators by tier.
        
        Args:
            validators: List of validator instances
            include_tiers: List of tiers to include (None = all tiers)
            
        Returns:
            Filtered list of validators
        """
        if include_tiers is None:
            return validators
        
        filtered = []
        for validator in validators:
            validator_name = validator.__class__.__name__
            tier = self.get_validator_tier(validator_name)
            if tier in include_tiers:
                filtered.append(validator)
        
        return filtered
    
    def get_validation_plan(
        self,
        validators: List[Any],
        time_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create validation plan based on tier and time budget.
        
        Args:
            validators: List of validator instances
            time_budget: Total time budget for validation (seconds)
            
        Returns:
            Dict with:
                - critical_validators: List of critical validators
                - important_validators: List of important validators
                - optional_validators: List of optional validators
                - should_run_optional: Whether optional validators should run
                - estimated_time: Estimated time for validation
        """
        critical = []
        important = []
        optional = []
        
        for validator in validators:
            validator_name = validator.__class__.__name__
            tier = self.get_validator_tier(validator_name)
            
            if tier == ValidatorTier.CRITICAL:
                critical.append(validator)
            elif tier == ValidatorTier.IMPORTANT:
                important.append(validator)
            else:
                optional.append(validator)
        
        # Estimate time (rough: 0.1s per validator)
        estimated_time = (len(critical) + len(important) + len(optional)) * 0.1
        
        # Determine if optional should run
        should_run_optional = True
        if time_budget is not None:
            time_for_critical_important = (len(critical) + len(important)) * 0.1
            time_remaining = time_budget - time_for_critical_important
            should_run_optional = time_remaining >= 1.0  # Need at least 1s for optional
        
        return {
            "critical_validators": critical,
            "important_validators": important,
            "optional_validators": optional,
            "should_run_optional": should_run_optional,
            "estimated_time": estimated_time,
            "time_budget": time_budget
        }


# Global tiered validation instance
_tiered_validation: Optional[TieredValidation] = None


def get_tiered_validation() -> TieredValidation:
    """Get global tiered validation instance"""
    global _tiered_validation
    if _tiered_validation is None:
        _tiered_validation = TieredValidation()
    return _tiered_validation

