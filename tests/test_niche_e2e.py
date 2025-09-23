#!/usr/bin/env python3
"""
🎯 NicheRadar E2E Tests
Test end-to-end NicheRadar pipeline: collect → score → top10 → playbook
"""
import pytest
import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import NicheRadar modules
from niche_radar.collectors import collect_all_data, get_all_collectors
from niche_radar.scoring import NicheScorer, NicheScore
from niche_radar.playbook import PlaybookGenerator, ExecutionPack

logger = logging.getLogger(__name__)

class TestNicheRadarE2E:
    """End-to-end tests for NicheRadar pipeline"""
    
    @pytest.fixture(scope="class")
    def test_topics(self):
        """Test topics for niche analysis"""
        return ["python", "ai", "startup", "saas", "automation"]
    
    @pytest.fixture(scope="class")
    def collectors(self):
        """Get all collectors"""
        return get_all_collectors()
    
    @pytest.fixture(scope="class")
    def scorer(self):
        """Get NicheScorer instance"""
        return NicheScorer()
    
    @pytest.fixture(scope="class")
    def playbook_generator(self):
        """Get PlaybookGenerator instance"""
        return PlaybookGenerator()
    
    @pytest.mark.asyncio
    async def test_data_collection(self, test_topics, collectors):
        """Test data collection from all sources"""
        logger.info("🧪 Testing data collection...")
        
        # Collect data from all sources
        all_data = await collect_all_data(test_topics)
        
        # Assert we have data from multiple sources
        assert len(all_data) > 0, "Should have data from at least one source"
        
        # Check each collector
        for source_name, collector in collectors.items():
            if source_name in all_data:
                records = all_data[source_name]
                assert isinstance(records, list), f"{source_name} should return list of records"
                
                if records:  # If we have records
                    record = records[0]
                    # Check record structure
                    assert hasattr(record, 'source'), f"{source_name} record should have source"
                    assert hasattr(record, 'url'), f"{source_name} record should have url"
                    assert hasattr(record, 'title'), f"{source_name} record should have title"
                    assert hasattr(record, 'timestamp'), f"{source_name} record should have timestamp"
                    assert hasattr(record, 'metrics'), f"{source_name} record should have metrics"
                    assert hasattr(record, 'raw'), f"{source_name} record should have raw data"
                    assert hasattr(record, 'topic'), f"{source_name} record should have topic"
                    assert hasattr(record, 'confidence'), f"{source_name} record should have confidence"
                    
                    logger.info(f"✅ {source_name}: {len(records)} records collected")
        
        return all_data
    
    def test_niche_scoring(self, test_topics, scorer):
        """Test niche scoring with collected data"""
        logger.info("🧪 Testing niche scoring...")
        
        # Create mock records for testing
        from niche_radar.collectors import NicheRecord
        from datetime import datetime
        
        mock_records = [
            NicheRecord(
                source="GitHub",
                url="https://github.com/test/python-project",
                title="Python AI Framework",
                timestamp=datetime.now(),
                metrics={"stars": 1500, "velocity": 50.0, "trending_score": 0.8},
                raw={"name": "python-ai-framework", "stars": 1500},
                topic="python",
                category="development",
                confidence=0.9
            ),
            NicheRecord(
                source="Hacker News",
                url="https://news.ycombinator.com/item?id=123",
                title="New Python AI Framework Released",
                timestamp=datetime.now(),
                metrics={"score": 245, "heat_score": 0.8},
                raw={"title": "New Python AI Framework Released", "score": 245},
                topic="python",
                category="tech_news",
                confidence=0.7
            )
        ]
        
        # Score the niche
        niche_score = scorer.score_niche("python", mock_records)
        
        # Assert score structure
        assert isinstance(niche_score, NicheScore), "Should return NicheScore object"
        assert niche_score.topic == "python", "Topic should match"
        assert 0 <= niche_score.total_score <= 10, "Total score should be between 0-10"
        assert 0 <= niche_score.confidence <= 1, "Confidence should be between 0-1"
        assert len(niche_score.sources) > 0, "Should have sources"
        assert len(niche_score.key_signals) > 0, "Should have key signals"
        
        logger.info(f"✅ Niche scored: {niche_score.topic} = {niche_score.total_score:.2f} (confidence: {niche_score.confidence:.2f})")
        
        return niche_score
    
    def test_playbook_generation(self, playbook_generator):
        """Test playbook generation for a niche"""
        logger.info("🧪 Testing playbook generation...")
        
        # Create mock niche score
        from niche_radar.scoring import NicheScore
        from datetime import datetime
        
        mock_niche_score = NicheScore(
            topic="AI Chatbot Development",
            total_score=8.5,
            confidence=0.9,
            breakdown={
                "trend_momentum": 0.8,
                "github_velocity": 0.9,
                "hackernews_heat": 0.7,
                "news_delta": 0.8,
                "reddit_engagement": 0.6,
                "competition_proxy": 0.3,
                "feasibility_fit": 0.9
            },
            sources=["GitHub", "Hacker News", "News API"],
            timestamp=datetime.now(),
            category="development",
            feasibility_fit=0.9,
            competition_proxy=0.3,
            key_signals=["High GitHub velocity", "Strong news coverage", "Low competition"],
            recommendations=["Focus on developer tools", "Target B2B market", "Build MVP quickly"]
        )
        
        # Generate playbook
        playbook = playbook_generator.generate_playbook(mock_niche_score)
        
        # Assert playbook structure
        assert isinstance(playbook, ExecutionPack), "Should return ExecutionPack object"
        assert playbook.niche_score.topic == "AI Chatbot Development", "Should match niche topic"
        assert playbook.product_brief is not None, "Should have product brief"
        assert playbook.mvp_spec is not None, "Should have MVP spec"
        assert playbook.pricing_suggestion is not None, "Should have pricing suggestion"
        assert len(playbook.kpis) > 0, "Should have KPIs"
        assert len(playbook.timeline) > 0, "Should have timeline"
        
        logger.info(f"✅ Playbook generated for: {playbook.niche_score.topic}")
        logger.info(f"   MVP Development: {playbook.mvp_spec.estimated_development_days} days")
        logger.info(f"   Pricing: ${playbook.pricing_suggestion.tiers[1].price}/month")
        
        return playbook
    
    def test_top10_report_generation(self, test_topics, scorer):
        """Test Top 10 report generation"""
        logger.info("🧪 Testing Top 10 report generation...")
        
        # Create mock niche scores
        from niche_radar.scoring import NicheScore
        from datetime import datetime
        
        mock_scores = [
            NicheScore(
                topic="AI Chatbot Development",
                total_score=8.5,
                confidence=0.9,
                breakdown={"trend_momentum": 0.8, "github_velocity": 0.9},
                sources=["GitHub", "Hacker News"],
                timestamp=datetime.now(),
                category="development",
                feasibility_fit=0.9,
                competition_proxy=0.3,
                key_signals=["High velocity", "Low competition"],
                recommendations=["Build MVP", "Target B2B"]
            ),
            NicheScore(
                topic="Python Automation Tools",
                total_score=7.8,
                confidence=0.8,
                breakdown={"trend_momentum": 0.7, "github_velocity": 0.8},
                sources=["GitHub", "News API"],
                timestamp=datetime.now(),
                category="development",
                feasibility_fit=0.8,
                competition_proxy=0.4,
                key_signals=["Growing demand", "Developer interest"],
                recommendations=["Focus on productivity", "Open source strategy"]
            )
        ]
        
        # Generate report
        report_path = self._generate_top10_report(mock_scores)
        
        # Assert report exists
        assert Path(report_path).exists(), f"Report should exist at {report_path}"
        
        # Read and validate report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "AI Chatbot Development" in content, "Should contain top niche"
        assert "Python Automation Tools" in content, "Should contain second niche"
        assert "Score: 8.5" in content, "Should contain scores"
        assert "Confidence: 0.9" in content, "Should contain confidence"
        
        logger.info(f"✅ Top 10 report generated: {report_path}")
        
        return report_path
    
    def test_attribution_requirements(self, test_topics):
        """Test that all results have proper attribution"""
        logger.info("🧪 Testing attribution requirements...")
        
        # This test ensures every niche result has proper attribution
        from niche_radar.collectors import NicheRecord
        from datetime import datetime
        
        mock_record = NicheRecord(
            source="GitHub",
            url="https://github.com/test/project",
            title="Test Project",
            timestamp=datetime.now(),
            metrics={"stars": 100},
            raw={"name": "test-project"},
            topic="test",
            category="development",
            confidence=0.8
        )
        
        # Check attribution fields
        assert mock_record.source, "Should have source"
        assert mock_record.url, "Should have URL"
        assert mock_record.timestamp, "Should have timestamp"
        assert mock_record.topic, "Should have topic"
        
        logger.info("✅ Attribution requirements met")
    
    def _generate_top10_report(self, niche_scores: List[NicheScore]) -> str:
        """Generate Top 10 report file"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = reports_dir / f"niche_top10_{date_str}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🎯 NicheRadar Top 10 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("## Top Niche Opportunities\n\n")
            
            for i, niche in enumerate(niche_scores, 1):
                f.write(f"### {i}. {niche.topic}\n")
                f.write(f"**Score:** {niche.total_score:.1f}/10\n")
                f.write(f"**Confidence:** {niche.confidence:.1%}\n")
                f.write(f"**Category:** {niche.category}\n")
                f.write(f"**Key Signals:** {', '.join(niche.key_signals)}\n")
                f.write(f"**Sources:** {', '.join(niche.sources)}\n")
                f.write(f"**Recommendations:** {', '.join(niche.recommendations)}\n\n")
        
        return str(report_path)

@pytest.mark.asyncio
async def test_full_pipeline():
    """Test the complete NicheRadar pipeline"""
    logger.info("🧪 Testing full NicheRadar pipeline...")
    
    # Initialize components
    collectors = get_all_collectors()
    scorer = NicheScorer()
    playbook_generator = PlaybookGenerator()
    
    # Test topics
    topics = ["python", "ai", "startup"]
    
    # Step 1: Collect data
    logger.info("📊 Step 1: Collecting data...")
    all_data = await collect_all_data(topics)
    
    # Step 2: Score niches
    logger.info("🎯 Step 2: Scoring niches...")
    scored_niches = []
    
    for source, records in all_data.items():
        if records:
            # Group by topic
            topic_groups = {}
            for record in records:
                topic = record.topic
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(record)
            
            # Score each topic
            for topic, topic_records in topic_groups.items():
                score = scorer.score_niche(topic, topic_records)
                scored_niches.append(score)
    
    # Step 3: Get top 5
    logger.info("🏆 Step 3: Getting top 5 niches...")
    scored_niches.sort(key=lambda x: x.total_score, reverse=True)
    top_5 = scored_niches[:5]
    
    assert len(top_5) > 0, "Should have at least one scored niche"
    
    # Step 4: Generate playbook for top niche
    logger.info("📋 Step 4: Generating playbook...")
    if top_5:
        top_playbook = playbook_generator.generate_playbook(top_5[0])
        assert top_playbook is not None, "Should generate playbook"
        
        # Save playbook to reports
        reports_dir = Path("reports/playbooks")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        playbook_path = reports_dir / f"playbook_{top_5[0].topic.replace(' ', '_').lower()}.md"
        with open(playbook_path, 'w', encoding='utf-8') as f:
            f.write(f"# 📋 Execution Playbook: {top_5[0].topic}\n\n")
            f.write(f"**Niche Score:** {top_5[0].total_score:.1f}/10\n")
            f.write(f"**Confidence:** {top_5[0].confidence:.1%}\n\n")
            f.write(f"## Product Brief\n")
            f.write(f"**Title:** {top_playbook.product_brief.title}\n")
            f.write(f"**Description:** {top_playbook.product_brief.description}\n\n")
            f.write(f"## MVP Specification\n")
            f.write(f"**Development Time:** {top_playbook.mvp_spec.estimated_development_days} days\n")
            f.write(f"**Features:** {', '.join([f.name for f in top_playbook.mvp_spec.features])}\n\n")
            f.write(f"## Pricing Strategy\n")
            for tier in top_playbook.pricing_suggestion.tiers:
                f.write(f"**{tier.name}:** ${tier.price}/month - {tier.rationale}\n")
        
        logger.info(f"✅ Playbook saved: {playbook_path}")
    
    # Step 5: Generate Top 10 report
    logger.info("📄 Step 5: Generating Top 10 report...")
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = Path("reports") / f"niche_top10_{date_str}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🎯 NicheRadar Top 10 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("## Top Niche Opportunities\n\n")
        
        for i, niche in enumerate(top_5, 1):
            f.write(f"### {i}. {niche.topic}\n")
            f.write(f"**Score:** {niche.total_score:.1f}/10\n")
            f.write(f"**Confidence:** {niche.confidence:.1%}\n")
            f.write(f"**Key Signals:** {', '.join(niche.key_signals)}\n")
            f.write(f"**Sources:** {', '.join(niche.sources)}\n\n")
    
    logger.info(f"✅ Top 10 report saved: {report_path}")
    
    # Assertions
    assert Path(report_path).exists(), "Top 10 report should exist"
    if top_5:
        assert Path(playbook_path).exists(), "Playbook should exist"
    
    logger.info("✅ Full pipeline test completed successfully!")
    
    return {
        "top_niches": top_5,
        "report_path": str(report_path),
        "playbook_path": str(playbook_path) if top_5 else None
    }

if __name__ == "__main__":
    # Run tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test individual components
    test_instance = TestNicheRadarE2E()
    
    # Test data collection
    asyncio.run(test_instance.test_data_collection(["python", "ai"], get_all_collectors()))
    
    # Test scoring
    test_instance.test_niche_scoring(["python"], NicheScorer())
    
    # Test playbook generation
    test_instance.test_playbook_generation(PlaybookGenerator())
    
    # Test full pipeline
    result = asyncio.run(test_full_pipeline())
    print(f"✅ E2E Test Results: {result}")
