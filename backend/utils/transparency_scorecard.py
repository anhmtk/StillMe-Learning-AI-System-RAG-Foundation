"""
Transparency Scorecard for StillMe

This module provides metrics to quantify StillMe's transparency,
enabling measurement and improvement of transparency over time.

Based on StillMe Manifesto Principle 6: "LOG EVERYTHING BECAUSE SECRETS CORRUPT TRUST"
- We value OPENNESS over EFFICIENCY
- Every decision is logged
- Every validation step is traceable

Metrics:
1. Citation Specificity - How specific are citations? (0.0-1.0)
2. Validation Completeness - How many validators ran? (0.0-1.0)
3. Epistemic Honesty - How well is uncertainty expressed? (0.0-1.0)
4. Process Traceability - How much of the process is logged? (0.0-1.0)
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TransparencyScorecard:
    """
    Scorecard for measuring StillMe's transparency.
    
    This enables StillMe to quantify its own transparency,
    making it possible to measure and improve over time.
    """
    citation_specificity: float = 0.0  # 0.0 = [general knowledge], 1.0 = [Document Title, Source, Date]
    validation_completeness: float = 0.0  # 0.0 = no validators, 1.0 = all validators ran
    epistemic_honesty: float = 0.0  # 0.0 = no uncertainty expression, 1.0 = full epistemic reasoning
    process_traceability: float = 0.0  # 0.0 = no logs, 1.0 = full traceability
    
    def calculate_overall(self) -> float:
        """
        Calculate overall transparency score.
        
        Uses weighted average:
        - Citation Specificity: 30%
        - Validation Completeness: 25%
        - Epistemic Honesty: 25%
        - Process Traceability: 20%
        
        Returns:
            Overall transparency score (0.0-1.0)
        """
        weights = {
            'citation_specificity': 0.30,
            'validation_completeness': 0.25,
            'epistemic_honesty': 0.25,
            'process_traceability': 0.20
        }
        
        overall = (
            self.citation_specificity * weights['citation_specificity'] +
            self.validation_completeness * weights['validation_completeness'] +
            self.epistemic_honesty * weights['epistemic_honesty'] +
            self.process_traceability * weights['process_traceability']
        )
        
        return round(overall, 3)
    
    def explain_scores(self) -> Dict[str, str]:
        """
        Explain what each score means.
        
        Returns:
            Dict mapping metric names to explanations
        """
        explanations = {}
        
        if self.citation_specificity < 0.3:
            explanations['citation_specificity'] = "Most citations are generic [general knowledge]"
        elif self.citation_specificity < 0.7:
            explanations['citation_specificity'] = "Some specific citations, but many generic"
        else:
            explanations['citation_specificity'] = "Most citations are specific with source metadata"
        
        if self.validation_completeness < 0.5:
            explanations['validation_completeness'] = "Many validators skipped or timed out"
        elif self.validation_completeness < 0.8:
            explanations['validation_completeness'] = "Most validators ran, some skipped"
        else:
            explanations['validation_completeness'] = "All or nearly all validators completed"
        
        if self.epistemic_honesty < 0.5:
            explanations['epistemic_honesty'] = "Uncertainty not well expressed or explained"
        elif self.epistemic_honesty < 0.8:
            explanations['epistemic_honesty'] = "Some uncertainty expression, but could be more detailed"
        else:
            explanations['epistemic_honesty'] = "Uncertainty well expressed with reasoning"
        
        if self.process_traceability < 0.5:
            explanations['process_traceability'] = "Limited logging, hard to trace process"
        elif self.process_traceability < 0.8:
            explanations['process_traceability'] = "Good logging, some gaps in traceability"
        else:
            explanations['process_traceability'] = "Excellent logging, full traceability"
        
        return explanations
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert scorecard to dictionary for logging/API.
        
        Returns:
            Dictionary representation
        """
        overall = self.calculate_overall()
        explanations = self.explain_scores()
        
        return {
            "overall_score": overall,
            "citation_specificity": self.citation_specificity,
            "validation_completeness": self.validation_completeness,
            "epistemic_honesty": self.epistemic_honesty,
            "process_traceability": self.process_traceability,
            "explanations": explanations
        }


class TransparencyScorer:
    """
    Calculates transparency scorecard from response process data.
    """
    
    def __init__(self):
        """Initialize transparency scorer"""
        pass
    
    def calculate_scorecard(
        self,
        citation: Optional[str] = None,
        validators_run: int = 0,
        validators_total: int = 12,
        has_epistemic_explanation: bool = False,
        has_uncertainty_expression: bool = False,
        log_count: int = 0,
        expected_logs: int = 10
    ) -> TransparencyScorecard:
        """
        Calculate transparency scorecard from process data.
        
        Args:
            citation: Citation string (e.g., "[Document Title, Source]" or "[general knowledge]")
            validators_run: Number of validators that ran
            validators_total: Total number of validators (default: 12)
            has_epistemic_explanation: Whether epistemic reasoning was used
            has_uncertainty_expression: Whether uncertainty was expressed
            log_count: Number of log entries
            expected_logs: Expected number of log entries (default: 10)
            
        Returns:
            TransparencyScorecard with calculated scores
        """
        # 1. Citation Specificity (0.0-1.0)
        citation_specificity = self._calculate_citation_specificity(citation)
        
        # 2. Validation Completeness (0.0-1.0)
        validation_completeness = self._calculate_validation_completeness(
            validators_run, validators_total
        )
        
        # 3. Epistemic Honesty (0.0-1.0)
        epistemic_honesty = self._calculate_epistemic_honesty(
            has_epistemic_explanation, has_uncertainty_expression
        )
        
        # 4. Process Traceability (0.0-1.0)
        process_traceability = self._calculate_process_traceability(
            log_count, expected_logs
        )
        
        return TransparencyScorecard(
            citation_specificity=citation_specificity,
            validation_completeness=validation_completeness,
            epistemic_honesty=epistemic_honesty,
            process_traceability=process_traceability
        )
    
    def _calculate_citation_specificity(self, citation: Optional[str]) -> float:
        """
        Calculate citation specificity score.
        
        Scoring:
        - [Document Title, Source, Date] → 1.0
        - [Document Title, Source] → 0.9
        - [Information from {Source} documents] → 0.7
        - [Background knowledge informed by context] → 0.5
        - [general knowledge] with explanation → 0.3
        - [general knowledge] without explanation → 0.1
        - No citation → 0.0
        
        Args:
            citation: Citation string
            
        Returns:
            Specificity score (0.0-1.0)
        """
        if not citation:
            return 0.0
        
        citation_lower = citation.lower()
        
        # Check for specific document citation
        if ',' in citation and '[' in citation and ']' in citation:
            # Format: [Title, Source, Date] or [Title, Source]
            parts = citation.split(',')
            if len(parts) >= 2:
                # Has title and source
                if len(parts) >= 3:
                    return 1.0  # Has date too
                else:
                    return 0.9  # Title and source, no date
        
        # Check for source-specific citation
        if 'information from' in citation_lower and 'documents' in citation_lower:
            return 0.7
        
        # Check for context-informed citation
        if 'background knowledge informed by' in citation_lower:
            return 0.5
        
        # Check for general knowledge with explanation
        if 'general knowledge' in citation_lower:
            if '(' in citation and ')' in citation:
                return 0.3  # Has explanation
            else:
                return 0.1  # No explanation
        
        # Default: some citation present but not recognized
        return 0.2
    
    def _calculate_validation_completeness(
        self,
        validators_run: int,
        validators_total: int
    ) -> float:
        """
        Calculate validation completeness score.
        
        Args:
            validators_run: Number of validators that ran
            validators_total: Total number of validators
            
        Returns:
            Completeness score (0.0-1.0)
        """
        if validators_total == 0:
            return 0.0
        
        return min(1.0, validators_run / validators_total)
    
    def _calculate_epistemic_honesty(
        self,
        has_epistemic_explanation: bool,
        has_uncertainty_expression: bool
    ) -> float:
        """
        Calculate epistemic honesty score.
        
        Scoring:
        - Has epistemic explanation (WHY uncertain) → 1.0
        - Has uncertainty expression (THAT uncertain) → 0.5
        - No uncertainty expression → 0.0
        
        Args:
            has_epistemic_explanation: Whether epistemic reasoning was used
            has_uncertainty_expression: Whether uncertainty was expressed
            
        Returns:
            Epistemic honesty score (0.0-1.0)
        """
        if has_epistemic_explanation:
            return 1.0
        elif has_uncertainty_expression:
            return 0.5
        else:
            return 0.0
    
    def _calculate_process_traceability(
        self,
        log_count: int,
        expected_logs: int
    ) -> float:
        """
        Calculate process traceability score.
        
        Args:
            log_count: Number of log entries
            expected_logs: Expected number of log entries
            
        Returns:
            Traceability score (0.0-1.0)
        """
        if expected_logs == 0:
            return 1.0 if log_count > 0 else 0.0
        
        return min(1.0, log_count / expected_logs)


# Global scorer instance
_transparency_scorer: Optional[TransparencyScorer] = None


def get_transparency_scorer() -> TransparencyScorer:
    """Get global transparency scorer instance"""
    global _transparency_scorer
    if _transparency_scorer is None:
        _transparency_scorer = TransparencyScorer()
    return _transparency_scorer

