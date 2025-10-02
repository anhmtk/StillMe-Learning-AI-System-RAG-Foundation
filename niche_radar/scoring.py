#!/usr/bin/env python3
"""
🎯 NicheRadar Scoring - Intelligent Niche Scoring Module
======================================================

Chuẩn hoá tín hiệu → [0,1] hoặc z-score.
Tính NicheScore với công thức:
NicheScore = w1*TrendMomentum + w2*GHVelocity + w3*HNHeat +
             w4*NewsDelta + w5*RedditEngagement - w6*CompetitionProxy + w7*FeasibilityFit

Author: StillMe Framework Team
Version: 1.5.0
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .collectors import NicheRecord

logger = logging.getLogger(__name__)

@dataclass
class NicheScore:
    """Niche score with detailed breakdown"""
    topic: str
    total_score: float
    confidence: float
    breakdown: dict[str, float]
    sources: list[str]
    timestamp: datetime
    category: str
    feasibility_fit: float
    competition_proxy: float
    key_signals: list[str]
    recommendations: list[str]

class NicheScorer:
    """Main scoring engine for niche opportunities"""

    def __init__(self, weights_file: str = "policies/niche_weights.yaml"):
        self.logger = logging.getLogger("niche_radar.scoring")
        self.weights_file = weights_file
        self.weights = self._load_weights()

    def _load_weights(self) -> dict[str, Any]:
        """Load scoring weights from YAML file"""
        try:
            weights_path = Path(self.weights_file)
            if not weights_path.exists():
                self.logger.warning(f"⚠️ Weights file not found: {self.weights_file}, using defaults")
                return self._get_default_weights()

            with open(weights_path, encoding='utf-8') as f:
                weights = yaml.safe_load(f)

            self.logger.info(f"✅ Loaded scoring weights from {self.weights_file}")
            return weights

        except Exception as e:
            self.logger.error(f"❌ Failed to load weights: {e}, using defaults")
            return self._get_default_weights()

    def _get_default_weights(self) -> dict[str, Any]:
        """Get default weights if file loading fails"""
        return {
            "scoring_weights": {
                "trend_momentum": 0.20,
                "github_velocity": 0.15,
                "hackernews_heat": 0.10,
                "news_delta": 0.10,
                "reddit_engagement": 0.05,
                "competition_proxy": 0.15,
                "feasibility_fit": 0.25
            },
            "normalization": {
                "github_velocity": {"mean": 5.0, "std": 10.0, "max_cap": 50.0},
                "hackernews_heat": {"mean": 50.0, "std": 100.0, "max_cap": 500.0},
                "news_delta": {"mean": 0.5, "std": 0.3, "max_cap": 1.0},
                "reddit_engagement": {"mean": 25.0, "std": 50.0, "max_cap": 200.0},
                "google_trends": {"mean": 50.0, "std": 25.0, "max_cap": 100.0}
            },
            "stillme_capabilities": {
                "high_fit": ["ai_assistant", "nlp_processing", "translation", "content_generation"],
                "medium_fit": ["web_scraping", "monitoring", "notification", "scheduling"],
                "low_fit": ["mobile_app", "game_development", "graphics_design", "video_editing"]
            }
        }

    def normalize_signal(self, value: float, signal_type: str, method: str = "z_score") -> float:
        """Normalize signal to [0,1] range"""
        try:
            if method == "z_score":
                norm_params = self.weights.get("normalization", {}).get(signal_type, {})
                mean = norm_params.get("mean", 0.0)
                std = norm_params.get("std", 1.0)
                max_cap = norm_params.get("max_cap", 100.0)

                # Cap the value
                capped_value = min(value, max_cap)

                # Calculate z-score
                z_score = (capped_value - mean) / std if std > 0 else 0.0

                # Convert to [0,1] using sigmoid
                normalized = 1 / (1 + math.exp(-z_score))

                return max(0.0, min(1.0, normalized))

            elif method == "min_max":
                # Simple min-max normalization (assumes value is already in reasonable range)
                return max(0.0, min(1.0, value / 100.0))

            else:
                return max(0.0, min(1.0, value))

        except Exception as e:
            self.logger.error(f"❌ Signal normalization failed for {signal_type}: {e}")
            return 0.0

    def calculate_feasibility_fit(self, topic: str, records: list[NicheRecord]) -> float:
        """Calculate how well the niche fits StillMe capabilities"""
        try:
            # Extract keywords from topic and records
            keywords = [topic.lower()]
            for record in records:
                title_words = record.title.lower().split()
                keywords.extend(title_words[:5])  # First 5 words

            # Get capability mappings
            capabilities = self.weights.get("stillme_capabilities", {})
            high_fit = capabilities.get("high_fit", [])
            medium_fit = capabilities.get("medium_fit", [])
            low_fit = capabilities.get("low_fit", [])

            # Calculate fit score
            fit_score = 0.0
            total_matches = 0

            for keyword in keywords:
                keyword = keyword.strip(".,!?")

                # Check high fit
                if any(cap in keyword for cap in high_fit):
                    fit_score += 0.9
                    total_matches += 1
                # Check medium fit
                elif any(cap in keyword for cap in medium_fit):
                    fit_score += 0.6
                    total_matches += 1
                # Check low fit
                elif any(cap in keyword for cap in low_fit):
                    fit_score += 0.3
                    total_matches += 1

            # Average fit score
            if total_matches > 0:
                return fit_score / total_matches
            else:
                # Default to medium fit if no matches
                return 0.5

        except Exception as e:
            self.logger.error(f"❌ Feasibility calculation failed: {e}")
            return 0.5

    def calculate_competition_proxy(self, topic: str, records: list[NicheRecord]) -> float:
        """Calculate competition proxy (higher = more competition)"""
        try:
            # Extract keywords
            keywords = [topic.lower()]
            for record in records:
                title_words = record.title.lower().split()
                keywords.extend(title_words[:3])

            # Get competition mappings
            competition = self.weights.get("competition_analysis", {})
            high_comp = competition.get("high_competition_keywords", [])
            medium_comp = competition.get("medium_competition_keywords", [])
            low_comp = competition.get("low_competition_keywords", [])

            # Calculate competition score
            comp_score = 0.0
            total_matches = 0

            for keyword in keywords:
                keyword = keyword.strip(".,!?")

                if any(comp in keyword for comp in high_comp):
                    comp_score += 0.9
                    total_matches += 1
                elif any(comp in keyword for comp in medium_comp):
                    comp_score += 0.6
                    total_matches += 1
                elif any(comp in keyword for comp in low_comp):
                    comp_score += 0.3
                    total_matches += 1

            if total_matches > 0:
                return comp_score / total_matches
            else:
                return 0.5  # Default medium competition

        except Exception as e:
            self.logger.error(f"❌ Competition calculation failed: {e}")
            return 0.5

    def calculate_confidence(self, records: list[NicheRecord]) -> float:
        """Calculate confidence based on source coverage and consistency"""
        try:
            if not records:
                return 0.0

            # Source coverage (0.4 weight)
            unique_sources = len({record.source for record in records})
            max_sources = 5  # We have 5 collectors
            source_coverage = min(unique_sources / max_sources, 1.0)

            # Signal consistency (0.3 weight)
            if len(records) > 1:
                scores = [record.confidence for record in records]
                mean_score = sum(scores) / len(scores)
                variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
                consistency = max(0.0, 1.0 - variance)
            else:
                consistency = records[0].confidence if records else 0.0

            # Data freshness (0.2 weight)
            now = datetime.now()
            freshness_scores = []
            for record in records:
                age_hours = (now - record.timestamp).total_seconds() / 3600
                freshness = max(0.0, 1.0 - (age_hours / 72.0))  # 72 hours max
                freshness_scores.append(freshness)
            data_freshness = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.0

            # Source credibility (0.1 weight)
            credibility_scores = []
            for record in records:
                cred_map = {
                    "GitHub": 0.9,
                    "Hacker News": 0.8,
                    "Google Trends": 0.9,
                    "Reddit": 0.6,
                    "News": 0.7
                }
                credibility_scores.append(cred_map.get(record.source, 0.5))
            source_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 0.5

            # Weighted confidence
            confidence = (
                0.4 * source_coverage +
                0.3 * consistency +
                0.2 * data_freshness +
                0.1 * source_credibility
            )

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"❌ Confidence calculation failed: {e}")
            return 0.5

    def score_niche(self, topic: str, records: list[NicheRecord]) -> NicheScore:
        """Calculate comprehensive niche score"""
        try:
            self.logger.info(f"🎯 Scoring niche: {topic} with {len(records)} records")

            if not records:
                return NicheScore(
                    topic=topic,
                    total_score=0.0,
                    confidence=0.0,
                    breakdown={},
                    sources=[],
                    timestamp=datetime.now(),
                    category="unknown",
                    feasibility_fit=0.0,
                    competition_proxy=0.0,
                    key_signals=[],
                    recommendations=[]
                )

            # Group records by source
            source_groups = {}
            for record in records:
                if record.source not in source_groups:
                    source_groups[record.source] = []
                source_groups[record.source].append(record)

            # Calculate individual signal scores
            scoring_weights = self.weights.get("scoring_weights", {})

            # Trend momentum (Google Trends)
            trend_momentum = 0.0
            if "Google Trends" in source_groups:
                trend_records = source_groups["Google Trends"]
                momentum_scores = [r.metrics.get("momentum_score", 0.0) for r in trend_records]
                trend_momentum = sum(momentum_scores) / len(momentum_scores) if momentum_scores else 0.0

            # GitHub velocity
            github_velocity = 0.0
            if "GitHub" in source_groups:
                github_records = source_groups["GitHub"]
                velocity_scores = [r.metrics.get("trending_score", 0.0) for r in github_records]
                github_velocity = sum(velocity_scores) / len(velocity_scores) if velocity_scores else 0.0

            # Hacker News heat
            hackernews_heat = 0.0
            if "Hacker News" in source_groups:
                hn_records = source_groups["Hacker News"]
                heat_scores = [r.metrics.get("heat_score", 0.0) for r in hn_records]
                hackernews_heat = sum(heat_scores) / len(heat_scores) if heat_scores else 0.0

            # News delta
            news_delta = 0.0
            if "News" in source_groups or any("News" in source for source in source_groups.keys()):
                news_records = []
                for source, records_list in source_groups.items():
                    if "News" in source:
                        news_records.extend(records_list)
                if news_records:
                    delta_scores = [r.metrics.get("delta_score", 0.0) for r in news_records]
                    news_delta = sum(delta_scores) / len(delta_scores) if delta_scores else 0.0

            # Reddit engagement
            reddit_engagement = 0.0
            if "Reddit" in source_groups:
                reddit_records = source_groups["Reddit"]
                engagement_scores = [r.metrics.get("engagement_score", 0.0) for r in reddit_records]
                reddit_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0

            # Calculate feasibility fit and competition proxy
            feasibility_fit = self.calculate_feasibility_fit(topic, records)
            competition_proxy = self.calculate_competition_proxy(topic, records)

            # Calculate total score using weighted formula
            total_score = (
                scoring_weights.get("trend_momentum", 0.20) * trend_momentum +
                scoring_weights.get("github_velocity", 0.15) * github_velocity +
                scoring_weights.get("hackernews_heat", 0.10) * hackernews_heat +
                scoring_weights.get("news_delta", 0.10) * news_delta +
                scoring_weights.get("reddit_engagement", 0.05) * reddit_engagement +
                scoring_weights.get("feasibility_fit", 0.25) * feasibility_fit -
                scoring_weights.get("competition_proxy", 0.15) * competition_proxy
            )

            # Ensure score is in [0,1] range
            total_score = max(0.0, min(1.0, total_score))

            # Calculate confidence
            confidence = self.calculate_confidence(records)

            # Create breakdown
            breakdown = {
                "trend_momentum": trend_momentum,
                "github_velocity": github_velocity,
                "hackernews_heat": hackernews_heat,
                "news_delta": news_delta,
                "reddit_engagement": reddit_engagement,
                "feasibility_fit": feasibility_fit,
                "competition_proxy": competition_proxy
            }

            # Identify key signals
            key_signals = []
            if trend_momentum > 0.7:
                key_signals.append("High Google Trends momentum")
            if github_velocity > 0.7:
                key_signals.append("Strong GitHub velocity")
            if hackernews_heat > 0.7:
                key_signals.append("High Hacker News engagement")
            if feasibility_fit > 0.8:
                key_signals.append("Excellent StillMe fit")
            if competition_proxy < 0.3:
                key_signals.append("Low competition")

            # Generate recommendations
            recommendations = []
            if feasibility_fit > 0.7:
                recommendations.append("High feasibility for StillMe implementation")
            if competition_proxy < 0.4:
                recommendations.append("Low competition - good opportunity")
            if total_score > 0.7:
                recommendations.append("Strong overall signal - prioritize")
            if confidence > 0.8:
                recommendations.append("High confidence data - reliable signals")

            # Determine category
            category = "general"
            if feasibility_fit > 0.8:
                category = "high_fit"
            elif feasibility_fit > 0.5:
                category = "medium_fit"
            else:
                category = "low_fit"

            return NicheScore(
                topic=topic,
                total_score=total_score,
                confidence=confidence,
                breakdown=breakdown,
                sources=list(source_groups.keys()),
                timestamp=datetime.now(),
                category=category,
                feasibility_fit=feasibility_fit,
                competition_proxy=competition_proxy,
                key_signals=key_signals,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"❌ Niche scoring failed for {topic}: {e}")
            return NicheScore(
                topic=topic,
                total_score=0.0,
                confidence=0.0,
                breakdown={},
                sources=[],
                timestamp=datetime.now(),
                category="error",
                feasibility_fit=0.0,
                competition_proxy=0.0,
                key_signals=[],
                recommendations=[]
            )

def calculate_confidence(records: list[NicheRecord]) -> float:
    """Standalone confidence calculation function"""
    scorer = NicheScorer()
    return scorer.calculate_confidence(records)

if __name__ == "__main__":
    # Test scoring
    from .collectors import NicheRecord

    # Create test records
    test_records = [
        NicheRecord(
            source="GitHub",
            url="https://github.com/test/repo",
            title="AI Assistant Framework",
            timestamp=datetime.now(),
            metrics={"trending_score": 0.8, "stars": 1000},
            raw={},
            topic="ai_assistant",
            category="development",
            confidence=0.9
        ),
        NicheRecord(
            source="Hacker News",
            url="https://news.ycombinator.com/item?id=123",
            title="New AI Assistant Tools",
            timestamp=datetime.now(),
            metrics={"heat_score": 0.7, "score": 150},
            raw={},
            topic="ai_assistant",
            category="tech_news",
            confidence=0.8
        )
    ]

    scorer = NicheScorer()
    score = scorer.score_niche("ai_assistant", test_records)

    print("🎯 Niche Score for 'ai_assistant':")
    print(f"  Total Score: {score.total_score:.3f}")
    print(f"  Confidence: {score.confidence:.3f}")
    print(f"  Feasibility Fit: {score.feasibility_fit:.3f}")
    print(f"  Competition Proxy: {score.competition_proxy:.3f}")
    print(f"  Key Signals: {score.key_signals}")
    print(f"  Recommendations: {score.recommendations}")
