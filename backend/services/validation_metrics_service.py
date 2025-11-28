"""
Validation Metrics Service
Aggregates per-validator metrics from validation_metrics_tracker for dashboard display

This service reads from persistent validation records and aggregates:
- Per-validator pass/fail counts
- Pass rates per validator
- Fallback usage statistics
- Confidence score distribution
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


# Mapping from validation reasons to validator names
# This is an approximation - actual validator names may vary
REASON_TO_VALIDATOR_MAP = {
    # CitationRequired
    "missing_citation": "CitationRequired",
    
    # CitationRelevance
    "citation_relevance_warning": "CitationRelevance",
    "citation_relevance": "CitationRelevance",
    
    # EvidenceOverlap
    "low_overlap": "EvidenceOverlap",
    "overlap": "EvidenceOverlap",
    
    # ConfidenceValidator
    "low_confidence": "ConfidenceValidator",
    "missing_uncertainty_no_context": "ConfidenceValidator",
    "uncertainty": "ConfidenceValidator",
    
    # FactualHallucinationValidator
    "factual_hallucination": "FactualHallucinationValidator",
    "explicit_fake_entity": "FactualHallucinationValidator",
    "suspicious_entity": "FactualHallucinationValidator",
    
    # IdentityCheckValidator
    "identity_violation": "IdentityCheckValidator",
    "identity_warning": "IdentityCheckValidator",
    
    # LanguageValidator
    "language_mismatch": "LanguageValidator",
    
    # PhilosophicalDepthValidator
    "optimistic_answer_missing_paradox": "PhilosophicalDepthValidator",
    "missing_philosophical_keywords": "PhilosophicalDepthValidator",
    
    # EgoNeutralityValidator
    "ego_violation": "EgoNeutralityValidator",
    
    # SourceConsensusValidator
    "source_contradiction": "SourceConsensusValidator",
    
    # NumericUnitsBasic
    "numeric_units": "NumericUnitsBasic",
    
    # EthicsAdapter
    "ethics_violation": "EthicsAdapter",
}


def _extract_validator_from_reason(reason: str) -> Optional[str]:
    """
    Extract validator name from validation reason string
    
    Args:
        reason: Validation reason string (e.g., "missing_citation", "identity_violation:...")
        
    Returns:
        Validator name if found, None otherwise
    """
    reason_lower = reason.lower()
    
    # Check direct mapping
    for pattern, validator in REASON_TO_VALIDATOR_MAP.items():
        if pattern in reason_lower:
            return validator
    
    # Check for validator_error format: "validator_error:{validator_name}:{error}"
    if reason.startswith("validator_error:"):
        parts = reason.split(":", 2)
        if len(parts) >= 2:
            return parts[1]
    
    # Check for colon-separated format: "validator_name:detail"
    if ":" in reason:
        validator_name = reason.split(":")[0]
        # Capitalize first letter to match class names
        if validator_name:
            return validator_name.capitalize()
    
    return None


class ValidationMetricsService:
    """
    Service to aggregate validation metrics for dashboard display
    """
    
    def __init__(self):
        """Initialize validation metrics service"""
        self.logger = logging.getLogger(__name__)
    
    def get_per_validator_metrics(
        self,
        days: int = 7,
        use_persistent_tracker: bool = True
    ) -> Dict[str, Any]:
        """
        Get per-validator metrics aggregated from validation records
        
        Args:
            days: Number of days to analyze (default: 7)
            use_persistent_tracker: Whether to use persistent tracker (default: True)
            
        Returns:
            Dictionary with per-validator metrics:
            {
                "total_responses": int,
                "total_fallbacks": int,
                "time_period_days": int,
                "validators": [
                    {
                        "name": str,
                        "total_checks": int,
                        "passed": int,
                        "failed": int,
                        "pass_rate": float,
                        "failure_reasons": List[str]
                    }
                ],
                "confidence_distribution": {
                    "min": float,
                    "max": float,
                    "avg": float,
                    "count": int
                }
            }
        """
        try:
            if use_persistent_tracker:
                from backend.validators.validation_metrics_tracker import get_validation_tracker
                tracker = get_validation_tracker()
                records = self._get_recent_records(tracker, days)
            else:
                # Fallback to in-memory metrics if persistent tracker not available
                from backend.validators.metrics import get_metrics
                metrics = get_metrics()
                records = []
                # In-memory metrics don't have per-validator breakdown
                # Return empty structure
                return self._create_empty_metrics(days)
            
            return self._aggregate_metrics(records, days)
            
        except Exception as e:
            self.logger.error(f"Error getting per-validator metrics: {e}", exc_info=True)
            return self._create_empty_metrics(days)
    
    def _get_recent_records(self, tracker, days: int) -> List:
        """
        Get recent validation records from tracker
        
        Args:
            tracker: ValidationMetricsTracker instance
            days: Number of days to look back
            
        Returns:
            List of ValidationRecord objects
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all records from tracker
        all_records = tracker._records if hasattr(tracker, '_records') else []
        
        # Filter by time
        recent_records = [
            r for r in all_records
            if datetime.fromisoformat(r.timestamp.replace('Z', '+00:00')) >= cutoff_time
        ]
        
        return recent_records
    
    def _aggregate_metrics(self, records: List, days: int) -> Dict[str, Any]:
        """
        Aggregate metrics from validation records
        
        Args:
            records: List of ValidationRecord objects
            days: Number of days analyzed
            
        Returns:
            Aggregated metrics dictionary
        """
        # Per-validator counters
        validator_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "failure_reasons": defaultdict(int)
        })
        
        # Overall stats
        total_responses = len(records)
        total_fallbacks = sum(1 for r in records if r.used_fallback)
        confidence_scores = [r.confidence_score for r in records if r.confidence_score is not None]
        
        # Aggregate per-validator stats
        for record in records:
            # Extract validators from reasons
            validators_involved = set()
            
            for reason in record.validation_reasons:
                validator = _extract_validator_from_reason(reason)
                if validator:
                    validators_involved.add(validator)
                    validator_stats[validator]["failure_reasons"][reason] += 1
            
            # Update validator stats
            # Only track validators that had explicit issues (from reasons)
            # If a record passed with no reasons, we can't know which validators ran
            # This is a limitation of current tracking - we only see failures/warnings, not successes
            for validator in validators_involved:
                validator_stats[validator]["total_checks"] += 1
                # If validator is in reasons, it means it had an issue
                # If record.passed = True, it's likely a warning (not a failure)
                # If record.passed = False, it's a failure
                if record.passed:
                    # Warnings - validator passed but had issues
                    validator_stats[validator]["passed"] += 1
                else:
                    # Failures - validator failed
                    validator_stats[validator]["failed"] += 1
            
            # Note: We can't track validators that passed without explicit tracking
            # This is a limitation - we only see failures/warnings in validation_reasons
            # For a complete picture, we would need to track all validators that ran,
            # not just those that had issues. This would require changes to ValidatorChain.
            
        # Convert to list format and calculate pass rates
        validators_list = []
        for validator_name, stats in sorted(validator_stats.items()):
            total_checks = stats["total_checks"]
            passed = stats["passed"]
            failed = stats["failed"]
            pass_rate = (passed / total_checks) if total_checks > 0 else 0.0
            
            validators_list.append({
                "name": validator_name,
                "total_checks": total_checks,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(pass_rate, 3),
                "failure_reasons": dict(stats["failure_reasons"])
            })
        
        # Calculate confidence distribution
        confidence_dist = {
            "min": round(min(confidence_scores), 3) if confidence_scores else 0.0,
            "max": round(max(confidence_scores), 3) if confidence_scores else 0.0,
            "avg": round(sum(confidence_scores) / len(confidence_scores), 3) if confidence_scores else 0.0,
            "count": len(confidence_scores)
        }
        
        return {
            "total_responses": total_responses,
            "total_fallbacks": total_fallbacks,
            "time_period_days": days,
            "validators": validators_list,
            "confidence_distribution": confidence_dist
        }
    
    def _create_empty_metrics(self, days: int) -> Dict[str, Any]:
        """
        Create empty metrics structure when no data is available
        
        Args:
            days: Number of days analyzed
            
        Returns:
            Empty metrics dictionary
        """
        return {
            "total_responses": 0,
            "total_fallbacks": 0,
            "time_period_days": days,
            "validators": [],
            "confidence_distribution": {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0
            }
        }


# Global service instance
_service = None


def get_validation_metrics_service() -> ValidationMetricsService:
    """Get global validation metrics service instance"""
    global _service
    if _service is None:
        _service = ValidationMetricsService()
    return _service

