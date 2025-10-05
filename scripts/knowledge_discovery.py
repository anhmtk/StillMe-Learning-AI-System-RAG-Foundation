#!/usr/bin/env python3
"""
StillMe IPC Knowledge Discovery System
Tự động tìm kiến thức mới từ web, RSS, documents
"""

import logging
import sys
import time
import requests
import feedparser
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.alerting.alerting_system import AlertingSystem
from stillme_core.learning.proposals_manager import ProposalsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
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
                    "info",
                )

            return discovered_count

        except Exception as e:
            logger.error(f"❌ Knowledge discovery failed: {e}")
            return 0

    def _discover_tech_trends(self) -> list[dict[str, Any]]:
        """Khám phá xu hướng công nghệ từ GitHub và Hacker News"""
        logger.info("📱 Discovering tech trends from real sources...")

        trends = []

        try:
            # GitHub Trending Repositories
            logger.info("🔍 Fetching GitHub trending repositories...")
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": "created:>2024-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10,
                },
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                for repo in data.get("items", [])[:5]:
                    # Calculate quality score based on stars and activity
                    stars = repo.get("stargazers_count", 0)
                    quality_score = min(0.95, max(0.6, stars / 1000))

                    trends.append(
                        {
                            "title": f"GitHub Trend: {repo['name']}",
                            "description": repo.get(
                                "description", "No description available"
                            )[:200],
                            "source": "github",
                            "priority": "high" if stars > 1000 else "medium",
                            "quality_score": quality_score,
                            "url": repo.get("html_url", ""),
                            "stars": stars,
                            "language": repo.get("language", "Unknown"),
                        }
                    )

                logger.info(f"✅ Found {len(trends)} trending GitHub repositories")
            else:
                logger.warning(f"GitHub API returned status {response.status_code}")

        except Exception as e:
            logger.warning(f"GitHub API failed: {e}")

        # Rate limiting
        time.sleep(1)

        try:
            # Hacker News Top Stories
            logger.info("🔍 Fetching Hacker News top stories...")
            hn_response = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10
            )

            if hn_response.status_code == 200:
                top_story_ids = hn_response.json()[:5]

                for story_id in top_story_ids:
                    try:
                        story_response = requests.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                            timeout=10,
                        )

                        if story_response.status_code == 200:
                            story = story_response.json()
                            if story and story.get("type") == "story":
                                # Calculate quality score based on score and comments
                                score = story.get("score", 0)
                                comments = story.get("descendants", 0)
                                quality_score = min(
                                    0.9, max(0.5, (score + comments) / 100)
                                )

                                trends.append(
                                    {
                                        "title": f"HN: {story.get('title', 'Untitled')}",
                                        "description": story.get(
                                            "url", "No URL available"
                                        ),
                                        "source": "hackernews",
                                        "priority": "high" if score > 100 else "medium",
                                        "quality_score": quality_score,
                                        "url": story.get("url", ""),
                                        "score": score,
                                        "comments": comments,
                                    }
                                )

                        # Rate limiting for individual story requests
                        time.sleep(0.2)

                    except Exception as e:
                        logger.warning(f"Failed to fetch HN story {story_id}: {e}")
                        continue

                logger.info(
                    f"✅ Found {len([t for t in trends if t['source'] == 'hackernews'])} Hacker News stories"
                )
            else:
                logger.warning(
                    f"Hacker News API returned status {hn_response.status_code}"
                )

        except Exception as e:
            logger.warning(f"Hacker News API failed: {e}")

        logger.info(f"📊 Total tech trends discovered: {len(trends)}")
        return trends

    def _discover_ai_news(self) -> list[dict[str, Any]]:
        """Khám phá tin tức AI/ML từ arXiv RSS và AI blogs"""
        logger.info("🤖 Discovering AI/ML news from real sources...")

        ai_topics = []

        try:
            # arXiv RSS Feed for AI papers
            logger.info("🔍 Fetching arXiv AI papers...")
            arxiv_feed = feedparser.parse("http://export.arxiv.org/rss/cs.AI")

            if arxiv_feed.bozo == 0:  # No parsing errors
                for entry in arxiv_feed.entries[:5]:
                    # Extract paper title and abstract
                    title = entry.get("title", "Untitled")
                    description = entry.get("summary", "No abstract available")

                    # Calculate quality score based on title keywords
                    quality_keywords = [
                        "transformer",
                        "neural",
                        "deep learning",
                        "machine learning",
                        "llm",
                        "gpt",
                    ]
                    quality_score = 0.6
                    for keyword in quality_keywords:
                        if (
                            keyword.lower() in title.lower()
                            or keyword.lower() in description.lower()
                        ):
                            quality_score += 0.1

                    quality_score = min(0.95, quality_score)

                    ai_topics.append(
                        {
                            "title": f"arXiv: {title}",
                            "description": description[:300] + "..."
                            if len(description) > 300
                            else description,
                            "source": "arxiv",
                            "priority": "high" if quality_score > 0.8 else "medium",
                            "quality_score": quality_score,
                            "url": entry.get("link", ""),
                            "published": entry.get("published", ""),
                        }
                    )

                logger.info(f"✅ Found {len(ai_topics)} arXiv AI papers")
            else:
                logger.warning("arXiv RSS feed parsing failed")

        except Exception as e:
            logger.warning(f"arXiv RSS failed: {e}")

        # Rate limiting
        time.sleep(1)

        try:
            # AI News from Reddit r/MachineLearning
            logger.info("🔍 Fetching AI news from Reddit...")
            reddit_response = requests.get(
                "https://www.reddit.com/r/MachineLearning/hot.json",
                headers={"User-Agent": "StillMe-IPC/1.0"},
                timeout=10,
            )

            if reddit_response.status_code == 200:
                data = reddit_response.json()
                posts = data.get("data", {}).get("children", [])[:3]

                for post in posts:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "Untitled")
                    selftext = post_data.get("selftext", "")
                    score = post_data.get("score", 0)
                    comments = post_data.get("num_comments", 0)

                    # Calculate quality score based on engagement
                    quality_score = min(0.9, max(0.5, (score + comments) / 50))

                    ai_topics.append(
                        {
                            "title": f"Reddit ML: {title}",
                            "description": selftext[:200] + "..."
                            if len(selftext) > 200
                            else selftext or "No description",
                            "source": "reddit_ml",
                            "priority": "high" if score > 50 else "medium",
                            "quality_score": quality_score,
                            "url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "score": score,
                            "comments": comments,
                        }
                    )

                logger.info(
                    f"✅ Found {len([t for t in ai_topics if t['source'] == 'reddit_ml'])} Reddit ML posts"
                )
            else:
                logger.warning(
                    f"Reddit API returned status {reddit_response.status_code}"
                )

        except Exception as e:
            logger.warning(f"Reddit API failed: {e}")

        logger.info(f"📊 Total AI/ML topics discovered: {len(ai_topics)}")
        return ai_topics

    def _discover_programming_trends(self) -> list[dict[str, Any]]:
        """Khám phá xu hướng lập trình từ Stack Overflow và GitHub"""
        logger.info("💻 Discovering programming trends from real sources...")

        prog_topics = []

        try:
            # Stack Overflow API - Trending Questions
            logger.info("🔍 Fetching Stack Overflow trending questions...")
            so_response = requests.get(
                "https://api.stackexchange.com/2.3/questions",
                params={
                    "order": "desc",
                    "sort": "activity",
                    "site": "stackoverflow",
                    "tagged": "python;javascript;java;rust;go",
                    "pagesize": 10,
                },
                timeout=15,
            )

            if so_response.status_code == 200:
                data = so_response.json()
                questions = data.get("items", [])[:5]

                for question in questions:
                    title = question.get("title", "Untitled")
                    tags = question.get("tags", [])
                    score = question.get("score", 0)
                    view_count = question.get("view_count", 0)
                    answer_count = question.get("answer_count", 0)

                    # Calculate quality score based on engagement
                    quality_score = min(
                        0.9, max(0.5, (score + view_count / 100 + answer_count) / 20)
                    )

                    # Determine priority based on tags and engagement
                    priority = (
                        "high"
                        if any(
                            tag in ["python", "javascript", "rust", "go"]
                            for tag in tags
                        )
                        and score > 10
                        else "medium"
                    )

                    prog_topics.append(
                        {
                            "title": f"SO: {title}",
                            "description": f"Tags: {', '.join(tags[:3])} | Score: {score} | Views: {view_count}",
                            "source": "stackoverflow",
                            "priority": priority,
                            "quality_score": quality_score,
                            "url": question.get("link", ""),
                            "tags": tags,
                            "score": score,
                            "views": view_count,
                        }
                    )

                logger.info(f"✅ Found {len(prog_topics)} Stack Overflow questions")
            else:
                logger.warning(
                    f"Stack Overflow API returned status {so_response.status_code}"
                )

        except Exception as e:
            logger.warning(f"Stack Overflow API failed: {e}")

        # Rate limiting
        time.sleep(1)

        try:
            # GitHub Trending Programming Languages
            logger.info("🔍 Fetching GitHub trending programming languages...")
            github_response = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": "language:python OR language:javascript OR language:rust OR language:go created:>2024-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5,
                },
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15,
            )

            if github_response.status_code == 200:
                data = github_response.json()
                repos = data.get("items", [])

                for repo in repos:
                    name = repo.get("name", "Untitled")
                    description = repo.get("description", "No description")
                    language = repo.get("language", "Unknown")
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)

                    # Calculate quality score based on stars and forks
                    quality_score = min(0.95, max(0.6, (stars + forks) / 500))

                    prog_topics.append(
                        {
                            "title": f"GitHub {language}: {name}",
                            "description": description[:200] + "..."
                            if len(description) > 200
                            else description,
                            "source": "github_programming",
                            "priority": "high" if stars > 500 else "medium",
                            "quality_score": quality_score,
                            "url": repo.get("html_url", ""),
                            "language": language,
                            "stars": stars,
                            "forks": forks,
                        }
                    )

                logger.info(
                    f"✅ Found {len([t for t in prog_topics if t['source'] == 'github_programming'])} GitHub programming repos"
                )
            else:
                logger.warning(
                    f"GitHub API returned status {github_response.status_code}"
                )

        except Exception as e:
            logger.warning(f"GitHub programming API failed: {e}")

        logger.info(f"📊 Total programming trends discovered: {len(prog_topics)}")
        return prog_topics

    def _create_proposal_from_topic(self, topic: dict[str, Any]) -> bool:
        """Tạo proposal từ topic được khám phá"""
        try:
            # Kiểm tra xem topic đã được tạo chưa
            if topic["title"] in self.discovered_topics:
                return False

            self.discovered_topics.add(topic["title"])

            # Tạo learning objectives dựa trên title và source
            learning_objectives = [
                f"Understand {topic['title']} concepts and principles",
                "Apply knowledge in practical scenarios",
                "Build real-world projects using the technology",
            ]

            # Customize objectives based on source
            if topic.get("source") == "github":
                learning_objectives.append("Contribute to open source projects")
            elif topic.get("source") == "arxiv":
                learning_objectives.append("Implement research findings in practice")
            elif topic.get("source") == "stackoverflow":
                learning_objectives.append("Solve real-world programming problems")

            # Tạo prerequisites dựa trên source
            prerequisites = [
                "Basic programming knowledge",
                "Understanding of computer science fundamentals",
            ]

            # Add source-specific prerequisites
            if topic.get("source") in ["github", "stackoverflow"]:
                prerequisites.append("Experience with version control systems")
            elif topic.get("source") == "arxiv":
                prerequisites.append("Understanding of mathematical concepts")

            # Tạo expected outcomes
            expected_outcomes = [
                f"Mastery of {topic['title']}",
                "Ability to implement practical solutions",
                "Enhanced technical skills and knowledge",
            ]

            # Add source-specific outcomes
            if topic.get("source") == "github":
                expected_outcomes.append("Ability to contribute to open source")
            elif topic.get("source") == "arxiv":
                expected_outcomes.append("Understanding of cutting-edge research")
            elif topic.get("source") == "stackoverflow":
                expected_outcomes.append("Problem-solving skills in programming")

            # Tạo risk assessment dựa trên quality score và priority
            complexity = "high" if topic["quality_score"] > 0.8 else "medium"
            time_commitment = (
                "high" if topic["priority"] in ["high", "critical"] else "medium"
            )

            risk_assessment = {
                "complexity": complexity,
                "time_commitment": time_commitment,
                "prerequisites": "medium",
                "practical_value": "high" if topic["quality_score"] > 0.7 else "medium",
            }

            # Estimate duration based on source and quality
            base_duration = 240  # 4 hours default
            if topic.get("source") == "arxiv":
                base_duration = 360  # 6 hours for research papers
            elif topic.get("source") == "github":
                base_duration = 180  # 3 hours for code repositories
            elif topic.get("source") == "stackoverflow":
                base_duration = 120  # 2 hours for Q&A content

            # Adjust based on quality score
            duration_multiplier = 0.8 + (topic["quality_score"] * 0.4)  # 0.8 to 1.2
            estimated_duration = int(base_duration * duration_multiplier)

            # Tạo proposal
            proposal = self.proposals_manager.create_proposal(
                title=topic["title"],
                description=topic["description"],
                learning_objectives=learning_objectives,
                prerequisites=prerequisites,
                expected_outcomes=expected_outcomes,
                estimated_duration=estimated_duration,
                quality_score=topic["quality_score"],
                source=f"knowledge_discovery_{topic['source']}",
                priority=topic["priority"],
                risk_assessment=risk_assessment,
                created_by="knowledge_discovery",
            )

            logger.info(
                f"✅ Created proposal: {proposal.title} (Source: {topic['source']}, Quality: {topic['quality_score']:.2f})"
            )
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
