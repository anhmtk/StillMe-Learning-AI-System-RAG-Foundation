"""
Adapter module for backward compatibility during migration.

This module forwards imports from stillme_core.validation to maintain
backward compatibility while we migrate the codebase.

TODO: Remove this adapter once all imports have been updated to use stillme_core.validation
"""

# Forward all imports from stillme_core.validation
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

__all__ = [
    "Validator",
    "ValidationResult",
    "ValidationEngine",
    "ValidatorChain",  # Backward compatibility
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

