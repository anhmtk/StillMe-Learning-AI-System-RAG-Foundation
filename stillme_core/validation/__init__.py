"""
StillMe Core Validation System

Provides validation engine and validators for ensuring response quality,
reducing hallucinations, and maintaining transparency.

This module has been migrated from backend/validators/ to stillme_core/validation/
"""

from .base import Validator, ValidationResult
from .chain import ValidationEngine

# Backward compatibility: Keep ValidatorChain as alias for ValidationEngine
# This allows existing code to continue working during migration
ValidatorChain = ValidationEngine
from .citation import CitationRequired
from .citation_relevance import CitationRelevance
from .evidence_overlap import EvidenceOverlap
from .numeric import NumericUnitsBasic
from .schema_format import SchemaFormat
from .ethics_adapter import EthicsAdapter
from .confidence import ConfidenceValidator
from .fallback_handler import FallbackHandler
from .review_adapter import ReviewAdapter
from .language import LanguageValidator
from .identity_check import IdentityCheckValidator
from .ego_neutrality import EgoNeutralityValidator
from .source_consensus import SourceConsensusValidator
from .self_critic_experience import SelfCriticExperience, self_correct_experience_claims
from .step_detector import StepDetector, Step
from .step_validator import StepValidator, StepValidationResult
from .consistency_checker import ConsistencyChecker, Claim
from .philosophical_depth import PhilosophicalDepthValidator
from .hallucination_explanation import HallucinationExplanationValidator
from .verbosity import VerbosityValidator

__all__ = [
    "Validator",
    "ValidationResult",
    "ValidationEngine",
    "ValidatorChain",  # Backward compatibility alias
    "CitationRequired",
    "CitationRelevance",
    "EvidenceOverlap",
    "NumericUnitsBasic",
    "SchemaFormat",
    "EthicsAdapter",
    "ConfidenceValidator",
    "FallbackHandler",
    "ReviewAdapter",
    "LanguageValidator",
    "IdentityCheckValidator",
    "EgoNeutralityValidator",
    "SourceConsensusValidator",
    "SelfCriticExperience",
    "self_correct_experience_claims",
    "StepDetector",
    "Step",
    "StepValidator",
    "StepValidationResult",
    "ConsistencyChecker",
    "Claim",
    "PhilosophicalDepthValidator",
    "HallucinationExplanationValidator",
    "VerbosityValidator",
]

