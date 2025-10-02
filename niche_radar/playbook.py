#!/usr/bin/env python3
"""
🎯 NicheRadar Playbook - Time-to-First-Dollar Execution Pack
===========================================================

Sinh "execution pack" cho mỗi cơ hội niche:
- Product Brief: persona, pain points, JTBD, USP
- MVP Spec (1–2 tuần): feature list, kiến trúc tối giản, dependency
- Pricing Suggestion: tier Basic/Pro/Team + rationales
- Assets: Landing skeleton, Repo scaffold, Email/DM outreach template

Author: StillMe Framework Team
Version: 1.5.0
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scoring import NicheScore

logger = logging.getLogger(__name__)

@dataclass
class Persona:
    """Target user persona"""
    name: str
    role: str
    company_size: str
    pain_points: List[str]
    goals: List[str]
    tech_stack: List[str]
    budget_range: str

@dataclass
class ProductBrief:
    """Product brief for niche opportunity"""
    title: str
    description: str
    personas: List[Persona]
    pain_points: List[str]
    jobs_to_be_done: List[str]
    unique_selling_proposition: str
    target_market: str
    competitive_advantage: str

@dataclass
class Feature:
    """MVP feature specification"""
    name: str
    description: str
    priority: str  # "must_have", "should_have", "nice_to_have"
    effort_days: int
    dependencies: List[str]
    stillme_capability: str

@dataclass
class MVPSpec:
    """MVP specification"""
    name: str
    description: str
    features: List[Feature]
    architecture: Dict[str, Any]
    tech_stack: List[str]
    estimated_development_days: int
    dependencies: List[str]
    deployment_requirements: List[str]

@dataclass
class PricingTier:
    """Pricing tier specification"""
    name: str
    price: float
    currency: str
    features: List[str]
    target_users: str
    rationale: str

@dataclass
class PricingSuggestion:
    """Pricing strategy suggestion"""
    tiers: List[PricingTier]
    pricing_model: str  # "subscription", "usage", "one_time"
    free_tier: bool
    trial_period_days: int
    rationale: str
    revenue_projections: Dict[str, float]

@dataclass
class LandingPageSpec:
    """Landing page specification"""
    headline: str
    subheadline: str
    value_propositions: List[str]
    features: List[str]
    testimonials: List[str]
    cta_text: str
    design_tokens: Dict[str, str]

@dataclass
class RepoScaffold:
    """Repository scaffold specification"""
    name: str
    description: str
    tech_stack: List[str]
    structure: Dict[str, List[str]]
    readme_template: str
    license: str
    initial_commits: List[str]

@dataclass
class OutreachTemplate:
    """Email/DM outreach template"""
    subject: str
    body: str
    language: str  # "en" or "vi"
    personalization_placeholders: List[str]
    call_to_action: str

@dataclass
class ExecutionPack:
    """Complete execution pack for niche opportunity"""
    niche_score: NicheScore
    product_brief: ProductBrief
    mvp_spec: MVPSpec
    pricing_suggestion: PricingSuggestion
    landing_page_spec: LandingPageSpec
    repo_scaffold: RepoScaffold
    outreach_templates: List[OutreachTemplate]
    risk_assessment: Dict[str, Any]
    compliance_notes: List[str]
    kpis: List[str]
    timeline: Dict[str, str]

class PlaybookGenerator:
    """Generate execution playbooks for niche opportunities"""

    def __init__(self):
        self.logger = logging.getLogger("niche_radar.playbook")

    def generate_playbook(self, niche_score: NicheScore) -> ExecutionPack:
        """Generate complete execution pack for niche opportunity"""
        try:
            self.logger.info(f"📋 Generating playbook for niche: {niche_score.topic}")

            # Generate each component
            product_brief = self._generate_product_brief(niche_score)
            mvp_spec = self._generate_mvp_spec(niche_score, product_brief)
            pricing_suggestion = self._generate_pricing_suggestion(niche_score, mvp_spec)
            landing_page_spec = self._generate_landing_page_spec(niche_score, product_brief)
            repo_scaffold = self._generate_repo_scaffold(niche_score, mvp_spec)
            outreach_templates = self._generate_outreach_templates(niche_score, product_brief)
            risk_assessment = self._generate_risk_assessment(niche_score)
            compliance_notes = self._generate_compliance_notes(niche_score)
            kpis = self._generate_kpis(niche_score)
            timeline = self._generate_timeline(niche_score, mvp_spec)

            return ExecutionPack(
                niche_score=niche_score,
                product_brief=product_brief,
                mvp_spec=mvp_spec,
                pricing_suggestion=pricing_suggestion,
                landing_page_spec=landing_page_spec,
                repo_scaffold=repo_scaffold,
                outreach_templates=outreach_templates,
                risk_assessment=risk_assessment,
                compliance_notes=compliance_notes,
                kpis=kpis,
                timeline=timeline
            )

        except Exception as e:
            self.logger.error(f"❌ Playbook generation failed: {e}")
            raise

    def _generate_product_brief(self, niche_score: NicheScore) -> ProductBrief:
        """Generate product brief"""
        topic = niche_score.topic

        # Generate personas based on topic
        personas = self._generate_personas(topic)

        # Generate pain points
        pain_points = self._generate_pain_points(topic, niche_score)

        # Generate jobs to be done
        jobs_to_be_done = self._generate_jobs_to_be_done(topic, pain_points)

        # Generate USP
        usp = self._generate_usp(topic, niche_score)

        return ProductBrief(
            title=f"{topic.title()} Assistant",
            description=f"AI-powered {topic} assistant built with StillMe framework",
            personas=personas,
            pain_points=pain_points,
            jobs_to_be_done=jobs_to_be_done,
            unique_selling_proposition=usp,
            target_market=self._determine_target_market(topic),
            competitive_advantage=f"Built on StillMe's proven AI framework with {niche_score.feasibility_fit:.0%} capability fit"
        )

    def _generate_personas(self, topic: str) -> List[Persona]:
        """Generate target personas"""
        personas = []

        if "ai" in topic.lower() or "assistant" in topic.lower():
            personas.append(Persona(
                name="Sarah Chen",
                role="Product Manager",
                company_size="50-200 employees",
                pain_points=[
                    "Manual data analysis takes too long",
                    "Need quick insights for decision making",
                    "Struggling with repetitive tasks"
                ],
                goals=[
                    "Automate routine analysis",
                    "Get instant insights",
                    "Focus on strategic work"
                ],
                tech_stack=["Python", "SQL", "Jupyter", "Slack"],
                budget_range="$100-500/month"
            ))

        if "translation" in topic.lower():
            personas.append(Persona(
                name="Marco Rodriguez",
                role="Content Manager",
                company_size="10-50 employees",
                pain_points=[
                    "Expensive translation services",
                    "Slow turnaround times",
                    "Quality inconsistencies"
                ],
                goals=[
                    "Fast, accurate translations",
                    "Cost-effective solution",
                    "Easy integration"
                ],
                tech_stack=["WordPress", "CMS", "API"],
                budget_range="$50-200/month"
            ))

        # Default persona if no specific match
        if not personas:
            personas.append(Persona(
                name="Alex Developer",
                role="Software Developer",
                company_size="1-10 employees",
                pain_points=[
                    "Need to automate repetitive tasks",
                    "Want to focus on core development",
                    "Limited time for tool research"
                ],
                goals=[
                    "Increase productivity",
                    "Automate workflows",
                    "Quick implementation"
                ],
                tech_stack=["Python", "JavaScript", "API"],
                budget_range="$25-100/month"
            ))

        return personas

    def _generate_pain_points(self, topic: str, niche_score: NicheScore) -> List[str]:
        """Generate pain points based on topic and signals"""
        pain_points = []

        # Base pain points by topic
        if "ai" in topic.lower():
            pain_points.extend([
                "Manual processes are time-consuming",
                "Need intelligent automation",
                "Lack of AI expertise in team"
            ])

        if "translation" in topic.lower():
            pain_points.extend([
                "Expensive human translation",
                "Slow turnaround times",
                "Quality inconsistencies"
            ])

        if "automation" in topic.lower():
            pain_points.extend([
                "Repetitive tasks waste time",
                "Manual processes are error-prone",
                "Need reliable automation"
            ])

        # Add pain points based on competition proxy
        if niche_score.competition_proxy > 0.7:
            pain_points.append("Existing solutions are too complex or expensive")
        elif niche_score.competition_proxy < 0.3:
            pain_points.append("No good solutions exist in the market")

        return pain_points[:5]  # Limit to 5 pain points

    def _generate_jobs_to_be_done(self, topic: str, pain_points: List[str]) -> List[str]:
        """Generate jobs to be done"""
        jobs = []

        for pain_point in pain_points:
            if "time" in pain_point.lower():
                jobs.append("Save time on repetitive tasks")
            elif "cost" in pain_point.lower() or "expensive" in pain_point.lower():
                jobs.append("Reduce operational costs")
            elif "quality" in pain_point.lower():
                jobs.append("Improve output quality and consistency")
            elif "complex" in pain_point.lower():
                jobs.append("Simplify complex processes")
            elif "manual" in pain_point.lower():
                jobs.append("Automate manual processes")

        # Add default jobs
        jobs.extend([
            "Get work done faster and more efficiently",
            "Focus on high-value activities",
            "Reduce errors and improve reliability"
        ])

        return list(set(jobs))[:5]  # Remove duplicates and limit to 5

    def _generate_usp(self, topic: str, niche_score: NicheScore) -> str:
        """Generate unique selling proposition"""
        if niche_score.feasibility_fit > 0.8:
            return f"Built on StillMe's proven AI framework - {topic} automation that actually works, implemented in days not months"
        elif niche_score.competition_proxy < 0.3:
            return f"First-to-market {topic} solution with StillMe's enterprise-grade AI capabilities"
        else:
            return f"StillMe-powered {topic} assistant - faster, smarter, more reliable than existing solutions"

    def _determine_target_market(self, topic: str) -> str:
        """Determine target market"""
        if "enterprise" in topic.lower() or "b2b" in topic.lower():
            return "B2B Enterprise (100+ employees)"
        elif "startup" in topic.lower() or "small" in topic.lower():
            return "B2B SMB (10-100 employees)"
        else:
            return "B2B SMB to Mid-market (10-500 employees)"

    def _generate_mvp_spec(self, niche_score: NicheScore, product_brief: ProductBrief) -> MVPSpec:
        """Generate MVP specification"""
        topic = niche_score.topic

        # Generate features based on feasibility fit
        features = []

        if niche_score.feasibility_fit > 0.8:
            # High fit - can implement advanced features
            features.extend([
                Feature(
                    name="Core AI Processing",
                    description=f"Main {topic} processing engine",
                    priority="must_have",
                    effort_days=3,
                    dependencies=[],
                    stillme_capability="ai_processing"
                ),
                Feature(
                    name="API Integration",
                    description="RESTful API for integration",
                    priority="must_have",
                    effort_days=2,
                    dependencies=["Core AI Processing"],
                    stillme_capability="api_integration"
                ),
                Feature(
                    name="Web Interface",
                    description="Simple web interface",
                    priority="should_have",
                    effort_days=2,
                    dependencies=["API Integration"],
                    stillme_capability="web_interface"
                ),
                Feature(
                    name="Batch Processing",
                    description="Process multiple items at once",
                    priority="nice_to_have",
                    effort_days=1,
                    dependencies=["Core AI Processing"],
                    stillme_capability="batch_processing"
                )
            ])
        else:
            # Lower fit - simpler features
            features.extend([
                Feature(
                    name="Basic Processing",
                    description=f"Basic {topic} functionality",
                    priority="must_have",
                    effort_days=2,
                    dependencies=[],
                    stillme_capability="basic_processing"
                ),
                Feature(
                    name="Simple API",
                    description="Basic API endpoint",
                    priority="must_have",
                    effort_days=1,
                    dependencies=["Basic Processing"],
                    stillme_capability="api_integration"
                )
            ])

        # Calculate total development days
        total_days = sum(f.effort_days for f in features if f.priority == "must_have")

        return MVPSpec(
            name=f"{topic.title()} Assistant MVP",
            description=f"Minimum viable product for {topic} automation",
            features=features,
            architecture={
                "backend": "StillMe Framework + FastAPI",
                "frontend": "React + Tailwind CSS",
                "database": "SQLite (development) / PostgreSQL (production)",
                "deployment": "Docker + Railway/Render"
            },
            tech_stack=["Python", "FastAPI", "React", "Tailwind CSS", "SQLite"],
            estimated_development_days=total_days,
            dependencies=["StillMe Framework", "OpenRouter API"],
            deployment_requirements=["Docker", "Domain", "SSL Certificate"]
        )

    def _generate_pricing_suggestion(self, niche_score: NicheScore, mvp_spec: MVPSpec) -> PricingSuggestion:
        """Generate pricing suggestion"""
        # Base pricing on feasibility fit and competition
        base_price = 29.0

        if niche_score.feasibility_fit > 0.8:
            base_price = 49.0
        elif niche_score.feasibility_fit < 0.5:
            base_price = 19.0

        if niche_score.competition_proxy > 0.7:
            base_price *= 0.8  # Price lower due to competition
        elif niche_score.competition_proxy < 0.3:
            base_price *= 1.2  # Price higher due to uniqueness

        tiers = [
            PricingTier(
                name="Starter",
                price=base_price * 0.5,
                currency="USD",
                features=[
                    "Basic processing",
                    "100 requests/month",
                    "Email support"
                ],
                target_users="Individual users",
                rationale="Low barrier to entry for testing"
            ),
            PricingTier(
                name="Professional",
                price=base_price,
                currency="USD",
                features=[
                    "Full feature set",
                    "1000 requests/month",
                    "API access",
                    "Priority support"
                ],
                target_users="Small teams",
                rationale="Main revenue tier for active users"
            ),
            PricingTier(
                name="Business",
                price=base_price * 2.0,
                currency="USD",
                features=[
                    "Unlimited requests",
                    "Custom integrations",
                    "Dedicated support",
                    "SLA guarantee"
                ],
                target_users="Growing businesses",
                rationale="Premium tier for enterprise features"
            )
        ]

        return PricingSuggestion(
            tiers=tiers,
            pricing_model="subscription",
            free_tier=True,
            trial_period_days=14,
            rationale=f"Subscription model provides predictable revenue. Free tier for user acquisition. Pricing based on {niche_score.feasibility_fit:.0%} feasibility fit and {niche_score.competition_proxy:.0%} competition level.",
            revenue_projections={
                "month_1": 0,
                "month_3": base_price * 10,
                "month_6": base_price * 50,
                "month_12": base_price * 200
            }
        )

    def _generate_landing_page_spec(self, niche_score: NicheScore, product_brief: ProductBrief) -> LandingPageSpec:
        """Generate landing page specification"""
        return LandingPageSpec(
            headline=f"Automate {niche_score.topic.title()} with AI",
            subheadline=f"StillMe-powered {niche_score.topic} assistant that saves you hours every day",
            value_propositions=[
                "Built on proven StillMe AI framework",
                f"{niche_score.feasibility_fit:.0%} capability fit - designed for this exact use case",
                "Deploy in days, not months",
                "Enterprise-grade reliability"
            ],
            features=[
                "Intelligent processing",
                "Easy API integration",
                "Real-time results",
                "Scalable architecture"
            ],
            testimonials=[
                "Finally, an AI tool that actually works for our use case!",
                "Saved us 10 hours per week from day one.",
                "Easy to integrate and reliable."
            ],
            cta_text="Start Free Trial",
            design_tokens={
                "primary_color": "#6366f1",
                "secondary_color": "#8b5cf6",
                "accent_color": "#06b6d4",
                "text_color": "#1f2937",
                "background_color": "#ffffff"
            }
        )

    def _generate_repo_scaffold(self, niche_score: NicheScore, mvp_spec: MVPSpec) -> RepoScaffold:
        """Generate repository scaffold"""
        topic = niche_score.topic
        repo_name = f"{topic.replace(' ', '-')}-assistant"

        return RepoScaffold(
            name=repo_name,
            description=f"AI-powered {topic} assistant built with StillMe framework",
            tech_stack=mvp_spec.tech_stack,
            structure={
                "backend": ["main.py", "models/", "api/", "services/"],
                "frontend": ["src/", "public/", "package.json"],
                "docs": ["README.md", "API.md", "DEPLOYMENT.md"],
                "tests": ["test_backend.py", "test_api.py"],
                "deployment": ["Dockerfile", "docker-compose.yml", ".env.example"]
            },
            readme_template=f"""# {topic.title()} Assistant

AI-powered {topic} assistant built with StillMe framework.

## Features

- Intelligent {topic} processing
- RESTful API
- Web interface
- Easy deployment

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run: `python main.py`

## API Documentation

See [API.md](API.md) for detailed API documentation.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

## License

MIT License - see [LICENSE](LICENSE) file.
""",
            license="MIT",
            initial_commits=[
                "Initial commit with StillMe framework integration",
                "Add basic API endpoints",
                "Add web interface",
                "Add deployment configuration"
            ]
        )

    def _generate_outreach_templates(self, niche_score: NicheScore, product_brief: ProductBrief) -> List[OutreachTemplate]:
        """Generate outreach templates"""
        templates = []

        # English template
        templates.append(OutreachTemplate(
            subject=f"Quick question about {niche_score.topic} automation",
            body=f"""Hi {{name}},

I noticed you're working on {{company}} and might be dealing with {niche_score.topic} challenges.

I just built a {niche_score.topic} assistant using StillMe's AI framework that could save you hours per week. It's specifically designed for your use case with {niche_score.feasibility_fit:.0%} capability fit.

Would you be interested in a quick 15-minute demo? No strings attached.

Best regards,
{{sender_name}}

P.S. Here's a quick preview: {{demo_link}}""",
            language="en",
            personalization_placeholders=["name", "company", "sender_name", "demo_link"],
            call_to_action="Schedule a 15-minute demo"
        ))

        # Vietnamese template
        templates.append(OutreachTemplate(
            subject=f"Câu hỏi nhanh về tự động hóa {niche_score.topic}",
            body=f"""Chào {{name}},

Tôi thấy bạn đang làm việc tại {{company}} và có thể đang gặp thách thức với {niche_score.topic}.

Tôi vừa xây dựng một trợ lý {niche_score.topic} sử dụng framework AI StillMe có thể tiết kiệm cho bạn hàng giờ mỗi tuần. Nó được thiết kế đặc biệt cho trường hợp sử dụng của bạn với {niche_score.feasibility_fit:.0%} khả năng phù hợp.

Bạn có quan tâm đến một demo nhanh 15 phút không? Không có ràng buộc gì.

Trân trọng,
{{sender_name}}

P.S. Đây là bản xem trước nhanh: {{demo_link}}""",
            language="vi",
            personalization_placeholders=["name", "company", "sender_name", "demo_link"],
            call_to_action="Đặt lịch demo 15 phút"
        ))

        return templates

    def _generate_risk_assessment(self, niche_score: NicheScore) -> Dict[str, Any]:
        """Generate risk assessment"""
        risks = []

        if niche_score.competition_proxy > 0.7:
            risks.append({
                "risk": "High competition",
                "impact": "Medium",
                "probability": "High",
                "mitigation": "Focus on unique StillMe capabilities and faster implementation"
            })

        if niche_score.confidence < 0.6:
            risks.append({
                "risk": "Low data confidence",
                "impact": "High",
                "probability": "Medium",
                "mitigation": "Validate with additional market research before full commitment"
            })

        if niche_score.feasibility_fit < 0.5:
            risks.append({
                "risk": "Low feasibility fit",
                "impact": "High",
                "probability": "Medium",
                "mitigation": "Consider simpler implementation or pivot to higher-fit features"
            })

        return {
            "overall_risk_level": "Medium" if len(risks) <= 2 else "High",
            "risks": risks,
            "recommendations": [
                "Start with MVP to validate market demand",
                "Focus on unique StillMe capabilities",
                "Monitor competition closely",
                "Build strong user feedback loop"
            ]
        }

    def _generate_compliance_notes(self, niche_score: NicheScore) -> List[str]:
        """Generate compliance notes"""
        notes = [
            "Ensure all data processing complies with GDPR/CCPA",
            "Implement proper data retention policies",
            "Add privacy policy and terms of service",
            "Consider data residency requirements for target markets",
            "Implement proper API rate limiting and abuse prevention",
            "Ensure all third-party integrations have proper agreements"
        ]

        if "translation" in niche_score.topic.lower():
            notes.extend([
                "Consider translation quality guarantees",
                "Implement content moderation for translated text",
                "Ensure compliance with language-specific regulations"
            ])

        return notes

    def _generate_kpis(self, niche_score: NicheScore) -> List[str]:
        """Generate KPIs for tracking"""
        return [
            "Leads per day (target: 5-10)",
            "Signups per day (target: 2-5)",
            "Trial-to-paid conversion rate (target: 15-25%)",
            "Monthly recurring revenue growth (target: 20%)",
            "Customer acquisition cost (target: <$50)",
            "Time to first value (target: <24 hours)",
            "User engagement score (target: >70%)",
            "Support ticket volume (target: <5% of users)"
        ]

    def _generate_timeline(self, niche_score: NicheScore, mvp_spec: MVPSpec) -> Dict[str, str]:
        """Generate development timeline"""
        start_date = datetime.now()

        return {
            "Week 1": "Core development and API setup",
            "Week 2": "Frontend development and testing",
            "Week 3": "Integration testing and deployment",
            "Week 4": "User testing and feedback collection",
            "Month 2": "Iteration based on feedback",
            "Month 3": "Scale and optimize"
        }

if __name__ == "__main__":
    # Test playbook generation
    from .scoring import NicheScore

    # Create test niche score
    test_score = NicheScore(
        topic="ai_translation",
        total_score=0.75,
        confidence=0.8,
        breakdown={"feasibility_fit": 0.9, "competition_proxy": 0.4},
        sources=["GitHub", "Hacker News"],
        timestamp=datetime.now(),
        category="high_fit",
        feasibility_fit=0.9,
        competition_proxy=0.4,
        key_signals=["High feasibility fit", "Low competition"],
        recommendations=["High feasibility for StillMe implementation"]
    )

    generator = PlaybookGenerator()
    playbook = generator.generate_playbook(test_score)

    print(f"📋 Generated playbook for: {playbook.niche_score.topic}")
    print(f"  MVP Development Days: {playbook.mvp_spec.estimated_development_days}")
    print(f"  Pricing Tiers: {len(playbook.pricing_suggestion.tiers)}")
    print(f"  Risk Level: {playbook.risk_assessment['overall_risk_level']}")
    print(f"  KPIs: {len(playbook.kpis)}")
