#!/usr/bin/env python3
"""
StillMe IPC Knowledge Discovery System
Tự động tìm kiến thức mới từ web, RSS, documents
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.alerting.alerting_system import AlertingSystem
from stillme_core.learning.proposals_manager import ProposalsManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeDiscovery:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
        self.discovered_topics = set()

    def discover_knowledge(self):
        """Khám phá kiến thức mới từ nhiều nguồn"""
        logger.info("🔍 StillMe IPC Knowledge Discovery")
        logger.info("==========================================")
        logger.info("🌐 Discovering new knowledge from various sources...")

        discovered_count = 0

        try:
            # 1. Discover from trending tech topics
            tech_topics = self._discover_tech_trends()
            for topic in tech_topics:
                if self._create_proposal_from_topic(topic):
                    discovered_count += 1

            # 2. Discover from AI/ML news
            ai_topics = self._discover_ai_news()
            for topic in ai_topics:
                if self._create_proposal_from_topic(topic):
                    discovered_count += 1

            # 3. Discover from programming trends
            prog_topics = self._discover_programming_trends()
            for topic in prog_topics:
                if self._create_proposal_from_topic(topic):
                    discovered_count += 1

            logger.info("🎉 Knowledge discovery completed!")
            logger.info(f"📊 Total new proposals created: {discovered_count}")

            if discovered_count > 0:
                self.alerting_system.send_alert(
                    "New Knowledge Discovered",
                    f"StillMe IPC has discovered {discovered_count} new learning opportunities!\n\n"
                    f"🔍 Sources checked:\n"
                    f"• Tech trends\n"
                    f"• AI/ML news\n"
                    f"• Programming trends\n\n"
                    f"Please review the new proposals in the dashboard!",
                    "info"
                )

            return discovered_count

        except Exception as e:
            logger.error(f"❌ Knowledge discovery failed: {e}")
            return 0

    def _discover_tech_trends(self) -> list[dict[str, Any]]:
        """Khám phá xu hướng công nghệ"""
        logger.info("📱 Discovering tech trends...")

        # Mock data - trong thực tế sẽ crawl từ GitHub, Stack Overflow, etc.
        tech_trends = [
            {
                "title": "Quantum Computing Fundamentals",
                "description": "Learn the basics of quantum computing, quantum algorithms, and quantum programming with Qiskit",
                "source": "tech_trends",
                "priority": "high",
                "quality_score": 0.92
            },
            {
                "title": "Edge Computing and IoT",
                "description": "Understanding edge computing architectures, IoT protocols, and real-time data processing",
                "source": "tech_trends",
                "priority": "medium",
                "quality_score": 0.88
            },
            {
                "title": "Blockchain Development",
                "description": "Learn blockchain fundamentals, smart contracts, and decentralized applications (DApps)",
                "source": "tech_trends",
                "priority": "high",
                "quality_score": 0.90
            }
        ]

        return tech_trends

    def _discover_ai_news(self) -> list[dict[str, Any]]:
        """Khám phá tin tức AI/ML"""
        logger.info("🤖 Discovering AI/ML news...")

        # Mock data - trong thực tế sẽ crawl từ AI news sites
        ai_topics = [
            {
                "title": "Large Language Models (LLMs) Architecture",
                "description": "Deep dive into transformer architecture, attention mechanisms, and training large language models",
                "source": "ai_news",
                "priority": "critical",
                "quality_score": 0.95
            },
            {
                "title": "Computer Vision with Deep Learning",
                "description": "Advanced computer vision techniques using CNNs, R-CNNs, and modern architectures like Vision Transformers",
                "source": "ai_news",
                "priority": "high",
                "quality_score": 0.91
            },
            {
                "title": "Reinforcement Learning Applications",
                "description": "Practical applications of RL in robotics, gaming, and autonomous systems",
                "source": "ai_news",
                "priority": "medium",
                "quality_score": 0.87
            }
        ]

        return ai_topics

    def _discover_programming_trends(self) -> list[dict[str, Any]]:
        """Khám phá xu hướng lập trình"""
        logger.info("💻 Discovering programming trends...")

        # Mock data - trong thực tế sẽ crawl từ GitHub, Stack Overflow trends
        prog_topics = [
            {
                "title": "Rust Systems Programming",
                "description": "Learn Rust programming language for systems programming, memory safety, and performance",
                "source": "programming_trends",
                "priority": "high",
                "quality_score": 0.93
            },
            {
                "title": "WebAssembly (WASM) Development",
                "description": "Building high-performance web applications using WebAssembly",
                "source": "programming_trends",
                "priority": "medium",
                "quality_score": 0.89
            },
            {
                "title": "Microservices Architecture",
                "description": "Design and implement scalable microservices architectures with modern tools",
                "source": "programming_trends",
                "priority": "high",
                "quality_score": 0.90
            }
        ]

        return prog_topics

    def _create_proposal_from_topic(self, topic: dict[str, Any]) -> bool:
        """Tạo proposal từ topic được khám phá"""
        try:
            # Kiểm tra xem topic đã được tạo chưa
            if topic["title"] in self.discovered_topics:
                return False

            self.discovered_topics.add(topic["title"])

            # Tạo learning objectives dựa trên title
            learning_objectives = [
                f"Understand {topic['title']} concepts and principles",
                "Apply knowledge in practical scenarios",
                "Build real-world projects using the technology"
            ]

            # Tạo prerequisites
            prerequisites = [
                "Basic programming knowledge",
                "Understanding of computer science fundamentals"
            ]

            # Tạo expected outcomes
            expected_outcomes = [
                f"Mastery of {topic['title']}",
                "Ability to implement practical solutions",
                "Enhanced technical skills and knowledge"
            ]

            # Tạo risk assessment
            risk_assessment = {
                "complexity": "high" if topic["priority"] in ["high", "critical"] else "medium",
                "time_commitment": "high" if topic["priority"] in ["high", "critical"] else "medium",
                "prerequisites": "medium",
                "practical_value": "high"
            }

            # Tạo proposal
            proposal = self.proposals_manager.create_proposal(
                title=topic["title"],
                description=topic["description"],
                learning_objectives=learning_objectives,
                prerequisites=prerequisites,
                expected_outcomes=expected_outcomes,
                estimated_duration=240,  # 4 hours default
                quality_score=topic["quality_score"],
                source=topic["source"],
                priority=topic["priority"],
                risk_assessment=risk_assessment,
                created_by="knowledge_discovery"
            )

            logger.info(f"✅ Created proposal: {proposal.title}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create proposal for {topic['title']}: {e}")
            return False

def main():
    """Main function"""
    discovery = KnowledgeDiscovery()

    try:
        discovered_count = discovery.discover_knowledge()

        if discovered_count > 0:
            print("\n🎉 Knowledge discovery completed!")
            print(f"📊 Found {discovered_count} new learning opportunities")
            print("📋 Check dashboard to review proposals: http://localhost:8506")
        else:
            print("\nℹ️ No new knowledge discovered at this time.")
            print("💡 Try running again later or add manual knowledge.")

    except Exception as e:
        logger.error(f"❌ Knowledge discovery failed: {e}")
        print(f"\n❌ Knowledge discovery failed: {e}")

if __name__ == "__main__":
    main()
