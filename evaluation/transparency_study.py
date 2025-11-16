"""
Transparency Perception User Study Framework

Framework for conducting user studies on transparency perception
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TransparencyRating:
    """Individual transparency rating from user"""
    question: str
    system_response: str
    system_name: str
    user_id: str
    transparency_score: int  # 1-5 scale
    citation_helpful: bool
    uncertainty_helpful: bool
    trust_score: int  # 1-5 scale
    comments: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TransparencyStudyResults:
    """Aggregated results from transparency study"""
    total_participants: int
    total_responses: int
    avg_transparency_score: float
    avg_trust_score: float
    citation_helpful_rate: float
    uncertainty_helpful_rate: float
    system_comparison: Dict[str, Dict[str, float]]
    detailed_ratings: List[TransparencyRating]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_participants": self.total_participants,
            "total_responses": self.total_responses,
            "avg_transparency_score": self.avg_transparency_score,
            "avg_trust_score": self.avg_trust_score,
            "citation_helpful_rate": self.citation_helpful_rate,
            "uncertainty_helpful_rate": self.uncertainty_helpful_rate,
            "system_comparison": self.system_comparison,
            "detailed_ratings": [
                {
                    "question": r.question,
                    "system_name": r.system_name,
                    "transparency_score": r.transparency_score,
                    "trust_score": r.trust_score,
                    "citation_helpful": r.citation_helpful,
                    "uncertainty_helpful": r.uncertainty_helpful,
                    "comments": r.comments,
                    "timestamp": r.timestamp
                }
                for r in self.detailed_ratings
            ]
        }


class TransparencyStudy:
    """Framework for conducting transparency perception studies"""
    
    def __init__(self, data_path: str = "data/evaluation/transparency_study.json"):
        """
        Initialize transparency study framework
        
        Args:
            data_path: Path to store study data
        """
        self.data_path = data_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.ratings: List[TransparencyRating] = []
        self._load_data()
    
    def _load_data(self):
        """Load existing study data"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.ratings = [
                        TransparencyRating(**r) for r in data.get("ratings", [])
                    ]
                self.logger.info(f"Loaded {len(self.ratings)} existing ratings")
            except Exception as e:
                self.logger.warning(f"Error loading study data: {e}")
    
    def _save_data(self):
        """Save study data"""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump({"ratings": [r.__dict__ for r in self.ratings]}, f, indent=2)
    
    def add_rating(self, rating: TransparencyRating):
        """
        Add a transparency rating
        
        Args:
            rating: TransparencyRating object
        """
        self.ratings.append(rating)
        self._save_data()
        self.logger.info(f"Added rating from user {rating.user_id}")
    
    def get_results(self) -> TransparencyStudyResults:
        """
        Get aggregated study results
        
        Returns:
            TransparencyStudyResults with aggregated metrics
        """
        if not self.ratings:
            return TransparencyStudyResults(
                total_participants=0,
                total_responses=0,
                avg_transparency_score=0.0,
                avg_trust_score=0.0,
                citation_helpful_rate=0.0,
                uncertainty_helpful_rate=0.0,
                system_comparison={},
                detailed_ratings=[]
            )
        
        total = len(self.ratings)
        unique_users = len(set(r.user_id for r in self.ratings))
        
        avg_transparency = sum(r.transparency_score for r in self.ratings) / total
        avg_trust = sum(r.trust_score for r in self.ratings) / total
        citation_helpful_rate = sum(1 for r in self.ratings if r.citation_helpful) / total
        uncertainty_helpful_rate = sum(1 for r in self.ratings if r.uncertainty_helpful) / total
        
        # System comparison
        system_comparison = {}
        systems = set(r.system_name for r in self.ratings)
        for system in systems:
            system_ratings = [r for r in self.ratings if r.system_name == system]
            system_comparison[system] = {
                "avg_transparency": sum(r.transparency_score for r in system_ratings) / len(system_ratings),
                "avg_trust": sum(r.trust_score for r in system_ratings) / len(system_ratings),
                "citation_helpful_rate": sum(1 for r in system_ratings if r.citation_helpful) / len(system_ratings),
                "uncertainty_helpful_rate": sum(1 for r in system_ratings if r.uncertainty_helpful) / len(system_ratings),
                "count": len(system_ratings)
            }
        
        return TransparencyStudyResults(
            total_participants=unique_users,
            total_responses=total,
            avg_transparency_score=avg_transparency,
            avg_trust_score=avg_trust,
            citation_helpful_rate=citation_helpful_rate,
            uncertainty_helpful_rate=uncertainty_helpful_rate,
            system_comparison=system_comparison,
            detailed_ratings=self.ratings
        )
    
    def generate_study_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate study report
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        results = self.get_results()
        
        report_lines = [
            "# Transparency Perception User Study Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total Participants: {results.total_participants}",
            f"- Total Responses: {results.total_responses}",
            f"- Average Transparency Score: {results.avg_transparency_score:.2f}/5.0",
            f"- Average Trust Score: {results.avg_trust_score:.2f}/5.0",
            f"- Citation Helpful Rate: {results.citation_helpful_rate:.2%}",
            f"- Uncertainty Helpful Rate: {results.uncertainty_helpful_rate:.2%}",
            "",
            "## System Comparison",
            ""
        ]
        
        # System comparison table
        report_lines.append("| System | Avg Transparency | Avg Trust | Citation Helpful | Uncertainty Helpful | Responses |")
        report_lines.append("|--------|-----------------|-----------|-----------------|---------------------|-----------|")
        
        for system_name, metrics in results.system_comparison.items():
            report_lines.append(
                f"| {system_name} | {metrics['avg_transparency']:.2f}/5.0 | "
                f"{metrics['avg_trust']:.2f}/5.0 | {metrics['citation_helpful_rate']:.2%} | "
                f"{metrics['uncertainty_helpful_rate']:.2%} | {metrics['count']} |"
            )
        
        report = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"Study report saved to {output_path}")
        
        return report

