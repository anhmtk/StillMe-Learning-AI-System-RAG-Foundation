"""
StillMe Validators Module
Provides validation chain to reduce hallucinations and ensure quality responses

⚠️ MIGRATION NOTE: This module is being migrated to stillme_core.validation.
During migration, imports are forwarded from stillme_core.validation for backward compatibility.
"""

# During migration: Forward imports from stillme_core.validation
try:
    from stillme_core.validation import (
        Validator,
        ValidationResult,
        ValidationEngine,
        ValidatorChain,  # Backward compatibility alias
        CitationRequired,
        CitationRelevance,
        EvidenceOverlap,
        NumericUnitsBasic,
        SchemaFormat,
        EthicsAdapter,
        ConfidenceValidator,
        FallbackHandler,
        ReviewAdapter,
        LanguageValidator,
        IdentityCheckValidator,
        EgoNeutralityValidator,
        SourceConsensusValidator,
        SelfCriticExperience,
        self_correct_experience_claims,
        StepDetector,
        Step,
        StepValidator,
        StepValidationResult,
        ConsistencyChecker,
        Claim,
        PhilosophicalDepthValidator,
    )
except ImportError:
    # Fallback to local imports if stillme_core is not available yet
    # This allows gradual migration
    from .base import Validator, ValidationResult
    from .chain import ValidatorChain
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

__all__ = [
    "Validator",
    "ValidationResult",
    "ValidatorChain",
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
]

